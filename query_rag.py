#!/usr/bin/env python3
"""
Interactive RAG Query Tool

Query the D&D RAG system from the command line.
Can search spells, monsters, classes, and races.

Usage:
    python query_rag.py                    # Interactive mode
    python query_rag.py "fireball"         # Quick search all collections
    python query_rag.py --spells "healing" # Search specific collection
"""

import argparse
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings


def format_result(doc: str, meta: dict, distance: float, index: int) -> str:
    """Format a search result for display"""
    name = meta.get('name', 'Unknown')
    content_type = meta.get('content_type', 'unknown')
    chunk_type = meta.get('chunk_type', '')

    # Build header
    header = f"{index}. {name}"

    # Add type-specific info
    if content_type == 'spell':
        level = meta.get('level', '?')
        school = meta.get('school', '?')
        header += f" (Level {level} {school})"
    elif content_type == 'monster':
        cr = meta.get('challenge_rating', '?')
        monster_type = meta.get('monster_type', '')
        header += f" (CR {cr})"
        if monster_type:
            header += f" - {monster_type}"
    elif content_type == 'race':
        size = meta.get('size', '')
        if size:
            header += f" ({size})"

    # Build output
    output = f"\n{header}"
    output += f"\n   Type: {content_type} ({chunk_type})"
    output += f"\n   Relevance: {1 - distance:.3f}"

    # Extract preview (skip the weighted name prefix)
    preview = doc
    if 'SPELL:' in doc or 'MONSTER:' in doc or 'CLASS:' in doc or 'RACE:' in doc:
        lines = doc.split('\n')
        # Skip first few lines with weighting
        content_start = 3  # Skip "TYPE: name", "name", blank line
        preview = '\n'.join(lines[content_start:])

    # Show first 200 chars
    preview = preview.strip()[:200]
    if len(doc) > 200:
        preview += "..."

    output += f"\n   {preview}"

    return output


def search_collection(db: ChromaDBManager, collection_name: str, query: str, n_results: int = 3):
    """Search a specific collection"""
    try:
        results = db.search(collection_name, query, n_results=n_results)

        if not results or not results['documents'] or len(results['documents'][0]) == 0:
            print(f"   No results found in {collection_name}")
            return

        print(f"\n🔍 Results from {collection_name}:")
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            print(format_result(doc, meta, distance, i))

    except Exception as e:
        print(f"   ❌ Error searching {collection_name}: {e}")


def search_all(db: ChromaDBManager, query: str, n_results: int = 2):
    """Search all collections"""
    print(f"\n{'='*70}")
    print(f"🔍 Searching for: '{query}'")
    print(f"{'='*70}")

    for name, collection_name in settings.COLLECTION_NAMES.items():
        try:
            stats = db.get_collection_stats(collection_name)
            if stats.get('total_documents', 0) > 0:
                search_collection(db, collection_name, query, n_results)
        except Exception:
            continue


def interactive_mode(db: ChromaDBManager):
    """Run in interactive mode"""
    print("="*70)
    print("🎲 D&D RAG SYSTEM - Interactive Query Tool")
    print("="*70)
    print("\nCommands:")
    print("  /spell <query>    - Search spells only")
    print("  /monster <query>  - Search monsters only")
    print("  /class <query>    - Search classes only")
    print("  /race <query>     - Search races only")
    print("  /all <query>      - Search all collections (default)")
    print("  /stats            - Show collection statistics")
    print("  /help             - Show this help")
    print("  /quit or Ctrl+C   - Exit")
    print("\nJust type your query to search all collections.")
    print("="*70)

    while True:
        try:
            query = input("\n🎲 Query: ").strip()

            if not query:
                continue

            # Handle commands
            if query.startswith('/quit') or query.startswith('/exit'):
                print("👋 Goodbye!")
                break

            elif query.startswith('/help'):
                print("\nAvailable commands listed above.")
                continue

            elif query.startswith('/stats'):
                print("\n📊 Collection Statistics:")
                stats = db.get_all_stats()
                for collection_name, col_stats in stats['collections'].items():
                    count = col_stats.get('total_documents', 0)
                    print(f"   {collection_name}: {count} documents")
                continue

            elif query.startswith('/spell '):
                search_text = query[7:].strip()
                search_collection(db, settings.COLLECTION_NAMES['spells'], search_text, 5)

            elif query.startswith('/monster '):
                search_text = query[9:].strip()
                search_collection(db, settings.COLLECTION_NAMES['monsters'], search_text, 5)

            elif query.startswith('/class '):
                search_text = query[7:].strip()
                search_collection(db, settings.COLLECTION_NAMES['classes'], search_text, 5)

            elif query.startswith('/race '):
                search_text = query[6:].strip()
                search_collection(db, settings.COLLECTION_NAMES['races'], search_text, 5)

            elif query.startswith('/all '):
                search_text = query[5:].strip()
                search_all(db, search_text, 3)

            else:
                # Default: search all
                search_all(db, query, 2)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Query the D&D RAG system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query_rag.py                          # Interactive mode
  python query_rag.py "fireball"               # Quick search
  python query_rag.py --spell "healing"        # Search spells only
  python query_rag.py --monster "dragon" -n 5  # Get 5 results
        """
    )

    parser.add_argument('query', nargs='?', help='Search query (interactive mode if not provided)')
    parser.add_argument('--spell', action='store_true', help='Search spells only')
    parser.add_argument('--monster', action='store_true', help='Search monsters only')
    parser.add_argument('--class', action='store_true', dest='class_search', help='Search classes only')
    parser.add_argument('--race', action='store_true', help='Search races only')
    parser.add_argument('-n', '--results', type=int, default=3, help='Number of results (default: 3)')

    args = parser.parse_args()

    # Initialize database
    try:
        db = ChromaDBManager()
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        print("\nMake sure to run: python initialize_rag.py")
        sys.exit(1)

    # Interactive mode if no query
    if not args.query:
        interactive_mode(db)
        return

    # Single query mode
    if args.spell:
        search_collection(db, settings.COLLECTION_NAMES['spells'], args.query, args.results)
    elif args.monster:
        search_collection(db, settings.COLLECTION_NAMES['monsters'], args.query, args.results)
    elif args.class_search:
        search_collection(db, settings.COLLECTION_NAMES['classes'], args.query, args.results)
    elif args.race:
        search_collection(db, settings.COLLECTION_NAMES['races'], args.query, args.results)
    else:
        search_all(db, args.query, args.results)


if __name__ == '__main__':
    main()
