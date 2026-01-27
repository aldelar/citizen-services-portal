"""CosmosDB-backed ChatMessageStore for persistent conversation history."""

import logging
import os
from datetime import datetime, timezone
from typing import Any, MutableMapping, Optional, Sequence
from uuid import uuid4

from agent_framework import ChatMessage, ChatMessageStore
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential

logger = logging.getLogger(__name__)


class CosmosChatMessageStore(ChatMessageStore):
    """ChatMessageStore implementation backed by Azure CosmosDB.
    
    This store persists messages to CosmosDB, allowing conversation history
    to be maintained across agent restarts and shared with other components
    (like the web UI) that read from the same container.
    
    The store adapts between the agent's ChatMessage format and the CosmosDB
    document format used by the web application.
    """
    
    def __init__(
        self,
        conversation_id: str,
        cosmos_client: CosmosClient,
        database_name: str,
        container_name: str = "messages",
        messages: Optional[Sequence[ChatMessage]] = None,
    ):
        """Initialize the CosmosDB chat message store.
        
        Args:
            conversation_id: The conversation/project ID for partitioning.
            cosmos_client: The CosmosDB async client.
            database_name: Name of the database.
            container_name: Name of the messages container.
            messages: Optional initial messages (for compatibility).
        """
        super().__init__(messages)
        self._conversation_id = conversation_id
        self._cosmos_client = cosmos_client
        self._database_name = database_name
        self._container_name = container_name
        self._loaded = False
    
    async def _get_container(self):
        """Get the CosmosDB container."""
        database = self._cosmos_client.get_database_client(self._database_name)
        return database.get_container_client(self._container_name)
    
    async def _load_messages_if_needed(self) -> None:
        """Load messages from CosmosDB on first access."""
        if self._loaded:
            return
        
        try:
            container = await self._get_container()
            
            # Query messages for this conversation, ordered by timestamp
            query = """
                SELECT * FROM c 
                WHERE c.projectId = @project_id 
                ORDER BY c.timestamp ASC
            """
            parameters = [{"name": "@project_id", "value": self._conversation_id}]
            
            items = container.query_items(
                query=query,
                parameters=parameters,
            )
            
            # Convert CosmosDB documents to ChatMessage objects
            loaded_messages = []
            async for item in items:
                chat_msg = self._cosmos_doc_to_chat_message(item)
                if chat_msg:
                    loaded_messages.append(chat_msg)
            
            # Prepend loaded messages to any existing messages
            self.messages = loaded_messages + self.messages
            self._loaded = True
            
            logger.info(
                f"Loaded {len(loaded_messages)} messages for conversation {self._conversation_id}"
            )
            
        except Exception as e:
            logger.error(f"Error loading messages from CosmosDB: {e}")
            self._loaded = True  # Don't retry on error
    
    def _cosmos_doc_to_chat_message(self, doc: dict) -> Optional[ChatMessage]:
        """Convert a CosmosDB document to a ChatMessage.
        
        Args:
            doc: CosmosDB document with role, content, etc.
            
        Returns:
            ChatMessage or None if conversion fails.
        """
        try:
            role = doc.get("role", "user")
            content = doc.get("content", "")
            message_id = doc.get("id")
            
            return ChatMessage(
                role=role,
                text=content,
                message_id=message_id,
            )
        except Exception as e:
            logger.warning(f"Failed to convert CosmosDB doc to ChatMessage: {e}")
            return None
    
    def _chat_message_to_cosmos_doc(self, message: ChatMessage) -> dict:
        """Convert a ChatMessage to a CosmosDB document.
        
        Args:
            message: The ChatMessage to convert.
            
        Returns:
            Dictionary suitable for CosmosDB storage.
        """
        # Extract role value (handle both Role object and string)
        role = message.role.value if hasattr(message.role, "value") else str(message.role)
        
        # Get text content
        text = message.text or ""
        
        # Use existing message_id or generate new one
        message_id = message.message_id or str(uuid4())
        
        return {
            "id": message_id,
            "projectId": self._conversation_id,  # camelCase for web-app compatibility
            "role": role,
            "content": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    async def add_messages(self, messages: Sequence[ChatMessage]) -> None:
        """Add messages to the store and persist to CosmosDB.
        
        Args:
            messages: Sequence of ChatMessage objects to add.
        """
        # First ensure we've loaded existing messages
        await self._load_messages_if_needed()
        
        # Add to in-memory list
        self.messages.extend(messages)
        
        # Persist each message to CosmosDB
        try:
            container = await self._get_container()
            
            for message in messages:
                doc = self._chat_message_to_cosmos_doc(message)
                await container.upsert_item(doc)
                logger.debug(f"Saved message {doc['id']} to CosmosDB")
                
        except Exception as e:
            logger.error(f"Error saving messages to CosmosDB: {e}")
            # Messages are still in memory, so agent can continue
    
    async def list_messages(self) -> list[ChatMessage]:
        """Get all messages from the store.
        
        Returns:
            List of ChatMessage objects in chronological order.
        """
        await self._load_messages_if_needed()
        return self.messages


# Singleton CosmosDB client for the agent process
_cosmos_client: Optional[CosmosClient] = None
_credential: Optional[DefaultAzureCredential] = None


async def _get_cosmos_client() -> CosmosClient:
    """Get or create the shared CosmosDB client."""
    global _cosmos_client, _credential
    
    if _cosmos_client is None:
        endpoint = os.environ.get("AGENT_COSMOS_ENDPOINT")
        if not endpoint:
            raise ValueError("AGENT_COSMOS_ENDPOINT environment variable is not set")
        
        _credential = DefaultAzureCredential()
        _cosmos_client = CosmosClient(endpoint, credential=_credential)
    
    return _cosmos_client


def create_cosmos_chat_store_factory():
    """Create a factory function for CosmosChatMessageStore instances.
    
    Returns:
        A factory function that creates CosmosChatMessageStore for a conversation_id.
    """
    database_name = os.environ.get("AGENT_COSMOS_DATABASE", "citizen-services")
    container_name = os.environ.get("AGENT_COSMOS_CONTAINER", "messages")
    
    async def factory(conversation_id: str) -> CosmosChatMessageStore:
        """Create a CosmosChatMessageStore for the given conversation.
        
        Args:
            conversation_id: The conversation/project ID.
            
        Returns:
            CosmosChatMessageStore instance.
        """
        client = await _get_cosmos_client()
        return CosmosChatMessageStore(
            conversation_id=conversation_id,
            cosmos_client=client,
            database_name=database_name,
            container_name=container_name,
        )
    
    return factory
