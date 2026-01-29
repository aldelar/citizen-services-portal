"""Tests for agent plan management behavior.

These tests validate that the agent:
1. Uses CSP MCP tools (plan.create, plan.update, plan.updateStep) instead of embedding JSON
2. Emits <<PLAN_UPDATED>> signal after plan modifications
3. Does not include json:plan blocks in chat responses

Test categories:
- Unit tests: Fast, mock-based, test signal extraction
- Integration tests: End-to-end with actual agent (requires services running)

Run unit tests: pytest tests/test_agent_plan_behavior.py -m "not integration"
Run integration tests: pytest tests/test_agent_plan_behavior.py -m "integration" -v
"""

import pytest
import os

# Import utility functions for testing
from utils.response_parser import (
    extract_plan_updated_signal,
    has_plan_updated_signal,
    has_embedded_plan_json,
)


# =============================================================================
# Signal Extraction Unit Tests (Fast, no external dependencies)
# =============================================================================

class TestPlanUpdatedSignalExtraction:
    """Unit tests for the <<PLAN_UPDATED>> signal extraction."""
    
    def test_extract_signal_simple(self):
        """Test extracting simple signal."""
        response = "I've created a plan for your solar installation.\n\n<<PLAN_UPDATED>>"
        _, found = extract_plan_updated_signal(response)
        assert found is True
    
    def test_extract_signal_from_middle_of_response(self):
        """Test extracting signal embedded in longer response."""
        response = """I've updated your plan to include the battery storage.

New steps added:
- Battery permit application
- Battery rebate application

<<PLAN_UPDATED>>

Let me know if you have any questions!"""
        
        _, found = extract_plan_updated_signal(response)
        assert found is True
    
    def test_no_signal_returns_false(self):
        """Test that responses without signal return False."""
        response = "I can help you with solar panel installation. What's your address?"
        _, found = extract_plan_updated_signal(response)
        assert found is False
    
    def test_signal_is_removed_from_display_text(self):
        """Test that the signal is replaced with visual indicator."""
        response = "Plan created!\n\n<<PLAN_UPDATED>>"
        cleaned, found = extract_plan_updated_signal(response)
        assert found is True
        assert "<<PLAN_UPDATED>>" not in cleaned
        assert "Plan updated" in cleaned


class TestNoPlanJsonInResponse:
    """Tests to ensure agent doesn't embed plan JSON in responses."""
    
    def test_detect_embedded_json_plan(self):
        """Test detection of json:plan blocks that should NOT appear."""
        good_responses = [
            "I've created a plan for your project.\n\n<<PLAN_UPDATED>>",
            "Your plan has been updated with the new steps.\n\n<<PLAN_UPDATED>>",
            "Here's what I found about permits:\n- Electrical permit required\n- Fee: $150",
        ]
        
        for response in good_responses:
            assert not has_embedded_plan_json(response), \
                f"Good response should not contain json:plan: {response[:50]}..."
    
    def test_bad_pattern_detected(self):
        """Verify that the old json:plan pattern is detectable."""
        bad_response = '''Here's your plan:
```json:plan
{
  "title": "Solar Installation",
  "steps": []
}
```'''
        
        assert has_embedded_plan_json(bad_response), \
            "Should detect embedded json:plan block"


# =============================================================================
# Integration Tests (Require actual agent running)
# =============================================================================

AGENT_URL = os.environ.get("CSP_AGENT_URL", "http://localhost:8088")


