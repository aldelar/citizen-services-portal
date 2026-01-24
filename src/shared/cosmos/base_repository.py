"""Base repository pattern for CosmosDB operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import uuid4

from azure.cosmos import exceptions as cosmos_exceptions
from pydantic import BaseModel

from .client import get_container
from .exceptions import ConflictError, NotFoundError

logger = logging.getLogger(__name__)

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """
    Base repository providing generic CRUD operations for CosmosDB.
    
    Subclasses should set:
        - container_name: str - The name of the container
        - model_class: Type[T] - The Pydantic model class for documents
        - partition_key_field: str - The field name used as partition key
    """

    container_name: str
    model_class: Type[T]
    partition_key_field: str = "id"

    async def create(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new document in the container.

        Args:
            item: Document data to create.

        Returns:
            Dict[str, Any]: The created document.

        Raises:
            ConflictError: If a document with the same ID already exists.
        """
        container = await get_container(self.container_name)
        
        # Add id if not present
        if "id" not in item:
            item["id"] = str(uuid4())
        
        # Add timestamps if not present
        now = datetime.now(timezone.utc).isoformat()
        if "createdAt" not in item:
            item["createdAt"] = now
        if "updatedAt" not in item:
            item["updatedAt"] = now
        
        try:
            created_item = await container.create_item(body=item)
            logger.debug(f"Created item {item['id']} in {self.container_name}")
            return created_item
        except cosmos_exceptions.CosmosResourceExistsError:
            raise ConflictError(f"Document with ID {item['id']} already exists")

    async def get_by_id(
        self, id: str, partition_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID and partition key.

        Args:
            id: The document ID.
            partition_key: The partition key value.

        Returns:
            Optional[Dict[str, Any]]: The document if found, None otherwise.
        """
        container = await get_container(self.container_name)
        
        try:
            item = await container.read_item(item=id, partition_key=partition_key)
            return item
        except cosmos_exceptions.CosmosResourceNotFoundError:
            return None

    async def update(
        self, id: str, partition_key: str, item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing document.

        Args:
            id: The document ID.
            partition_key: The partition key value.
            item: The updated document data.

        Returns:
            Dict[str, Any]: The updated document.

        Raises:
            NotFoundError: If the document is not found.
        """
        container = await get_container(self.container_name)
        
        # Ensure id is set
        item["id"] = id
        
        # Update timestamp
        item["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        try:
            updated_item = await container.replace_item(item=id, body=item)
            logger.debug(f"Updated item {id} in {self.container_name}")
            return updated_item
        except cosmos_exceptions.CosmosResourceNotFoundError:
            raise NotFoundError(f"Document with ID {id} not found")

    async def delete(self, id: str, partition_key: str) -> bool:
        """
        Delete a document by ID and partition key.

        Args:
            id: The document ID.
            partition_key: The partition key value.

        Returns:
            bool: True if deleted, False if not found.
        """
        container = await get_container(self.container_name)
        
        try:
            await container.delete_item(item=id, partition_key=partition_key)
            logger.debug(f"Deleted item {id} from {self.container_name}")
            return True
        except cosmos_exceptions.CosmosResourceNotFoundError:
            return False

    async def query(
        self,
        query: str,
        parameters: Optional[List[Dict[str, Any]]] = None,
        partition_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query against the container.

        Args:
            query: SQL query string.
            parameters: Query parameters.
            partition_key: Optional partition key for scoped queries.

        Returns:
            List[Dict[str, Any]]: List of matching documents.
        """
        container = await get_container(self.container_name)
        
        query_kwargs: Dict[str, Any] = {
            "query": query,
        }
        
        if parameters:
            query_kwargs["parameters"] = parameters
        
        if partition_key:
            query_kwargs["partition_key"] = partition_key
        else:
            query_kwargs["enable_cross_partition_query"] = True
        
        items = []
        async for item in container.query_items(**query_kwargs):
            items.append(item)
        
        return items

    async def list_by_partition(
        self, partition_key: str, order_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all documents in a partition.

        Args:
            partition_key: The partition key value.
            order_by: Optional field to order by (e.g., "createdAt DESC").

        Returns:
            List[Dict[str, Any]]: List of documents in the partition.
        """
        order_clause = f" ORDER BY c.{order_by}" if order_by else ""
        query = f"SELECT * FROM c WHERE c.{self.partition_key_field} = @pk{order_clause}"
        parameters = [{"name": "@pk", "value": partition_key}]
        
        return await self.query(
            query=query,
            parameters=parameters,
            partition_key=partition_key,
        )

    async def upsert(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update a document.

        Args:
            item: Document data to upsert.

        Returns:
            Dict[str, Any]: The upserted document.
        """
        container = await get_container(self.container_name)
        
        # Add id if not present
        if "id" not in item:
            item["id"] = str(uuid4())
        
        # Update timestamp
        now = datetime.now(timezone.utc).isoformat()
        if "createdAt" not in item:
            item["createdAt"] = now
        item["updatedAt"] = now
        
        upserted_item = await container.upsert_item(body=item)
        logger.debug(f"Upserted item {item['id']} in {self.container_name}")
        return upserted_item
