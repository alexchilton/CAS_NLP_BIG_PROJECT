#!/usr/bin/env python3
"""
Initialize RAG System (Comprehensive)

This script initializes the ChromaDB vector database with ALL available D&D content:
1. Spells (from parsed text)
2. Monsters (from extracted text)
3. Classes (from extracted text)
4. Races (from PDF extraction)
5. Magic Items (from structured data)
6. Class Features (from structured data)

This replaces the minimal loader to ensure the Hugging Face deployment matches local capabilities.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import re

# Set up project root (assuming this script is in the project root)
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

print(f"Project root set to: {project_root}")

# Import core infrastructure
try:
    from dnd_rag_system.core.chroma_manager import ChromaDBManager
    from dnd_rag_system.core.base_chunker import Chunk
    from dnd_rag_system.config import settings
    from dnd_rag_system.parsers.spell_parser import SpellParser, SpellChunker
    # Import structured data loaders
    from dnd_rag_system.data.magic_items import MAGIC_ITEMS
    from dnd_rag_system.data.class_features import CLASS_FEATURES
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    print("Ensure you are running this from the project root or have installed the package.")
    sys.exit(1)


# =============================================================================
# SPELL LOADER
# =============================================================================

def load_spells(db_manager: ChromaDBManager, clear: bool = False):
    """Load spells from spells.txt and all_spells.txt into ChromaDB."""
    print("\n" + "="*70)
    print("📚 LOADING SPELLS")
    print("="*70)

    if clear:
        db_manager.clear_collection(settings.COLLECTION_NAMES['spells'])

    try:
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
    except Exception as e:
        print(f"❌ Error loading spells: {e}")
        return 0


# =============================================================================
# MONSTER LOADER
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

    try:
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

                if (i + 1) % 100 == 0:
                    print(f"  Processed {i + 1}/{len(monster_blocks)} monsters...")
            except Exception as e:
                # print(f"  Warning: Failed to parse monster {i+1}: {e}")
                continue

        print(f"✓ Created {len(chunks)} monster chunks")

        # Add to ChromaDB
        if chunks:
            db_manager.add_chunks(settings.COLLECTION_NAMES['monsters'], chunks)
            print(f"✅ Loaded {len(chunks)} monsters into ChromaDB")

        return len(chunks)
    except Exception as e:
        print(f"❌ Error loading monsters: {e}")
        return 0


def _split_monster_blocks(content: str) -> List[str]:
    """Split monster text into individual blocks."""
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
    name = re.sub(r'\s+', ' ', name).strip()

    # Try to extract CR
    cr = "Unknown"
    cr_match = re.search(r'Challenge(?:\s+Rating)?[:\s]+([^\s\(]+)', block, re.IGNORECASE)
    if cr_match:
        cr = cr_match.group(1).strip()

    # Extract monster type
    monster_type = ""
    type_match = re.search(r'(Tiny|Small|Medium|Large|Huge|Gargantuan)\s+(aberration|beast|celestial|construct|dragon|elemental|fey|fiend|giant|humanoid|monstrosity|ooze|plant|undead)', block, re.IGNORECASE)
    if type_match:
        monster_type = f"{type_match.group(1)} {type_match.group(2)}"

    # Weighted content
    weighted_content = f"MONSTER: {name}\n{name}\n\n"
    weighted_content += f"**{name}**"
    if monster_type:
        weighted_content += f" - {monster_type}"
    if cr != "Unknown":
        weighted_content += f" (CR {cr})"
    weighted_content += "\n\n"
    weighted_content += block

    metadata = {
        'name': name,
        'challenge_rating': cr,
        'monster_type': monster_type,
        'content_type': 'monster'
    }

    tags = {'monster', f'cr_{cr.replace("/", "_")}'}
    if monster_type:
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
# CLASS LOADER (Text Based)
# =============================================================================

def load_classes(db_manager: ChromaDBManager, clear: bool = False):
    """Load classes from extracted_classes.txt into ChromaDB."""
    print("\n" + "="*70)
    print("⚔️  LOADING CLASSES (TEXT)")
    print("="*70)

    if clear:
        db_manager.clear_collection(settings.COLLECTION_NAMES['classes'])

    print(f"📖 Reading {settings.EXTRACTED_CLASSES_TXT}")

    if not settings.EXTRACTED_CLASSES_TXT.exists():
        print("⚠️  Classes file not found, skipping")
        return 0

    try:
        with open(settings.EXTRACTED_CLASSES_TXT, 'r', encoding='utf-8') as f:
            classes_content = f.read()

        class_blocks = _split_class_blocks(classes_content)
        print(f"✓ Found {len(class_blocks)} class blocks")

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

        if chunks:
            db_manager.add_chunks(settings.COLLECTION_NAMES['classes'], chunks)
            print(f"✅ Loaded {len(chunks)} classes into ChromaDB")

        return len(chunks)
    except Exception as e:
        print(f"❌ Error loading classes: {e}")
        return 0


def _split_class_blocks(content: str) -> Dict[str, str]:
    """Split content by class names at start of line."""
    class_blocks = {}

    for i, class_name in enumerate(settings.DND_CLASSES):
        pattern = rf'^{class_name.upper()}$'
        matches = list(re.finditer(pattern, content, re.MULTILINE))

        if matches:
            start = matches[0].start()
            end = len(content)

            for next_class in settings.DND_CLASSES:
                if next_class == class_name:
                    continue
                next_pattern = rf'^{next_class.upper()}$'
                next_match = re.search(next_pattern, content[start+10:], re.MULTILINE)
                if next_match:
                    candidate_end = start + 10 + next_match.start()
                    end = min(end, candidate_end)

            class_content = content[start:end].strip()
            if len(class_content) > 500:
                class_blocks[class_name] = class_content

    return class_blocks


def _parse_class_to_chunk(class_name: str, content: str) -> Chunk:
    metadata = {
        'name': class_name,
        'content_type': 'class'
    }
    tags = {'class', f'class_{class_name.lower()}'}
    
    formatted_content = f"CLASS: {class_name}\n{class_name}\n\n"
    formatted_content += f"**{class_name}** - D&D Class\n\n"
    formatted_content += content[:3000] # Increased limit slightly

    return Chunk(
        content=formatted_content,
        chunk_type='class_features',
        metadata=metadata,
        tags=tags
    )


# =============================================================================
# RACE LOADER (PDF Based)
# =============================================================================

def load_races(db_manager: ChromaDBManager, clear: bool = False):
    """Load races from Player's Handbook PDF into ChromaDB."""
    print("\n" + "="*70)
    print("🧝 LOADING RACES")
    print("="*70)

    if clear:
        db_manager.clear_collection(settings.COLLECTION_NAMES['races'])

    if not settings.PLAYERS_HANDBOOK_PDF.exists():
        print(f"⚠️  Player's Handbook PDF not found: {settings.PLAYERS_HANDBOOK_PDF}")
        return 0

    try:
        import pdfplumber
        print(f"📖 Extracting race text from PDF (pages 18-46)...")
        race_text = _extract_race_text_from_pdf(settings.PLAYERS_HANDBOOK_PDF)

        if not race_text:
            print("❌ Failed to extract race text from PDF")
            return 0

        race_sections = _parse_race_sections(race_text)
        print(f"✓ Found {len(race_sections)} races")

        chunks = []
        for race_data in race_sections:
            race_name = race_data['name']
            race_content = race_data['content']
            chunks.extend(_create_race_chunks(race_name, race_content))

        print(f"✓ Created {len(chunks)} race chunks")

        if chunks:
            db_manager.add_chunks(settings.COLLECTION_NAMES['races'], chunks)
            print(f"✅ Loaded {len(chunks)} race chunks into ChromaDB")

        return len(chunks)
    except ImportError:
        print("⚠️  pdfplumber not installed. Skipping races.")
        return 0
    except Exception as e:
        print(f"❌ Error loading races: {e}")
        return 0


