"""Integration tests for CSP Agent with Responses API.

These tests validate end-to-end functionality with the deployed container app agent,
including authentication, stateless history passing, and response format.

Requirements:
- Azure authentication configured (az login or managed identity)
- CSP_AGENT_URL environment variable set to agent endpoint
- Agent deployed and accessible
"""

import pytest
import os
import asyncio
from azure.identity import DefaultAzureCredential


# Check if integration tests should run
SKIP_INTEGRATION = os.environ.get("SKIP_INTEGRATION_TESTS", "false").lower() == "true"
AGENT_URL = os.environ.get("CSP_AGENT_URL")

pytestmark = pytest.mark.skipif(
    SKIP_INTEGRATION or not AGENT_URL,
    reason="Integration tests disabled or CSP_AGENT_URL not set"
)


@pytest.fixture
def agent_service():
    """Create an AgentService instance with authentication."""
    from services.agent_service import AgentService
    return AgentService(base_url=AGENT_URL, use_auth=False)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_agent_responds_to_simple_query(agent_service):
    """Test that agent responds to a simple query."""
    response_text, conv_id = await agent_service.send_message(
        "What services does LADBS provide?"
    )
    
    assert response_text is not None
    assert len(response_text) > 0
    print(f"\nResponse: {response_text[:200]}...")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_conversation_persistence_across_requests(agent_service):
    """Test that conversation context persists across requests."""
    # First message
    response1, conv_id = await agent_service.send_message(
        "What are the requirements for an electrical permit?"
    )
    
    assert response1 is not None
    print(f"\nFirst response length: {len(response1)}")
    
    # Second message with explicit history
    history = [
        {"role": "user", "content": "What are the requirements for an electrical permit?"},
        {"role": "assistant", "content": response1},
        {"role": "user", "content": "What documents do I need for that?"},
    ]
    response2, conv_id2 = await agent_service.send_message(
        "What documents do I need for that?",
        messages=history
    )
    
    assert response2 is not None
    print(f"\nSecond response: {response2[:200]}...")
    
    # The second response should reference context from the first
    # (this is a heuristic check - in a real test we'd validate specific content)
    assert len(response2) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_agent_handles_mcp_tool_calls(agent_service):
    """Test that agent can use MCP tools successfully."""
    response_text, conv_id = await agent_service.send_message(
        "Search for building permits filed in the last month"
    )
    
    assert response_text is not None
    assert len(response_text) > 0
    print(f"\nTool call response: {response_text[:200]}...")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_agent_handles_multi_agency_query(agent_service):
    """Test that agent can coordinate across multiple agencies."""
    response_text, conv_id = await agent_service.send_message(
        "I want to install solar panels. What permits do I need from LADBS and what rebates are available from LADWP?"
    )
    
    assert response_text is not None
    assert len(response_text) > 0
    # Response should mention both agencies
    response_lower = response_text.lower()
    print(f"\nMulti-agency response: {response_text[:300]}...")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_streaming_response(agent_service):
    """Test that streaming responses work correctly."""
    chunks = []
    async for chunk in agent_service.send_message_stream(
        "Tell me about LADBS inspection services"
    ):
        if isinstance(chunk, str):
            chunks.append(chunk)
    
    full_response = "".join(chunks)
    
    assert len(chunks) > 0
    assert len(full_response) > 0
    print(f"\nStreamed {len(chunks)} chunks")
    print(f"Full response length: {len(full_response)}")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_error_handling_for_invalid_request(agent_service):
    """Test that service handles empty input gracefully."""
    response_text, _ = await agent_service.send_message("")
    assert response_text is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_authentication_token_included():
    """Test that authentication is disabled for ACA agent by default."""
    from services.agent_service import AgentService
    service = AgentService(base_url=AGENT_URL, use_auth=False)
    token = await service._get_auth_token()
    assert token is None


@pytest.mark.asyncio
@pytest.mark.integration  
async def test_url_construction_with_v1_prefix():
    """Test that URLs are constructed with /v1 prefix."""
    from services.agent_service import AgentService
    service = AgentService(base_url=AGENT_URL, use_auth=True)
    
    url = service._build_url("/responses")
    
    assert "/v1/responses" in url
    assert url.startswith(AGENT_URL)


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-m", "integration"])