@pytest.mark.integration
class TestAgentPlanIntegration:
    """Integration tests that hit the actual agent.
    
    These tests require:
    - CSP Agent running at localhost:8088
    - MCP CSP server running at localhost:8004
    - CosmosDB accessible
    
    Run with: pytest tests/test_agent_plan_behavior.py -m integration -v
    """
    
    @pytest.fixture
    def agent_service(self):
        """Create an AgentService instance."""
        from services.agent_service import AgentService
        return AgentService(base_url=AGENT_URL, use_auth=False)
    
    @pytest.mark.asyncio
    async def test_plan_creation_emits_signal(self, agent_service):
        """Test that asking for a plan triggers plan creation and signal emission."""
        test_project_id = "test-integration-001"
        test_user_id = "test-user-001"
        
        messages = [
            {"role": "system", "content": f"Project ID: {test_project_id}\nUser ID: {test_user_id}"},
            {"role": "user", "content": "I want to install solar panels on my home at 123 Test St, Los Angeles 90012. I have a 6kW system without battery storage. Please create a plan for me."}
        ]
        
        response_text, _ = await agent_service.send_message(
            message=messages[-1]["content"],
            messages=messages
        )
        
        print(f"\n--- Agent Response ---\n{response_text}\n--- End Response ---")
        
        # Verify signal was emitted
        assert has_plan_updated_signal(response_text), \
            "Agent should emit <<PLAN_UPDATED>> signal after creating a plan"
        
        # Verify no embedded json:plan
        assert not has_embedded_plan_json(response_text), \
            "Agent should NOT embed json:plan blocks in response"
    
    @pytest.mark.asyncio
    async def test_plan_update_emits_signal(self, agent_service):
        """Test that updating a plan triggers signal emission."""
        test_project_id = "test-integration-002"
        test_user_id = "test-user-001"
        
        # Simulate conversation where plan exists and user wants to add battery
        messages = [
            {"role": "system", "content": f"Project ID: {test_project_id}\nUser ID: {test_user_id}"},
            {"role": "user", "content": "I want to install solar panels."},
            {"role": "assistant", "content": "I've created a plan for your 6kW solar installation.\n\n<<PLAN_UPDATED>>"},
            {"role": "user", "content": "Actually, I'd also like to add battery storage. Please update my plan."}
        ]
        
        response_text, _ = await agent_service.send_message(
            message=messages[-1]["content"],
            messages=messages
        )
        
        print(f"\n--- Agent Response ---\n{response_text}\n--- End Response ---")
        
        # Verify signal was emitted for the update
        assert has_plan_updated_signal(response_text), \
            "Agent should emit <<PLAN_UPDATED>> signal after updating a plan"
    
    @pytest.mark.asyncio
    async def test_info_query_response(self, agent_service):
        """Test that informational queries get a valid response."""
        response_text, _ = await agent_service.send_message(
            message="What are the requirements for an electrical permit in Los Angeles?"
        )
        
        print(f"\n--- Agent Response ---\n{response_text}\n--- End Response ---")
        
        # Should get a valid response
        assert response_text is not None and len(response_text) > 50
        
        # Verify no embedded json:plan for info queries
        assert not has_embedded_plan_json(response_text)
    
    @pytest.mark.asyncio 
    async def test_agent_uses_mcp_tools_not_embedded_json(self, agent_service):
        """Test that agent uses MCP pattern correctly for plan creation."""
        test_project_id = "test-integration-003"
        test_user_id = "test-user-001"
        
        messages = [
            {"role": "system", "content": f"Project ID: {test_project_id}\nUser ID: {test_user_id}"},
            {"role": "user", "content": "Create a plan for scheduling a bulky item pickup at 456 Demo Ave, Los Angeles 90015. I need to dispose of an old sofa and refrigerator."}
        ]
        
        response_text, _ = await agent_service.send_message(
            message=messages[-1]["content"],
            messages=messages
        )
        
        print(f"\n--- Agent Response ---\n{response_text}\n--- End Response ---")
        
        # Check for PLAN_UPDATED signal
        assert has_plan_updated_signal(response_text), \
            "Agent should emit <<PLAN_UPDATED>> signal"
        
        # Check for absence of json:plan
        assert not has_embedded_plan_json(response_text), \
            "Agent should NOT embed json:plan blocks in response"
    
    @pytest.mark.asyncio
    async def test_step_update_emits_signal(self, agent_service):
        """Test that updating a step status triggers signal emission.
        
        When user reports completing an action (e.g., inspection passed),
        the agent should update the step and emit <<PLAN_UPDATED>>.
        """
        test_project_id = "test-integration-004"
        test_user_id = "test-user-001"
        
        # Simulate conversation where user reports completing an inspection
        messages = [
            {"role": "system", "content": f"Project ID: {test_project_id}\nUser ID: {test_user_id}"},
            {"role": "user", "content": "I want to install solar panels."},
            {"role": "assistant", "content": "I've created a plan for your solar installation with the following steps:\n1. Submit electrical permit (P1)\n2. Schedule inspection (I1)\n\n<<PLAN_UPDATED>>"},
            {"role": "user", "content": "Great news! I submitted the permit application and got permit number ELEC-2026-123456. Please update my plan."}
        ]
        
        response_text, _ = await agent_service.send_message(
            message=messages[-1]["content"],
            messages=messages
        )
        
        print(f"\n--- Agent Response ---\n{response_text}\n--- End Response ---")
        
        # Agent should update the step and emit signal
        assert has_plan_updated_signal(response_text), \
            "Agent should emit <<PLAN_UPDATED>> signal after updating a step status"
