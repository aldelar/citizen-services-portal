# Copyright (c) Microsoft. All rights reserved.

import os
from pathlib import Path

from agent_framework import HostedMCPTool
from agent_framework.azure import AzureOpenAIChatClient
from azure.ai.agentserver.agentframework import from_agent_framework  # pyright: ignore[reportUnknownVariableType]
from azure.identity import DefaultAzureCredential, ChainedTokenCredential, ManagedIdentityCredential, EnvironmentCredential, AzureCliCredential

# Configure OpenTelemetry - reads environment variables automatically:
#   - APPLICATIONINSIGHTS_CONNECTION_STRING (for Azure Monitor)
#   - OTEL_EXPORTER_OTLP_ENDPOINT (for Aspire Dashboard/OTLP)
#   - ENABLE_INSTRUMENTATION=true (required)
#   - OTEL_SERVICE_NAME (defaults to agent_framework)
from agent_framework.observability import configure_otel_providers
configure_otel_providers()


def load_system_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    prompt_path = Path(__file__).parent / "prompts" / "system_prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text()
    
    # Fallback to a basic prompt if file not found
    return (
        "You are the Citizen Services Portal Agent (CSP Agent), an AI assistant for "
        "City of Los Angeles government services. You help citizens navigate services across "
        "LADBS (Building & Safety), LADWP (Water & Power), LASAN (Sanitation), and other departments."
    )


def create_agent():
    """Create the CSP Agent with connections to all MCP servers."""
    
    # Get MCP server URLs from environment variables
    mcp_ladbs_url = os.environ.get("MCP_LADBS_URL")
    mcp_ladwp_url = os.environ.get("MCP_LADWP_URL")
    mcp_lasan_url = os.environ.get("MCP_LASAN_URL")
    mcp_reporting_url = os.environ.get("MCP_REPORTING_URL")
    
    # Build list of available MCP tools
    tools = []
    
    if mcp_ladbs_url:
        tools.append(HostedMCPTool(
            name="LADBS",
            url=mcp_ladbs_url,
        ))
    
    if mcp_ladwp_url:
        tools.append(HostedMCPTool(
            name="LADWP",
            url=mcp_ladwp_url,
        ))
    
    if mcp_lasan_url:
        tools.append(HostedMCPTool(
            name="LASAN",
            url=mcp_lasan_url,
        ))
    
    if mcp_reporting_url:
        tools.append(HostedMCPTool(
            name="Reporting",
            url=mcp_reporting_url,
        ))
    
    # Get Azure OpenAI configuration from environment
    azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
    deployment_name = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4.1")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")  # Optional: for local dev
    
    # Construct model URL
    model_url = f"{azure_openai_endpoint}/openai/deployments/{deployment_name}"
    
    # Load system prompt
    instructions = load_system_prompt()
    
    # Create the agent using Azure OpenAI Chat Client
    # Use API key if provided (for local dev), otherwise use credential chain (for production)
    if api_key:
        client = AzureOpenAIChatClient(api_key=api_key)
    else:
        # Use a credential chain for authentication
        # For local dev: AzureCliCredential (uses 'az login')
        # For production (Azure): ManagedIdentityCredential
        mi_client_id = os.environ.get("AZURE_CLIENT_ID")
        credential = ChainedTokenCredential(
            EnvironmentCredential(),  # For explicit env var auth
            AzureCliCredential(),  # For local dev with 'az login'
            ManagedIdentityCredential(client_id=mi_client_id)  # For production in Azure (user-assigned MI)
        )
        client = AzureOpenAIChatClient(credential=credential)
    
    agent = client.create_agent(
        name="csp-agent",
        instructions=instructions,
        model_url=model_url,
        tools=tools,
    )
    
    return agent


def main():
    """Run the CSP Agent as a hosted agent.
    
    The agent is stateless. Conversation history is managed by the client
    (web app) and sent on each request.
    """
    agent = create_agent()
    
    # Run the hosted agent without server-side thread persistence
    from_agent_framework(agent).run()


if __name__ == "__main__":
    main()