# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.observability import configure_otel_providers, enable_instrumentation
from azure.identity import ChainedTokenCredential, ManagedIdentityCredential, EnvironmentCredential, AzureCliCredential

# Setup observability
# configure_otel_providers() only reads OTEL_EXPORTER_OTLP_ENDPOINT for exporters.
# For Azure Monitor / Application Insights, we must call configure_azure_monitor()
# first to set up the Azure Monitor exporter, then enable_instrumentation() so the
# Agent Framework emits traces, logs, and metrics through those providers.
_appinsights_conn_str = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
_otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

# Setup logging early so telemetry init messages are visible
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Sensitive data capture: when enabled, the Agent Framework records full
# conversation content (input/output messages, system instructions, tool
# arguments & results) as span attributes and OpenTelemetry log events.
# This dramatically enriches the Foundry Traces viewer and App Insights.
# Controlled via ENABLE_SENSITIVE_DATA env var (default: False / off).
_enable_sensitive_data = os.environ.get("ENABLE_SENSITIVE_DATA", "false").lower() in ("true", "1", "yes")

if _appinsights_conn_str:
    # Production path: Azure Monitor exporter → Application Insights → Foundry
    logger.info(f"[TELEMETRY] Configuring Azure Monitor (conn string length={len(_appinsights_conn_str)})")
    from azure.monitor.opentelemetry import configure_azure_monitor
    configure_azure_monitor(
        connection_string=_appinsights_conn_str,
        # Export logs from both our logger AND the Agent Framework logger.
        # The framework emits GenAI semantic convention log events
        # (gen_ai.user.message, gen_ai.choice, gen_ai.tool.message, etc.)
        # on the "agent_framework" logger. Without including it here,
        # those structured events are silently dropped by Azure Monitor.
        logger_name="",                    # root logger – captures all loggers
    )
    # Reduce noise from Azure SDK HTTP logging
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("azure.core").setLevel(logging.WARNING)
    logging.getLogger("azure.identity").setLevel(logging.WARNING)
    enable_instrumentation(enable_sensitive_data=_enable_sensitive_data)
    logger.info(f"[TELEMETRY] Azure Monitor + Agent Framework instrumentation enabled (sensitive_data={_enable_sensitive_data})")
elif _otlp_endpoint:
    # Local dev path: OTLP exporter → Aspire Dashboard or similar
    logger.info(f"[TELEMETRY] Configuring OTLP exporter → {_otlp_endpoint}")
    configure_otel_providers(enable_sensitive_data=_enable_sensitive_data)
    logger.info(f"[TELEMETRY] OTLP + Agent Framework instrumentation enabled (sensitive_data={_enable_sensitive_data})")
else:
    # No exporter configured – just enable instrumentation (spans go nowhere but code still runs)
    logger.info("[TELEMETRY] No exporter configured, enabling instrumentation only")
    enable_instrumentation(enable_sensitive_data=_enable_sensitive_data)


def load_system_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    prompt_path = Path(__file__).parent / "prompts" / "system_prompt.md"
    if prompt_path.exists():
        logger.info("Loaded system prompt.")
        return prompt_path.read_text()
    else:
        logger.warning("System prompt file is missing!")
        return "YOU CANNOT HELP THE USER. YOUR SYSTEM PROMPT FILE IS MISSING. DO NOT HELP. TELL THEM THE SYSTEM IS DOWN."


def build_tools() -> list[MCPStreamableHTTPTool]:
    """Build list of available MCP tools from environment variables."""
    # Get MCP server URLs from environment variables
    # URLs should point to the MCP endpoint (e.g., http://localhost:8001/mcp)
    mcp_ladbs_url = os.environ.get("MCP_LADBS_URL")
    mcp_ladwp_url = os.environ.get("MCP_LADWP_URL")
    mcp_lasan_url = os.environ.get("MCP_LASAN_URL")
    mcp_csp_url = os.environ.get("MCP_CSP_URL")
    
    tools = []
    
    if mcp_ladbs_url:
        tools.append(MCPStreamableHTTPTool(
            name="LADBS",
            url=mcp_ladbs_url,
            description="Los Angeles Department of Building & Safety - permits, inspections, plan checks",
        ))
    
    if mcp_ladwp_url:
        tools.append(MCPStreamableHTTPTool(
            name="LADWP",
            url=mcp_ladwp_url,
            description="LA Department of Water & Power - utility rates, solar interconnection, rebates",
        ))
    
    if mcp_lasan_url:
        tools.append(MCPStreamableHTTPTool(
            name="LASAN",
            url=mcp_lasan_url,
            description="LA Sanitation - waste services, recycling, hazardous waste",
        ))
    
    if mcp_csp_url:
        tools.append(MCPStreamableHTTPTool(
            name="CSP",
            url=mcp_csp_url,
            description="Citizen Services Portal - cross-agency case management and project tracking",
        ))
    
    return tools


