"""Agent service for communicating with the CSP Agent.

Uses the OpenAI Responses API format for structured multi-turn conversations.
The agent is served via agent_framework.devui which exposes a /v1/responses endpoint.

IMPORTANT: The agent framework works best with string-based input format.
This service converts all messages and context into a single formatted string before sending
to the agent. See _build_input_string() for the conversion logic.
"""

import json
import httpx
from typing import Optional
from config import settings
from azure.identity.aio import DefaultAzureCredential


class AgentService:
    """Service for interacting with the CSP Agent via Responses API.
    
    Uses string input format for best compatibility with agent framework.
    """
    
    # Default agent name - used to construct entity_id for devui server
    DEFAULT_AGENT_NAME = "csp-agent"
    
    def __init__(self, base_url: Optional[str] = None, use_auth: bool | None = None):
        """Initialize the agent service.
        
        Args:
            base_url: Base URL of the CSP Agent. Defaults to settings.CSP_AGENT_URL.
            use_auth: Whether to use AAD authentication (defaults to config).
        """
        self.base_url = (base_url or settings.CSP_AGENT_URL).rstrip('/')
        self.timeout = 120.0  # Agent responses can take time (longer for multi-tool calls)
        self.use_auth = settings.CSP_AGENT_USE_AUTH if use_auth is None else use_auth
        self._credential = None
        self._entity_id: str | None = None  # Cached entity_id from devui server
    
    async def _get_auth_token(self) -> Optional[str]:
        """Get AAD access token for AI Foundry."""
        if not self.use_auth:
            return None
        
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        
        token = await self._credential.get_token("https://ai.azure.com/.default")
        return token.token
    
    def _build_url(self, path: str) -> str:
        """Build full URL for the devui server."""
        return f"{self.base_url}/v1{path}"
    
    async def _get_entity_id(self) -> str:
        """Get the entity_id for the csp-agent from the devui server.
        
        The devui server assigns dynamic entity IDs. We need to query /v1/entities
        to find the correct ID for our agent.
        """
        if self._entity_id:
            return self._entity_id
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/v1/entities")
            response.raise_for_status()
            data = response.json()
            
            # Find the csp-agent entity
            for entity in data.get("entities", []):
                if entity.get("name") == self.DEFAULT_AGENT_NAME:
                    self._entity_id = entity["id"]
                    return self._entity_id
            
            # Fallback: use first agent entity if available
            for entity in data.get("entities", []):
                if entity.get("type") == "agent":
                    self._entity_id = entity["id"]
                    return self._entity_id
            
            raise ValueError(f"No agent entity found at {self.base_url}/v1/entities")
    
    def _build_input_string(self, messages: list[dict], instructions: str | None = None) -> str:
        """Build a single input string for the Responses API.
        
        This method converts all messages (system, user, assistant) into a single
        formatted string with [Context] blocks for system messages.
        
        Args:
            messages: List of messages with 'role' and 'content' keys.
            instructions: Optional context (user info, project ID, etc.)
            
        Returns:
            A single string containing the full conversation context.
        """
        parts = []
        
        # Collect all system context
        system_context_parts = []
        if instructions:
            system_context_parts.append(instructions)
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system" and content:
                system_context_parts.append(content)
        
        # Add system context at the beginning wrapped in [Context] tags
        if system_context_parts:
            parts.append("[Context]")
            parts.extend(system_context_parts)
            parts.append("[/Context]")
            parts.append("")  # blank line
        
        # Add conversation history as "Role: content" format
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if not role or not content:
                continue
            
            if role == "system":
                continue  # Already handled above
            elif role == "user":
                parts.append(f"User: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")
        
        return "\n".join(parts)
    
    async def send_message(
        self,
        message: str,
        messages: list[dict] | None = None,
        instructions: str | None = None,
        stream: bool = False,
    ) -> tuple[str, Optional[str]]:
        """Send a message to the CSP Agent and get a response.
        
        Args:
            message: The user's message (used if messages is None).
            messages: Optional list of previous messages for context.
                      Each message should have 'role' and 'content' keys.
            instructions: Optional system/developer instructions for context (embedded in input).
            stream: Whether to stream the response (not yet implemented).
            
        Returns:
            Tuple of (response_text, None).
            
        Raises:
            Exception: If the agent fails to respond.
        """
        # Build input string from messages
        if messages:
            input_string = self._build_input_string(messages, instructions)
        else:
            input_string = self._build_input_string([{"role": "user", "content": message}], instructions)
        
        # Get entity_id for the devui server
        entity_id = await self._get_entity_id()
        
        payload = {
            "input": input_string,
            "stream": stream,
            "metadata": {
                "entity_id": entity_id
            }
        }
        
        # Build headers with auth token if needed
        headers = {"Content-Type": "application/json"}
        token = await self._get_auth_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        url = self._build_url("/responses")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            
            # Parse response - the agent returns OpenAI Responses API format
            data = response.json()
            
            # Extract text from OpenAI Responses API format
            # Format: {"id": "...", "output": [{"type": "message", "content": [{"type": "output_text", "text": "..."}]}]}
            return self._extract_response_text(data), None
    
    def _extract_response_text(self, data) -> str:
        """Extract text content from OpenAI Responses API format."""
        if isinstance(data, str):
            return data
        
        if not isinstance(data, dict):
            return str(data)
        
        # Try OpenAI Responses API format: output[].content[].text
        if "output" in data and isinstance(data["output"], list):
            texts = []
            for item in data["output"]:
                if isinstance(item, dict):
                    # Check for content array (message type)
                    if "content" in item and isinstance(item["content"], list):
                        for content in item["content"]:
                            if isinstance(content, dict) and "text" in content:
                                texts.append(content["text"])
                    # Check for direct text field
                    elif "text" in item:
                        texts.append(item["text"])
            if texts:
                return "\n".join(texts)
        
        # Try simple field names
        for field in ["output_text", "response", "message", "content", "text", "output"]:
            if field in data:
                val = data[field]
                if isinstance(val, str):
                    return val
        
        # Fallback: return JSON for debugging
        return f"[Raw response]: {json.dumps(data, indent=2)[:500]}"
    
    async def send_message_stream(
        self,
        message: str,
        messages: list[dict] | None = None,
        instructions: str | None = None,
    ):
        """Send a message and stream the response.
        
        Args:
            message: The current user message (used if messages is None).
            messages: Optional list of previous messages for context.
                      Each message should have 'role' and 'content' keys.
            instructions: Optional system/developer instructions for context (embedded in input).
        
        Yields:
            str: Chunks of the response text.
        """
        # Build input string from messages
        if messages:
            input_string = self._build_input_string(messages, instructions)
        else:
            input_string = self._build_input_string([{"role": "user", "content": message}], instructions)
        
        # Get entity_id for the devui server
        entity_id = await self._get_entity_id()
        
        payload = {
            "input": input_string,
            "stream": True,
            "metadata": {
                "entity_id": entity_id
            }
        }
        
        # Build headers with auth token if needed
        headers = {"Content-Type": "application/json"}
        token = await self._get_auth_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        url = self._build_url("/responses")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                url,
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                
                # Remove any conversation-id side-channel for stateless app endpoint
                buffer = ""
                
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    # Process complete lines
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        
                        if not line:
                            continue
                        
                        # Handle SSE format: "data: {...}"
                        if line.startswith("data:"):
                            data_str = line[5:].strip()
                            if data_str and data_str != "[DONE]":
                                try:
                                    data = json.loads(data_str)
                                    
                                    text = self._extract_delta_text(data)
                                    if text:
                                        yield text
                                except json.JSONDecodeError:
                                    # Not JSON, might be raw text
                                    if data_str:
                                        yield data_str
                        elif line.startswith("{"):
                            # Direct JSON (non-SSE streaming)
                            try:
                                data = json.loads(line)
                                
                                text = self._extract_delta_text(data)
                                if text:
                                    yield text
                            except json.JSONDecodeError:
                                pass
                
                # Process remaining buffer - but skip final response events
                # (we already got the content via deltas)
                if buffer.strip():
                    # Don't process final buffer - it would duplicate content
                    pass

    def _extract_conversation_id(self, data: dict) -> str | None:
        """Extract conversation ID from streaming event.
        
        The conversation ID appears in the response.created event or
        in the conversation object of any event.
        """
        if not isinstance(data, dict):
            return None
        
        # Check for conversation object with id
        conversation = data.get("conversation")
        if isinstance(conversation, dict):
            conv_id = conversation.get("id")
            if conv_id:
                return conv_id
        elif isinstance(conversation, str):
            return conversation
        
        # Check common alternative keys
        for key in ("conversation_id", "conversationId"):
            conv_id = data.get(key)
            if isinstance(conv_id, str) and conv_id:
                return conv_id
        
        # Check in response object
        response_obj = data.get("response")
        if isinstance(response_obj, dict):
            conversation = response_obj.get("conversation")
            if isinstance(conversation, dict):
                return conversation.get("id")
            for key in ("conversation_id", "conversationId"):
                conv_id = response_obj.get(key)
                if isinstance(conv_id, str) and conv_id:
                    return conv_id
        
        return None
    
    def _extract_delta_text(self, data: dict) -> str:
        """Extract text from streaming delta event.
        
        Returns text ONLY for delta events, not for final/complete events.
        """
        if not isinstance(data, dict):
            return ""
        
        event_type = data.get("type", "")
        
        # Skip non-delta events (these contain the full response, causing duplication)
        # We only want incremental delta events
        if event_type in ("response.completed", "response.done", "response.output_text.done"):
            return ""
        
        # OpenAI Responses API streaming format
        # {"type": "response.output_text.delta", "delta": "text"}
        if event_type == "response.output_text.delta":
            delta = data.get("delta", "")
            if isinstance(delta, str):
                return delta
        
        # Alternative: delta object with text/content
        if "delta" in data:
            delta = data["delta"]
            if isinstance(delta, str):
                return delta
            if isinstance(delta, dict):
                return delta.get("text", "") or delta.get("content", "")
        
        # Check for output_text in various formats
        if "output_text" in data:
            return str(data["output_text"])
        
        # Direct text/content fields
        if "text" in data and isinstance(data["text"], str):
            return data["text"]
        if "content" in data and isinstance(data["content"], str):
            return data["content"]
        
        return ""
    
    async def health_check(self) -> bool:
        """Check if the agent is healthy.
        
        Returns:
            True if the agent is reachable, False otherwise.
        """
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
            except Exception:
                return False


# Singleton instance
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """Get the singleton agent service instance."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService(use_auth=settings.CSP_AGENT_USE_AUTH)
    return _agent_service