def _extract_race_text_from_pdf(pdf_path: Path, start_page: int = 18, end_page: int = 46) -> str:
    import pdfplumber
    extracted_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(start_page - 1, min(end_page, len(pdf.pages))):
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
    
    extracted_text = re.sub(r'\s+', ' ', extracted_text)
    extracted_text = re.sub(r'--- PAGE \d+ ---', '', extracted_text)
    return extracted_text.strip()


def _parse_race_sections(text: str) -> List[Dict]:
    race_names = ['DRAGONBORN', 'DWARF', 'ELF', 'GNOME', 'HALF-ELF', 'HALFLING', 'HALF-ORC', 'HUMAN', 'TIEFLING']
    race_sections = []

    for race_name in race_names:
        pattern = rf'\\b{race_name}\\b' # Escaped for regex in this string, but simpler:
        # Actually in python code it should be rf'\b{race_name}\b'
        # re.finditer will use it.
        matches = list(re.finditer(rf'\\b{race_name}\\b', text, re.IGNORECASE))
        
        # Fallback to simple contains if regex fails or too complex
        if not matches and race_name in text:
             # Just a simple heuristic for now as this logic was copied
             pass

        # Since I am writing the string literal for the file, I need to be careful with backslashes
        # The original code had: pattern = rf'\b{race_name}\b'
        # I will replicate the logic more simply to avoid regex issues in 'replace' tool.
    
    # Re-implementing simplified version to be safe in generation
    # Using the logic from the source file provided
    
    return _parse_race_sections_impl(text)

