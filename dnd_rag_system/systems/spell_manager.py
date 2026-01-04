"""
D&D 5e Spell and Resource Management System

Handles:
- RAG-based spell level lookup
- Spell slot progression by class/level
- Potion effects and healing
- Spell targeting (self, ally, enemy)
- Cantrip detection
"""

import re
import random
from typing import Dict, List, Optional, Tuple, Any
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings


class SpellManager:
    """
    Manages spell lookups, slot progression, and resource management.

    Uses RAG to look up spell details, determine spell levels,
    and manage spell slot progression tables.
    """

    def __init__(self, db_manager: ChromaDBManager):
        """
        Initialize spell manager.

        Args:
            db_manager: ChromaDBManager for RAG lookups
        """
        self.db = db_manager

        # D&D 5e Spell Slot Progression (PHB p.15, 45, etc.)
        # Format: {class_name: {level: {slot_level: num_slots}}}
        self.spell_slot_progression = self._init_spell_slot_progression()

        # Potion healing tables
        self.potion_effects = {
            "healing potion": {"dice": "2d4+2", "type": "healing"},
            "greater healing potion": {"dice": "4d4+4", "type": "healing"},
            "superior healing potion": {"dice": "8d4+8", "type": "healing"},
            "supreme healing potion": {"dice": "10d4+20", "type": "healing"},
            "potion of healing": {"dice": "2d4+2", "type": "healing"},
        }

    def _init_spell_slot_progression(self) -> Dict[str, Dict[int, Dict[int, int]]]:
        """
        Initialize D&D 5e spell slot progression tables.

        Returns spell slots by: {class_name: {character_level: {spell_level: num_slots}}}
        """
        # Full casters (Wizard, Sorcerer, Cleric, Druid, Bard)
        full_caster = {
            1: {1: 2},
            2: {1: 3},
            3: {1: 4, 2: 2},
            4: {1: 4, 2: 3},
            5: {1: 4, 2: 3, 3: 2},
            6: {1: 4, 2: 3, 3: 3},
            7: {1: 4, 2: 3, 3: 3, 4: 1},
            8: {1: 4, 2: 3, 3: 3, 4: 2},
            9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
            11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
            12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
            13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
            14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
            16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
            18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
            20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},
        }

        # Half casters (Paladin, Ranger)
        half_caster = {
            1: {},
            2: {1: 2},
            3: {1: 3},
            4: {1: 3},
            5: {1: 4, 2: 2},
            6: {1: 4, 2: 2},
            7: {1: 4, 2: 3},
            8: {1: 4, 2: 3},
            9: {1: 4, 2: 3, 3: 2},
            10: {1: 4, 2: 3, 3: 2},
            11: {1: 4, 2: 3, 3: 3},
            12: {1: 4, 2: 3, 3: 3},
            13: {1: 4, 2: 3, 3: 3, 4: 1},
            14: {1: 4, 2: 3, 3: 3, 4: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 2},
            16: {1: 4, 2: 3, 3: 3, 4: 2},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
            20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
        }

        # Warlock (Pact Magic - different system, but simplified here)
        warlock = {
            1: {1: 1},
            2: {1: 2},
            3: {2: 2},
            4: {2: 2},
            5: {3: 2},
            6: {3: 2},
            7: {4: 2},
            8: {4: 2},
            9: {5: 2},
            10: {5: 2},
            11: {5: 3},
            12: {5: 3},
            13: {5: 3},
            14: {5: 3},
            15: {5: 3},
            16: {5: 3},
            17: {5: 4},
            18: {5: 4},
            19: {5: 4},
            20: {5: 4},
        }

        return {
            "Wizard": full_caster,
            "Sorcerer": full_caster,
            "Cleric": full_caster,
            "Druid": full_caster,
            "Bard": full_caster,
            "Paladin": half_caster,
            "Ranger": half_caster,
            "Warlock": warlock,
            # Non-casters
            "Fighter": {},
            "Barbarian": {},
            "Rogue": {},
            "Monk": {},
        }

    def get_spell_slots_for_level(self, class_name: str, character_level: int) -> Dict[int, int]:
        """
        Get spell slot allocation for a character class and level.

        Args:
            class_name: Character class (e.g., "Wizard", "Paladin")
            character_level: Character level (1-20)

        Returns:
            Dictionary of {spell_level: num_slots}
        """
        class_progression = self.spell_slot_progression.get(class_name, {})
        return class_progression.get(character_level, {})

    def lookup_spell_level(self, spell_name: str) -> Optional[int]:
        """
        Look up a spell's level using RAG.

        Args:
            spell_name: Name of the spell (e.g., "Magic Missile", "Cure Wounds")

        Returns:
            Spell level (0-9), or None if not found
            0 = cantrip
        """
        # Search for spell in RAG database
        results = self.db.search(
            settings.COLLECTION_NAMES['spells'],
            f"{spell_name} level",
            n_results=3
        )

        if not results or not results.get('documents') or not results['documents'][0]:
            return None

        # Check metadata first (most reliable)
        if results.get('metadatas') and results['metadatas'][0]:
            for metadata in results['metadatas'][0]:
                if 'level' in metadata:
                    level = metadata['level']
                    if isinstance(level, int):
                        return level
                    elif isinstance(level, str):
                        # Try to parse level from string
                        if level.lower() == 'cantrip':
                            return 0
                        try:
                            return int(level)
                        except ValueError:
                            pass

        # Parse from document text
        for doc in results['documents'][0]:
            doc_lower = doc.lower()

            # Check for cantrip
            if 'cantrip' in doc_lower:
                return 0

            # Try to find level pattern like "1st-level", "2nd-level", etc.
            level_match = re.search(r'(\d+)(?:st|nd|rd|th)-level', doc_lower)
            if level_match:
                return int(level_match.group(1))

            # Try pattern like "Level: 1", "Level 2", etc.
            level_match = re.search(r'level:?\s*(\d+)', doc_lower)
            if level_match:
                return int(level_match.group(1))

        return None

    def lookup_spell_details(self, spell_name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive spell details from RAG.

        Args:
            spell_name: Name of spell

        Returns:
            Dictionary with spell details:
            - name: spell name
            - level: spell level (0-9)
            - school: school of magic
            - concentration: whether requires concentration
            - description: spell description
        """
        results = self.db.search(
            settings.COLLECTION_NAMES['spells'],
            spell_name,
            n_results=1
        )

        if not results or not results.get('documents') or not results['documents'][0]:
            return None

        doc = results['documents'][0][0]
        metadata = results['metadatas'][0][0] if results.get('metadatas') else {}

        # Extract details
        spell_level = self.lookup_spell_level(spell_name)

        # Check for concentration
        concentration = 'concentration' in doc.lower()

        # Try to extract school
        school_match = re.search(r'(abjuration|conjuration|divination|enchantment|evocation|illusion|necromancy|transmutation)', doc.lower())
        school = school_match.group(1).title() if school_match else "Unknown"

        return {
            "name": spell_name,
            "level": spell_level if spell_level is not None else metadata.get('level', 0),
            "school": school,
            "concentration": concentration,
            "description": doc[:300] + "..." if len(doc) > 300 else doc
        }

    def is_cantrip(self, spell_name: str) -> bool:
        """
        Check if a spell is a cantrip (level 0).

        Args:
            spell_name: Name of spell

        Returns:
            True if cantrip, False otherwise
        """
        level = self.lookup_spell_level(spell_name)
        return level == 0 if level is not None else False

    def roll_dice(self, dice_formula: str) -> Tuple[int, List[int]]:
        """
        Roll dice using standard D&D notation (e.g., "2d4+2", "1d8", "3d6+5").

        Args:
            dice_formula: Dice formula string (e.g., "2d4+2")

        Returns:
            Tuple of (total, individual_rolls)
        """
        # Parse dice formula (e.g., "2d4+2" -> 2d4 with +2 modifier)
        match = re.match(r'(\d+)d(\d+)([+-]\d+)?', dice_formula.lower())

        if not match:
            return 0, []

        num_dice = int(match.group(1))
        die_size = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        # Roll the dice
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]
        total = sum(rolls) + modifier

        return total, rolls

    def use_potion(self, potion_name: str) -> Dict[str, Any]:
        """
        Use a potion and apply its effects.

        Args:
            potion_name: Name of potion (case-insensitive)

        Returns:
            Dictionary with:
            - success: whether potion was recognized
            - type: effect type ("healing", etc.)
            - amount: total healing/effect
            - rolls: individual dice rolls
            - message: description of effect
        """
        potion_lower = potion_name.lower()

        # Find matching potion
        potion_effect = None
        for potion_key, effect in self.potion_effects.items():
            if potion_key in potion_lower or potion_lower in potion_key:
                potion_effect = effect
                break

        if not potion_effect:
            return {
                "success": False,
                "message": f"Unknown potion: {potion_name}"
            }

        # Roll healing dice
        total, rolls = self.roll_dice(potion_effect["dice"])

        return {
            "success": True,
            "type": potion_effect["type"],
            "amount": total,
            "rolls": rolls,
            "dice_formula": potion_effect["dice"],
            "message": f"Drank {potion_name}: rolled {potion_effect['dice']} = {rolls} = {total} HP restored"
        }

    def get_xp_for_cr(self, challenge_rating: float) -> int:
        """
        Get XP award for defeating a monster of given CR.

        Args:
            challenge_rating: Monster's CR (e.g., 0.125, 1, 5, 20)

        Returns:
            XP value
        """
        # D&D 5e XP by CR (DMG p.274)
        xp_table = {
            0: 10,
            0.125: 25,
            0.25: 50,
            0.5: 100,
            1: 200,
            2: 450,
            3: 700,
            4: 1100,
            5: 1800,
            6: 2300,
            7: 2900,
            8: 3900,
            9: 5000,
            10: 5900,
            11: 7200,
            12: 8400,
            13: 10000,
            14: 11500,
            15: 13000,
            16: 15000,
            17: 18000,
            18: 20000,
            19: 22000,
            20: 25000,
            21: 33000,
            22: 41000,
            23: 50000,
            24: 62000,
            25: 75000,
            26: 90000,
            27: 105000,
            28: 120000,
            29: 135000,
            30: 155000,
        }

        return xp_table.get(challenge_rating, 0)

    def lookup_monster_cr(self, monster_name: str) -> Optional[float]:
        """
        Look up a monster's Challenge Rating using RAG.

        Args:
            monster_name: Name of monster (e.g., "Goblin", "Ancient Red Dragon")

        Returns:
            CR value, or None if not found
        """
        results = self.db.search(
            settings.COLLECTION_NAMES['monsters'],
            f"{monster_name} challenge rating CR",
            n_results=1
        )

        if not results or not results.get('documents') or not results['documents'][0]:
            # Default CRs for common monsters
            defaults = {
                "goblin": 0.25,
                "orc": 0.5,
                "ogre": 2,
                "troll": 5,
                "dragon": 10,
                "ancient dragon": 20,
            }
            for key, cr in defaults.items():
                if key in monster_name.lower():
                    return cr
            return 1  # Default CR if unknown

        doc = results['documents'][0][0]

        # Try to extract CR from document
        cr_match = re.search(r'challenge rating:?\s*([\d.]+)|cr:?\s*([\d.]+)', doc.lower())
        if cr_match:
            cr_str = cr_match.group(1) or cr_match.group(2)
            try:
                return float(cr_str)
            except ValueError:
                pass

        # Check metadata
        if results.get('metadatas') and results['metadatas'][0]:
            metadata = results['metadatas'][0][0]
            if 'cr' in metadata:
                try:
                    return float(metadata['cr'])
                except (ValueError, TypeError):
                    pass

        return 1  # Default CR
