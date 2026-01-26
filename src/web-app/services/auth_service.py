"""Authentication service for the Citizen Services Portal."""

from typing import Optional
from config import settings
from models.user import User


def get_current_user() -> Optional[User]:
    """Get current user - mock for local dev, Easy Auth for Azure.
    
    In Azure deployment, this would read from Easy Auth headers:
    - X-MS-CLIENT-PRINCIPAL-ID
    - X-MS-CLIENT-PRINCIPAL-NAME
    
    For local development, returns a mock user.
    """
    if settings.USE_MOCK_AUTH:
        return User(
            id=settings.MOCK_USER_ID,
            email=settings.MOCK_USER_EMAIL,
            name=settings.MOCK_USER_NAME,
        )
    
    # TODO: Implement Easy Auth header parsing for Azure deployment
    # request = app.native.request
    # principal_id = request.headers.get('X-MS-CLIENT-PRINCIPAL-ID')
    # principal_name = request.headers.get('X-MS-CLIENT-PRINCIPAL-NAME')
    return None