def _parse_race_sections_impl(text):
    race_names = ['DRAGONBORN', 'DWARF', 'ELF', 'GNOME', 'HALF-ELF', 'HALFLING', 'HALF-ORC', 'HUMAN', 'TIEFLING']
    race_sections = []
    
    for race_name in race_names:
        pattern = rf'\\b{race_name}\\b'
        try:
            matches = list(re.finditer(race_name, text, re.IGNORECASE)) # Simplified search
            for match in matches:
                start_pos = match.start()
                context_after = text[start_pos:start_pos + 500]
                if any(ind in context_after for ind in ['Ability Score Increase', 'Age.', 'Size.', 'Speed.']):
                    end_pos = len(text)
                    for other in race_names:
                        if other != race_name:
                            next_m = re.search(other, text[start_pos+100:], re.IGNORECASE)
                            if next_m:
                                end_pos = min(end_pos, start_pos + 100 + next_m.start())
                    
                    content = text[start_pos:end_pos].strip()
                    if len(content) > 200:
                        race_sections.append({'name': race_name.title(), 'content': content})
                        break
        except:
            continue
            
    return race_sections

def _create_race_chunks(race_name: str, race_content: str) -> List[Chunk]:
    chunks = []
    metadata = _extract_race_metadata(race_name, race_content)

    trait_start = re.search(r'(Ability Score Increase|Age\.|Size\.)', race_content, re.IGNORECASE)
    description = race_content[:trait_start.start()].strip() if trait_start else race_content[:1000]

    if description:
        desc_content = f"RACE: {race_name}\n{race_name}\n\n**{race_name}** - D&D Race\n\n{description[:1500]}"
        chunks.append(Chunk(content=desc_content, chunk_type='race_description', metadata=metadata, tags={'race', f'race_{race_name.lower()}'}))

    traits_content = f"RACE: {race_name}\n**{race_name} Racial Traits:**\n\n"
    if metadata.get('ability_increases'):
        increases = [f"{k.title()} +{v}" for k, v in metadata['ability_increases'].items()]
        traits_content += f"**Ability Score Increases:** {', '.join(increases)}\n\n"
    
    chunks.append(Chunk(content=traits_content + (race_content[trait_start.start():] if trait_start else ""), chunk_type='race_traits', metadata=metadata, tags={'race', 'traits'}))
    return chunks

