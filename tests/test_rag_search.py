#!/usr/bin/env python3
"""
Test RAG Search Functionality

Tests that spells, monsters, classes, and races can be found via semantic search.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings


def test_spell_search(db: ChromaDBManager):
    """Test spell searches."""
    print("\n" + "="*70)
    print("🔮 TESTING SPELL SEARCHES")
    print("="*70)

    test_queries = [
        "fireball spell",
        "healing magic",
        "wizard cantrip",
        "magic missile damage",
        "cure wounds"
    ]

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = db.search(settings.COLLECTION_NAMES['spells'], query, n_results=3)

        if results['documents'] and results['documents'][0]:
            print(f"✓ Found {len(results['documents'][0])} results")
            # Show top result
            top_doc = results['documents'][0][0]
            top_meta = results['metadatas'][0][0]
            distance = results['distances'][0][0]

            print(f"  Top result: {top_meta.get('name', 'Unknown')}")
            print(f"  Distance: {distance:.3f}")
            print(f"  Preview: {top_doc[:100]}...")
        else:
            print("✗ No results found")


def test_monster_search(db: ChromaDBManager):
    """Test monster searches."""
    print("\n" + "="*70)
    print("👹 TESTING MONSTER SEARCHES")
    print("="*70)

    test_queries = [
        "goblin",
        "dragon fire breath",
        "undead creature",
        "challenge rating 5",
        "orc warrior"
    ]

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = db.search(settings.COLLECTION_NAMES['monsters'], query, n_results=3)

        if results['documents'] and results['documents'][0]:
            print(f"✓ Found {len(results['documents'][0])} results")
            # Show top result
            top_doc = results['documents'][0][0]
            top_meta = results['metadatas'][0][0]
            distance = results['distances'][0][0]

            print(f"  Top result: {top_meta.get('name', 'Unknown')}")
            print(f"  CR: {top_meta.get('challenge_rating', 'Unknown')}")
            print(f"  Distance: {distance:.3f}")
            print(f"  Preview: {top_doc[:100]}...")
        else:
            print("✗ No results found")


def test_class_search(db: ChromaDBManager):
    """Test class searches."""
    print("\n" + "="*70)
    print("⚔️  TESTING CLASS SEARCHES")
    print("="*70)

    test_queries = [
        "wizard spellcasting",
        "fighter extra attack",
        "rogue sneak attack",
        "barbarian rage",
        "cleric healing"
    ]

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = db.search(settings.COLLECTION_NAMES['classes'], query, n_results=3)

        if results['documents'] and results['documents'][0]:
            print(f"✓ Found {len(results['documents'][0])} results")
            # Show top result
            top_doc = results['documents'][0][0]
            top_meta = results['metadatas'][0][0]
            distance = results['distances'][0][0]

            print(f"  Top result: {top_meta.get('name', 'Unknown')}")
            print(f"  Distance: {distance:.3f}")
            print(f"  Preview: {top_doc[:100]}...")
        else:
            print("✗ No results found")


def test_cross_collection_search(db: ChromaDBManager):
    """Test searching across multiple collections."""
    print("\n" + "="*70)
    print("🔍 TESTING CROSS-COLLECTION SEARCH")
    print("="*70)

    query = "fire damage"
    print(f"\nQuery: '{query}' (searching all collections)")

    results = db.search_all(query, n_results_per_collection=2)

    for collection_name, col_results in results.items():
        if col_results['documents'] and col_results['documents'][0]:
            print(f"\n  {collection_name}:")
            for doc, meta in zip(col_results['documents'][0], col_results['metadatas'][0]):
                print(f"    - {meta.get('name', 'Unknown')}")


def test_stats(db: ChromaDBManager):
    """Show collection statistics."""
    print("\n" + "="*70)
    print("📊 COLLECTION STATISTICS")
    print("="*70)

    stats = db.get_all_stats()

    print(f"\nTotal documents: {stats['total_documents']}")
    print(f"Database: {stats['persist_dir']}")
    print(f"Embedding model: {stats['embedding_model']}")

    print("\nCollections:")
    for collection_name, col_stats in stats['collections'].items():
        total = col_stats.get('total_documents', 0)
        print(f"  {collection_name}: {total} documents")

        if 'chunk_types' in col_stats:
            for chunk_type, count in col_stats['chunk_types'].items():
                print(f"    - {chunk_type}: {count}")


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("🧪 D&D RAG SEARCH TEST SUITE")
    print("="*70)

    # Initialize database connection
    print("\n🔧 Connecting to ChromaDB...")
    db = ChromaDBManager()

    # Run tests
    try:
        test_stats(db)
        test_spell_search(db)
        test_monster_search(db)
        test_class_search(db)
        test_cross_collection_search(db)

        print("\n" + "="*70)
        print("✅ TEST SUITE COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
