"""Configuration management for CSP (Citizen Services Portal) MCP server."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server configuration
    mcp_server_host: str = Field(default="0.0.0.0", alias="MCP_SERVER_HOST")
    mcp_server_port: int = Field(default=8000, alias="MCP_SERVER_PORT")

    # Azure configuration
    azure_tenant_id: Optional[str] = Field(default=None, alias="AZURE_TENANT_ID")
    azure_client_id: Optional[str] = Field(default=None, alias="AZURE_CLIENT_ID")
    azure_client_secret: Optional[str] = Field(default=None, alias="AZURE_CLIENT_SECRET")

    # Cosmos DB configuration
    cosmos_endpoint: Optional[str] = Field(default=None, alias="COSMOS_ENDPOINT")
    
    # Consolidated CSP database (contains all CSP data: projects, users, step_completions, etc.)
    cosmos_database: str = Field(default="csp", alias="COSMOS_DATABASE")
    cosmos_container_projects: str = Field(default="projects", alias="COSMOS_CONTAINER_PROJECTS")
    cosmos_container_step_completions: str = Field(default="step_completions", alias="COSMOS_CONTAINER_STEP_COMPLETIONS")


# Global settings instance
settings = Settings()
