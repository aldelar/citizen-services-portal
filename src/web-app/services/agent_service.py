"""Agent service for communicating with the CSP Agent."""

import httpx
from typing import Optional
from config import settings
from azure.identity.aio import DefaultAzureCredential


class AgentService:
    """Service for interacting with the CSP Agent."""
    
    # Responses API version aligned with spec
    API_VERSION = "2025-11-15-preview"
    
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
    
    async def _get_auth_token(self) -> Optional[str]:
        """Get AAD access token for AI Foundry."""
        if not self.use_auth:
            return None
        
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        
        token = await self._credential.get_token("https://ai.azure.com/.default")
        return token.token
    
    def _build_url(self, path: str) -> str:
        """Build full URL with api-version query parameter."""
        separator = "&" if "?" in path else "?"
        return f"{self.base_url}{path}{separator}api-version={self.API_VERSION}"
    
    async def send_message(
        self,
        message: str,
        messages: list[dict] | None = None,
        stream: bool = False,
    ) -> tuple[str, Optional[str]]:
        """Send a message to the CSP Agent and get a response.
        
        Args:
            message: The user's message.
            messages: Optional list of previous messages for context.
                      Each message should have 'role' and 'content' keys.
            stream: Whether to stream the response (not yet implemented).
            
        Returns:
            Tuple of (response_text, None).
            
        Raises:
            Exception: If the agent fails to respond.
        """
        payload = {
            "stream": stream,
        }
        
        if messages:
            payload["input"] = self._build_input_text(messages)
        else:
            payload["input"] = message
        
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
        import json
        return f"[Raw response]: {json.dumps(data, indent=2)[:500]}"
    
    async def send_message_stream(
        self,
        message: str,
        messages: list[dict] | None = None,
    ):
        """Send a message and stream the response.
        
        Args:
            message: The current user message.
            messages: Optional list of previous messages for context.
                      Each message should have 'role' and 'content' keys.
        
        Yields:
            str: Chunks of the response text.
        """
        import json
        
        # Build input with conversation history if provided
        if messages:
            # Format as array of messages for Responses API
            # The messages list should already include the current user message
            payload = {
                "input": self._build_input_text(messages),
                "stream": True,
            }
        else:
            payload = {
                "input": message,
                "stream": True,
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

    def _build_input_text(self, messages: list[dict]) -> str:
        """Flatten message history into a single input string.
        
        Messages are structured as:
        - Regular conversation (user/assistant) comes first
        - System messages (user context, current plan) are appended at the end
        """
        conversation_lines = []
        system_lines = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not role or not content:
                continue
            
            if role == "system":
                system_lines.append(content)
            elif role == "user":
                conversation_lines.append(f"User: {content}")
            else:
                conversation_lines.append(f"Assistant: {content}")
        
        lines = ["Conversation so far:"]
        lines.extend(conversation_lines)
        
        # Add system context at the end
        if system_lines:
            lines.append("\n--- Context ---")
            lines.extend(system_lines)
        
        # Add plan update instructions
        lines.append("""
--- Instructions ---
BEFORE creating a plan, use queryKB tools to research requirements, fees, and processes. Do this automatically - don't make "research" a plan step.

When you create or update a project plan, include the plan as a JSON code block with the identifier 'json:plan'.

CRITICAL: Every step MUST have a "depends_on" array. Think carefully about what must complete BEFORE each step can start.
- First steps have depends_on: []
- Most steps depend on at least one prior step
- Use step IDs (e.g., "P1", "U1") to reference dependencies

Format:
```json:plan
{
  "id": "plan-id",
  "title": "Plan Title",
  "status": "active",
  "steps": [
    {
      "id": "P1",
      "title": "Submit electrical permit application",
      "agency": "LADBS",
      "status": "not_started",
      "action_type": "automated",
      "depends_on": []
    },
    {
      "id": "P2",
      "title": "Hire licensed electrician",
      "agency": "LADBS",
      "status": "not_started",
      "action_type": "user_action",
      "depends_on": []
    },
    {
      "id": "U1",
      "title": "Request LADWP service upgrade",
      "agency": "LADWP",
      "status": "not_started",
      "action_type": "user_action",
      "depends_on": ["P1"]
    },
    {
      "id": "I1",
      "title": "Schedule and pass LADBS inspection",
      "agency": "LADBS",
      "status": "not_started",
      "action_type": "user_action",
      "depends_on": ["P2", "U1"]
    },
    {
      "id": "F1",
      "title": "LADWP finalizes service connection",
      "agency": "LADWP",
      "status": "not_started",
      "action_type": "information",
      "depends_on": ["I1"]
    }
  ]
}
```

action_type values:
- "automated" = Agent can execute directly via tools (🤖)
- "user_action" = User must take action like call, email, visit (👤)  
- "information" = Waiting period or external process (ℹ️)

Dependency logic for above example:
- P1 (submit permit) → no dependencies, can start immediately
- P2 (hire electrician) → no dependencies, can run parallel to P1
- U1 (utility request) → depends on P1 (permit must be submitted first)
- I1 (inspection) → depends on P2 AND U1 (work done + utility ready)
- F1 (finalize) → depends on I1 (inspection must pass)

DO NOT include "research" steps - you do research automatically using queryKB before presenting the plan.
Update the plan whenever there's new information that affects scope, steps, dependencies, or when a step status changes.
Respond to the latest user message using the context above.""")
        
        return "\n".join(lines)
    
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
