"""Thread repository for CosmosDB operations.

This repository reads from the 'threads' collection which contains serialized
agent thread state. The agent (via its thread_repository) writes to this collection,
and the web-app reads from it to display message history.

Note: The 'messages' collection is deprecated - messages are now stored within
the serialized thread state in the 'threads' collection.
"""

from typing import Any, Dict, List, Optional

from azure.cosmos import exceptions as cosmos_exceptions

from ..client import get_container


class ThreadRepository:
    """Repository for reading thread state from CosmosDB.
    
    The web-app uses this to read message history for display.
    The agent writes to this collection via its thread_repository.
    """

    def __init__(self):
        """Initialize the thread repository."""
        self.container_name = "threads"

    async def get_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a thread document by ID.

        Args:
            thread_id: The thread/conversation/project ID.

        Returns:
            The thread document if found, None otherwise.
        """
        container = await get_container(self.container_name)
        
        try:
            item = await container.read_item(
                item=thread_id,
                partition_key=thread_id,
            )
            return item
        except cosmos_exceptions.CosmosResourceNotFoundError:
            return None

    async def get_messages_from_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Extract messages from a serialized thread.

        Args:
            thread_id: The thread/conversation/project ID.

        Returns:
            List of message dictionaries with 'role' and 'content' keys,
            ordered chronologically. Returns empty list if thread not found.
        """
        thread_doc = await self.get_thread(thread_id)
        
        if not thread_doc:
            return []
        
        return self._extract_messages(thread_doc)
    
    def _extract_messages(self, thread_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract messages from a thread document.
        
        Handles the serialized thread format:
        {
            "serialized_thread": {
                "chat_message_store_state": {
                    "messages": [
                        {
                            "role": {"value": "user"},
                            "contents": [{"type": "text", "text": "..."}]
                        }
                    ]
                }
            }
        }

        Args:
            thread_doc: The thread document from CosmosDB.

        Returns:
            List of message dictionaries in UI-friendly format.
        """
        messages = []
        
        serialized = thread_doc.get("serialized_thread") or thread_doc.get("serializedThread", {})
        store_state = (
            serialized.get("chat_message_store_state")
            or serialized.get("chatMessageStoreState")
            or {}
        )
        raw_messages = store_state.get("messages", [])
        
        for msg in raw_messages:
            # Extract role
            role_obj = msg.get("role", {})
            role = role_obj.get("value", "user") if isinstance(role_obj, dict) else str(role_obj)
            
            # Extract text content from contents/content arrays (supports legacy + Responses API shapes)
            contents = msg.get("contents") or msg.get("content") or []
            text_parts = []
            if isinstance(contents, str):
                text_parts.append(contents)
            elif isinstance(contents, list):
                for content in contents:
                    if isinstance(content, dict):
                        content_type = content.get("type")
                        if content_type in ("text", "input_text", "output_text"):
                            text = content.get("text", "")
                            if text:
                                text_parts.append(text)
                        elif "text" in content and isinstance(content.get("text"), str):
                            text_parts.append(content["text"])
            
            # Fallbacks for alternate shapes
            if not text_parts:
                if isinstance(msg.get("text"), str):
                    text_parts.append(msg["text"])
                elif isinstance(msg.get("content"), str):
                    text_parts.append(msg["content"])
            
            content = "\n".join([part for part in text_parts if part])
            
            # Build UI-friendly message dict
            messages.append({
                "id": msg.get("message_id") or msg.get("id") or f"msg-{len(messages)}",
                "role": role,
                "content": content,
                "project_id": thread_doc.get("id"),
            })
        
        return messages
