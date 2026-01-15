#!/usr/bin/env python3
"""
Auto-apply class features during character creation using SRD RAG data.

This module queries ChromaDB for class information and automatically:
- Sets correct hit dice (d6/d8/d10/d12) FROM RAG
- Applies proficiencies (armor, weapons, tools, saving throws) FROM RAG
- Adds class abilities by level
- Sets spell slots for caster classes (hardcoded - not in SRD)
- Looks up and adds appropriate spells FROM RAG

Usage:
    from dnd_rag_system.systems.rag_character_enhancer import enhance_character_with_rag
    from dnd_rag_system.constants import CharacterClasses
    
    character = Character(name="Gandalf", character_class=CharacterClasses.WIZARD, level=1)
    enhance_character_with_rag(character)
"""

import sys
import chromadb
from pathlib import Path
from typing import Dict, List, Optional

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Use constants for class names
from dnd_rag_system.constants import CharacterClasses, CharacterRaces


class RAGCharacterEnhancer:
    """Enhance character creation with RAG-powered class/spell lookups."""
    
    # Spell slots by level (NOT in SRD, must be hardcoded)
    SPELL_SLOTS_FULL_CASTER = {
        1: [2, 0, 0, 0, 0, 0, 0, 0, 0],  # Level 1: 2x 1st-level slots
        2: [3, 0, 0, 0, 0, 0, 0, 0, 0],
        3: [4, 2, 0, 0, 0, 0, 0, 0, 0],
        4: [4, 3, 0, 0, 0, 0, 0, 0, 0],
        5: [4, 3, 2, 0, 0, 0, 0, 0, 0],
    }
    
    # Half-caster spell slots (Paladin, Ranger)
    SPELL_SLOTS_HALF_CASTER = {
        1: [0, 0, 0, 0, 0, 0, 0, 0, 0],  # No spells at level 1
        2: [2, 0, 0, 0, 0, 0, 0, 0, 0],
        3: [3, 0, 0, 0, 0, 0, 0, 0, 0],
        4: [3, 0, 0, 0, 0, 0, 0, 0, 0],
        5: [4, 2, 0, 0, 0, 0, 0, 0, 0],
    }
    
    # Caster types (using constants)
    FULL_CASTERS = [
        CharacterClasses.BARD,
        CharacterClasses.CLERIC, 
        CharacterClasses.DRUID,
        CharacterClasses.SORCERER,
        CharacterClasses.WIZARD
    ]
    HALF_CASTERS = [CharacterClasses.PALADIN, CharacterClasses.RANGER]
    WARLOCK = CharacterClasses.WARLOCK  # Pact magic (different system)
    
    def __init__(self, chroma_path: str = 'chromadb'):
        """Initialize with ChromaDB connection."""
        self.client = chromadb.PersistentClient(path=chroma_path)
        
        try:
            self.srd_collection = self.client.get_collection("dnd5e_srd")
            print("✅ Connected to SRD collection")
        except Exception as e:
            print(f"⚠️  Warning: Could not load SRD collection: {e}")
            self.srd_collection = None
    
    def query_class_info(self, class_name: str) -> Optional[Dict]:
        """Query ChromaDB for class information."""
        if not self.srd_collection:
            return None
        
        results = self.srd_collection.query(
            query_texts=[f"{class_name} class features hit dice proficiencies"],
            n_results=1,
            where={"$and": [{"type": {"$eq": "class"}}, {"name": {"$eq": class_name}}]}
        )
        
        if results['documents'] and results['documents'][0]:
            return {
                'document': results['documents'][0][0],
                'metadata': results['metadatas'][0][0]
            }
        return None
    
    def query_spells_for_class(self, class_name: str, max_level: int = 1, limit: int = 10) -> List[Dict]:
        """Query ChromaDB for appropriate spells for a class."""
        if not self.srd_collection:
            return []
        
        # Query for cantrips and spells up to character level
        spells = []
        
        for spell_level in range(0, max_level + 1):
            results = self.srd_collection.query(
                query_texts=[f"{class_name} spells level {spell_level}"],
                n_results=limit,
                where={"$and": [{"type": {"$eq": "spell"}}, {"level": {"$eq": spell_level}}]}
            )
            
            if results['documents'] and results['documents'][0]:
                for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                    spells.append({
                        'name': meta.get('name', 'Unknown'),
                        'level': meta.get('level', 0),
                        'school': meta.get('school', 'Unknown')
                    })
        
        return spells
    
    def get_hit_die(self, class_name: str) -> int:
        """Get hit die for class FROM RAG (not hardcoded)."""
        # Try RAG lookup FIRST
        class_info = self.query_class_info(class_name)
        if class_info and 'metadata' in class_info:
            hit_die_str = class_info['metadata'].get('hit_die', 'd8')
            try:
                return int(hit_die_str.replace('d', ''))
            except:
                pass
        
        # Fallback to d8 only if RAG fails
        print(f"  ⚠️  Could not get hit die from RAG for {class_name}, using d8")
        return 8
    
    def get_primary_abilities(self, class_name: str) -> List[str]:
        """Get recommended primary abilities for a class FROM RAG."""
        # Try RAG lookup
        class_info = self.query_class_info(class_name)
        if class_info and 'document' in class_info:
            doc_text = class_info['document']
            
            # Extract "Primary Ability: Intelligence" from document
            import re
            match = re.search(r'Primary Ability:\s*([^\n]+)', doc_text, re.IGNORECASE)
            if match:
                abilities_str = match.group(1).strip()
                # Parse "Strength and Charisma" or "Intelligence"
                abilities = re.findall(r'\b(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\b', abilities_str, re.IGNORECASE)
                return [a.capitalize() for a in abilities]
        
        # Fallback
        return []
    
    def get_spell_slots(self, class_name: str, level: int) -> List[int]:
        """Get spell slots for class at given level."""
        if class_name in self.FULL_CASTERS:
            return self.SPELL_SLOTS_FULL_CASTER.get(level, [0] * 9)
        elif class_name in self.HALF_CASTERS:
            return self.SPELL_SLOTS_HALF_CASTER.get(level, [0] * 9)
        elif class_name == self.WARLOCK:
            # Warlock has pact magic (fewer but higher-level slots)
            if level == 1:
                return [1, 0, 0, 0, 0, 0, 0, 0, 0]  # 1 slot, all at pact level
            elif level <= 5:
                return [2, 0, 0, 0, 0, 0, 0, 0, 0]  # 2 slots
        
        return [0] * 9  # No spellcasting
    
    def extract_proficiencies(self, class_doc: str) -> Dict[str, List[str]]:
        """Extract proficiencies from class document text."""
        proficiencies = {
            'armor': [],
            'weapons': [],
            'tools': [],
            'saving_throws': []
        }
        
        lines = class_doc.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'armor proficiency:' in line_lower:
                prof = line.split(':', 1)[1].strip()
                if prof and prof != 'None':
                    proficiencies['armor'] = [p.strip() for p in prof.split(',')]
            elif 'weapon proficiency:' in line_lower:
                prof = line.split(':', 1)[1].strip()
                if prof and prof != 'None':
                    proficiencies['weapons'] = [p.strip() for p in prof.split(',')]
            elif 'saving throws:' in line_lower:
                prof = line.split(':', 1)[1].strip()
                if prof and prof != 'N/A':
                    proficiencies['saving_throws'] = [p.strip() for p in prof.split(',')[:2]]
        
        return proficiencies
    
    def enhance_character(self, character) -> None:
        """
        Enhance character with RAG-powered class features.
        
        Args:
            character: Character object to enhance (modified in-place)
        """
        print(f"\n🔮 Enhancing {character.name} ({character.character_class})...")
        
        # Skip if already enhanced (check for marker)
        if any('SRD-enhanced' in str(f) for f in character.class_features):
            print("  ⏭️  Already enhanced, skipping")
            return
        
        # 1. Set correct hit die and HP (only if HP is 0)
        if character.hit_points == 0:
            hit_die = self.get_hit_die(character.character_class)
            character.hit_points = character.calculate_hit_points(hit_die)
            print(f"  ✓ Hit Die: d{hit_die} → HP: {character.hit_points}")
        
        # 2. Query class info from RAG
        class_info = self.query_class_info(character.character_class)
        
        if class_info:
            doc_text = class_info['document']
            
            # 3. Extract and apply proficiencies
            proficiencies = self.extract_proficiencies(doc_text)
            
            prof_list = []
            if proficiencies['armor']:
                prof_list.append(f"Armor: {', '.join(proficiencies['armor'])}")
            if proficiencies['weapons']:
                prof_list.append(f"Weapons: {', '.join(proficiencies['weapons'])}")
            if proficiencies['saving_throws']:
                prof_list.append(f"Saves: {', '.join(proficiencies['saving_throws'])}")
            
            character.proficiencies.extend(prof_list)
            print(f"  ✓ Proficiencies: {len(prof_list)} added")
        
        # 4. Add class features
        basic_features = self._get_basic_class_features(character.character_class, character.level)
        character.class_features.extend(basic_features)
        print(f"  ✓ Class Features: {len(basic_features)} added")
        
        # 5. Set spell slots for casters
        spell_slots = self.get_spell_slots(character.character_class, character.level)
        if any(slot > 0 for slot in spell_slots):
            slots_summary = ', '.join(f"{i+1}st: {slot}" for i, slot in enumerate(spell_slots[:5]) if slot > 0)
            character.class_features.append(f"Spell Slots: {slots_summary}")
            print(f"  ✓ Spell Slots: {slots_summary}")
            
            # 6. Look up appropriate spells
            spells = self.query_spells_for_class(character.character_class, max_level=1, limit=6)
            if spells:
                for spell in spells[:6]:  # Add up to 6 starting spells
                    character.spells.append(f"{spell['name']} ({spell['school']} {spell['level']})")
                print(f"  ✓ Spells: {len(spells)} suggested")
        
        # Mark as enhanced
        character.class_features.append("(SRD-enhanced)")
        
        print(f"✨ {character.name} enhanced!")
    
    def _get_basic_class_features(self, class_name: str, level: int) -> List[str]:
        """Get basic class features by level."""
        features = []
        
        # Level 1 features for each class (using constants to avoid magic strings)
        level_1_features = {
            CharacterClasses.BARBARIAN: ['Rage (2/day)', 'Unarmored Defense'],
            CharacterClasses.BARD: ['Spellcasting', 'Bardic Inspiration (d6)'],
            CharacterClasses.CLERIC: ['Spellcasting', 'Divine Domain'],
            CharacterClasses.DRUID: ['Spellcasting', 'Druidic'],
            CharacterClasses.FIGHTER: ['Fighting Style', 'Second Wind'],
            CharacterClasses.MONK: ['Unarmored Defense', 'Martial Arts'],
            CharacterClasses.PALADIN: ['Divine Sense', 'Lay on Hands'],
            CharacterClasses.RANGER: ['Favored Enemy', 'Natural Explorer'],
            CharacterClasses.ROGUE: ['Expertise', 'Sneak Attack (1d6)', 'Thieves\' Cant'],
            CharacterClasses.SORCERER: ['Spellcasting', 'Sorcerous Origin'],
            CharacterClasses.WARLOCK: ['Otherworldly Patron', 'Pact Magic'],
            CharacterClasses.WIZARD: ['Spellcasting', 'Arcane Recovery']
        }
        
        if level >= 1 and class_name in level_1_features:
            features.extend(level_1_features[class_name])
        
        return features


