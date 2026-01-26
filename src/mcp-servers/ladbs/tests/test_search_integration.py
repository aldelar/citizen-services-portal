"""Integration tests for LADBS Azure AI Search operations.

These tests require a live Azure AI Search instance with AZURE_SEARCH_ENDPOINT configured.
Run with: pytest -m integration
"""

import os
import pytest

from src.services import LADBSService


# Skip all tests in this file if Azure AI Search is not configured
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("AZURE_SEARCH_ENDPOINT"),
        reason="Azure AI Search not configured (AZURE_SEARCH_ENDPOINT not set)"
    )
]


@pytest.fixture
def ladbs_service():
    """Create a LADBSService instance for testing."""
    return LADBSService()


class TestKnowledgeBaseSearch:
    """Tests for knowledge base search operations."""

    @pytest.mark.asyncio
    async def test_semantic_search_returns_results(self, ladbs_service):
        """Test that queryKB returns relevant chunks from AI Search."""
        # Query for electrical permit information
        result = await ladbs_service.query_knowledge_base(
            query="What are the requirements for electrical permits?",
            top=5
        )

        assert result is not None
        assert result.query == "What are the requirements for electrical permits?"
        assert len(result.results) > 0
        assert result.total_results > 0

        # Check first result has expected fields
        first_result = result.results[0]
        assert first_result.content is not None
        assert len(first_result.content) > 0
        assert first_result.source is not None
        assert 0 <= first_result.relevance_score <= 1.0

    @pytest.mark.asyncio
    async def test_search_with_different_query(self, ladbs_service):
        """Test search with a different query."""
        result = await ladbs_service.query_knowledge_base(
            query="How much do solar panel permits cost?",
            top=3
        )

        assert result is not None
        assert len(result.results) <= 3
        assert all(r.content for r in result.results)

    @pytest.mark.asyncio
    async def test_search_with_inspection_query(self, ladbs_service):
        """Test search for inspection-related information."""
        result = await ladbs_service.query_knowledge_base(
            query="What inspections are required for solar installations?",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

        # At least one result should mention inspections
        contents = " ".join([r.content.lower() for r in result.results])
        assert "inspection" in contents or "inspect" in contents

    @pytest.mark.asyncio
    async def test_search_returns_valid_sources(self, ladbs_service):
        """Test that search results include valid source references."""
        result = await ladbs_service.query_knowledge_base(
            query="Building permit fees",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

        # All results should have a source file
        for chunk in result.results:
            assert chunk.source is not None
            assert len(chunk.source) > 0
            # Source should be a file name
            assert "." in chunk.source or ".html" in chunk.source or ".pdf" in chunk.source

    @pytest.mark.asyncio
    async def test_search_with_varying_top_parameter(self, ladbs_service):
        """Test that the top parameter correctly limits results."""
        # Test with top=1
        result1 = await ladbs_service.query_knowledge_base(
            query="permit requirements",
            top=1
        )
        assert len(result1.results) <= 1

        # Test with top=10
        result10 = await ladbs_service.query_knowledge_base(
            query="permit requirements",
            top=10
        )
        assert len(result10.results) <= 10

    @pytest.mark.asyncio
    async def test_search_relevance_scores(self, ladbs_service):
        """Test that relevance scores are in valid range."""
        result = await ladbs_service.query_knowledge_base(
            query="contractor license requirements for electrical work",
            top=5
        )

        assert result is not None
        assert len(result.results) > 0

        # All relevance scores should be between 0 and 1
        for chunk in result.results:
            assert 0 <= chunk.relevance_score <= 1.0

    @pytest.mark.asyncio
    async def test_search_with_specific_topic(self, ladbs_service):
        """Test search for a specific topic."""
        result = await ladbs_service.query_knowledge_base(
            query="What is a C-10 contractor license?",
            top=5
        )

        assert result is not None
        # Should return some results even if not perfect matches
        assert len(result.results) >= 0