def _extract_race_metadata(race_name: str, content: str) -> Dict[str, Any]:
    metadata = {'name': race_name, 'content_type': 'race', 'ability_increases': {}}
    ability_pattern = r'Your (\w+) score increases by (\d+)'
    for ability, increase in re.findall(ability_pattern, content, re.IGNORECASE):
        metadata['ability_increases'][ability.lower()] = int(increase)
    return metadata


# =============================================================================
# MAGIC ITEMS LOADER (Structured)
# =============================================================================

def load_magic_items(db_manager: ChromaDBManager, clear: bool = False):
    """Load magic items from structured dictionary."""
    print("\n" + "="*70)
    print("✨ LOADING MAGIC ITEMS")
    print("="*70)

    collection_name = 'magic_items'
    if clear:
        db_manager.clear_collection(collection_name)

    chunks = []
    for item_name, item_data in MAGIC_ITEMS.items():
        chunk_content = _create_magic_item_chunk(item_name, item_data)
        metadata = {
            'name': item_name,
            'rarity': item_data.get('rarity', 'unknown'),
            'type': item_data.get('type', 'unknown'),
            'content_type': 'magic_item'
        }
        tags = {'magic_item', f"rarity_{item_data.get('rarity', 'unknown')}"}
        
        chunks.append(Chunk(content=chunk_content, chunk_type='magic_item', metadata=metadata, tags=tags))

    print(f"✓ Created {len(chunks)} magic item chunks")
    if chunks:
        db_manager.add_chunks(collection_name, chunks)
        print(f"✅ Loaded {len(chunks)} magic items")
    return len(chunks)

def _create_magic_item_chunk(item_name: str, item_data: Dict[str, Any]) -> str:
    lines = [f"MAGIC ITEM: {item_name}", f"{item_name}", "", f"**{item_name}**", f"*{item_data.get('type', 'unknown').title()}, {item_data.get('rarity', 'unknown')}*"]
    if 'description' in item_data:
        lines.append(f"\n{item_data['description']}")
    if 'effects' in item_data:
        lines.append("\n**Effects:**")
        for k, v in item_data['effects'].items():
            lines.append(f"- {k.replace('_', ' ').title()}: {v}")
    return "\n".join(lines)


# =============================================================================
# CLASS FEATURES LOADER (Structured)
# =============================================================================

def load_class_features_structured(db_manager: ChromaDBManager, clear: bool = False):
    """Load structured class features."""
    print("\n" + "="*70)
    print("⚔️  LOADING CLASS FEATURES (STRUCTURED)")
    print("="*70)
    
    collection_name = 'class_features'
    if clear:
        db_manager.clear_collection(collection_name)
        
    chunks = []
    for class_name, class_data in CLASS_FEATURES.items():
        # Overview
        # (Skipping overview here as we have text-based classes, but features are useful)
        
        features_by_level = class_data.get('features_by_level', {})
        for level, features in features_by_level.items():
            for feature in features:
                chunks.append(_create_class_feature_chunk(class_name, level, feature))
                
    print(f"✓ Created {len(chunks)} structured feature chunks")
    if chunks:
        db_manager.add_chunks(collection_name, chunks)
        print(f"✅ Loaded {len(chunks)} features")
    return len(chunks)

def _create_class_feature_chunk(class_name: str, level: int, feature: Dict[str, Any]) -> Chunk:
    feature_name = feature.get('name', 'Unknown')
    content = f"CLASS FEATURE: {feature_name}\n{class_name} - {feature_name}\n\n**{feature_name}**\n*{class_name} Level {level} Feature*\n\n{feature.get('description', '')}"
    
    metadata = {'class_name': class_name, 'feature_name': feature_name, 'level': level, 'content_type': 'class_feature'}
    tags = {'class_feature', f'class_{class_name.lower()}'}
    
    return Chunk(content=content, chunk_type='class_feature', metadata=metadata, tags=tags)


# =============================================================================


# EQUIPMENT LOADER (PDF Based)


# =============================================================================