def enhance_character_with_rag(character, chroma_path: str = 'chromadb'):
    """
    Convenience function to enhance a character with RAG data.
    
    Args:
        character: Character object to enhance
        chroma_path: Path to ChromaDB database
    """
    enhancer = RAGCharacterEnhancer(chroma_path)
    enhancer.enhance_character(character)


# Example usage
if __name__ == '__main__':
    # Mock Character class for testing
    from dataclasses import dataclass, field
    from typing import List
    
    @dataclass
    class Character:
        name: str = ""
        character_class: str = ""
        level: int = 1
        constitution: int = 10
        hit_points: int = 0
        proficiencies: List[str] = field(default_factory=list)
        class_features: List[str] = field(default_factory=list)
        spells: List[str] = field(default_factory=list)
        
        def get_ability_modifier(self, score: int) -> int:
            return (score - 10) // 2
        
        def calculate_hit_points(self, hit_die: int) -> int:
            con_mod = self.get_ability_modifier(self.constitution)
            return hit_die + con_mod
    
    # Test with a Wizard
    gandalf = Character(
        name="Gandalf",
        character_class="Wizard",
        level=1,
        constitution=14
    )
    
    enhance_character_with_rag(gandalf)
    
    print("\n📜 Character Sheet:")
    print(f"Name: {gandalf.name}")
    print(f"Class: {gandalf.character_class} {gandalf.level}")
    print(f"HP: {gandalf.hit_points}")
    print(f"\nProficiencies:")
    for prof in gandalf.proficiencies:
        print(f"  - {prof}")
    print(f"\nClass Features:")
    for feature in gandalf.class_features:
        print(f"  - {feature}")
    print(f"\nSpells:")
    for spell in gandalf.spells:
        print(f"  - {spell}")
