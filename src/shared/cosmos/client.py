"""CosmosDB client initialization and helper functions."""

import os
from typing import Optional

from azure.cosmos.aio import CosmosClient, DatabaseProxy, ContainerProxy
from azure.identity.aio import DefaultAzureCredential

# Global client instance
_cosmos_client: Optional[CosmosClient] = None
_credential: Optional[DefaultAzureCredential] = None


async def get_cosmos_client() -> CosmosClient:
    """
    Get or create the async CosmosDB client instance.

    Returns:
        CosmosClient: The async Cosmos client instance.

    Raises:
        ValueError: If COSMOS_ENDPOINT environment variable is not set.
    """
    global _cosmos_client, _credential

    if _cosmos_client is None:
        endpoint = os.environ.get("COSMOS_ENDPOINT")
        if not endpoint:
            raise ValueError("COSMOS_ENDPOINT environment variable is not set")

        _credential = DefaultAzureCredential()
        _cosmos_client = CosmosClient(endpoint, credential=_credential)

    return _cosmos_client


async def get_database() -> DatabaseProxy:
    """
    Get the database proxy for the citizen-services database.

    Returns:
        DatabaseProxy: The database proxy instance.

    Raises:
        ValueError: If COSMOS_DATABASE environment variable is not set.
    """
    client = await get_cosmos_client()
    database_name = os.environ.get("COSMOS_DATABASE", "citizen-services")
    return client.get_database_client(database_name)


async def get_container(container_name: str) -> ContainerProxy:
    """
    Get a container proxy for the specified container.

    Args:
        container_name: Name of the container.

    Returns:
        ContainerProxy: The container proxy instance.
    """
    database = await get_database()
    return database.get_container_client(container_name)


async def close_client():
    """Close the CosmosDB client and credential."""
    global _cosmos_client, _credential

    if _cosmos_client:
        await _cosmos_client.close()
        _cosmos_client = None

    if _credential:
        await _credential.close()
        _credential = None