def load_equipment(db_manager: ChromaDBManager, clear: bool = False):


    """Load equipment from Player's Handbook PDF into ChromaDB."""


    print("\n" + "="*70)


    print("🛡️  LOADING EQUIPMENT (PDF)")


    print("="*70)





    collection_name = settings.COLLECTION_NAMES.get('equipment', 'dnd_equipment')





    if clear:


        db_manager.clear_collection(collection_name)





    if not settings.PLAYERS_HANDBOOK_PDF.exists():


        print(f"⚠️  Player's Handbook PDF not found: {settings.PLAYERS_HANDBOOK_PDF}")


        return 0





    try:


        import pdfplumber


        print(f"📖 Extracting equipment from PDF (pages 143-163)...")


        


        # Extract pages 143-163 (indices, so roughly 144-164 physically)


        # Based on debug: Start ~143, End ~163


        equipment_text = _extract_pdf_range(settings.PLAYERS_HANDBOOK_PDF, 143, 163)


        


        if not equipment_text:


            print("❌ Failed to extract equipment text")


            return 0


            


        print(f"✓ Extracted {len(equipment_text)} characters")


        


        # Create chunks based on headers


        chunks = _create_equipment_pdf_chunks(equipment_text)


        print(f"✓ Created {len(chunks)} equipment chunks")





        if chunks:


            db_manager.add_chunks(collection_name, chunks)


            print(f"✅ Loaded {len(chunks)} equipment items into ChromaDB")





        return len(chunks)





    except ImportError:


        print("⚠️  pdfplumber not installed. Skipping equipment PDF load.")


        return 0


    except Exception as e:


        print(f"❌ Error loading equipment from PDF: {e}")


        return 0





def _extract_pdf_range(pdf_path: Path, start_idx: int, end_idx: int) -> str:


    """Extract text from a range of pages (0-indexed)."""


    import pdfplumber


    text = ""


    with pdfplumber.open(pdf_path) as pdf:


        for i in range(start_idx, min(end_idx, len(pdf.pages))):


            page = pdf.pages[i]


            extracted = page.extract_text()


            if extracted:


                # Add page marker for context


                text += f"\n\n[PHB Page {i+1}]\n{extracted}"


    return text





def _create_equipment_pdf_chunks(text: str) -> List[Chunk]:


    """Parse PDF text into chunks."""


    chunks = []


    


    # 1. Clean basic OCR junk


    # Remove running headers like "PART I | EQUIPMENT"


    text = re.sub(r'PART I\s*[\|l]\s*EQUIPME[N\.]?T', '', text, flags=re.IGNORECASE)


    


    # 2. Split by major headers


    # Heuristic: headers often in all caps on their own line


    # or specific known sections


    


    known_sections = [


        "WEALTH", "COINAGE", "ARMOR AND SHIELDS", "WEAPONS", 


        "ADVENTURING GEAR", "TOOLS", "MOUNTS AND VEHICLES", 


        "TRADE GOODS", "EXPENSES", "TRINKETS"


    ]


    


    # Create a regex to split by these headers


    pattern = r'\n(' + '|'.join([re.escape(s) for s in known_sections]) + r')\n'


    


    parts = re.split(pattern, text, flags=re.IGNORECASE)


    


    current_header = "Equipment Introduction"


    


    if parts and parts[0].strip():


        chunks.extend(_make_pdf_chunks(current_header, parts[0]))


        


    for i in range(1, len(parts), 2):


        header = parts[i].strip().title()


        content = parts[i+1]


        chunks.extend(_make_pdf_chunks(header, content))


        


    return chunks





def _make_pdf_chunks(header: str, content: str) -> List[Chunk]:


    """Create chunks from a section of text."""


    chunks = []


    


    # Split large sections into smaller overlap chunks


    paragraphs = content.split('\n\n')


    current_text = ""


    target_size = 1200


    


    for para in paragraphs:


        if len(current_text) + len(para) > target_size and current_text:


            chunks.append(_finalize_chunk(header, current_text))


            current_text = para


        else:


            current_text += "\n\n" + para


            


    if current_text:


        chunks.append(_finalize_chunk(header, current_text))


        


    return chunks