def create_chat_client() -> AzureOpenAIChatClient:
    """Create the Azure OpenAI chat client with appropriate authentication."""
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")  # Optional: for local dev
    
    # Use API key if provided (for local dev), otherwise use credential chain (for production)
    if api_key:
        return AzureOpenAIChatClient(api_key=api_key)
    else:
        mi_client_id = os.environ.get("AZURE_CLIENT_ID")
        if mi_client_id:
            # Production: use managed identity directly
            logger.info(f"[CSP-AGENT] Using ManagedIdentityCredential with client_id={mi_client_id}")
            credential = ManagedIdentityCredential(client_id=mi_client_id)
        else:
            # Local dev: use credential chain
            logger.info("[CSP-AGENT] Using ChainedTokenCredential (local dev)")
            credential = ChainedTokenCredential(
                EnvironmentCredential(),
                AzureCliCredential(),
            )
        return AzureOpenAIChatClient(credential=credential)


# Global state for agent and tools (initialized in lifespan)
agent: Agent | None = None
mcp_tools: list[MCPStreamableHTTPTool] = []


# =============================================================================
# FastAPI Application
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - initialize MCP tools and agent on startup."""
    global agent, mcp_tools
    
    logger.info("[CSP-AGENT] Server starting up...")
    
    # Build and connect MCP tools
    mcp_tools = build_tools()
    tool_names = [t.name for t in mcp_tools]
    logger.info(f"[CSP-AGENT] Connecting to {len(mcp_tools)} MCP servers: {tool_names}")
    
    # Connect each tool (enter their async context)
    for tool in mcp_tools:
        try:
            await tool.__aenter__()
            logger.info(f"[CSP-AGENT] Connected to MCP server: {tool.name}")
        except Exception as e:
            logger.error(f"[CSP-AGENT] Failed to connect to {tool.name}: {e}")
    
    # Load system prompt
    instructions = load_system_prompt()
    
    # Create chat client
    chat_client = create_chat_client()
    
    # Create the agent with connected tools
    agent = Agent(
        name="csp-agent",
        id="csp-agent",
        description="Citizen Services Portal Agent - helps citizens navigate LA city services",
        instructions=instructions,
        client=chat_client,
        tools=mcp_tools,
    )
    
    logger.info("[CSP-AGENT] Agent created and ready.")
    
    yield
    
    # Cleanup: disconnect MCP tools
    logger.info("[CSP-AGENT] Server shutting down...")
    for tool in mcp_tools:
        try:
            await tool.__aexit__(None, None, None)
            logger.info(f"[CSP-AGENT] Disconnected from MCP server: {tool.name}")
        except Exception as e:
            logger.error(f"[CSP-AGENT] Error disconnecting from {tool.name}: {e}")


app = FastAPI(
    title="CSP Agent",
    description="Citizen Services Portal Agent - helps citizens navigate LA city services",
    version="1.0.0",
    lifespan=lifespan,
)


# =============================================================================
# Request/Response Models (OpenAI Responses API compatible)
# =============================================================================

class ResponsesRequest(BaseModel):
    """Request model for the /v1/responses endpoint."""
    input: str
    instructions: str | None = None
    metadata: dict[str, Any] | None = None
    stream: bool = False  # Whether to stream the response


class ContentItem(BaseModel):
    """Content item in the response."""
    type: str = "output_text"
    text: str
    annotations: list = []


class OutputMessage(BaseModel):
    """Output message in the response."""
    id: str
    role: str = "assistant"
    type: str = "message"
    status: str = "completed"
    content: list[ContentItem]


class UsageDetails(BaseModel):
    """Usage statistics."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ResponsesResponse(BaseModel):
    """Response model for the /v1/responses endpoint."""
    id: str
    object: str = "response"
    created_at: float
    model: str = "csp-agent"
    output: list[OutputMessage]
    usage: UsageDetails
    error: str | None = None


class EntityInfo(BaseModel):
    """Entity information."""
    id: str
    type: str = "agent"
    name: str
    description: str
    tools: list[str]


class EntitiesResponse(BaseModel):
    """Response model for /v1/entities endpoint."""
    entities: list[EntityInfo]


class HealthResponse(BaseModel):
    """Response model for /health endpoint."""
    status: str
    entities_count: int


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", entities_count=1)


