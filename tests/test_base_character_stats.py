"""
Tests for Base Character Stats Storage System

Tests the Dict-based character storage system that supports
both solo mode and party mode.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.game_state import GameSession
from dnd_rag_system.systems.character_creator import Character


@pytest.fixture
def thorin():
    """Thorin Stormshield character"""
    return Character(
        name="Thorin Stormshield",
        race="Dwarf",
        character_class="Fighter",
        strength=16,
        dexterity=12,
        constitution=16,
        intelligence=10,
        wisdom=13,
        charisma=8,
        proficiency_bonus=2,
    )


@pytest.fixture
def elara():
    """Elara Moonwhisper character"""
    return Character(
        name="Elara Moonwhisper",
        race="Elf",
        character_class="Wizard",
        strength=8,
        dexterity=16,
        constitution=12,
        intelligence=18,
        wisdom=14,
        charisma=10,
        proficiency_bonus=2,
    )


@pytest.fixture
def murren():
    """Murren Nightshade character"""
    return Character(
        name="Murren Nightshade",
        race="Halfling",
        character_class="Rogue",
        strength=10,
        dexterity=18,
        constitution=12,
        intelligence=12,
        wisdom=13,
        charisma=14,
        proficiency_bonus=2,
    )


class TestSingleCharacterStorage:
    """Test storing a single character (solo mode)"""

    def test_store_single_character(self, thorin):
        """Test storing one character by name"""
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin

        assert "Thorin Stormshield" in session.base_character_stats
        assert session.base_character_stats["Thorin Stormshield"] == thorin

    def test_retrieve_character_stats(self, thorin):
        """Test retrieving character stats by name"""
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin

        char = session.base_character_stats["Thorin Stormshield"]
        assert char.strength == 16
        assert char.character_class == "Fighter"
        assert char.proficiency_bonus == 2

    def test_empty_dict_on_initialization(self):
        """Test that base_character_stats is empty dict on init"""
        session = GameSession()
        assert isinstance(session.base_character_stats, dict)
        assert len(session.base_character_stats) == 0

    def test_overwrite_character(self, thorin):
        """Test overwriting a character with updated stats"""
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin

        # Update and overwrite
        thorin.strength = 18  # Leveled up!
        session.base_character_stats[thorin.name] = thorin

        assert session.base_character_stats["Thorin Stormshield"].strength == 18


class TestMultipleCharacterStorage:
    """Test storing multiple characters (party mode)"""

    def test_store_multiple_characters(self, thorin, elara, murren):
        """Test storing three characters in party"""
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin
        session.base_character_stats[elara.name] = elara
        session.base_character_stats[murren.name] = murren

        assert len(session.base_character_stats) == 3
        assert "Thorin Stormshield" in session.base_character_stats
        assert "Elara Moonwhisper" in session.base_character_stats
        assert "Murren Nightshade" in session.base_character_stats

    def test_each_character_has_own_stats(self, thorin, elara):
        """Test that each character maintains separate stats"""
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin
        session.base_character_stats[elara.name] = elara

        # Verify stats are not mixed
        assert session.base_character_stats["Thorin Stormshield"].strength == 16
        assert session.base_character_stats["Elara Moonwhisper"].strength == 8
        assert session.base_character_stats["Thorin Stormshield"].character_class == "Fighter"
        assert session.base_character_stats["Elara Moonwhisper"].character_class == "Wizard"

    def test_retrieve_all_characters(self, thorin, elara, murren):
        """Test retrieving all characters from dict"""
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin
        session.base_character_stats[elara.name] = elara
        session.base_character_stats[murren.name] = murren

        all_chars = list(session.base_character_stats.values())
        assert len(all_chars) == 3
        assert thorin in all_chars
        assert elara in all_chars
        assert murren in all_chars

    def test_remove_character_from_party(self, thorin, elara):
        """Test removing a character from the dict"""
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin
        session.base_character_stats[elara.name] = elara

        # Remove Thorin
        del session.base_character_stats["Thorin Stormshield"]

        assert len(session.base_character_stats) == 1
        assert "Thorin Stormshield" not in session.base_character_stats
        assert "Elara Moonwhisper" in session.base_character_stats


class TestCharacterLookup:
    """Test looking up characters by name"""

    def test_get_existing_character(self, thorin):
        """Test get() for existing character"""
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin

        char = session.base_character_stats.get("Thorin Stormshield")
        assert char is not None
        assert char.name == "Thorin Stormshield"

    def test_get_nonexistent_character_returns_none(self):
        """Test get() for non-existent character returns None"""
        session = GameSession()

        char = session.base_character_stats.get("Nobody")
        assert char is None

    def test_get_with_default(self):
        """Test get() with default value"""
        session = GameSession()

        default_char = Character(name="Default", character_class="Commoner")
        char = session.base_character_stats.get("Nobody", default_char)
        assert char == default_char

    def test_check_character_exists_with_in(self, thorin):
        """Test using 'in' to check if character exists"""
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin

        assert "Thorin Stormshield" in session.base_character_stats
        assert "Nobody" not in session.base_character_stats


class TestAbilityModifiers:
    """Test retrieving ability modifiers from stored characters"""

    def test_get_ability_modifiers(self, thorin):
        """Test retrieving calculated ability modifiers"""
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin

        char = session.base_character_stats["Thorin Stormshield"]
        assert char.get_ability_modifier(char.strength) == 3  # STR 16 → +3
        assert char.get_ability_modifier(char.dexterity) == 1  # DEX 12 → +1
        assert char.get_ability_modifier(char.charisma) == -1  # CHA 8 → -1

    def test_get_all_modifiers(self, elara):
        """Test get_modifiers() method"""
        session = GameSession()
        session.base_character_stats[elara.name] = elara

        char = session.base_character_stats["Elara Moonwhisper"]
        mods = char.get_modifiers()

        assert mods['strength'] == -1  # STR 8
        assert mods['dexterity'] == 3  # DEX 16
        assert mods['intelligence'] == 4  # INT 18


class TestEquipmentAccess:
    """Test accessing equipment from stored characters"""

    def test_access_equipment_list(self, thorin):
        """Test accessing equipment from stored character"""
        thorin.equipment = ["Longsword", "Shield", "Plate Armor"]
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin

        char = session.base_character_stats["Thorin Stormshield"]
        assert "Longsword" in char.equipment
        assert "Shield" in char.equipment
        assert len(char.equipment) == 3

    def test_modify_equipment(self, thorin):
        """Test modifying equipment list"""
        thorin.equipment = ["Dagger"]
        session = GameSession()
        session.base_character_stats[thorin.name] = thorin

        char = session.base_character_stats["Thorin Stormshield"]
        char.equipment.append("Longsword")

        assert "Longsword" in char.equipment
        assert len(char.equipment) == 2


class TestCompatibilityWithCharacterState:
    """Test that base_character_stats works alongside character_state"""

    def test_separate_from_character_state(self, thorin):
        """Test that base_character_stats and character_state are separate"""
        from dnd_rag_system.systems.game_state import CharacterState

        session = GameSession()
        session.base_character_stats[thorin.name] = thorin
        session.character_state = CharacterState(
            character_name="Thorin Stormshield",
            max_hp=28,
            current_hp=15,  # Damaged
        )

        # Base stats unchanged
        assert session.base_character_stats["Thorin Stormshield"].strength == 16

        # Dynamic state has HP
        assert session.character_state.current_hp == 15
        assert session.character_state.max_hp == 28

    def test_lookup_by_character_state_name(self, thorin):
        """Test using character_state.character_name to lookup base stats"""
        from dnd_rag_system.systems.game_state import CharacterState

        session = GameSession()
        session.base_character_stats[thorin.name] = thorin
        session.character_state = CharacterState(
            character_name="Thorin Stormshield",
            max_hp=28,
            current_hp=28,
        )

        # Lookup using character_state's name
        char_name = session.character_state.character_name
        base_stats = session.base_character_stats.get(char_name)

        assert base_stats is not None
        assert base_stats.strength == 16


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_duplicate_name_overwrites(self, thorin):
        """Test that adding character with same name overwrites"""
        session = GameSession()
        session.base_character_stats["Thorin Stormshield"] = thorin

        # Create another character with same name but different stats
        fake_thorin = Character(
            name="Thorin Stormshield",
            character_class="Wizard",  # Different!
            strength=8,  # Different!
        )
        session.base_character_stats["Thorin Stormshield"] = fake_thorin

        # Should be overwritten
        assert session.base_character_stats["Thorin Stormshield"].character_class == "Wizard"
        assert session.base_character_stats["Thorin Stormshield"].strength == 8

    def test_empty_string_name(self):
        """Test handling character with empty name"""
        char = Character(name="", character_class="Fighter")
        session = GameSession()
        session.base_character_stats[""] = char

        # Should work, even if it's weird
        assert "" in session.base_character_stats

    def test_special_characters_in_name(self):
        """Test names with special characters"""
        char = Character(name="Grök the Destroyer", character_class="Barbarian")
        session = GameSession()
        session.base_character_stats[char.name] = char

        assert "Grök the Destroyer" in session.base_character_stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