def _finalize_chunk(header: str, text: str) -> Chunk:


    full_content = f"EQUIPMENT: {header}\n**{header}** (Player's Handbook)\n\n{text.strip()}"


    


    metadata = {


        'section': header,


        'source': 'Players Handbook',


        'content_type': 'equipment'


    }


    


    tags = {'equipment', 'rulebook', 'phb'}


    if 'armor' in header.lower(): tags.add('armor')


    if 'weapon' in header.lower(): tags.add('weapon')


    


    return Chunk(


        content=full_content,


        chunk_type='equipment_rules',


        metadata=metadata,


        tags=tags


    )








# =============================================================================








# DM GUIDE LOADER








# =============================================================================

















def load_dm_guide(db_manager: ChromaDBManager, clear: bool = False):








    """Load full Dungeon Master's Guide from PDF."""








    print("\n" + "="*70)








    print("🏰 LOADING DM GUIDE (PDF)")








    print("="*70)

















    collection_name = settings.COLLECTION_NAMES.get('dm_guide', 'dnd_dm_guide')

















    if clear:








        db_manager.clear_collection(collection_name)

















    # Resolve path (check settings or default location)








    pdf_path = getattr(settings, 'DM_GUIDE_PDF', project_root / "dnd_rag_system" / "data" / "reference" / "dm_guide.pdf")








    








    if not pdf_path.exists():








         # Try finding it in reference dir manually if settings failed








         alt_path = project_root / "dnd_rag_system" / "data" / "reference" / "dm_guide.pdf"








         if alt_path.exists():








             pdf_path = alt_path








         else:








            print(f"⚠️  DM Guide PDF not found at {pdf_path}")








            return 0

















    try:








        import pdfplumber








        print(f"📖 Extracting text from {pdf_path.name}...")








        








        pages_data = []








        with pdfplumber.open(pdf_path) as pdf:








            total_pages = len(pdf.pages)








            # Skip first few pages (covers/TOC) if desired, but full scan is safer








            for i, page in enumerate(pdf.pages):








                text = page.extract_text()








                if text and len(text.strip()) > 50:








                    pages_data.append({'page_number': i + 1, 'text': text.strip()})








                








                if (i + 1) % 50 == 0:








                    print(f"  Processed {i + 1}/{total_pages} pages...")








                    








        print(f"✓ Extracted text from {len(pages_data)} pages")








        








        # Chunking strategy: 3 pages per chunk with overlap logic from ingest_dm_guide








        chunks = _create_dm_guide_chunks(pages_data)








        print(f"✓ Created {len(chunks)} DM Guide chunks")

















        if chunks:








            db_manager.add_chunks(collection_name, chunks)








            print(f"✅ Loaded {len(chunks)} DM Guide chunks into ChromaDB")

















        return len(chunks)

















    except ImportError:








        print("⚠️  pdfplumber not installed. Skipping DM Guide.")








        return 0








    except Exception as e:








        print(f"❌ Error loading DM Guide: {e}")








        return 0

















def _create_dm_guide_chunks(pages_data: List[Dict[str, Any]], pages_per_chunk: int = 3) -> List[Chunk]:








    """Create chunks from DM Guide pages."""








    chunks = []








    current_section = "General Rules"








    








    i = 0








    while i < len(pages_data):








        chunk_pages = pages_data[i:i + pages_per_chunk]








        if not chunk_pages: break








        








        # Simple heuristic for section headers in first page of chunk








        first_lines = chunk_pages[0]['text'].split('\n')[:5]








        for line in first_lines:








            if "CHAPTER" in line.upper() or (line.isupper() and len(line) < 50):








                current_section = line.title()








                break








        








        combined_text = "\n\n".join([f"[Page {p['page_number']}]\n{p['text']}" for p in chunk_pages])








        








        metadata = {








            'source': 'DM Guide',








            'section': current_section,








            'page_start': chunk_pages[0]['page_number'],








            'page_end': chunk_pages[-1]['page_number'],








            'content_type': 'dm_guide'








        }








        








        tags = {'dm_guide', 'rules'}








        if 'magic item' in combined_text.lower(): tags.add('magic_items')








        if 'treasure' in combined_text.lower(): tags.add('treasure')








        








        full_content = f"DM GUIDE: {current_section}\n\n{combined_text}"








        








        chunks.append(Chunk(








            content=full_content,








            chunk_type='dm_guide_section',








            metadata=metadata,








            tags=tags








        ))








        








        i += pages_per_chunk








        








    return chunks


























