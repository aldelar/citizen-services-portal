"""User repository for CosmosDB operations."""

from datetime import datetime, timezone
from typing import Optional

from azure.cosmos import exceptions as cosmos_exceptions

from ..client import get_container
from ..exceptions import ConflictError, NotFoundError
from ..models import User


class UserRepository:
    """Repository for user CRUD operations."""

    def __init__(self):
        """Initialize the user repository."""
        self.container_name = "users"

    async def create_user(self, user: User) -> User:
        """
        Create a new user in the database.

        Args:
            user: User object to create.

        Returns:
            User: The created user object.

        Raises:
            ConflictError: If a user with the same ID already exists.
        """
        container = await get_container(self.container_name)
        
        try:
            user_dict = user.model_dump(by_alias=True, mode="json")
            created_item = await container.create_item(body=user_dict)
            return User.model_validate(created_item)
        except cosmos_exceptions.CosmosResourceExistsError:
            raise ConflictError(f"User with ID {user.id} already exists")

    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: The user ID.

        Returns:
            Optional[User]: The user object if found, None otherwise.
        """
        container = await get_container(self.container_name)
        
        try:
            item = await container.read_item(item=user_id, partition_key=user_id)
            return User.model_validate(item)
        except cosmos_exceptions.CosmosResourceNotFoundError:
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email address.

        Args:
            email: The user's email address.

        Returns:
            Optional[User]: The user object if found, None otherwise.
        """
        container = await get_container(self.container_name)
        
        query = "SELECT * FROM c WHERE c.email = @email"
        parameters = [{"name": "@email", "value": email}]
        
        items = []
        async for item in container.query_items(
            query=query, parameters=parameters, enable_cross_partition_query=True
        ):
            items.append(item)
        
        if items:
            return User.model_validate(items[0])
        return None

    async def update_last_login(self, user_id: str) -> User:
        """
        Update the last login timestamp for a user.

        Args:
            user_id: The user ID.

        Returns:
            User: The updated user object.

        Raises:
            NotFoundError: If the user is not found.
        """
        container = await get_container(self.container_name)
        
        try:
            # Read the current user
            item = await container.read_item(item=user_id, partition_key=user_id)
            user = User.model_validate(item)
            
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            
            # Replace the item
            user_dict = user.model_dump(by_alias=True, mode="json")
            updated_item = await container.replace_item(item=user_id, body=user_dict)
            return User.model_validate(updated_item)
        except cosmos_exceptions.CosmosResourceNotFoundError:
            raise NotFoundError(f"User with ID {user_id} not found")
