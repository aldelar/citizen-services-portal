"""Test fixtures and configuration for Reporting MCP server tests."""

import pytest
import pytest_asyncio
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop that persists for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def cosmos_cleanup():
    """Clean up the Cosmos client at the end of the test session."""
    yield
    try:
        from citizen_services_shared.cosmos.client import close_client
        await close_client()
    except (ImportError, Exception):
        pass
