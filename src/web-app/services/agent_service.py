"""Agent service for communicating with the CSP Agent."""

import httpx
from typing import Optional
from config import settings


class AgentService:
    """Service for interacting with the CSP Agent."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize the agent service.
        
        Args:
            base_url: Base URL of the CSP Agent. Defaults to settings.CSP_AGENT_URL.
        """
        self.base_url = (base_url or settings.CSP_AGENT_URL).rstrip('/')
        self.timeout = 120.0  # Agent responses can take time (longer for multi-tool calls)
    
    async def send_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        stream: bool = False,
    ) -> str:
        """Send a message to the CSP Agent and get a response.
        
        Args:
            message: The user's message.
            conversation_id: Optional conversation/thread ID for context.
            stream: Whether to stream the response (not yet implemented).
            
        Returns:
            The agent's response text.
            
        Raises:
            Exception: If the agent fails to respond.
        """
        payload = {
            "input": message,
            "stream": stream,
        }
        
        # Add conversation context if available (uses Foundry format)
        if conversation_id:
            payload["conversation"] = {"id": conversation_id}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/responses",
                json=payload,
            )
            response.raise_for_status()
            
            # Parse response - the agent returns OpenAI Responses API format
            data = response.json()
            
            # Extract text from OpenAI Responses API format
            # Format: {"id": "...", "output": [{"type": "message", "content": [{"type": "output_text", "text": "..."}]}]}
            return self._extract_response_text(data)
    
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
        conversation_id: str | None = None,
        messages: list[dict] | None = None,
    ):
        """Send a message and stream the response.
        
        Args:
            message: The current user message.
            conversation_id: Optional conversation/thread ID.
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
            input_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role and content:
                    input_messages.append({"role": role, "content": content})
            payload = {
                "input": input_messages,
                "stream": True,
            }
        else:
            payload = {
                "input": message,
                "stream": True,
            }
        
        # Add conversation context if available (uses Foundry format)
        if conversation_id:
            payload["conversation"] = {"id": conversation_id}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/responses",
                json=payload,
            ) as response:
                response.raise_for_status()
                
                # Always try to parse as SSE, regardless of content-type
                buffer = ""
                conversation_id_yielded = False
                
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
                                    
                                    # Extract conversation_id from response.created event
                                    if not conversation_id_yielded:
                                        conv_id = self._extract_conversation_id(data)
                                        if conv_id:
                                            yield {"_conversation_id": conv_id}
                                            conversation_id_yielded = True
                                    
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
                                
                                # Extract conversation_id
                                if not conversation_id_yielded:
                                    conv_id = self._extract_conversation_id(data)
                                    if conv_id:
                                        yield {"_conversation_id": conv_id}
                                        conversation_id_yielded = True
                                
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
        
        # Check in response object
        response_obj = data.get("response")
        if isinstance(response_obj, dict):
            conversation = response_obj.get("conversation")
            if isinstance(conversation, dict):
                return conversation.get("id")
        
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
        _agent_service = AgentService()
    return _agent_service