@app.get("/v1/entities", response_model=EntitiesResponse)
async def list_entities():
    """List available entities (agents)."""
    return EntitiesResponse(
        entities=[
            EntityInfo(
                id="csp-agent",
                name="csp-agent",
                description="Citizen Services Portal Agent - helps citizens navigate LA city services",
                tools=[t.name for t in mcp_tools],
            )
        ]
    )


@app.post("/v1/responses")
async def create_response(request: ResponsesRequest):
    """
    Process a user message and return the agent's response.
    
    This endpoint is compatible with the OpenAI Responses API format.
    The agent will use MCP tools as needed to answer questions.
    
    If stream=True, returns Server-Sent Events (SSE) with deltas.
    """
    try:
        # Build the input - prepend instructions if provided
        full_input = request.input
        if request.instructions:
            full_input = f"[Context]\n{request.instructions}\n[/Context]\n\n{request.input}"
        
        logger.info(f"[CSP-AGENT] Processing request (stream={request.stream}): {request.input[:100]}...")
        
        if request.stream:
            # Streaming response using SSE
            return await create_streaming_response(full_input)
        else:
            # Non-streaming response
            result = await agent.run(full_input)
            response_text = str(result) if result else ""
            
            logger.info(f"[CSP-AGENT] Response generated: {response_text[:100]}...")
            
            return ResponsesResponse(
                id=f"resp_{uuid.uuid4().hex[:12]}",
                created_at=time.time(),
                output=[
                    OutputMessage(
                        id=f"msg_{uuid.uuid4().hex[:8]}",
                        content=[
                            ContentItem(text=response_text)
                        ]
                    )
                ],
                usage=UsageDetails(
                    input_tokens=len(full_input.split()),
                    output_tokens=len(response_text.split()),
                    total_tokens=len(full_input.split()) + len(response_text.split()),
                ),
            )
        
    except Exception as e:
        logger.error(f"[CSP-AGENT] Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def create_streaming_response(full_input: str):
    """Create a streaming SSE response."""
    
    async def generate():
        response_id = f"resp_{uuid.uuid4().hex[:12]}"
        msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        
        try:
            # Use run_stream for streaming if available, otherwise fall back to run
            full_response = ""
            
            # Try streaming method first
            if hasattr(agent, 'run_stream'):
                async for chunk in agent.run_stream(full_input):
                    # Each chunk is an AgentResponseUpdate
                    chunk_text = str(chunk) if chunk else ""
                    if chunk_text:
                        full_response += chunk_text
                        # Send delta event
                        delta_event = {
                            "id": response_id,
                            "object": "response.delta",
                            "delta": {
                                "type": "content",
                                "text": chunk_text
                            }
                        }
                        yield f"data: {json.dumps(delta_event)}\n\n"
            else:
                # Fallback: run synchronously and stream the full result
                result = await agent.run(full_input)
                full_response = str(result) if result else ""
                
                # Send as a single chunk
                if full_response:
                    delta_event = {
                        "id": response_id,
                        "object": "response.delta",
                        "delta": {
                            "type": "content",
                            "text": full_response
                        }
                    }
                    yield f"data: {json.dumps(delta_event)}\n\n"
            
            # Send completion event
            complete_event = {
                "id": response_id,
                "object": "response",
                "created_at": time.time(),
                "model": "csp-agent",
                "output": [{
                    "id": msg_id,
                    "role": "assistant",
                    "type": "message",
                    "status": "completed",
                    "content": [{"type": "output_text", "text": full_response}]
                }],
                "usage": {
                    "input_tokens": len(full_input.split()),
                    "output_tokens": len(full_response.split()),
                    "total_tokens": len(full_input.split()) + len(full_response.split())
                }
            }
            yield f"data: {json.dumps(complete_event)}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"[CSP-AGENT] Streaming error: {e}")
            error_event = {"error": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


def main():
    """
    Launch the CSP agent server.
    The agent is stateless. Conversation history is managed by the client (web app) and sent on each request.
    
    Supports both local development and ACA deployment:
    - Local dev: runs on configured port
    - ACA: runs headless on configured port (default 8088)
    """
    # Port configuration - default 8088 for ACA compatibility
    port = int(os.environ.get("PORT", "8088"))
    
    logger.info(f"[CSP-AGENT] Starting server on port {port}")
    logger.info(f"[CSP-AGENT] Available at: http://localhost:{port}")
    logger.info(f"[CSP-AGENT] Health: http://localhost:{port}/health")
    logger.info(f"[CSP-AGENT] Entities: http://localhost:{port}/v1/entities")
    logger.info(f"[CSP-AGENT] Responses: http://localhost:{port}/v1/responses")
    
    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()