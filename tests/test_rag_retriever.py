"""
Unit tests for RAGRetriever.

Tests the extracted RAG retrieval and formatting logic.
"""

import pytest
from unittest.mock import Mock, MagicMock
from dnd_rag_system.dialogue.rag_retriever import RAGRetriever


@pytest.fixture
def mock_chromadb():
    """Create a mock ChromaDB manager."""
    mock_db = Mock()
    return mock_db


@pytest.fixture
def rag_retriever(mock_chromadb):
    """Create a RAGRetriever instance with mock DB."""
    return RAGRetriever(mock_chromadb)


class TestRAGRetriever:
    """Test suite for RAGRetriever class."""

    def test_initialization(self, mock_chromadb):
        """Test that RAGRetriever initializes correctly."""
        retriever = RAGRetriever(mock_chromadb)
        assert retriever.db == mock_chromadb

    def test_search_rag_returns_dict(self, rag_retriever, mock_chromadb):
        """Test that search_rag returns a dictionary."""
        # Mock the search method to return valid data
        mock_chromadb.search.return_value = {
            'documents': [['Fireball spell description']],
            'metadatas': [[{'name': 'Fireball'}]],
            'distances': [[0.5]]
        }

        results = rag_retriever.search_rag("fireball spell")

        assert isinstance(results, dict)
        assert mock_chromadb.search.called

    def test_search_rag_handles_empty_results(self, rag_retriever, mock_chromadb):
        """Test that search_rag handles empty results gracefully."""
        # Mock empty results
        mock_chromadb.search.return_value = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }

        results = rag_retriever.search_rag("nonexistent")

        assert isinstance(results, dict)
        assert len(results) == 0  # Should skip empty collections

    def test_search_rag_handles_exceptions(self, rag_retriever, mock_chromadb):
        """Test that search_rag handles database exceptions gracefully."""
        # Mock exception
        mock_chromadb.search.side_effect = Exception("Database error")

        results = rag_retriever.search_rag("test query")

        # Should return empty dict, not crash
        assert isinstance(results, dict)

    def test_format_rag_context_empty_results(self, rag_retriever):
        """Test formatting with no results."""
        context = rag_retriever.format_rag_context({})

        assert context == "No specific rules retrieved."

    def test_format_rag_context_filters_by_distance(self, rag_retriever):
        """Test that only results with distance < 1.0 are included."""
        rag_results = {
            'spells': {
                'documents': ['Fireball spell...', 'Lightning bolt...'],
                'metadatas': [{'name': 'Fireball'}, {'name': 'Lightning Bolt'}],
                'distances': [0.5, 1.5]  # Second should be excluded
            }
        }

        context = rag_retriever.format_rag_context(rag_results)

        assert 'Fireball' in context
        assert 'Lightning Bolt' not in context

    def test_format_rag_context_truncates_documents(self, rag_retriever):
        """Test that long documents are truncated to 400 characters."""
        long_doc = "A" * 1000  # 1000 character document
        rag_results = {
            'spells': {
                'documents': [long_doc],
                'metadatas': [{'name': 'Long Spell'}],
                'distances': [0.5]
            }
        }

        context = rag_retriever.format_rag_context(rag_results)

        # Should contain truncated version (400 chars)
        assert len([part for part in context.split('\n') if 'A' in part][0]) <= 450  # Account for prefix

    def test_format_rag_context_includes_collection_type(self, rag_retriever):
        """Test that collection type is included in formatted output."""
        rag_results = {
            'spells': {
                'documents': ['Fireball spell...'],
                'metadatas': [{'name': 'Fireball'}],
                'distances': [0.5]
            },
            'monsters': {
                'documents': ['Goblin description...'],
                'metadatas': [{'name': 'Goblin'}],
                'distances': [0.7]
            }
        }

        context = rag_retriever.format_rag_context(rag_results)

        assert '[SPELLS]' in context
        assert '[MONSTERS]' in context

    def test_format_rag_context_handles_missing_name(self, rag_retriever):
        """Test that missing metadata names are handled gracefully."""
        rag_results = {
            'spells': {
                'documents': ['Some spell...'],
                'metadatas': [{}],  # No 'name' key
                'distances': [0.5]
            }
        }

        context = rag_retriever.format_rag_context(rag_results)

        assert 'Unknown' in context
        assert 'Some spell' in context

    def test_format_rag_context_all_irrelevant(self, rag_retriever):
        """Test formatting when all results are too distant."""
        rag_results = {
            'spells': {
                'documents': ['Fireball...'],
                'metadatas': [{'name': 'Fireball'}],
                'distances': [1.5]  # Too far
            }
        }

        context = rag_retriever.format_rag_context(rag_results)

        assert context == "No highly relevant rules found."

    def test_search_rag_multiple_collections(self, rag_retriever, mock_chromadb):
        """Test searching multiple collections."""
        # Mock settings with multiple collections
        from dnd_rag_system.config import settings
        original_collections = settings.COLLECTION_NAMES

        try:
            settings.COLLECTION_NAMES = {
                'spells': 'dnd_spells',
                'monsters': 'dnd_monsters',
                'items': 'dnd_items'
            }

            mock_chromadb.search.return_value = {
                'documents': [['Test doc']],
                'metadatas': [[{'name': 'Test'}]],
                'distances': [[0.5]]
            }

            results = rag_retriever.search_rag("test")

            # Should have called search for each collection
            assert mock_chromadb.search.call_count == 3

        finally:
            settings.COLLECTION_NAMES = original_collections


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
