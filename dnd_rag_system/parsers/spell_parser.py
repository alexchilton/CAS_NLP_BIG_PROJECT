"""
Spell Parser

Parses D&D spells from spells.txt and all_spells.txt files.
Handles OCR errors and text formatting issues from PDF extraction.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

# Import base classes
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.base_parser import TextParser, ParsedContent, clean_extracted_text
from core.base_chunker import BaseChunker, Chunk, estimate_tokens
from config import settings


@dataclass
class SpellData:
    """Container for spell information."""
    name: str
    level: int
    school: str
    casting_time: str
    range: str
    components: str
    duration: str
    description: str
    classes: List[str] = field(default_factory=list)
    ritual: bool = False
    concentration: bool = False
    higher_levels: Optional[str] = None


class SpellParser(TextParser):
    """
    Parser for D&D 5e spells.

    Extracts spells from two sources:
    1. spells.txt - Detailed spell descriptions
    2. all_spells.txt - Class/level associations
    """

    def __init__(self):
        super().__init__(content_type='spell')
        self.spells: Dict[str, SpellData] = {}

    def parse(self, source: Path = None) -> List[ParsedContent]:
        """
        Parse spells from files.

        Args:
            source: Not used, files are from settings

        Returns:
            List of ParsedContent objects
        """
        print("📖 Parsing D&D spells...")

        # Parse detailed descriptions
        self._parse_spells_txt(settings.SPELLS_TXT)

        # Parse class associations
        self._parse_all_spells_txt(settings.ALL_SPELLS_TXT)

        # Convert to ParsedContent
        parsed_items = []
        for spell_name, spell_data in self.spells.items():
            parsed_items.append(ParsedContent(
                content_type='spell',
                name=spell_name,
                raw_text=spell_data.description,
                metadata=self._spell_to_metadata(spell_data)
            ))

        self.parsed_items = parsed_items
        print(f"✓ Parsed {len(parsed_items)} spells")
        return parsed_items

    def validate(self, content: ParsedContent) -> bool:
        """Validate spell content."""
        # Check required fields
        if not content.name or not content.raw_text:
            return False

        metadata = content.metadata
        required_fields = ['level', 'school']

        for field in required_fields:
            if field not in metadata:
                return False

        return True

    def _parse_spells_txt(self, file_path: Path):
        """
        Parse spells.txt file with detailed descriptions.

        Handles OCR errors and formatting issues.
        """
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return

        text = self.read_text_file(file_path)

        # Clean OCR issues
        text = self._clean_spell_text(text)

        # Split into individual spells
        spell_blocks = self._split_spell_blocks(text)

        print(f"  Found {len(spell_blocks)} spell blocks in {file_path.name}")

        for block in spell_blocks:
            spell_data = self._parse_spell_block(block)
            if spell_data and spell_data.name:
                self.spells[spell_data.name.upper()] = spell_data

    def _parse_all_spells_txt(self, file_path: Path):
        """
        Parse all_spells.txt file for class associations.

        Format: Class name followed by spell lists by level.
        """
        if not file_path.exists():
            print(f"Warning: {file_path} not found")
            return

        text = self.read_text_file(file_path)
        text = self._clean_spell_text(text)

        # Parse by class sections
        class_sections = self._split_by_class(text)

        for class_name, spells_by_level in class_sections.items():
            for level, spell_names in spells_by_level.items():
                for spell_name in spell_names:
                    spell_key = spell_name.upper()
                    if spell_key in self.spells:
                        if class_name not in self.spells[spell_key].classes:
                            self.spells[spell_key].classes.append(class_name)
                    else:
                        # Create minimal entry for spells only in all_spells.txt
                        self.spells[spell_key] = SpellData(
                            name=spell_name,
                            level=level,
                            school="Unknown",
                            casting_time="",
                            range="",
                            components="",
                            duration="",
                            description="",
                            classes=[class_name]
                        )

    def _clean_spell_text(self, text: str) -> str:
        """
        Clean OCR errors and formatting issues from spell text.

        Common issues:
        - 'l' replaced with 'I' or '1'
        - 'O' replaced with '0'
        - Missing spaces between words
        - Extra whitespace
        - Broken words across lines
        """
        if not text:
            return ""

        # Fix common OCR errors
        # Note: Order matters - fix specific patterns before general ones
        text = re.sub(r'(\d+)(st|nd|rd|th)-/evel', r'\1\2-level', text, flags=re.IGNORECASE)  # Fix /evel -> level
        text = re.sub(r'(\d+)(st|nd|rd|th)-leve[Il1]', r'\1\2-level', text, flags=re.IGNORECASE)  # Fix leveI/leve1
        text = re.sub(r'\bevoeation\b', 'evocation', text, flags=re.IGNORECASE)  # evoeation -> evocation
        text = re.sub(r'\bdivinatian\b', 'divination', text, flags=re.IGNORECASE)  # divinatian -> divination
        text = re.sub(r'\beonjuration\b', 'conjuration', text, flags=re.IGNORECASE)  # eonjuration -> conjuration
        text = re.sub(r'\billusion\b', 'illusion', text, flags=re.IGNORECASE)  # iIlusion -> illusion
        text = re.sub(r'\btransmutation\b', 'transmutation', text, flags=re.IGNORECASE)  # Fix transmutation

        ocr_fixes = {
            r'\blevel\b': 'level',  # Ensure 'level' not 'leveI'
            r'\bcall\b': 'call',    # Ensure 'call' not 'caIl'
            r'\btotal\b': 'total',
            r'\bspell\b': 'spell',
            r'\barea\b': 'area',
            r'(\d+)st-level': r'\1st-level',  # Fix level formatting
            r'(\d+)nd-level': r'\1nd-level',
            r'(\d+)rd-level': r'\1rd-level',
            r'(\d+)th-level': r'\1th-level',
        }

        for pattern, replacement in ocr_fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Fix missing spaces after periods
        text = re.sub(r'\.([A-Z])', r'. \1', text)

        # Fix line breaks in middle of words (common OCR issue)
        text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)

        # Fix excessive whitespace on same line (preserve newlines!)
        text = re.sub(r'[ \t]+', ' ', text)  # Only collapse spaces/tabs, NOT newlines
        text = re.sub(r'\n\n+', '\n\n', text)  # Collapse multiple blank lines to 2 newlines max

        return text.strip()

    def _split_spell_blocks(self, text: str) -> List[str]:
        """
        Split text into individual spell blocks.

        Spells typically start with NAME in caps/title case followed by level/school.
        Handles formats like:
        - "ACID SPLASH\nConjuration cantrip"
        - "Aid\n2nd-level abjuration"
        - "ALARM\n1st-level abjuration (ritual)"
        """
        # Pattern to match spell name followed by school/level line
        # Spell name: Starts with uppercase, can have uppercase letters, spaces, apostrophes, hyphens
        # School/level: Contains either "cantrip" or "Xth-level" followed by a school name
        pattern = r'^([A-Z][A-Z\s\'\-]*[A-Z]|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\n\s*([A-Za-z]+\s+cantrip|\d+[a-z]{2}-level\s+[a-z]+)'

        matches = list(re.finditer(pattern, text, re.MULTILINE))
        blocks = []

        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            blocks.append(text[start_pos:end_pos].strip())

        return blocks

    def _parse_spell_block(self, block: str) -> Optional[SpellData]:
        """Parse a single spell block into SpellData."""
        try:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if len(lines) < 3:
                return None

            # First line is spell name
            name = lines[0].strip()

            # Second line is level and school
            level_school = lines[1]
            level, school = self._parse_level_school(level_school)

            # Parse remaining lines for spell details
            casting_time = ""
            range_str = ""
            components = ""
            duration = ""
            description_lines = []
            higher_levels = None

            in_description = False

            for line in lines[2:]:
                line_lower = line.lower()

                if line_lower.startswith('casting time:'):
                    casting_time = line.split(':', 1)[1].strip()
                elif line_lower.startswith('range:'):
                    range_str = line.split(':', 1)[1].strip()
                elif line_lower.startswith('components:'):
                    components = line.split(':', 1)[1].strip()
                elif line_lower.startswith('duration:'):
                    duration = line.split(':', 1)[1].strip()
                    in_description = True
                elif 'at higher levels' in line_lower:
                    higher_levels = line
                    in_description = False
                elif in_description:
                    description_lines.append(line)

            description = ' '.join(description_lines).strip()

            # Check for ritual and concentration
            ritual = 'ritual' in block.lower()
            concentration = 'concentration' in duration.lower()

            return SpellData(
                name=name,
                level=level,
                school=school,
                casting_time=casting_time,
                range=range_str,
                components=components,
                duration=duration,
                description=description,
                ritual=ritual,
                concentration=concentration,
                higher_levels=higher_levels
            )

        except Exception as e:
            print(f"Warning: Failed to parse spell block: {e}")
            return None

    def _parse_level_school(self, text: str) -> tuple:
        """
        Parse spell level and school from text.

        Examples:
        - "1st-level evocation"
        - "Evocation cantrip"
        - "3rd-level illusion"
        """
        text = text.lower()

        # Determine level
        if 'cantrip' in text:
            level = 0
        else:
            level_match = re.search(r'(\d+)(?:st|nd|rd|th)-level', text)
            if level_match:
                level = int(level_match.group(1))
            else:
                level = 0

        # Determine school
        schools = ['abjuration', 'conjuration', 'divination', 'enchantment',
                  'evocation', 'illusion', 'necromancy', 'transmutation']

        school = 'unknown'
        for s in schools:
            if s in text:
                school = s.capitalize()
                break

        return level, school

    def _split_by_class(self, text: str) -> Dict[str, Dict[int, List[str]]]:
        """
        Split all_spells.txt by class and level.

        Returns:
            Dict mapping class_name -> {level -> [spell_names]}
        """
        class_sections = {}
        current_class = None
        current_level = None

        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a class header
            if any(cls in line.upper() for cls in settings.DND_CLASSES):
                # Extract class name
                for cls in settings.DND_CLASSES:
                    if cls.upper() in line.upper():
                        current_class = cls
                        class_sections[current_class] = {}
                        break

            # Check if this is a level header
            elif 'level' in line.lower() or 'cantrip' in line.lower():
                if current_class:
                    level_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s+level', line, re.IGNORECASE)
                    if level_match:
                        current_level = int(level_match.group(1))
                    elif 'cantrip' in line.lower():
                        current_level = 0

                    if current_level is not None and current_level not in class_sections[current_class]:
                        class_sections[current_class][current_level] = []

            # Otherwise, this should be spell names
            elif current_class and current_level is not None:
                # Split by commas and clean
                spell_names = [s.strip() for s in line.split(',') if s.strip()]
                class_sections[current_class][current_level].extend(spell_names)

        return class_sections

    def _spell_to_metadata(self, spell: SpellData) -> Dict[str, Any]:
        """Convert SpellData to metadata dictionary."""
        return {
            'name': spell.name,
            'level': spell.level,
            'school': spell.school,
            'casting_time': spell.casting_time,
            'range': spell.range,
            'components': spell.components,
            'duration': spell.duration,
            'classes': spell.classes,
            'ritual': spell.ritual,
            'concentration': spell.concentration,
            'has_higher_levels': spell.higher_levels is not None
        }


class SpellChunker(BaseChunker):
    """
    Creates optimized chunks for spell RAG retrieval.

    Creates multiple chunk types:
    - full_spell: Complete spell with all details
    - quick_reference: Concise mechanical summary
    - by_class: Class-specific reference
    - by_level: Level-specific reference
    """

    def create_chunks(self, parsed_content: ParsedContent) -> List[Chunk]:
        """Create spell chunks from parsed content."""
        chunks = []
        metadata = parsed_content.metadata

        # 1. Full spell chunk
        full_chunk = self._create_full_spell_chunk(parsed_content)
        if full_chunk:
            chunks.append(full_chunk)

        # 2. Quick reference chunk
        quick_ref_chunk = self._create_quick_reference_chunk(parsed_content)
        if quick_ref_chunk:
            chunks.append(quick_ref_chunk)

        # 3. Class-specific chunks (one per class)
        if metadata.get('classes'):
            for class_name in metadata['classes']:
                class_chunk = self._create_class_chunk(parsed_content, class_name)
                if class_chunk:
                    chunks.append(class_chunk)

        return chunks

    def _create_full_spell_chunk(self, parsed_content: ParsedContent) -> Chunk:
        """Create full spell description chunk with weighted spell name."""
        meta = parsed_content.metadata

        # IMPROVEMENT: Add spell name multiple times at the start for better retrieval
        # This increases the weight of the spell name in embeddings
        spell_name = meta['name']
        name_weight = f"SPELL: {spell_name}\n{spell_name}\n"

        content_parts = [
            name_weight,  # Spell name appears multiple times for weighting
            f"**{spell_name}**",
            f"Level {meta['level']} {meta['school']}",
            f"**Casting Time:** {meta['casting_time']}",
            f"**Range:** {meta['range']}",
            f"**Components:** {meta['components']}",
            f"**Duration:** {meta['duration']}",
            "",
            parsed_content.raw_text
        ]

        if meta.get('classes'):
            content_parts.insert(3, f"**Classes:** {', '.join(meta['classes'])}")

        content = "\n".join(content_parts)

        tags = {
            'spell',
            'full_description',
            f"level_{meta['level']}",
            f"school_{meta['school'].lower()}"
        }

        if meta.get('ritual'):
            tags.add('ritual')
        if meta.get('concentration'):
            tags.add('concentration')

        return Chunk(
            content=content,
            chunk_type='full_spell',
            metadata=meta.copy(),
            tags=tags
        )

    def _create_quick_reference_chunk(self, parsed_content: ParsedContent) -> Chunk:
        """Create quick reference chunk with just mechanics and weighted spell name."""
        meta = parsed_content.metadata

        # IMPROVEMENT: Repeat spell name for better matching
        spell_name = meta['name']
        content = f"SPELL: {spell_name}\n{spell_name}\n\n"
        content += f"**{spell_name}** - Level {meta['level']} {meta['school']}\n"
        content += f"Cast: {meta['casting_time']} | Range: {meta['range']} | "
        content += f"Components: {meta['components']} | Duration: {meta['duration']}\n"

        # Add first sentence of description
        first_sentence = parsed_content.raw_text.split('.')[0] + '.'
        content += f"\n{first_sentence}"

        return Chunk(
            content=content,
            chunk_type='quick_reference',
            metadata=meta.copy(),
            tags={'spell', 'quick_ref', f"level_{meta['level']}"}
        )

    def _create_class_chunk(self, parsed_content: ParsedContent, class_name: str) -> Chunk:
        """Create class-specific spell chunk with weighted spell name."""
        meta = parsed_content.metadata.copy()
        meta['for_class'] = class_name

        # IMPROVEMENT: Include spell name for better retrieval
        spell_name = meta['name']
        content = f"SPELL: {spell_name}\n"
        content += f"**{class_name} Spell: {spell_name}** (Level {meta['level']})\n"
        content += f"{meta['school']} | {meta['casting_time']} | {meta['range']}\n\n"
        content += parsed_content.raw_text[:300] + "..."  # Truncate for class-specific

        return Chunk(
            content=content,
            chunk_type='by_class',
            metadata=meta,
            tags={'spell', 'class_specific', f"class_{class_name.lower()}", f"level_{meta['level']}"}
        )
