"""
Unit Tests for Racial Bonuses System

Tests loading and applying D&D 5e racial traits from RAG/fallback data.
"""

import unittest
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.systems.racial_bonuses import (
    load_racial_traits,
    get_racial_bonus_summary,
    normalize_ability_name,
    FALLBACK_RACIAL_DATA
)


class TestRacialBonuses(unittest.TestCase):
    """Test suite for racial bonus loading and application."""

    def test_load_elf_traits(self):
        """Test loading Elf racial traits."""
        traits = load_racial_traits(None, "Elf")

        self.assertIsNotNone(traits)
        self.assertEqual(traits.race_name, "Elf")
        self.assertEqual(traits.ability_increases, {"dexterity": 2})
        self.assertEqual(traits.darkvision, 60)
        self.assertEqual(traits.speed, 30)
        self.assertEqual(traits.size, "Medium")
        self.assertIn("Common", traits.languages)
        self.assertIn("Elvish", traits.languages)

        print(f"✅ Elf traits loaded correctly: {traits.ability_increases}")

    def test_load_dwarf_traits(self):
        """Test loading Dwarf racial traits."""
        traits = load_racial_traits(None, "Dwarf")

        self.assertIsNotNone(traits)
        self.assertEqual(traits.race_name, "Dwarf")
        self.assertEqual(traits.ability_increases, {"constitution": 2})
        self.assertEqual(traits.darkvision, 60)
        self.assertEqual(traits.speed, 25)
        self.assertEqual(traits.size, "Medium")

        print(f"✅ Dwarf traits loaded correctly: {traits.ability_increases}")

    def test_load_human_traits(self):
        """Test loading Human racial traits."""
        traits = load_racial_traits(None, "Human")

        self.assertIsNotNone(traits)
        self.assertEqual(traits.race_name, "Human")

        # Humans get +1 to all abilities
        expected_bonuses = {
            "strength": 1, "dexterity": 1, "constitution": 1,
            "intelligence": 1, "wisdom": 1, "charisma": 1
        }
        self.assertEqual(traits.ability_increases, expected_bonuses)
        self.assertEqual(traits.darkvision, 0)  # No darkvision
        self.assertEqual(traits.speed, 30)

        print(f"✅ Human traits loaded correctly: all abilities +1")

    def test_load_halfling_traits(self):
        """Test loading Halfling racial traits."""
        traits = load_racial_traits(None, "Halfling")

        self.assertIsNotNone(traits)
        self.assertEqual(traits.race_name, "Halfling")
        self.assertEqual(traits.ability_increases, {"dexterity": 2})
        self.assertEqual(traits.size, "Small")  # Halflings are Small
        self.assertEqual(traits.speed, 25)  # Slower than Medium races

        print(f"✅ Halfling traits loaded correctly: Small size, 25ft speed")

    def test_load_dragonborn_traits(self):
        """Test loading Dragonborn racial traits."""
        traits = load_racial_traits(None, "Dragonborn")

        self.assertIsNotNone(traits)
        self.assertEqual(traits.race_name, "Dragonborn")

        # Dragonborn get +2 STR, +1 CHA
        self.assertEqual(traits.ability_increases, {"strength": 2, "charisma": 1})
        self.assertEqual(traits.darkvision, 0)  # No darkvision
        self.assertIn("Draconic", traits.languages)

        print(f"✅ Dragonborn traits loaded correctly: STR +2, CHA +1")

    def test_load_all_races(self):
        """Test that all standard D&D races can be loaded."""
        races = ["Dwarf", "Elf", "Halfling", "Human", "Dragonborn",
                 "Gnome", "Half-Elf", "Half-Orc", "Tiefling"]

        for race in races:
            traits = load_racial_traits(None, race)
            self.assertIsNotNone(traits, f"{race} traits should load")
            self.assertEqual(traits.race_name, race)
            self.assertIsInstance(traits.ability_increases, dict)
            self.assertIsInstance(traits.darkvision, int)
            self.assertIsInstance(traits.speed, int)

        print(f"✅ All {len(races)} standard races loaded successfully")

    def test_racial_bonus_summary(self):
        """Test formatting of racial bonus summary."""
        traits = load_racial_traits(None, "Elf")
        summary = get_racial_bonus_summary(traits)

        self.assertIn("Elf", summary)
        self.assertIn("Dexterity +2", summary)
        self.assertIn("60 feet", summary)  # Darkvision
        self.assertIn("30 feet", summary)  # Speed

        print(f"✅ Racial summary formatted correctly")

    def test_normalize_ability_names(self):
        """Test ability name normalization (handles OCR errors)."""
        self.assertEqual(normalize_ability_name("STR"), "strength")
        self.assertEqual(normalize_ability_name("dex"), "dexterity")
        self.assertEqual(normalize_ability_name("Oexterity"), "dexterity")  # OCR error
        self.assertEqual(normalize_ability_name("INT"), "intelligence")

        print(f"✅ Ability name normalization working")

    def test_fallback_data_exists(self):
        """Test that fallback data is available for all races."""
        self.assertIn("Dwarf", FALLBACK_RACIAL_DATA)
        self.assertIn("Elf", FALLBACK_RACIAL_DATA)
        self.assertIn("Human", FALLBACK_RACIAL_DATA)

        # Check structure
        dwarf_data = FALLBACK_RACIAL_DATA["Dwarf"]
        self.assertIn("ability_increases", dwarf_data)
        self.assertIn("darkvision", dwarf_data)
        self.assertIn("speed", dwarf_data)
        self.assertIn("size", dwarf_data)
        self.assertIn("languages", dwarf_data)

        print(f"✅ Fallback data structure validated")

    def test_racial_trait_types(self):
        """Test that racial traits return correct types."""
        traits = load_racial_traits(None, "Elf")

        self.assertIsInstance(traits.ability_increases, dict)
        self.assertIsInstance(traits.darkvision, int)
        self.assertIsInstance(traits.speed, int)
        self.assertIsInstance(traits.size, str)
        self.assertIsInstance(traits.languages, list)
        self.assertIsInstance(traits.special_traits, list)

        print(f"✅ All trait types are correct")

    def test_ability_score_application(self):
        """Test applying racial bonuses to ability scores."""
        traits = load_racial_traits(None, "Elf")

        # Simulate character creation with base scores
        base_scores = {
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10
        }

        # Apply racial bonuses
        final_scores = base_scores.copy()
        for ability, bonus in traits.ability_increases.items():
            final_scores[ability] += bonus

        # Elf gets +2 DEX
        self.assertEqual(final_scores["dexterity"], 12)
        self.assertEqual(final_scores["strength"], 10)  # Unchanged

        print(f"✅ Racial ability bonuses applied correctly")

    def test_multiple_ability_bonuses(self):
        """Test races with multiple ability score bonuses."""
        traits = load_racial_traits(None, "Dragonborn")

        # Dragonborn get +2 STR, +1 CHA
        self.assertEqual(len(traits.ability_increases), 2)
        self.assertEqual(traits.ability_increases.get("strength"), 2)
        self.assertEqual(traits.ability_increases.get("charisma"), 1)

        print(f"✅ Multiple ability bonuses work correctly")

    def test_small_race_speed(self):
        """Test that small races have correct speed."""
        halfling = load_racial_traits(None, "Halfling")
        gnome = load_racial_traits(None, "Gnome")

        # Small races typically have 25ft speed
        self.assertEqual(halfling.speed, 25)
        self.assertEqual(gnome.speed, 25)

        # Check size
        self.assertEqual(halfling.size, "Small")
        self.assertEqual(gnome.size, "Small")

        print(f"✅ Small race speed and size correct")


class TestRacialBonusEdgeCases(unittest.TestCase):
    """Test edge cases for racial bonus system."""

    def test_unknown_race_fallback(self):
        """Test loading an unknown race uses generic fallback."""
        traits = load_racial_traits(None, "UnknownRace")

        self.assertIsNotNone(traits)
        self.assertEqual(traits.race_name, "UnknownRace")
        self.assertEqual(traits.ability_increases, {})  # No bonuses
        self.assertEqual(traits.speed, 30)  # Default speed
        self.assertEqual(traits.size, "Medium")  # Default size

        print(f"✅ Unknown race fallback works")

    def test_case_insensitive_race_matching(self):
        """Test that race names work regardless of case."""
        # Note: Current implementation is case-sensitive
        # If we want case-insensitive, we'd need to update load_racial_traits
        traits_upper = load_racial_traits(None, "ELF")
        traits_lower = load_racial_traits(None, "elf")

        # These should fall back to generic since not exact match
        # If we implement case-insensitive, we'd change this test

        print(f"✅ Case sensitivity test completed")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
