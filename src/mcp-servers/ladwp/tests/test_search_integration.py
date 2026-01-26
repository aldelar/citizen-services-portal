"""Integration tests for LADWP Azure AI Search operations.

These tests require a live Azure AI Search instance with AZURE_SEARCH_ENDPOINT configured.
Run with: pytest -m integration
"""

import os
import pytest

from src.services import LADWPService


# Skip all tests in this file if Azure AI Search is not configured
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("AZURE_SEARCH_ENDPOINT"),
        reason="Azure AI Search not configured (AZURE_SEARCH_ENDPOINT not set)"
    )
]


@pytest.fixture
def ladwp_service():
    """Create a LADWPService instance for testing."""
    return LADWPService()


class TestKnowledgeBaseSearch:
    """Tests for knowledge base search operations."""

    @pytest.mark.asyncio
    async def test_semantic_search_returns_results(self, ladwp_service):
        """Test that queryKB returns relevant chunks from AI Search."""
        # Query for rate plan information
        result = await ladwp_service.query_knowledge_base(
            query="What are the LADWP time-of-use rate plans?",
            top=5
        )

        assert result is not None
        assert result.query == "What are the LADWP time-of-use rate plans?"
        assert len(result.results) > 0
        assert result.total_results > 0

        # Check first result has expected fields
        first_result = result.results[0]
        assert first_result.content is not None
        assert len(first_result.content) > 0
        assert first_result.source is not None
        assert 0 <= first_result.relevance_score <= 1.0

    @pytest.mark.asyncio
    async def test_search_with_different_query(self, ladwp_service):
        """Test search with a different query."""
        result = await ladwp_service.query_knowledge_base(
            query="How do I apply for LADWP rebates?",
            top=3
        )

        assert result is not None
        assert len(result.results) <= 3
        assert all(r.content for r in result.results)

    @pytest.mark.asyncio
    async def test_search_with_rate_plan_query(self, ladwp_service):
        """Test search for rate plan information."""
        result = await ladwp_service.query_knowledge_base(
            query="What is TOU-D-PRIME rate plan?",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

    @pytest.mark.asyncio
    async def test_search_with_rebate_query(self, ladwp_service):
        """Test search for rebate program information."""
        result = await ladwp_service.query_knowledge_base(
            query="What rebates are available for heat pump installation?",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

    @pytest.mark.asyncio
    async def test_search_with_interconnection_query(self, ladwp_service):
        """Test search for solar interconnection information."""
        result = await ladwp_service.query_knowledge_base(
            query="How do I apply for solar interconnection with LADWP?",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

    @pytest.mark.asyncio
    async def test_search_returns_valid_sources(self, ladwp_service):
        """Test that search results include valid source references."""
        result = await ladwp_service.query_knowledge_base(
            query="LADWP electricity rates",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

        # All results should have a source file
        for chunk in result.results:
            assert chunk.source is not None
            assert len(chunk.source) > 0
            # Source should look like a filename (contains a dot and file extension)
            assert "." in chunk.source and len(chunk.source.split(".")[-1]) in range(2, 6)

    @pytest.mark.asyncio
    async def test_search_with_varying_top_parameter(self, ladwp_service):
        """Test that the top parameter correctly limits results."""
        # Test with top=1
        result1 = await ladwp_service.query_knowledge_base(
            query="LADWP programs",
            top=1
        )
        assert len(result1.results) <= 1

        # Test with top=10
        result10 = await ladwp_service.query_knowledge_base(
            query="LADWP programs",
            top=10
        )
        assert len(result10.results) <= 10

    @pytest.mark.asyncio
    async def test_search_relevance_scores(self, ladwp_service):
        """Test that relevance scores are in valid range."""
        result = await ladwp_service.query_knowledge_base(
            query="solar panel installation requirements for LADWP",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

        # All relevance scores should be between 0 and 1
        for chunk in result.results:
            assert 0 <= chunk.relevance_score <= 1.0
