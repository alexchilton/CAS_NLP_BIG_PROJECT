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
from dnd_rag_system.parsers.spell_parser import SpellParser, SpellChunker


# =============================================================================
# SPELL LOADER (using proper SpellParser)
# =============================================================================

def load_spells(db_manager: ChromaDBManager, clear: bool = False):
    """Load spells from spells.txt and all_spells.txt into ChromaDB."""

    print("\n" + "="*70)
    print("📚 LOADING SPELLS")
    print("="*70)

    if clear:
        db_manager.clear_collection(settings.COLLECTION_NAMES['spells'])

    # Use the proper SpellParser
    parser = SpellParser()
    parsed_spells = parser.parse()
    print(f"✓ Parsed {len(parsed_spells)} spells")

    # Use SpellChunker to create optimized chunks
    chunker = SpellChunker()
    all_chunks = []

    for parsed_spell in parsed_spells:
        chunks = chunker.create_chunks(parsed_spell)
        all_chunks.extend(chunks)

    print(f"✓ Created {len(all_chunks)} spell chunks (multiple chunks per spell)")

    # Add to ChromaDB
    if all_chunks:
        db_manager.add_chunks(settings.COLLECTION_NAMES['spells'], all_chunks)
        print(f"✅ Loaded {len(all_chunks)} spell chunks into ChromaDB")

    return len(all_chunks)


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
    """Parse a monster block into a Chunk object with weighted name."""
    lines = [l.strip() for l in block.split('\n') if l.strip()]

    if not lines:
        return None

    # Extract name (usually first line)
    name = lines[0].strip()

    # Clean up common formatting issues in monster names
    name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
    name = name.strip()

    # Try to extract CR
    cr = "Unknown"
    cr_match = re.search(r'Challenge(?:\s+Rating)?[:\s]+([^\s\(]+)', block, re.IGNORECASE)
    if cr_match:
        cr = cr_match.group(1).strip()

    # Extract monster type if present (e.g., "Large dragon", "Medium humanoid")
    monster_type = ""
    type_match = re.search(r'(Tiny|Small|Medium|Large|Huge|Gargantuan)\s+(aberration|beast|celestial|construct|dragon|elemental|fey|fiend|giant|humanoid|monstrosity|ooze|plant|undead)', block, re.IGNORECASE)
    if type_match:
        monster_type = f"{type_match.group(1)} {type_match.group(2)}"

    # IMPROVEMENT: Add monster name weighting for better retrieval
    # Repeat name multiple times at the start for better matching
    weighted_content = f"MONSTER: {name}\n{name}\n\n"

    # Add formatted header with key info
    weighted_content += f"**{name}**"
    if monster_type:
        weighted_content += f" - {monster_type}"
    if cr != "Unknown":
        weighted_content += f" (CR {cr})"
    weighted_content += "\n\n"

    # Add the full monster stat block
    weighted_content += block

    metadata = {
        'name': name,
        'challenge_rating': cr,
        'monster_type': monster_type,
        'content_type': 'monster'
    }

    tags = {'monster', f'cr_{cr.replace("/", "_")}'}
    if monster_type:
        # Add type tag (e.g., 'dragon', 'humanoid')
        type_only = monster_type.split()[-1] if monster_type else ''
        if type_only:
            tags.add(f'type_{type_only.lower()}')

    return Chunk(
        content=weighted_content,
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
    """Parse a class block into a Chunk object with weighted name."""
    metadata = {
        'name': class_name,
        'content_type': 'class'
    }

    tags = {'class', f'class_{class_name.lower()}'}

    # IMPROVEMENT: Add class name weighting for better retrieval
    formatted_content = f"CLASS: {class_name}\n{class_name}\n\n"
    formatted_content += f"**{class_name}** - D&D Class\n\n"
    formatted_content += content[:2000]  # Limit size

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
    """Load races from Player's Handbook PDF into ChromaDB."""

    print("\n" + "="*70)
    print("🧝 LOADING RACES")
    print("="*70)

    if clear:
        db_manager.clear_collection(settings.COLLECTION_NAMES['races'])

    # Check if PDF exists
    if not settings.PLAYERS_HANDBOOK_PDF.exists():
        print(f"⚠️  Player's Handbook PDF not found: {settings.PLAYERS_HANDBOOK_PDF}")
        print("   Skipping race loading")
        return 0

    try:
        import pdfplumber
    except ImportError:
        print("⚠️  pdfplumber not installed. Install with: pip install pdfplumber")
        return 0

    print(f"📖 Extracting race text from PDF (pages 18-46)...")

    # Extract text from PDF
    race_text = _extract_race_text_from_pdf(settings.PLAYERS_HANDBOOK_PDF)

    if not race_text:
        print("❌ Failed to extract race text from PDF")
        return 0

    print(f"✓ Extracted {len(race_text)} characters")

    # Parse race sections
    race_sections = _parse_race_sections(race_text)
    print(f"✓ Found {len(race_sections)} races")

    # Create chunks
    chunks = []
    for race_data in race_sections:
        race_name = race_data['name']
        race_content = race_data['content']

        print(f"  Processing: {race_name}")

        # Create chunks for this race
        race_chunks = _create_race_chunks(race_name, race_content)
        chunks.extend(race_chunks)

    print(f"✓ Created {len(chunks)} race chunks")

    # Add to ChromaDB
    if chunks:
        db_manager.add_chunks(settings.COLLECTION_NAMES['races'], chunks)
        print(f"✅ Loaded {len(chunks)} race chunks into ChromaDB")

    return len(chunks)


def _extract_race_text_from_pdf(pdf_path: Path, start_page: int = 18, end_page: int = 46) -> str:
    """Extract race text from Player's Handbook PDF."""
    import pdfplumber

    extracted_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # PDF pages are 0-indexed
            for page_num in range(start_page - 1, min(end_page, len(pdf.pages))):
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"

        # Clean up the text
        extracted_text = re.sub(r'\s+', ' ', extracted_text)
        extracted_text = re.sub(r'--- PAGE \d+ ---', '', extracted_text)

        return extracted_text.strip()

    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        return ""


def _parse_race_sections(text: str) -> List[Dict]:
    """Parse text into individual race sections."""
    race_names = ['DRAGONBORN', 'DWARF', 'ELF', 'GNOME', 'HALF-ELF',
                  'HALFLING', 'HALF-ORC', 'HUMAN', 'TIEFLING']

    race_sections = []

    for race_name in race_names:
        # Find race section
        pattern = rf'\b{race_name}\b'
        matches = list(re.finditer(pattern, text, re.IGNORECASE))

        for match in matches:
            start_pos = match.start()

            # Check if this looks like a race header
            context_after = text[start_pos:start_pos + 500]

            # Look for indicators this is a section header
            if any(indicator in context_after for indicator in
                   ['Ability Score Increase', 'Age.', 'Size.', 'Speed.']):

                # Find end of section (next race or end of text)
                end_pos = len(text)
                for other_race in race_names:
                    if other_race != race_name:
                        next_match = re.search(rf'\b{other_race}\b', text[start_pos + 100:])
                        if next_match:
                            candidate_end = start_pos + 100 + next_match.start()
                            if any(indicator in text[candidate_end:candidate_end + 200]
                                   for indicator in ['Ability Score Increase', 'Age.', 'Size.']):
                                end_pos = min(end_pos, candidate_end)

                race_content = text[start_pos:end_pos].strip()

                if len(race_content) > 200:
                    race_sections.append({
                        'name': race_name.title(),
                        'content': race_content
                    })
                    break  # Take first good match

    return race_sections


def _create_race_chunks(race_name: str, race_content: str) -> List[Chunk]:
    """Create chunks from race content."""
    chunks = []

    # Extract basic metadata
    metadata = _extract_race_metadata(race_name, race_content)

    # 1. Main description chunk (first part before traits)
    trait_start = re.search(r'(Ability Score Increase|Age\.|Size\.)', race_content, re.IGNORECASE)
    if trait_start:
        description = race_content[:trait_start.start()].strip()
    else:
        description = race_content[:1000]

    if description:
        desc_content = f"RACE: {race_name}\n{race_name}\n\n**{race_name}** - D&D Race\n\n{description[:1500]}"

        chunks.append(Chunk(
            content=desc_content,
            chunk_type='race_description',
            metadata=metadata,
            tags={'race', f'race_{race_name.lower()}', 'description'}
        ))

    # 2. Traits chunk
    traits_content = f"RACE: {race_name}\n**{race_name} Racial Traits:**\n\n"

    if metadata.get('ability_increases'):
        increases = [f"{k.title()} +{v}" for k, v in metadata['ability_increases'].items()]
        traits_content += f"**Ability Score Increases:** {', '.join(increases)}\n\n"

    if metadata.get('size'):
        traits_content += f"**Size:** {metadata['size']}\n"

    if metadata.get('speed'):
        traits_content += f"**Speed:** {metadata['speed']}\n"

    if metadata.get('darkvision'):
        traits_content += f"**Darkvision:** {metadata['darkvision']} feet\n"

    if metadata.get('languages'):
        traits_content += f"**Languages:** {', '.join(metadata['languages'])}\n"

    traits_content += f"\n{race_content[trait_start.start():trait_start.start() + 1000] if trait_start else ''}"

    chunks.append(Chunk(
        content=traits_content,
        chunk_type='race_traits',
        metadata=metadata,
        tags={'race', f'race_{race_name.lower()}', 'traits', 'mechanics'}
    ))

    return chunks


def _extract_race_metadata(race_name: str, content: str) -> Dict[str, Any]:
    """Extract metadata from race content."""
    metadata = {
        'name': race_name,
        'content_type': 'race',
        'ability_increases': {},
        'size': '',
        'speed': '',
        'darkvision': 0,
        'languages': []
    }

    # Ability increases
    ability_pattern = r'Your (\w+) score increases by (\d+)'
    for ability, increase in re.findall(ability_pattern, content, re.IGNORECASE):
        metadata['ability_increases'][ability.lower()] = int(increase)

    # Size
    size_match = re.search(r'Size\.\s*([^.]{0,200}?)\.', content, re.IGNORECASE | re.DOTALL)
    if size_match:
        size_text = size_match.group(1).strip()
        if 'Medium' in size_text:
            metadata['size'] = 'Medium'
        elif 'Small' in size_text:
            metadata['size'] = 'Small'

    # Speed
    speed_match = re.search(r'Speed\.\s*([^.]{0,200}?)\.', content, re.IGNORECASE | re.DOTALL)
    if speed_match:
        speed_text = speed_match.group(1).strip()
        metadata['speed'] = speed_text[:50]

    # Darkvision
    darkvision_match = re.search(r'darkvision.*?(\d+)\s*feet', content, re.IGNORECASE)
    if darkvision_match:
        metadata['darkvision'] = int(darkvision_match.group(1))

    # Languages
    lang_match = re.search(r'Languages\.\s*([^.]{0,200}?)\.', content, re.IGNORECASE | re.DOTALL)
    if lang_match:
        lang_text = lang_match.group(1)
        for lang in ['Common', 'Elvish', 'Dwarvish', 'Draconic', 'Giant', 'Gnomish', 'Goblin', 'Halfling', 'Orc']:
            if lang in lang_text:
                metadata['languages'].append(lang)

    return metadata


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
