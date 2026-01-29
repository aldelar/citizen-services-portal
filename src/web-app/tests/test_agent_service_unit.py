"""Unit tests for AgentService using Responses API contract.

Tests validate request construction and response parsing for stateless history,
without making actual network calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json


@pytest.fixture
def agent_service():
    """Create an AgentService instance without authentication."""
    from services.agent_service import AgentService
    service = AgentService(base_url="https://test.example.com", use_auth=False)
    # Pre-set entity_id to avoid needing to mock the entities endpoint
    service._entity_id = "agent_test_csp-agent_123"
    return service


@pytest.mark.asyncio
async def test_build_url_uses_v1_prefix(agent_service):
    """Test that _build_url correctly adds /v1 prefix."""
    url = agent_service._build_url("/responses")
    assert url == "https://test.example.com/v1/responses"


@pytest.mark.asyncio
async def test_build_url_entities_endpoint(agent_service):
    """Test that _build_url works for entities endpoint."""
    url = agent_service._build_url("/entities")
    assert url == "https://test.example.com/v1/entities"


@pytest.mark.asyncio
async def test_send_message_constructs_correct_payload(agent_service):
    """Test that send_message constructs the correct request payload."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": [{"content": [{"text": "Test response"}]}],
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result_text, conv_id = await agent_service.send_message("Hello")
        
        # Verify the call
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        assert call_args is not None
        
        # Check URL uses /v1/responses
        url = call_args[0][0]
        assert "/v1/responses" in url
        
        # Check payload uses string input format and includes metadata
        payload = call_args[1]["json"]
        assert isinstance(payload["input"], str)
        assert "Hello" in payload["input"]
        assert payload["stream"] is False
        assert "metadata" in payload
        assert payload["metadata"]["entity_id"] == "agent_test_csp-agent_123"


@pytest.mark.asyncio
async def test_send_message_includes_history(agent_service):
    """Test that send_message includes message history when provided."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": [{"content": [{"text": "Follow-up response"}]}],
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "Follow-up"},
        ]
        result_text, conv_id = await agent_service.send_message("Follow-up", messages=history)
        
        # Check payload includes message history as formatted string
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        payload = call_args[1]["json"]
        assert isinstance(payload["input"], str)
        assert "User: Hi" in payload["input"]
        assert "Assistant: Hello" in payload["input"]
        assert "User: Follow-up" in payload["input"]
        # Check entity_id is included
        assert payload["metadata"]["entity_id"] == "agent_test_csp-agent_123"


@pytest.mark.asyncio
async def test_extract_response_text_from_output():
    """Test that response text is correctly extracted from output array."""
    from services.agent_service import AgentService
    service = AgentService(use_auth=False)
    
    data = {
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": "This is the response"}
                ]
            }
        ]
    }
    
    text = service._extract_response_text(data)
    assert text == "This is the response"


@pytest.mark.asyncio
async def test_extract_conversation_id_from_response():
    """Test that conversation ID is correctly extracted from response."""
    from services.agent_service import AgentService
    service = AgentService(use_auth=False)
    
    data = {
        "conversation": {"id": "conv-456"},
        "output": []
    }
    
    conv_id = service._extract_conversation_id(data)
    assert conv_id == "conv-456"


@pytest.mark.asyncio
async def test_extract_conversation_id_handles_string():
    """Test that conversation ID extraction handles string format."""
    from services.agent_service import AgentService
    service = AgentService(use_auth=False)
    
    data = {
        "conversation": "conv-789",
        "output": []
    }
    
    conv_id = service._extract_conversation_id(data)
    assert conv_id == "conv-789"


@pytest.mark.asyncio
async def test_extract_conversation_id_returns_none_when_missing():
    """Test that conversation ID extraction returns None when missing."""
    from services.agent_service import AgentService
    service = AgentService(use_auth=False)
    
    data = {"output": []}
    
    conv_id = service._extract_conversation_id(data)
    assert conv_id is None


@pytest.mark.asyncio
async def test_send_message_returns_tuple(agent_service):
    """Test that send_message returns tuple of (text, None)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": [{"content": [{"text": "Response text"}]}],
        "conversation": {"id": "conv-abc"}
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await agent_service.send_message("Test")
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "Response text"
        assert result[1] is None


@pytest.mark.asyncio
async def test_auth_token_not_requested_when_disabled(agent_service):
    """Test that auth token is not requested when use_auth is False."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "output": [{"content": [{"text": "Test"}]}]
    }
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        await agent_service.send_message("Hello")
        
        # Check headers don't include Authorization
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        headers = call_args[1]["headers"]
        assert "Authorization" not in headers


@pytest.mark.asyncio
async def test_extract_delta_text_for_streaming():
    """Test that streaming delta text is correctly extracted."""
    from services.agent_service import AgentService
    service = AgentService(use_auth=False)
    
    # Test response.output_text.delta event
    data = {
        "type": "response.output_text.delta",
        "delta": "chunk of text"
    }
    
    text = service._extract_delta_text(data)
    assert text == "chunk of text"


@pytest.mark.asyncio
async def test_extract_delta_text_skips_completed_events():
    """Test that completed events don't return text (to avoid duplication)."""
    from services.agent_service import AgentService
    service = AgentService(use_auth=False)
    
    # Test response.completed event (should be skipped)
    data = {
        "type": "response.completed",
        "output": [{"content": [{"text": "Full response"}]}]
    }
    
    text = service._extract_delta_text(data)
    assert text == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
