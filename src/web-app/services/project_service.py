"""Project service for managing projects and messages with CosmosDB.

This service wraps the shared cosmos repositories to provide a simplified
interface for the web application. It handles creating new projects with
auto-generated names and persisting conversation messages.
"""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

# Add shared library to path BEFORE any other imports
# This must happen at the top of the module
_shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
if _shared_path not in sys.path:
    sys.path.insert(0, _shared_path)

from config import settings

logger = logging.getLogger(__name__)


def generate_project_title() -> str:
    """Generate a project title using YYMMDD-HHMM format."""
    now = datetime.now()
    return now.strftime("%y%m%d-%H%M")


# In-memory storage for when CosmosDB is not available
_in_memory_projects: dict[str, dict] = {}  # project_id -> project
_in_memory_messages: dict[str, list[dict]] = {}  # project_id -> messages


class ProjectService:
    """Service for project and message operations with CosmosDB."""
    
    def __init__(self):
        """Initialize the project service."""
        self._project_repo = None
        self._message_repo = None
        self._cosmos_available = None
    
    async def _check_cosmos_available(self) -> bool:
        """Check if CosmosDB is available and configured."""
        if self._cosmos_available is not None:
            return self._cosmos_available
        
        if not settings.cosmos_enabled:
            logger.info("CosmosDB not configured - using in-memory storage")
            self._cosmos_available = False
            return False
        
        # Set environment variables for the shared library
        os.environ.setdefault("COSMOS_ENDPOINT", settings.COSMOS_ENDPOINT)
        os.environ.setdefault("COSMOS_DATABASE", settings.COSMOS_DATABASE)
        
        try:
            from cosmos.repositories import ProjectRepository, MessageRepository
            from cosmos.client import get_cosmos_client
            
            # Try to get the client to verify connection
            await get_cosmos_client()
            self._project_repo = ProjectRepository()
            self._message_repo = MessageRepository()
            self._cosmos_available = True
            logger.info("CosmosDB connection established")
            return True
        except Exception as e:
            logger.warning(f"CosmosDB not available: {e}")
            self._cosmos_available = False
            return False
    
    async def get_user_projects(self, user_id: str) -> List[dict]:
        """Get all projects for a user.
        
        Args:
            user_id: The user ID.
            
        Returns:
            List of project dictionaries.
        """
        if not await self._check_cosmos_available():
            # Return in-memory projects for this user
            return [p for p in _in_memory_projects.values() if p.get("userId") == user_id or p.get("user_id") == user_id]
        
        try:
            projects = await self._project_repo.get_user_projects(user_id)
            return [p.model_dump() for p in projects]
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            # Fall back to in-memory on error
            self._cosmos_available = False
            return [p for p in _in_memory_projects.values() if p.get("userId") == user_id or p.get("user_id") == user_id]
    
    async def get_project(self, project_id: str, user_id: str) -> Optional[dict]:
        """Get a project by ID.
        
        Args:
            project_id: The project ID.
            user_id: The user ID (partition key).
            
        Returns:
            Project dictionary or None if not found.
        """
        if not await self._check_cosmos_available():
            # Return from in-memory storage
            return _in_memory_projects.get(project_id)
        
        try:
            project = await self._project_repo.get_project(project_id, user_id)
            return project.model_dump() if project else None
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            return None
    
    async def create_project(self, user_id: str, title: Optional[str] = None) -> Optional[dict]:
        """Create a new project for a user.
        
        Args:
            user_id: The user ID.
            title: Optional project title. If not provided, auto-generates using YYMMDD-HHMM format.
            
        Returns:
            Created project dictionary or None if creation failed.
        """
        if not await self._check_cosmos_available():
            # Create and store in-memory project
            project_id = str(uuid4())
            now = datetime.now(timezone.utc)
            project = {
                "id": project_id,
                "userId": user_id,
                "user_id": user_id,
                "title": title or generate_project_title(),
                "status": "active",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "context": {
                    "address": "",
                    "property_type": None,
                    "project_description": None,
                },
                "plan": None,
                "summary": {
                    "total_steps": 0,
                    "completed_steps": 0,
                },
            }
            _in_memory_projects[project_id] = project
            _in_memory_messages[project_id] = []
            return project
        
        try:
            from cosmos.models import ProjectContext
            
            # Create minimal context - will be updated as conversation progresses
            context = ProjectContext(
                address="",  # Will be populated from conversation
                project_description=None,
            )
            
            project = await self._project_repo.create_project(user_id, context)
            
            # Update with custom title if provided or auto-generated
            project.title = title or generate_project_title()
            project = await self._project_repo.update_project(project)
            
            return project.model_dump()
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None
    
    async def get_messages(self, project_id: str, limit: int = 100) -> List[dict]:
        """Get messages for a project.
        
        Args:
            project_id: The project ID.
            limit: Maximum number of messages to return.
            
        Returns:
            List of message dictionaries ordered by timestamp ascending.
        """
        if not await self._check_cosmos_available():
            # Return from in-memory storage
            return _in_memory_messages.get(project_id, [])
        
        try:
            # Get messages in descending order, then reverse for chronological display
            messages = await self._message_repo.get_messages(project_id, limit=limit)
            # Messages come back in descending order, reverse for UI
            return [m.model_dump() for m in reversed(messages)]
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    async def save_message(
        self,
        project_id: str,
        role: str,
        content: str,
        tool_calls: Optional[list] = None,
    ) -> Optional[dict]:
        """Save a message to the database.
        
        Args:
            project_id: The project ID.
            role: Message role ('user' or 'assistant').
            content: Message content.
            tool_calls: Optional list of tool calls for assistant messages.
            
        Returns:
            Created message dictionary or None if save failed.
        """
        if not await self._check_cosmos_available():
            # Store in in-memory storage
            message = {
                "id": str(uuid4()),
                "project_id": project_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_calls": tool_calls,
            }
            if project_id not in _in_memory_messages:
                _in_memory_messages[project_id] = []
            _in_memory_messages[project_id].append(message)
            
            # Update project's updated_at timestamp
            if project_id in _in_memory_projects:
                _in_memory_projects[project_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            return message
        
        try:
            from cosmos.models import Message
            
            message = Message(
                id=str(uuid4()),
                project_id=project_id,
                role=role,
                content=content,
                timestamp=datetime.now(timezone.utc),
            )
            
            saved = await self._message_repo.append_message(message)
            
            # Update project's updated_at timestamp
            # Note: In CosmosDB mode, we need to find the user_id first
            # We'll get it from the project if available in memory, otherwise skip the update
            # The agent service should handle this update separately
            
            return saved.model_dump()
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    async def update_project(
        self,
        project_id: str,
        user_id: str,
        updates: dict,
    ) -> Optional[dict]:
        """Update a project with new fields.
        
        Args:
            project_id: The project ID.
            user_id: The user ID (partition key).
            updates: Dictionary of fields to update (e.g., {'title': 'New Title', 'status': 'completed'}).
            
        Returns:
            Updated project dictionary or None if update failed.
        """
        if not await self._check_cosmos_available():
            # Update in-memory storage
            if project_id in _in_memory_projects:
                project = _in_memory_projects[project_id]
                project.update(updates)
                project["updated_at"] = datetime.now(timezone.utc).isoformat()
                return project
            return None
        
        try:
            project = await self._project_repo.get_project(project_id, user_id)
            if not project:
                return None
            
            # Update fields
            for key, value in updates.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            
            # Always update the timestamp
            project.updated_at = datetime.now(timezone.utc)
            
            updated = await self._project_repo.update_project(project)
            return updated.model_dump()
        except Exception as e:
            logger.error(f"Error updating project: {e}")
            return None
    
    async def touch_project(self, project_id: str, user_id: str) -> Optional[dict]:
        """Update the project's updated_at timestamp to current time.
        
        Args:
            project_id: The project ID.
            user_id: The user ID (partition key).
            
        Returns:
            Updated project dictionary or None if update failed.
        """
        return await self.update_project(project_id, user_id, {})


# Singleton instance
_project_service: Optional[ProjectService] = None


def get_project_service() -> ProjectService:
    """Get or create the project service singleton."""
    global _project_service
    if _project_service is None:
        _project_service = ProjectService()
    return _project_service
