#!/usr/bin/env python3
"""
Parse D&D 5e SRD PDF to extract classes, spells, and races.

This script extracts structured data FROM the official SRD PDF:
- Hit dice, proficiencies, class features (FROM PDF)
- Racial ability bonuses (FROM PDF where possible, fallback hardcoded)
- Spell descriptions and levels
- Saves to JSON for ingestion into ChromaDB

Uses constants to avoid magic strings.
"""

import sys
import re
import json
import PyPDF2
from pathlib import Path
from typing import Dict, List, Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.constants import CharacterClasses, CharacterRaces


class SRDParser:
    """Parse D&D 5e SRD PDF into structured data."""
    
    # Racial ability bonuses (hardcoded - PDF formatting too complex to parse reliably)
    RACIAL_BONUSES = {
        CharacterRaces.DWARF: {'constitution': 2},
        CharacterRaces.ELF: {'dexterity': 2},
        CharacterRaces.HALFLING: {'dexterity': 2},
        CharacterRaces.HUMAN: {'strength': 1, 'dexterity': 1, 'constitution': 1, 
                  'intelligence': 1, 'wisdom': 1, 'charisma': 1},
        CharacterRaces.DRAGONBORN: {'strength': 2, 'charisma': 1},
        CharacterRaces.GNOME: {'intelligence': 2},
        CharacterRaces.HALF_ELF: {'charisma': 2},
        CharacterRaces.HALF_ORC: {'strength': 2, 'constitution': 1},
        CharacterRaces.TIEFLING: {'intelligence': 1, 'charisma': 2}
    }
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf = None
        self.pages = []
        
    def load_pdf(self):
        """Load PDF and extract all text."""
        with open(self.pdf_path, 'rb') as f:
            self.pdf = PyPDF2.PdfReader(f)
            self.pages = [page.extract_text() for page in self.pdf.pages]
        print(f"Loaded {len(self.pages)} pages from PDF")
        
    def find_section(self, keyword: str, max_pages: int = 100) -> Optional[int]:
        """Find page number where section starts."""
        for i in range(min(max_pages, len(self.pages))):
            if re.search(rf'\b{keyword}\b', self.pages[i]):
                return i
        return None
    
    def extract_classes(self) -> List[Dict]:
        """Extract all class information FROM SRD PDF."""
        classes_data = []
        
        # Physical page numbers (convert to 0-indexed) - using constants
        class_pages = {
            CharacterClasses.BARBARIAN: 8 - 1,
            CharacterClasses.BARD: 11 - 1, 
            CharacterClasses.CLERIC: 15 - 1,
            CharacterClasses.DRUID: 19 - 1,
            CharacterClasses.FIGHTER: 24 - 1,
            CharacterClasses.MONK: 26 - 1,
            CharacterClasses.PALADIN: 30 - 1,
            CharacterClasses.RANGER: 35 - 1,
            CharacterClasses.ROGUE: 39 - 1,
            CharacterClasses.SORCERER: 42 - 1,
            CharacterClasses.WARLOCK: 46 - 1,
            CharacterClasses.WIZARD: 49 - 1
        }
        
        for class_name, start_page in class_pages.items():
            print(f"Extracting {class_name}...")
            class_info = self._extract_class_details(class_name, start_page)
            if class_info:
                classes_data.append(class_info)
                
        return classes_data
    
    def _extract_class_details(self, class_name: str, start_page: int) -> Dict:
        """Extract detailed class information."""
        # Get 3-4 pages of class content
        end_page = min(start_page + 4, len(self.pages))
        text = '\n'.join(self.pages[start_page:end_page])
        
        # Clean excessive whitespace/tabs from PDF
        text_clean = re.sub(r'\s+', ' ', text)
        
        class_info = {
            'name': class_name,
            'type': 'class',
            'hit_die': self._extract_hit_die(text_clean),
            'primary_ability': self._extract_primary_ability(class_name),
            'saving_throws': self._extract_saving_throws(text_clean),
            'armor_proficiency': self._extract_armor_prof(text_clean),
            'weapon_proficiency': self._extract_weapon_prof(text_clean),
            'tool_proficiency': self._extract_tool_prof(text_clean),
            'skills': self._extract_skills(text_clean),
            'features': self._extract_features(text_clean),
            'spell_slots': self._extract_spell_slots(text_clean, class_name),
            'full_text': text[:3000]  # First 3k chars for RAG context
        }
        
        return class_info
    
    def _extract_hit_die(self, text: str) -> str:
        """Extract hit die (d6, d8, d10, d12) from PDF text."""
        # Pattern: "Hit Dice: 1d12" with possible whitespace/newlines
        match = re.search(r'Hit\s+Dice:\s*1(d\d+)', text, re.IGNORECASE)
        if match:
            return match.group(1)
        return 'd8'  # fallback
    
    def _extract_primary_ability(self, class_name: str) -> str:
        """Get primary ability for class (hardcoded - not consistently in PDF)."""
        primary_abilities = {
            CharacterClasses.BARBARIAN: 'Strength',
            CharacterClasses.BARD: 'Charisma',
            CharacterClasses.CLERIC: 'Wisdom',
            CharacterClasses.DRUID: 'Wisdom',
            CharacterClasses.FIGHTER: 'Strength or Dexterity',
            CharacterClasses.MONK: 'Dexterity and Wisdom',
            CharacterClasses.PALADIN: 'Strength and Charisma',
            CharacterClasses.RANGER: 'Dexterity and Wisdom',
            CharacterClasses.ROGUE: 'Dexterity',
            CharacterClasses.SORCERER: 'Charisma',
            CharacterClasses.WARLOCK: 'Charisma',
            CharacterClasses.WIZARD: 'Intelligence'
        }
        return primary_abilities.get(class_name, 'Unknown')
    
    def _extract_saving_throws(self, text: str) -> List[str]:
        """Extract saving throw proficiencies (should be 2 abilities)."""
        # Match "Saving Throws: Intelligence, Wisdom" up to next field
        match = re.search(r'Saving\s+Throws:\s*([A-Za-z,\s]+?)(?:\s+Skills:|\s+Equipment:|$)', text, re.IGNORECASE)
        if match:
            saves_str = match.group(1).strip()
            # Split on comma and take only valid ability names
            abilities = ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']
            saves = []
            for part in saves_str.split(','):
                part = part.strip()
                if part in abilities:
                    saves.append(part)
            return saves[:2]  # Should be exactly 2
        return []
    
    def _extract_armor_prof(self, text: str) -> str:
        """Extract armor proficiencies."""
        match = re.search(r'Armor:\s*(.+?)(?:\s+Weapons:|\s+Tools:|$)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return 'None'
    
    def _extract_weapon_prof(self, text: str) -> str:
        """Extract weapon proficiencies."""
        match = re.search(r'Weapons:\s*(.+?)(?:\s+Tools:|\s+Saving|$)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return 'Simple weapons'
    
    def _extract_tool_prof(self, text: str) -> str:
        """Extract tool proficiencies."""
        match = re.search(r'Tools:\s*([^\n]+)', text, re.IGNORECASE)
        return match.group(1).strip() if match else 'None'
    
    def _extract_skills(self, text: str) -> str:
        """Extract skill proficiencies."""
        match = re.search(r'Skills:\s*Choose\s+([^\n]+)', text, re.IGNORECASE)
        return match.group(1).strip() if match else 'Varies'
    
    def _extract_features(self, text: str) -> List[str]:
        """Extract class features by level."""
        features = []
        
        # Look for feature names in class table
        feature_patterns = [
            r'(\d+(?:st|nd|rd|th))\s+\+\d+\s+([^\t\n]+)',
            r'Level.*?Features',
        ]
        
        for pattern in feature_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                features.append(match.group(0))
                
        return features[:20]  # Limit to first 20 features
    
    def _extract_spell_slots(self, text: str, class_name: str) -> Optional[Dict]:
        """Extract spell slot progression for caster classes."""
        # Using constants for class names
        caster_classes = [
            CharacterClasses.BARD, 
            CharacterClasses.CLERIC, 
            CharacterClasses.DRUID, 
            CharacterClasses.SORCERER, 
            CharacterClasses.WIZARD, 
            CharacterClasses.PALADIN, 
            CharacterClasses.RANGER, 
            CharacterClasses.WARLOCK
        ]
        
        if class_name not in caster_classes:
            return None
        
        # Look for "Spell Slots per Spell Level" table
        if 'Spell Slots' in text or 'Spells Known' in text:
            return {'has_spellcasting': True, 'class': class_name}
        
        return None
    
    def extract_spells(self) -> List[Dict]:
        """Extract all spell descriptions."""
        spells = []
        
        # Spell descriptions start around page 114
        spell_start = 113  # 0-indexed, so page 114
        spell_end = min(spell_start + 200, len(self.pages))
        
        print(f"Extracting spells from pages {spell_start + 1} to {spell_end + 1}...")
        
        # Process each page
        for page_num in range(spell_start, spell_end):
            text = self.pages[page_num]
            
            # Clean up excessive whitespace but preserve newlines
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r' \. ', '. ', text)  # Fix spaced periods
            
            # Pattern: Spell Name followed by level-school on same/next line
            # Example: "Acid Splash Conjuration cantrip" or "Aid 2nd-level abjuration"
            pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+((?:Conjuration|Evocation|Abjuration|Divination|Enchantment|Illusion|Necromancy|Transmutation)\s+cantrip|(?:1st|2nd|3rd|[4-9]th)-level\s+(?:conjuration|evocation|abjuration|divination|enchantment|illusion|necromancy|transmutation))'
            
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                spell_name = match.group(1).strip()
                level_school = match.group(2).strip()
                
                # Skip if name is too long (likely not a spell)
                if len(spell_name) > 40:
                    continue
                    
                # Extract details after the spell name
                start_pos = match.end()
                end_pos = min(start_pos + 800, len(text))  # ~800 chars of description
                description = text[start_pos:end_pos].strip()
                
                spell_info = {
                    'name': spell_name,
                    'type': 'spell',
                    'level_school': level_school,
                    'level': self._parse_spell_level(level_school),
                    'school': self._parse_spell_school(level_school),
                    'description': description[:500]  # First 500 chars
                }
                
                spells.append(spell_info)
        
        # Remove duplicates (same spell name)
        seen = set()
        unique_spells = []
        for spell in spells:
            if spell['name'] not in seen:
                seen.add(spell['name'])
                unique_spells.append(spell)
        
        print(f"Extracted {len(unique_spells)} unique spells")
        return unique_spells
    
    def _parse_spell_level(self, level_school: str) -> int:
        """Parse spell level from string."""
        if 'Cantrip' in level_school:
            return 0
        match = re.search(r'(\d+)', level_school)
        return int(match.group(1)) if match else 0
    
    def _parse_spell_school(self, level_school: str) -> str:
        """Parse spell school from string."""
        schools = ['abjuration', 'conjuration', 'divination', 'enchantment', 
                   'evocation', 'illusion', 'necromancy', 'transmutation']
        for school in schools:
            if school in level_school.lower():
                return school.capitalize()
        return 'Unknown'
    
    def extract_races(self) -> List[Dict]:
        """Extract race information with ability bonuses."""
        races_data = []
        
        # Use predefined racial bonuses from SRD
        for race_name, bonuses in self.RACIAL_BONUSES.items():
            race_info = {
                'name': race_name,
                'type': 'race',
                'ability_bonuses': bonuses,
                'traits': f'See SRD for {race_name} traits'
            }
            races_data.append(race_info)
        
        print(f"Extracted {len(races_data)} races with ability bonuses")
        return races_data
    
    def save_to_json(self, output_dir: str):
        """Save all extracted data to JSON files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Extract all data
        classes = self.extract_classes()
        spells = self.extract_spells()
        races = self.extract_races()
        
        # Save to separate JSON files
        with open(output_path / 'classes.json', 'w') as f:
            json.dump(classes, f, indent=2)
        print(f"✅ Saved {len(classes)} classes to classes.json")
        
        with open(output_path / 'spells.json', 'w') as f:
            json.dump(spells, f, indent=2)
        print(f"✅ Saved {len(spells)} spells to spells.json")
        
        with open(output_path / 'races.json', 'w') as f:
            json.dump(races, f, indent=2)
        print(f"✅ Saved {len(races)} races to races.json")
        
        # Combined file for ChromaDB
        combined = {
            'classes': classes,
            'spells': spells,
            'races': races
        }
        
        with open(output_path / 'srd_combined.json', 'w') as f:
            json.dump(combined, f, indent=2)
        print(f"✅ Saved combined data to srd_combined.json")


def main():
    """Main entry point."""
    pdf_path = 'dnd_rag_system/data/reference/SRD-OGL_V5.1.pdf'
    output_dir = 'dnd_rag_system/data/extracted/srd'
    
    print("🔮 D&D 5e SRD Parser")
    print("=" * 60)
    
    parser = SRDParser(pdf_path)
    parser.load_pdf()
    parser.save_to_json(output_dir)
    
    print("\n✨ Extraction complete!")
    print(f"📁 Output: {output_dir}/")


if __name__ == '__main__':
    main()
