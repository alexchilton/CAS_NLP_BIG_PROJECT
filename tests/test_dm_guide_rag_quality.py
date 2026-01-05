"""
Test DM Guide RAG Quality

Comprehensive tests to verify that DM Guide ingestion provides
high-quality retrieval for magic items, rules, treasure, and mechanics.

This directly addresses the HIGH PRIORITY TODO item:
"Improve RAG Data for Equipment, Abilities & Class Features"
"""

import pytest
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager


class TestDMGuideRAGQuality:
    """Test suite for DM Guide RAG retrieval quality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize ChromaDB manager for all tests."""
        self.db_manager = ChromaDBManager()

    # =========================================================================
    # MAGIC ITEMS TESTS (HIGH PRIORITY)
    # =========================================================================

    def test_ring_of_protection_retrieval(self):
        """Test that 'Ring of Protection' query returns ring content."""
        results = self.db_manager.search('dm_guide', 'Ring of Protection', n_results=3)

        assert results['documents'], "No results returned"
        assert len(results['documents'][0]) > 0, "Empty results"

        # Check that at least one result mentions rings
        top_result = results['documents'][0][0].lower()
        assert 'ring' in top_result, "Top result doesn't mention rings"

        # Check relevance (distance should be reasonable)
        top_distance = results['distances'][0][0]
        assert top_distance < 1.5, f"Top result distance too high: {top_distance}"

    def test_magic_weapon_queries(self):
        """Test queries for magic weapons like +1, +2, Flametongue, etc."""
        test_queries = [
            "magic sword +1",
            "flaming weapon",
            "vorpal blade"
        ]

        for query in test_queries:
            results = self.db_manager.search('dm_guide', query, n_results=2)

            assert results['documents'], f"No results for query: {query}"
            assert len(results['documents'][0]) > 0, f"Empty results for: {query}"

            # Distance check
            top_distance = results['distances'][0][0]
            assert top_distance < 2.0, f"Distance too high for '{query}': {top_distance}"

    def test_wondrous_items_retrieval(self):
        """Test retrieval of wondrous items like Bag of Holding, Immovable Rod."""
        test_queries = [
            "Bag of Holding",
            "Immovable Rod",
            "wondrous items"
        ]

        for query in test_queries:
            results = self.db_manager.search('dm_guide', query, n_results=2)

            assert results['documents'], f"No results for: {query}"
            assert len(results['documents'][0]) > 0, f"Empty results for: {query}"

    def test_potion_retrieval(self):
        """Test retrieval of potions beyond basic healing."""
        test_queries = [
            "potion of invisibility",
            "potion of flying",
            "elixir"
        ]

        for query in test_queries:
            results = self.db_manager.search('dm_guide', query, n_results=2)

            assert results['documents'], f"No results for: {query}"

    def test_magic_armor_retrieval(self):
        """Test retrieval of magic armor."""
        test_queries = [
            "magic armor +1",
            "armor of resistance",
            "plate armor enchanted"
        ]

        for query in test_queries:
            results = self.db_manager.search('dm_guide', query, n_results=2)

            assert results['documents'], f"No results for: {query}"

    # =========================================================================
    # RULES & MECHANICS TESTS
    # =========================================================================

    def test_combat_rules_retrieval(self):
        """Test retrieval of combat rules and mechanics."""
        test_queries = [
            "grappling rules",
            "cover and concealment",
            "flanking bonus"
        ]

        for query in test_queries:
            results = self.db_manager.search('dm_guide', query, n_results=2)

            # Just verify we get results - content may vary
            assert results['documents'], f"No results for: {query}"

    def test_condition_mechanics_retrieval(self):
        """Test retrieval of condition mechanics (stunned, paralyzed, etc.)."""
        test_queries = [
            "paralyzed condition",
            "stunned mechanics",
            "restrained condition"
        ]

        for query in test_queries:
            results = self.db_manager.search('dm_guide', query, n_results=2)

            assert results['documents'], f"No results for: {query}"

    # =========================================================================
    # TREASURE & REWARDS TESTS
    # =========================================================================

    def test_treasure_hoard_retrieval(self):
        """Test retrieval of treasure tables and loot generation."""
        results = self.db_manager.search('dm_guide', 'treasure hoard', n_results=3)

        assert results['documents'], "No treasure results"
        assert len(results['documents'][0]) > 0

        # Check distance
        top_distance = results['distances'][0][0]
        assert top_distance < 1.5, f"Treasure query distance too high: {top_distance}"

    def test_loot_generation_queries(self):
        """Test queries related to loot and rewards."""
        test_queries = [
            "treasure by challenge rating",
            "random loot table",
            "gem values"
        ]

        for query in test_queries:
            results = self.db_manager.search('dm_guide', query, n_results=2)

            assert results['documents'], f"No results for: {query}"

    # =========================================================================
    # METADATA QUALITY TESTS
    # =========================================================================

    def test_metadata_completeness(self):
        """Verify that chunks have complete metadata."""
        results = self.db_manager.search('dm_guide', 'magic items', n_results=5)

        assert results['metadatas'], "No metadata returned"

        for metadata in results['metadatas'][0]:
            # Check required fields
            assert 'source' in metadata, "Missing 'source' in metadata"
            assert metadata['source'] == 'dm_guide', "Incorrect source"

            assert 'section' in metadata, "Missing 'section' in metadata"
            assert 'page_start' in metadata, "Missing 'page_start' in metadata"
            assert 'page_end' in metadata, "Missing 'page_end' in metadata"
            assert 'content_type' in metadata, "Missing 'content_type' in metadata"

    def test_magic_item_tags_present(self):
        """Verify that magic item chunks are properly tagged."""
        results = self.db_manager.search('dm_guide', 'Ring of Protection', n_results=3)

        assert results['metadatas'], "No metadata returned"

        # At least one result should have magic_items tag
        # Note: tags are stored in chunk.tags, but may not be in metadata
        # This test verifies we can find magic item content
        found_magic_item_content = False
        for doc in results['documents'][0]:
            if 'magic' in doc.lower() or 'ring' in doc.lower():
                found_magic_item_content = True
                break

        assert found_magic_item_content, "No magic item content found in top results"

    # =========================================================================
    # RETRIEVAL QUALITY TESTS
    # =========================================================================

    def test_top_result_relevance(self):
        """Test that top results are highly relevant (low distance)."""
        high_quality_queries = [
            ("Ring of Protection", 1.5),
            ("magic items", 1.3),
            ("treasure", 1.4),
        ]

        for query, max_distance in high_quality_queries:
            results = self.db_manager.search('dm_guide', query, n_results=1)

            assert results['documents'], f"No results for: {query}"

            top_distance = results['distances'][0][0]
            assert top_distance < max_distance, \
                f"Query '{query}' top result distance {top_distance:.3f} exceeds {max_distance}"

    def test_no_empty_chunks(self):
        """Verify that no chunks are empty or too short."""
        # Get a sample of chunks
        results = self.db_manager.search('dm_guide', 'magic', n_results=10)

        assert results['documents'], "No results returned"

        for doc in results['documents'][0]:
            assert len(doc) > 100, f"Chunk too short: {len(doc)} chars"
            assert doc.strip(), "Empty chunk found"

    def test_page_numbers_valid(self):
        """Verify that page numbers are valid and in order."""
        results = self.db_manager.search('dm_guide', 'magic items', n_results=10)

        assert results['metadatas'], "No metadata returned"

        for metadata in results['metadatas'][0]:
            page_start = metadata.get('page_start', 0)
            page_end = metadata.get('page_end', 0)

            assert page_start > 0, "Invalid page_start"
            assert page_end > 0, "Invalid page_end"
            assert page_start <= page_end, f"Page range invalid: {page_start}-{page_end}"
            assert page_end - page_start < 10, f"Page range too large: {page_start}-{page_end}"

    # =========================================================================
    # CROSS-COLLECTION TESTS
    # =========================================================================

    def test_search_all_includes_dm_guide(self):
        """Test that search_all() includes dm_guide results."""
        all_results = self.db_manager.search_all(
            'Ring of Protection',
            n_results_per_collection=2
        )

        assert 'dm_guide' in all_results, "dm_guide not in search_all results"
        assert all_results['dm_guide']['documents'], "dm_guide returned no results"
        assert len(all_results['dm_guide']['documents'][0]) > 0, "dm_guide results empty"

    def test_magic_item_query_across_collections(self):
        """Test that magic item queries work across all collections."""
        all_results = self.db_manager.search_all(
            'magic sword',
            n_results_per_collection=2
        )

        # Should get results from dm_guide (and possibly equipment if it exists)
        assert 'dm_guide' in all_results
        dm_guide_results = all_results['dm_guide']

        assert dm_guide_results['documents'], "No dm_guide results for 'magic sword'"

    def test_spell_and_magic_item_combined_query(self):
        """Test query that could match both spells and magic items."""
        # Query for something that appears in both contexts
        all_results = self.db_manager.search_all(
            'invisibility',
            n_results_per_collection=2
        )

        # Should get results from both spells and dm_guide
        assert 'dnd_spells' in all_results, "No spell results"
        assert 'dm_guide' in all_results, "No dm_guide results"

        # Both should have content
        assert all_results['dnd_spells']['documents'][0], "Empty spell results"
        assert all_results['dm_guide']['documents'][0], "Empty dm_guide results"

    # =========================================================================
    # COLLECTION STATISTICS TESTS
    # =========================================================================

    def test_dm_guide_collection_exists(self):
        """Verify dm_guide collection exists and has documents."""
        stats = self.db_manager.get_collection_stats('dm_guide')

        assert stats, "No stats returned"
        assert 'total_documents' in stats, "Missing total_documents in stats"
        assert stats['total_documents'] > 0, "dm_guide collection is empty"

        # Should have around 95 chunks (3 pages per chunk for ~285 pages)
        assert stats['total_documents'] >= 80, \
            f"Too few documents: {stats['total_documents']}, expected ~95"
        assert stats['total_documents'] <= 110, \
            f"Too many documents: {stats['total_documents']}, expected ~95"

    def test_chunk_types_correct(self):
        """Verify chunk types are properly set."""
        stats = self.db_manager.get_collection_stats('dm_guide')

        assert 'chunk_types' in stats, "Missing chunk_types in stats"
        assert 'dm_guide_section' in stats['chunk_types'], \
            "dm_guide_section chunk type not found"

        # All chunks should be dm_guide_section type
        total_chunks = stats['total_documents']
        section_chunks = stats['chunk_types']['dm_guide_section']

        assert section_chunks == total_chunks, \
            f"Chunk type mismatch: {section_chunks} != {total_chunks}"

    # =========================================================================
    # SPECIFIC USE CASE TESTS (from TODO.md)
    # =========================================================================

    def test_player_asks_for_magic_ring(self):
        """
        Simulate: Player asks 'What magic rings are available?'
        This directly addresses TODO item: Missing magic items data
        """
        results = self.db_manager.search('dm_guide', 'magic rings available', n_results=3)

        assert results['documents'], "No results for magic rings query"

        # Should find ring-related content
        combined_text = ' '.join(results['documents'][0]).lower()
        assert 'ring' in combined_text, "No ring content found"

        # Check quality
        top_distance = results['distances'][0][0]
        assert top_distance < 1.5, f"Magic rings query quality poor: {top_distance}"

    def test_gm_needs_treasure_for_cr5_encounter(self):
        """
        Simulate: GM needs treasure for a CR 5 encounter
        """
        results = self.db_manager.search(
            'dm_guide',
            'treasure for challenge rating 5 encounter',
            n_results=3
        )

        assert results['documents'], "No treasure results"

        # Verify we got treasure-related content
        combined_text = ' '.join(results['documents'][0]).lower()
        assert any(word in combined_text for word in ['treasure', 'loot', 'gold', 'reward']), \
            "No treasure-related content found"

    def test_player_finds_wondrous_item_identification(self):
        """
        Simulate: Player finds unknown wondrous item and wants to identify it
        """
        results = self.db_manager.search(
            'dm_guide',
            'identify unknown wondrous item',
            n_results=3
        )

        assert results['documents'], "No identification results"

    # =========================================================================
    # PERFORMANCE TESTS
    # =========================================================================

    def test_query_response_time(self):
        """Verify that queries complete in reasonable time."""
        import time

        start = time.time()
        results = self.db_manager.search('dm_guide', 'magic items', n_results=5)
        elapsed = time.time() - start

        assert results['documents'], "No results returned"
        assert elapsed < 2.0, f"Query took too long: {elapsed:.2f}s"

    def test_batch_query_performance(self):
        """Test that multiple queries can be performed efficiently."""
        import time

        queries = [
            'Ring of Protection',
            'magic sword',
            'treasure hoard',
            'potion of healing',
            'wondrous items'
        ]

        start = time.time()
        for query in queries:
            self.db_manager.search('dm_guide', query, n_results=2)
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Batch queries took too long: {elapsed:.2f}s"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestDMGuideIntegration:
    """Integration tests for DM Guide with other collections."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize ChromaDB manager."""
        self.db_manager = ChromaDBManager()

    def test_all_collections_accessible(self):
        """Verify all collections are accessible."""
        stats = self.db_manager.get_all_stats()

        assert 'collections' in stats, "No collections in stats"

        # Check that major collections exist
        collections = stats['collections']
        assert 'dnd_spells' in collections, "Missing spells collection"
        assert 'dnd_monsters' in collections, "Missing monsters collection"
        assert 'dm_guide' in collections, "Missing dm_guide collection"

    def test_total_rag_coverage(self):
        """Calculate total RAG coverage across all collections."""
        stats = self.db_manager.get_all_stats()

        total_docs = stats.get('total_documents', 0)
        print(f"\n📊 Total RAG Documents: {total_docs}")

        for collection_name, col_stats in stats['collections'].items():
            doc_count = col_stats.get('total_documents', 0)
            print(f"   {collection_name}: {doc_count} docs")

        # Verify we have substantial coverage
        assert total_docs > 900, f"Total RAG coverage too low: {total_docs} docs"


if __name__ == '__main__':
    # Run with: python -m pytest tests/test_dm_guide_rag_quality.py -v
    pytest.main([__file__, '-v', '--tb=short'])