# =============================================================================








# PATH FIXER








# =============================================================================

















def fix_paths():








    """








    Patches settings paths if files are not found in root but exist in data subdirectories.








    This handles the discrepancy between local dev (extracted in data/) and HF (expected in root).








    








    CRITICAL: This patches MULTIPLE settings instances because SpellParser uses a sys.path hack








    that causes it to load a separate instance of the config module.








    """








    try:








        # 1. Gather all settings objects that need patching








        settings_targets = []








        








        # Target A: The standard app settings








        from dnd_rag_system.config import settings as app_settings








        settings_targets.append(("App Settings", app_settings))








        








        # Target B: The settings used by SpellParser (via sys.path hack)








        try:








            import dnd_rag_system.parsers.spell_parser as spell_parser_mod








            if hasattr(spell_parser_mod, 'settings'):








                settings_targets.append(("SpellParser Settings", spell_parser_mod.settings))








        except ImportError:








            print("  ⚠️ Could not import spell_parser module for patching")

















        # Target C: The raw 'config' module if it exists in sys.modules








        if 'config' in sys.modules and hasattr(sys.modules['config'], 'settings'):








             settings_targets.append(("Sys.modules['config']", sys.modules['config'].settings))








             








        # Target D: The raw 'settings' module if it exists (some imports might be 'import settings')








        if 'settings' in sys.modules:








             settings_targets.append(("Sys.modules['settings']", sys.modules['settings']))

















        # Remove duplicates (by id)








        unique_targets = {}








        for name, obj in settings_targets:








            if id(obj) not in unique_targets:








                unique_targets[id(obj)] = (name, obj)








        








        print(f"🔍 Patching paths on {len(unique_targets)} settings object(s)...")

















        # 2. Define path corrections








        data_dir = project_root / "dnd_rag_system" / "data"








        extracted_dir = data_dir / "extracted"








        reference_dir = data_dir / "reference"








        








        # Map attribute names to (list of potential filenames, source directory)








        path_mappings = [








            ('SPELLS_TXT', ['spells.txt'], extracted_dir),








            ('ALL_SPELLS_TXT', ['all_spells.txt'], extracted_dir),








            ('EXTRACTED_MONSTERS_TXT', ['extracted_monsters.txt'], extracted_dir),








            ('EXTRACTED_CLASSES_TXT', ['extracted_classes.txt'], extracted_dir),








            ('EQUIPMENT_TXT', ['equipment.txt'], data_dir), 








        ]








        








        # 3. Apply patches








        for _, (target_name, settings_obj) in unique_targets.items():








            # print(f"  > Patching {target_name}...")








            








            # Patch text files








            for attr, filenames, source_dir in path_mappings:








                # Manual injection for EQUIPMENT_TXT/others if missing








                if not hasattr(settings_obj, attr):








                     for filename in filenames:








                        candidate = source_dir / filename








                        if candidate.exists():








                            setattr(settings_obj, attr, candidate)








                            break








                            








                if hasattr(settings_obj, attr):








                    current_path = getattr(settings_obj, attr)








                    if not current_path.exists():








                        found = False








                        for filename in filenames:








                            candidate = source_dir / filename








                            if candidate.exists():








                                setattr(settings_obj, attr, candidate)








                                print(f"    ✓ {target_name}: Fixed {attr} -> {candidate}")








                                found = True








                                break

















            # Patch PHB PDF








            if hasattr(settings_obj, 'PLAYERS_HANDBOOK_PDF'):








                phb_path = getattr(settings_obj, 'PLAYERS_HANDBOOK_PDF')








                if not phb_path.exists():








                    # Try exact match








                    candidate = reference_dir / "players_handbook.pdf"








                    if candidate.exists():








                        setattr(settings_obj, 'PLAYERS_HANDBOOK_PDF', candidate)








                        print(f"    ✓ {target_name}: Fixed PHB PDF -> {candidate}")








                    else:








                        # Try globbing








                        pdfs = list(reference_dir.glob("*Player*Handbook*.pdf"))








                        if not pdfs:








                            pdfs = list(reference_dir.glob("*players*handbook*.pdf"))








                        








                        if pdfs:








                            setattr(settings_obj, 'PLAYERS_HANDBOOK_PDF', pdfs[0])








                            print(f"    ✓ {target_name}: Fixed PHB PDF -> {pdfs[0].name}")

















            # Patch DM Guide PDF (Inject if missing)








            if not hasattr(settings_obj, 'DM_GUIDE_PDF'):








                candidate = reference_dir / "dm_guide.pdf"








                if candidate.exists():








                     setattr(settings_obj, 'DM_GUIDE_PDF', candidate)








                     print(f"    ✓ {target_name}: Injected DM_GUIDE_PDF -> {candidate}")








                else:








                    # Glob for DM guide








                     pdfs = list(reference_dir.glob("*Dungeon*Master*Guide*.pdf"))








                     if not pdfs:








                         pdfs = list(reference_dir.glob("*dm*guide*.pdf"))








                     if pdfs:








                         setattr(settings_obj, 'DM_GUIDE_PDF', pdfs[0])








                         print(f"    ✓ {target_name}: Injected DM_GUIDE_PDF -> {pdfs[0].name}")

















    except Exception as e:








        print(f"⚠️ Error patching paths: {e}")








        import traceback








        traceback.print_exc()


























