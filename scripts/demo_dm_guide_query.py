#!/usr/bin/env python3
"""
Quick test script to verify DM Guide ingestion works.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.core.chroma_manager import ChromaDBManager

def test_query(query: str, n_results: int = 3):
    """Test a query against the dm_guide collection."""
    print(f"\n{'='*70}")
    print(f"Query: '{query}'")
    print('='*70)

    db_manager = ChromaDBManager()
    results = db_manager.search('dm_guide', query, n_results=n_results)

    if results and results['documents'] and results['documents'][0]:
        print(f"\nFound {len(results['documents'][0])} results:\n")

        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            print(f"\n--- Result {i} (distance: {distance:.3f}) ---")
            print(f"Section: {metadata.get('section', 'Unknown')}")
            print(f"Pages: {metadata.get('page_start', '?')}-{metadata.get('page_end', '?')}")
            print(f"\nContent preview (first 500 chars):")
            print(doc[:500])
            print("...")
    else:
        print("\nNo results found!")

if __name__ == '__main__':
    # Test queries
    test_query("Ring of Protection", n_results=2)
    test_query("magic items for wizards", n_results=2)
    test_query("treasure hoard", n_results=2)

    print("\n" + "="*70)
    print("✅ DM Guide query test complete!")
    print("="*70)
