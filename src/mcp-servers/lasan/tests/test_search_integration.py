"""Integration tests for LASAN Azure AI Search operations.

These tests require a live Azure AI Search instance with AZURE_SEARCH_ENDPOINT configured.
Run with: pytest -m integration
"""

import os
import pytest

from src.services import LASANService


# Skip all tests in this file if Azure AI Search is not configured
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("AZURE_SEARCH_ENDPOINT"),
        reason="Azure AI Search not configured (AZURE_SEARCH_ENDPOINT not set)"
    )
]


@pytest.fixture
def lasan_service():
    """Create a LASANService instance for testing."""
    return LASANService()


class TestKnowledgeBaseSearch:
    """Tests for knowledge base search operations."""

    @pytest.mark.asyncio
    async def test_semantic_search_returns_results(self, lasan_service):
        """Test that queryKB returns relevant chunks from AI Search."""
        # Query for bulky item pickup information
        result = await lasan_service.query_knowledge_base(
            query="How do I schedule a bulky item pickup?",
            top=5
        )

        assert result is not None
        assert result.query == "How do I schedule a bulky item pickup?"
        assert len(result.results) > 0
        assert result.total_results > 0

        # Check first result has expected fields
        first_result = result.results[0]
        assert first_result.content is not None
        assert len(first_result.content) > 0
        assert first_result.source is not None
        assert 0 <= first_result.relevance_score <= 1.0

    @pytest.mark.asyncio
    async def test_search_with_different_query(self, lasan_service):
        """Test search with a different query."""
        result = await lasan_service.query_knowledge_base(
            query="What is the recycling schedule?",
            top=3
        )

        assert result is not None
        assert len(result.results) <= 3
        assert all(r.content for r in result.results)

    @pytest.mark.asyncio
    async def test_search_with_bulky_item_query(self, lasan_service):
        """Test search for bulky item pickup information."""
        result = await lasan_service.query_knowledge_base(
            query="What items are accepted for bulky item pickup?",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

        # At least one result should mention bulky items or pickup
        contents = " ".join([r.content.lower() for r in result.results])
        assert "bulky" in contents or "pickup" in contents or "item" in contents

    @pytest.mark.asyncio
    async def test_search_with_recycling_query(self, lasan_service):
        """Test search for recycling guidelines."""
        result = await lasan_service.query_knowledge_base(
            query="What can I put in my recycling bin?",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

    @pytest.mark.asyncio
    async def test_search_with_ewaste_query(self, lasan_service):
        """Test search for e-waste disposal information."""
        result = await lasan_service.query_knowledge_base(
            query="How do I dispose of old electronics and e-waste?",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

    @pytest.mark.asyncio
    async def test_search_with_hazmat_query(self, lasan_service):
        """Test search for hazardous waste information."""
        result = await lasan_service.query_knowledge_base(
            query="How do I dispose of paint and hazardous materials?",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

    @pytest.mark.asyncio
    async def test_search_returns_valid_sources(self, lasan_service):
        """Test that search results include valid source references."""
        result = await lasan_service.query_knowledge_base(
            query="LASAN collection schedule",
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
    async def test_search_with_varying_top_parameter(self, lasan_service):
        """Test that the top parameter correctly limits results."""
        # Test with top=1
        result1 = await lasan_service.query_knowledge_base(
            query="trash pickup",
            top=1
        )
        assert len(result1.results) <= 1

        # Test with top=10
        result10 = await lasan_service.query_knowledge_base(
            query="trash pickup",
            top=10
        )
        assert len(result10.results) <= 10

    @pytest.mark.asyncio
    async def test_search_relevance_scores(self, lasan_service):
        """Test that relevance scores are in valid range."""
        result = await lasan_service.query_knowledge_base(
            query="S.A.F.E. centers for hazardous waste",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

        # All relevance scores should be between 0 and 1
        for chunk in result.results:
            assert 0 <= chunk.relevance_score <= 1.0