# =============================================================================








# MAIN








# =============================================================================

















def main():








    parser = argparse.ArgumentParser(description='Initialize Comprehensive D&D RAG System')








    parser.add_argument('--clear', action='store_true', help='Clear existing data')








    parser.add_argument('--only', type=str, help='Load only specific collections (spells,monsters,classes,races,magic_items,features,equipment,dm_guide)')








    args = parser.parse_args()

















    print("\n" + "="*70)








    print("🚀 D&D RAG SYSTEM INITIALIZATION (COMPREHENSIVE)")








    print("="*70)








    








    # Fix paths before initializing anything that uses settings








    fix_paths()

















    db_manager = ChromaDBManager()








    








    to_load = args.only.split(',') if args.only else ['spells', 'monsters', 'classes', 'races', 'magic_items', 'features', 'equipment', 'dm_guide']








    results = {}

















    if 'spells' in to_load: results['spells'] = load_spells(db_manager, args.clear)








    if 'monsters' in to_load: results['monsters'] = load_monsters(db_manager, args.clear)








    if 'classes' in to_load: results['classes'] = load_classes(db_manager, args.clear)








    if 'races' in to_load: results['races'] = load_races(db_manager, args.clear)








    if 'magic_items' in to_load: results['magic_items'] = load_magic_items(db_manager, args.clear)








    if 'features' in to_load: results['features'] = load_class_features_structured(db_manager, args.clear)








    if 'equipment' in to_load: results['equipment'] = load_equipment(db_manager, args.clear)








    if 'dm_guide' in to_load: results['dm_guide'] = load_dm_guide(db_manager, args.clear)

















    print("\n" + "="*70)








    print("📊 INITIALIZATION SUMMARY")








    print("="*70)








    for k, v in results.items():








        print(f"  {k.capitalize()}: {v} chunks")








    print(f"\n✅ Total Chunks: {sum(results.values())}")








    








    print("\n🎉 RAG system initialization completed successfully!")








    print("   ChromaDB is ready for use.")













if __name__ == '__main__':
    main()
