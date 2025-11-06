#!/usr/bin/env python3
"""
D&D RAG System Initialization Script

Loads all D&D content into ChromaDB using existing notebook parsing code.
This is a pragmatic wrapper that uses proven parsing logic.

Usage:
    python initialize_rag.py [--clear] [--only spells,monsters,classes,races]

Examples:
    python initialize_rag.py                    # Load all content
    python initialize_rag.py --clear            # Clear and reload all
    python initialize_rag.py --only spells      # Load only spells
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
import re

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our core infrastructure
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.core.base_chunker import Chunk
from dnd_rag_system.config import settings


# =============================================================================
# SPELL LOADER (adapted from rag_spells2.ipynb)
# =============================================================================

def load_spells(db_manager: ChromaDBManager, clear: bool = False):
    """Load spells from spells.txt and all_spells.txt into ChromaDB."""

    print("\n" + "="*70)
    print("📚 LOADING SPELLS")
    print("="*70)

    if clear:
        db_manager.clear_collection(settings.COLLECTION_NAMES['spells'])

    # Read spells.txt
    print(f"📖 Reading {settings.SPELLS_TXT}")
    with open(settings.SPELLS_TXT, 'r', encoding='utf-8') as f:
        spells_content = f.read()

    # Simple spell parsing (adapted from your notebook)
    spell_blocks = _split_spell_blocks(spells_content)
    print(f"✓ Found {len(spell_blocks)} spell blocks")

    # Create chunks
    chunks = []
    for i, block in enumerate(spell_blocks):
        try:
            spell_chunk = _parse_spell_to_chunk(block)
            if spell_chunk:
                chunks.append(spell_chunk)

            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(spell_blocks)} spells...")
        except Exception as e:
            print(f"  Warning: Failed to parse spell {i+1}: {e}")
            continue

    print(f"✓ Created {len(chunks)} spell chunks")

    # Add to ChromaDB
    if chunks:
        db_manager.add_chunks(settings.COLLECTION_NAMES['spells'], chunks)
        print(f"✅ Loaded {len(chunks)} spells into ChromaDB")

    return len(chunks)


def _split_spell_blocks(content: str) -> List[str]:
    """Split spell text into individual spell blocks."""
    # Pattern: UPPERCASE SPELL NAME followed by spell details
    spell_pattern = r'\n(?=[A-Z][A-Z\s\']{2,}\s*\n)'
    blocks = re.split(spell_pattern, content)

    # Filter valid blocks (must contain "level" or "cantrip")
    valid_blocks = []
    for block in blocks:
        block = block.strip()
        if len(block) > 100 and ('level' in block.lower() or 'cantrip' in block.lower()):
            valid_blocks.append(block)

    return valid_blocks


def _parse_spell_to_chunk(block: str) -> Chunk:
    """Parse a spell block into a Chunk object."""
    lines = [l.strip() for l in block.split('\n') if l.strip()]

    if len(lines) < 3:
        return None

    # Extract spell name (first line, uppercase)
    name = lines[0].strip()

    # Extract level and school (second line)
    level_school_line = lines[1].lower()
    level = 0
    if 'cantrip' in level_school_line:
        level = 0
    else:
        level_match = re.search(r'(\d+)(?:st|nd|rd|th)', level_school_line)
        if level_match:
            level = int(level_match.group(1))

    # Determine school
    schools = ['abjuration', 'conjuration', 'divination', 'enchantment',
               'evocation', 'illusion', 'necromancy', 'transmutation']
    school = 'unknown'
    for s in schools:
        if s in level_school_line:
            school = s.capitalize()
            break

    # Rest is the description
    description = '\n'.join(lines[2:])

    # Create full spell text
    content = f"**{name}**\n"
    content += f"Level {level} {school}\n\n"
    content += description

    metadata = {
        'name': name,
        'level': level,
        'school': school,
        'content_type': 'spell'
    }

    tags = {
        'spell',
        f'level_{level}',
        f'school_{school.lower()}'
    }

    return Chunk(
        content=content,
        chunk_type='full_spell',
        metadata=metadata,
        tags=tags
    )


# =============================================================================
# MONSTER LOADER (adapted from monster_to_rag.ipynb)
# =============================================================================

def load_monsters(db_manager: ChromaDBManager, clear: bool = False):
    """Load monsters from extracted_monsters.txt into ChromaDB."""

    print("\n" + "="*70)
    print("👹 LOADING MONSTERS")
    print("="*70)

    if clear:
        db_manager.clear_collection(settings.COLLECTION_NAMES['monsters'])

    # Read extracted monsters
    print(f"📖 Reading {settings.EXTRACTED_MONSTERS_TXT}")

    if not settings.EXTRACTED_MONSTERS_TXT.exists():
        print("⚠️  Monster file not found, skipping")
        return 0

    with open(settings.EXTRACTED_MONSTERS_TXT, 'r', encoding='utf-8') as f:
        monsters_content = f.read()

    # Simple monster parsing
    monster_blocks = _split_monster_blocks(monsters_content)
    print(f"✓ Found {len(monster_blocks)} monster blocks")

    # Create chunks
    chunks = []
    for i, block in enumerate(monster_blocks):
        try:
            monster_chunk = _parse_monster_to_chunk(block)
            if monster_chunk:
                chunks.append(monster_chunk)

            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(monster_blocks)} monsters...")
        except Exception as e:
            print(f"  Warning: Failed to parse monster {i+1}: {e}")
            continue

    print(f"✓ Created {len(chunks)} monster chunks")

    # Add to ChromaDB
    if chunks:
        db_manager.add_chunks(settings.COLLECTION_NAMES['monsters'], chunks)
        print(f"✅ Loaded {len(chunks)} monsters into ChromaDB")

    return len(chunks)


def _split_monster_blocks(content: str) -> List[str]:
    """Split monster text into individual blocks."""
    # Pattern: MONSTER NAME (often all caps or title case)
    blocks = content.split('\n\n')
    valid_blocks = [b.strip() for b in blocks if len(b.strip()) > 200]
    return valid_blocks


def _parse_monster_to_chunk(block: str) -> Chunk:
    """Parse a monster block into a Chunk object."""
    lines = [l.strip() for l in block.split('\n') if l.strip()]

    if not lines:
        return None

    # Extract name (usually first line)
    name = lines[0].strip()

    # Full content
    content = block

    # Try to extract CR
    cr = "Unknown"
    cr_match = re.search(r'Challenge(?:\s+Rating)?[:\s]+([^\s\(]+)', block, re.IGNORECASE)
    if cr_match:
        cr = cr_match.group(1).strip()

    metadata = {
        'name': name,
        'challenge_rating': cr,
        'content_type': 'monster'
    }

    tags = {'monster', f'cr_{cr.replace("/", "_")}'}

    return Chunk(
        content=content,
        chunk_type='monster_stats',
        metadata=metadata,
        tags=tags
    )


# =============================================================================
# CLASS LOADER (adapted from classes_to_rag.ipynb)
# =============================================================================

def load_classes(db_manager: ChromaDBManager, clear: bool = False):
    """Load classes from extracted_classes.txt into ChromaDB."""

    print("\n" + "="*70)
    print("⚔️  LOADING CLASSES")
    print("="*70)

    if clear:
        db_manager.clear_collection(settings.COLLECTION_NAMES['classes'])

    # Read extracted classes
    print(f"📖 Reading {settings.EXTRACTED_CLASSES_TXT}")

    if not settings.EXTRACTED_CLASSES_TXT.exists():
        print("⚠️  Classes file not found, skipping")
        return 0

    with open(settings.EXTRACTED_CLASSES_TXT, 'r', encoding='utf-8') as f:
        classes_content = f.read()

    # Simple class parsing - split by known class names
    class_blocks = _split_class_blocks(classes_content)
    print(f"✓ Found {len(class_blocks)} class blocks")

    # Create chunks
    chunks = []
    for class_name, content in class_blocks.items():
        try:
            class_chunk = _parse_class_to_chunk(class_name, content)
            if class_chunk:
                chunks.append(class_chunk)
        except Exception as e:
            print(f"  Warning: Failed to parse class {class_name}: {e}")
            continue

    print(f"✓ Created {len(chunks)} class chunks")

    # Add to ChromaDB
    if chunks:
        db_manager.add_chunks(settings.COLLECTION_NAMES['classes'], chunks)
        print(f"✅ Loaded {len(chunks)} classes into ChromaDB")

    return len(chunks)


def _split_class_blocks(content: str) -> Dict[str, str]:
    """Split content by class names."""
    class_blocks = {}

    for i, class_name in enumerate(settings.DND_CLASSES):
        # Find this class
        pattern = rf'\b{class_name.upper()}\b'
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        if matches:
            start = matches[0].start()
            # Find end (next class or end of text)
            end = len(content)
            for next_class in settings.DND_CLASSES[i+1:]:
                next_pattern = rf'\b{next_class.upper()}\b'
                next_matches = re.search(next_pattern, content[start+100:], re.IGNORECASE)
                if next_matches:
                    end = start + 100 + next_matches.start()
                    break

            class_content = content[start:end].strip()
            if len(class_content) > 500:  # Substantial content
                class_blocks[class_name] = class_content

    return class_blocks


def _parse_class_to_chunk(class_name: str, content: str) -> Chunk:
    """Parse a class block into a Chunk object."""
    metadata = {
        'name': class_name,
        'content_type': 'class'
    }

    tags = {'class', f'class_{class_name.lower()}'}

    # Format content
    formatted_content = f"**{class_name}**\n\n{content[:2000]}"  # Limit size

    return Chunk(
        content=formatted_content,
        chunk_type='class_features',
        metadata=metadata,
        tags=tags
    )


# =============================================================================
# RACE LOADER (adapted from races_to_rag.ipynb)
# =============================================================================

def load_races(db_manager: ChromaDBManager, clear: bool = False):
    """Load races - placeholder for now."""

    print("\n" + "="*70)
    print("🧝 LOADING RACES")
    print("="*70)
    print("⚠️  Race loader not yet implemented (can add later)")

    return 0


# =============================================================================
# MAIN INITIALIZATION
# =============================================================================

def main():
    """Main initialization function."""
    parser = argparse.ArgumentParser(description='Initialize D&D RAG System')
    parser.add_argument('--clear', action='store_true', help='Clear existing data')
    parser.add_argument('--only', type=str, help='Load only specific collections (comma-separated)')
    args = parser.parse_args()

    print("\n" + "="*70)
    print("🎲 D&D RAG SYSTEM INITIALIZATION")
    print("="*70)

    # Initialize ChromaDB
    print("\n🔧 Initializing ChromaDB...")
    db_manager = ChromaDBManager()

    # Determine what to load
    load_all = args.only is None
    to_load = args.only.split(',') if args.only else ['spells', 'monsters', 'classes', 'races']

    # Load each collection
    results = {}

    if load_all or 'spells' in to_load:
        results['spells'] = load_spells(db_manager, args.clear)

    if load_all or 'monsters' in to_load:
        results['monsters'] = load_monsters(db_manager, args.clear)

    if load_all or 'classes' in to_load:
        results['classes'] = load_classes(db_manager, args.clear)

    if load_all or 'races' in to_load:
        results['races'] = load_races(db_manager, args.clear)

    # Summary
    print("\n" + "="*70)
    print("📊 INITIALIZATION SUMMARY")
    print("="*70)

    total_chunks = sum(results.values())
    for content_type, count in results.items():
        print(f"  {content_type.capitalize()}: {count} chunks")

    print(f"\n✅ Total: {total_chunks} chunks loaded into ChromaDB")

    # Show collection stats
    print("\n📈 Collection Statistics:")
    stats = db_manager.get_all_stats()
    for collection_name, col_stats in stats['collections'].items():
        print(f"  {collection_name}: {col_stats.get('total_documents', 0)} documents")

    print("\n🎉 Initialization complete!")
    print(f"   Database: {db_manager.persist_dir}")
    print("\n💡 Next steps:")
    print("   - Test searches: python test_rag_search.py")
    print("   - Run GM dialogue: python run_gm_dialogue.py")


if __name__ == '__main__':
    main()
