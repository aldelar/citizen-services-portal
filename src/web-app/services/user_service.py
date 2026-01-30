"""User service for managing user profiles with CosmosDB.

This service handles loading and saving user profile data to CosmosDB,
with fallback to in-memory storage for local development.
"""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Optional

# Add shared library to path BEFORE any other imports
# Try multiple locations: Docker (/app/shared) or local dev (../../shared)
for _candidate in [
    os.path.join(os.path.dirname(__file__), '..', 'shared'),  # Docker: /app/shared
    os.path.join(os.path.dirname(__file__), '..', '..', 'shared'),  # Local: ../../shared
]:
    _shared_path = os.path.abspath(_candidate)
    if os.path.isdir(_shared_path) and _shared_path not in sys.path:
        sys.path.insert(0, _shared_path)
        break

from config import settings
from models.user import User, UserPreferences

logger = logging.getLogger(__name__)


# In-memory storage for when CosmosDB is not available
_in_memory_users: dict[str, dict] = {}


class UserService:
    """Service for user profile operations with CosmosDB."""
    
    def __init__(self):
        """Initialize the user service."""
        self._cosmos_available = None
        self._container = None
    
    async def _check_cosmos_available(self) -> bool:
        """Check if CosmosDB is available and configured."""
        if self._cosmos_available is not None:
            return self._cosmos_available
        
        if not settings.cosmos_enabled:
            logger.info("CosmosDB not configured for users - using in-memory storage")
            self._cosmos_available = False
            return False
        
        try:
            from cosmos.client import get_cosmos_client
            
            client = await get_cosmos_client()
            database = client.get_database_client(settings.COSMOS_DATABASE)
            self._container = database.get_container_client("users")
            self._cosmos_available = True
            logger.info("CosmosDB users container connected")
            return True
        except Exception as e:
            logger.warning(f"CosmosDB users container not available: {e}")
            self._cosmos_available = False
            return False
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID.
        
        Args:
            user_id: The user ID.
            
        Returns:
            User object if found, None otherwise.
        """
        if not await self._check_cosmos_available():
            # Return from in-memory storage
            user_data = _in_memory_users.get(user_id)
            if user_data:
                return User(**user_data)
            return None
        
        try:
            response = await self._container.read_item(item=user_id, partition_key=user_id)
            return User(
                id=response.get("id"),
                email=response.get("email", ""),
                name=response.get("name", ""),
                phone=response.get("phone"),
                address=response.get("address"),
                created_at=datetime.fromisoformat(response["createdAt"].replace("Z", "+00:00")) if response.get("createdAt") else None,
                last_login_at=datetime.fromisoformat(response["lastLoginAt"].replace("Z", "+00:00")) if response.get("lastLoginAt") else None,
                preferences=UserPreferences(**response.get("preferences", {})) if response.get("preferences") else UserPreferences(),
            )
        except Exception as e:
            logger.debug(f"User not found in CosmosDB: {e}")
            return None
    
    async def save_user(self, user: User) -> User:
        """Save or update a user profile.
        
        Args:
            user: The user object to save.
            
        Returns:
            The saved user object.
        """
        user_data = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "address": user.address,
            "createdAt": user.created_at.isoformat() if user.created_at else datetime.now(timezone.utc).isoformat(),
            "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
            "preferences": user.preferences.model_dump() if user.preferences else {},
        }
        
        if not await self._check_cosmos_available():
            # Store in memory
            _in_memory_users[user.id] = user_data
            logger.info(f"User {user.id} saved to in-memory storage")
            return user
        
        try:
            await self._container.upsert_item(body=user_data)
            logger.info(f"User {user.id} saved to CosmosDB")
            return user
        except Exception as e:
            logger.error(f"Error saving user to CosmosDB: {e}")
            # Fall back to in-memory on error
            _in_memory_users[user.id] = user_data
            return user
    
    async def update_user_profile(
        self, 
        user_id: str, 
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Optional[User]:
        """Update specific fields of a user profile.
        
        Args:
            user_id: The user ID.
            name: New name (optional).
            email: New email (optional).
            phone: New phone (optional).
            address: New address (optional).
            
        Returns:
            Updated user object if successful, None otherwise.
        """
        # Get existing user or create new one
        user = await self.get_user(user_id)
        
        if user is None:
            # Create new user with provided data
            user = User(
                id=user_id,
                email=email or "",
                name=name or "",
                phone=phone,
                address=address,
                created_at=datetime.now(timezone.utc),
            )
        else:
            # Update existing user
            if name is not None:
                user.name = name
            if email is not None:
                user.email = email
            if phone is not None:
                user.phone = phone
            if address is not None:
                user.address = address
        
        return await self.save_user(user)


# Singleton instance
_user_service: Optional[UserService] = None


def get_user_service() -> UserService:
    """Get or create the user service singleton."""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service
