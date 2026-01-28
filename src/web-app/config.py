"""Configuration management for the Citizen Services Portal web application."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings from environment variables."""
    
    # Debug/Development mode
    DEBUG: bool = os.getenv('DEBUG', 'true').lower() == 'true'
    
    # Auth settings
    USE_MOCK_AUTH: bool = os.getenv('USE_MOCK_AUTH', 'true').lower() == 'true'
    MOCK_USER_ID: str = os.getenv('MOCK_USER_ID', 'local_user')
    MOCK_USER_EMAIL: str = os.getenv('MOCK_USER_EMAIL', '')
    MOCK_USER_NAME: str = os.getenv('MOCK_USER_NAME', '')
    
    # Server settings
    NICEGUI_PORT: int = int(os.getenv('NICEGUI_PORT', '8080'))
    NICEGUI_HOST: str = os.getenv('NICEGUI_HOST', '0.0.0.0')
    
    # Backend services
    CSP_AGENT_URL: str = os.getenv('CSP_AGENT_URL', 'http://localhost:8088')
    CSP_AGENT_USE_AUTH: bool = os.getenv('CSP_AGENT_USE_AUTH', 'false').lower() == 'true'
    
    # CosmosDB settings
    COSMOS_ENDPOINT: str = os.getenv('COSMOS_ENDPOINT', '')
    COSMOS_DATABASE: str = os.getenv('COSMOS_DATABASE', 'citizen-services')
    
    @property
    def cosmos_enabled(self) -> bool:
        """Check if CosmosDB is configured."""
        return bool(self.COSMOS_ENDPOINT)


settings = Settings()
