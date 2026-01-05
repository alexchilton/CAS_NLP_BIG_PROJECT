#!/usr/bin/env python3
"""
DM Guide PDF Ingestion Script

Loads the entire DM Guide PDF into ChromaDB with intelligent chunking.
Chunks by page groups and section headers for optimal retrieval.

Usage:
    python ingest_dm_guide.py [--clear]
"""

import argparse
import sys
import re
from pathlib import Path
from typing import List, Dict, Any

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import core infrastructure
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.core.base_chunker import Chunk
from dnd_rag_system.config import settings


def extract_text_from_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Extract text from DM Guide PDF, organized by pages.

    Returns:
        List of dicts with page_number and text
    """
    try:
        import pdfplumber
    except ImportError:
        print("❌ pdfplumber not installed. Install with: pip install pdfplumber")
        sys.exit(1)

    print(f"📖 Reading PDF: {pdf_path}")

    pages_data = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"   Total pages: {total_pages}")

            for i, page in enumerate(pdf.pages):
                page_num = i + 1

                # Extract text
                text = page.extract_text()

                if text and len(text.strip()) > 50:  # Skip mostly empty pages
                    pages_data.append({
                        'page_number': page_num,
                        'text': text.strip()
                    })

                # Progress indicator
                if page_num % 50 == 0:
                    print(f"   Processed {page_num}/{total_pages} pages...")

        print(f"✓ Extracted text from {len(pages_data)} pages (skipped empty pages)")
        return pages_data

    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        sys.exit(1)


def detect_section_header(text: str) -> str:
    """
    Try to detect if this page starts with a major section header.

    Returns:
        Section name if detected, empty string otherwise
    """
    # Common DM Guide section patterns
    lines = text.split('\n')[:5]  # Check first 5 lines

    for line in lines:
        line_clean = line.strip()

        # All caps lines that are short (likely headers)
        if line_clean.isupper() and 5 < len(line_clean) < 60:
            # Skip common non-headers
            if line_clean not in ['CONTENTS', 'INDEX', 'PAGE']:
                return line_clean.title()

        # Chapter patterns
        chapter_match = re.match(r'^(Chapter\s+\d+)[:\s]*(.+?)$', line_clean, re.IGNORECASE)
        if chapter_match:
            return f"{chapter_match.group(1)}: {chapter_match.group(2)}"

    return ""


def create_chunks_from_pages(pages_data: List[Dict[str, Any]], pages_per_chunk: int = 3) -> List[Chunk]:
    """
    Create chunks from page data.

    Strategy:
    - Group pages into chunks (default 3 pages per chunk for ~1500-2000 tokens)
    - Detect section headers and create metadata
    - Add page numbers for reference

    Args:
        pages_data: List of page dictionaries
        pages_per_chunk: How many pages to combine per chunk

    Returns:
        List of Chunk objects
    """
    chunks = []
    current_section = "Introduction"

    print(f"\n📦 Creating chunks ({pages_per_chunk} pages per chunk)...")

    i = 0
    while i < len(pages_data):
        # Get pages for this chunk
        chunk_pages = pages_data[i:i + pages_per_chunk]

        if not chunk_pages:
            break

        # Check if first page has a section header
        first_page_text = chunk_pages[0]['text']
        section_header = detect_section_header(first_page_text)

        if section_header:
            current_section = section_header

        # Combine text from all pages in chunk
        combined_text = "\n\n".join([
            f"[Page {p['page_number']}]\n{p['text']}"
            for p in chunk_pages
        ])

        # Create metadata
        page_numbers = [p['page_number'] for p in chunk_pages]
        metadata = {
            'source': 'dm_guide',
            'section': current_section,
            'page_start': page_numbers[0],
            'page_end': page_numbers[-1],
            'content_type': 'dm_guide'
        }

        # Create tags
        tags = {'dm_guide', 'rules'}

        # Add section-based tags
        section_lower = current_section.lower()
        if 'magic item' in section_lower or 'treasure' in section_lower:
            tags.add('magic_items')
            tags.add('treasure')
        elif 'combat' in section_lower:
            tags.add('combat')
        elif 'monster' in section_lower or 'creature' in section_lower:
            tags.add('monsters')
        elif 'encounter' in section_lower:
            tags.add('encounters')

        # Create chunk with section header emphasized
        chunk_content = f"DM GUIDE - {current_section}\n\n{combined_text}"

        chunk = Chunk(
            content=chunk_content,
            chunk_type='dm_guide_section',
            metadata=metadata,
            tags=tags
        )

        chunks.append(chunk)

        # Progress
        if (len(chunks) % 20) == 0:
            print(f"   Created {len(chunks)} chunks (pages {page_numbers[0]}-{page_numbers[-1]})")

        i += pages_per_chunk

    print(f"✓ Created {len(chunks)} total chunks")
    return chunks


def detect_magic_items_in_chunk(chunk: Chunk) -> bool:
    """
    Heuristic to detect if a chunk likely contains magic item descriptions.
    Updates chunk tags if detected.
    """
    text_lower = chunk.content.lower()

    # Magic item indicators
    indicators = [
        'wondrous item',
        'requires attunement',
        'uncommon',
        'rare',
        'very rare',
        'legendary',
        'ring of',
        'cloak of',
        'boots of',
        '+1 ',
        '+2 ',
        '+3 ',
        'potion of',
        'scroll of'
    ]

    # Count matches
    matches = sum(1 for indicator in indicators if indicator in text_lower)

    if matches >= 2:  # At least 2 indicators = likely magic item content
        chunk.tags.add('magic_items')
        chunk.metadata['contains_magic_items'] = True
        return True

    return False


def load_dm_guide(db_manager: ChromaDBManager, clear: bool = False, pages_per_chunk: int = 3):
    """
    Load DM Guide into ChromaDB.

    Args:
        db_manager: ChromaDB manager instance
        clear: Whether to clear existing collection
        pages_per_chunk: How many pages to combine per chunk
    """
    print("\n" + "="*70)
    print("📚 LOADING DM GUIDE")
    print("="*70)

    collection_name = 'dm_guide'

    # Clear if requested
    if clear:
        print(f"\n🗑️  Clearing existing '{collection_name}' collection...")
        db_manager.clear_collection(collection_name)

    # Check if PDF exists
    pdf_path = Path(__file__).parent / "dm_guide.pdf"

    if not pdf_path.exists():
        print(f"❌ DM Guide PDF not found: {pdf_path}")
        sys.exit(1)

    # Extract text
    pages_data = extract_text_from_pdf(pdf_path)

    if not pages_data:
        print("❌ No text extracted from PDF")
        sys.exit(1)

    # Create chunks
    chunks = create_chunks_from_pages(pages_data, pages_per_chunk)

    # Enhanced: Detect magic items in chunks
    print("\n🔍 Analyzing chunks for magic items...")
    magic_item_chunks = 0
    for chunk in chunks:
        if detect_magic_items_in_chunk(chunk):
            magic_item_chunks += 1
    print(f"✓ Detected {magic_item_chunks} chunks containing magic items")

    # Add to ChromaDB
    if chunks:
        print(f"\n💾 Adding {len(chunks)} chunks to ChromaDB...")
        db_manager.add_chunks(collection_name, chunks)
        print(f"✅ Successfully loaded {len(chunks)} chunks into '{collection_name}' collection")
    else:
        print("❌ No chunks created")
        sys.exit(1)

    return len(chunks)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Ingest DM Guide PDF into ChromaDB')
    parser.add_argument('--clear', action='store_true', help='Clear existing dm_guide collection')
    parser.add_argument('--pages-per-chunk', type=int, default=3,
                       help='Pages per chunk (default: 3, ~1500-2000 tokens)')
    args = parser.parse_args()

    print("\n" + "="*70)
    print("🎲 DM GUIDE INGESTION")
    print("="*70)

    # Initialize ChromaDB
    print("\n🔧 Initializing ChromaDB...")
    db_manager = ChromaDBManager()

    # Load DM Guide
    chunk_count = load_dm_guide(
        db_manager,
        clear=args.clear,
        pages_per_chunk=args.pages_per_chunk
    )

    # Show stats
    print("\n" + "="*70)
    print("📊 INGESTION SUMMARY")
    print("="*70)
    print(f"  Total chunks: {chunk_count}")
    print(f"  Pages per chunk: {args.pages_per_chunk}")

    # Collection stats
    print("\n📈 Collection Statistics:")
    stats = db_manager.get_collection_stats('dm_guide')
    print(f"  dm_guide: {stats.get('total_documents', 0)} documents")

    if stats.get('chunk_types'):
        print("\n  Chunk types:")
        for chunk_type, count in stats['chunk_types'].items():
            print(f"    {chunk_type}: {count}")

    print("\n🎉 DM Guide ingestion complete!")
    print(f"   Database: {db_manager.persist_dir}")

    print("\n💡 Next steps:")
    print("   - Test search: python query_rag.py")
    print("   - Query example: 'Ring of Protection'")
    print("   - Query example: 'magic items for wizards'")


if __name__ == '__main__':
    main()
