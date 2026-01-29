"""Message repository for CosmosDB operations."""

from datetime import datetime
from typing import List, Optional

from azure.cosmos import exceptions as cosmos_exceptions

from ..client import get_container
from ..models import Message


class MessageRepository:
    """Repository for message operations with pagination support."""

    def __init__(self):
        """Initialize the message repository."""
        self.container_name = "messages"

    async def append_message(self, message: Message) -> Message:
        """
        Append a new message to the database.

        Args:
            message: Message object to create.

        Returns:
            Message: The created message object.
        """
        container = await get_container(self.container_name)
        
        message_dict = message.model_dump(by_alias=True, mode="json")
        created_item = await container.create_item(body=message_dict)
        return Message.model_validate(created_item)

    async def get_messages(
        self,
        project_id: str,
        limit: int = 50,
        before: Optional[datetime] = None,
    ) -> List[Message]:
        """
        Get messages for a project with pagination support.

        Args:
            project_id: The project ID.
            limit: Maximum number of messages to return.
            before: Optional timestamp to get messages before this time.

        Returns:
            List[Message]: List of message objects ordered by timestamp descending.
        """
        container = await get_container(self.container_name)
        
        if before:
            query = """
                SELECT * FROM c 
                WHERE c.projectId = @projectId AND c.timestamp < @before
                ORDER BY c.timestamp DESC
                OFFSET 0 LIMIT @limit
            """
            parameters = [
                {"name": "@projectId", "value": project_id},
                {"name": "@before", "value": before.isoformat()},
                {"name": "@limit", "value": limit},
            ]
        else:
            query = """
                SELECT * FROM c 
                WHERE c.projectId = @projectId
                ORDER BY c.timestamp DESC
                OFFSET 0 LIMIT @limit
            """
            parameters = [
                {"name": "@projectId", "value": project_id},
                {"name": "@limit", "value": limit},
            ]
        
        items = []
        async for item in container.query_items(
            query=query,
            parameters=parameters,
            partition_key=project_id,
        ):
            items.append(Message.model_validate(item))
        
        return items

    async def count_messages(self, project_id: str) -> int:
        """
        Count the total number of messages for a project.

        Args:
            project_id: The project ID.

        Returns:
            int: The total number of messages.
        """
        container = await get_container(self.container_name)
        
        query = "SELECT VALUE COUNT(1) FROM c WHERE c.projectId = @projectId"
        parameters = [{"name": "@projectId", "value": project_id}]
        
        items = []
        async for item in container.query_items(
            query=query,
            parameters=parameters,
            partition_key=project_id,
        ):
            items.append(item)
        
        return items[0] if items else 0

    async def delete_message(self, message_id: str, project_id: str) -> bool:
        """
        Delete a message by ID and project ID (partition key).

        Args:
            message_id: The message ID.
            project_id: The project ID (partition key).

        Returns:
            bool: True if deleted successfully.
        """
        container = await get_container(self.container_name)
        
        try:
            await container.delete_item(item=message_id, partition_key=project_id)
            return True
        except cosmos_exceptions.CosmosResourceNotFoundError:
            return False
