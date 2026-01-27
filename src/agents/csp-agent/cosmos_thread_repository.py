"""CosmosDB-backed AgentThreadRepository for persistent conversation threads.

This module provides a thread repository that stores serialized agent threads
in Azure CosmosDB. Each conversation (identified by conversation_id/project_id)
gets a single document in the 'threads' container containing the full serialized
thread state.

Architecture Notes:
- The hosted agent server calls get() before agent.run() to load existing threads
- The hosted agent server calls set() after agent.run() to persist updated threads
- The web-app reads from the 'threads' collection to display message history
- The agent itself is stateless - it doesn't know about CosmosDB

Future Optimization:
- Current approach stores entire thread as one document (simple but grows over time)
- Can be optimized to store messages separately and reconstruct on load
- See project docs for the optimized architecture design
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from agent_framework import AgentProtocol, ChatMessageStore
from azure.ai.agentserver.agentframework.persistence import SerializedAgentThreadRepository
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential

logger = logging.getLogger(__name__)


class CosmosAgentThreadRepository(SerializedAgentThreadRepository):
    """Thread repository that stores serialized threads in CosmosDB.
    
    Each conversation_id maps to one document in the 'threads' container.
    The document contains the full serialized thread state including all messages.
    
    Document structure:
    {
        "id": "<conversation_id>",
        "serialized_thread": {
            "type": "agent_thread_state",
            "service_thread_id": null,
            "chat_message_store_state": {
                "messages": [...]
            }
        },
        "updated_at": "2026-01-26T12:00:00Z"
    }
    """
    
    def __init__(
        self,
        agent: AgentProtocol,
        cosmos_client: CosmosClient,
        database_name: str,
        container_name: str = "threads",
    ):
        """Initialize the CosmosDB thread repository.
        
        Args:
            agent: The agent instance (used for deserialization).
            cosmos_client: The async CosmosDB client.
            database_name: Name of the database.
            container_name: Name of the container for threads (default: "threads").
        """
        super().__init__(agent)
        self._cosmos_client = cosmos_client
        self._database_name = database_name
        self._container_name = container_name
    
    def _get_container(self):
        """Get the CosmosDB container client."""
        database = self._cosmos_client.get_database_client(self._database_name)
        return database.get_container_client(self._container_name)
    
    async def read_from_storage(self, conversation_id: str) -> Optional[Any]:
        """Read the serialized thread from CosmosDB.
        
        Args:
            conversation_id: The conversation/project ID.
            
        Returns:
            The serialized thread dict if found, None otherwise.
        """
        try:
            container = self._get_container()
            item = await container.read_item(
                item=conversation_id,
                partition_key=conversation_id,
            )
            serialized_thread = item.get("serialized_thread")
            
            if serialized_thread:
                logger.info(f"Loaded thread for conversation {conversation_id}")
                return serialized_thread
            
            return None
            
        except CosmosResourceNotFoundError:
            logger.debug(f"No existing thread found for conversation {conversation_id}")
            return None
        except Exception as e:
            logger.error(f"Error reading thread from CosmosDB: {e}")
            raise
    
    async def write_to_storage(self, conversation_id: str, serialized_thread: Any) -> None:
        """Write the serialized thread to CosmosDB.
        
        Args:
            conversation_id: The conversation/project ID.
            serialized_thread: The serialized thread state to save.
        """
        try:
            container = self._get_container()
            
            doc = {
                "id": conversation_id,
                "serialized_thread": serialized_thread,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await container.upsert_item(doc)
            logger.info(f"Saved thread for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error writing thread to CosmosDB: {e}")
            raise


# Module-level singleton for CosmosDB client
_cosmos_client: Optional[CosmosClient] = None
_credential: Optional[DefaultAzureCredential] = None


async def _get_cosmos_client() -> CosmosClient:
    """Get or create the shared async CosmosDB client."""
    global _cosmos_client, _credential
    
    if _cosmos_client is None:
        endpoint = os.environ.get("AGENT_COSMOS_ENDPOINT")
        if not endpoint:
            raise ValueError("AGENT_COSMOS_ENDPOINT environment variable is not set")
        
        _credential = DefaultAzureCredential()
        _cosmos_client = CosmosClient(endpoint, credential=_credential)
    
    return _cosmos_client


def create_cosmos_thread_repository(agent: AgentProtocol) -> CosmosAgentThreadRepository:
    """Create a CosmosDB-backed thread repository.
    
    This is a synchronous factory that creates the repository instance.
    The actual CosmosDB client initialization happens lazily on first use.
    
    Args:
        agent: The agent instance (needed for thread deserialization).
        
    Returns:
        CosmosAgentThreadRepository instance.
    """
    endpoint = os.environ.get("AGENT_COSMOS_ENDPOINT")
    if not endpoint:
        raise ValueError("AGENT_COSMOS_ENDPOINT environment variable is not set")
    
    database_name = os.environ.get("AGENT_COSMOS_DATABASE", "citizen-services")
    container_name = os.environ.get("AGENT_COSMOS_THREADS_CONTAINER", "threads")
    
    # Create credential and client synchronously
    credential = DefaultAzureCredential()
    cosmos_client = CosmosClient(endpoint, credential=credential)
    
    return CosmosAgentThreadRepository(
        agent=agent,
        cosmos_client=cosmos_client,
        database_name=database_name,
        container_name=container_name,
    )
