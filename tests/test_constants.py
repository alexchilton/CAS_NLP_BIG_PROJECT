"""
Tests for constants module

Verifies that:
1. Constants are imported correctly
2. Constants match expected values
3. Helper functions work correctly
4. No duplicate command strings
"""

import pytest
from dnd_rag_system.constants import (
    Commands, ItemEffects, EquipmentSlots, LocationTypes,
    SpellKeywords, DamageTypes, CharacterClasses, CharacterRaces,
    ActionKeywords, Conditions, is_command, normalize_slot
)


class TestCommands:
    """Test command constants."""
    
    def test_combat_commands(self):
        """Test combat command strings."""
        assert Commands.START_COMBAT == '/start_combat'
        assert Commands.END_COMBAT == '/end_combat'
        assert Commands.NEXT_TURN == '/next_turn'
        assert Commands.INITIATIVE == '/initiative'
    
    def test_character_commands(self):
        """Test character command strings."""
        assert Commands.STATS == '/stats'
        assert Commands.CHARACTER == '/character'
        assert Commands.CAST == '/cast'
    
    def test_exploration_commands(self):
        """Test exploration command strings."""
        assert Commands.MAP == '/map'
        assert Commands.LOCATIONS == '/locations'
        assert Commands.TRAVEL == '/travel'
    
    def test_all_commands_returns_list(self):
        """Test that all_commands() returns a complete list."""
        commands = Commands.all_commands()
        assert isinstance(commands, list)
        assert len(commands) > 0
        assert Commands.START_COMBAT in commands
        assert Commands.MAP in commands
    
    def test_combat_commands_list(self):
        """Test combat_commands() returns combat-specific commands."""
        combat_cmds = Commands.combat_commands()
        assert Commands.START_COMBAT in combat_cmds
        assert Commands.END_COMBAT in combat_cmds
        assert Commands.MAP not in combat_cmds
    
    def test_unconscious_allowed_commands(self):
        """Test unconscious_allowed_commands() returns restricted list."""
        allowed = Commands.unconscious_allowed_commands()
        assert Commands.HELP in allowed
        assert Commands.STATS in allowed
        assert Commands.DEATH_SAVE in allowed
        assert Commands.CAST not in allowed
        assert Commands.START_COMBAT not in allowed
    
    def test_no_duplicate_commands(self):
        """Test that there are no duplicate command strings."""
        commands = Commands.all_commands()
        assert len(commands) == len(set(commands)), "Duplicate commands found"


class TestActionKeywords:
    """Test action keyword lists."""
    
    def test_attack_keywords(self):
        """Test attack keywords include common actions."""
        keywords = ActionKeywords.ATTACK_KEYWORDS
        assert 'attack' in keywords
        assert 'strike' in keywords
        assert 'shoot' in keywords
    
    def test_spell_keywords(self):
        """Test spell keywords include casting terms."""
        keywords = ActionKeywords.SPELL_KEYWORDS
        assert 'cast' in keywords
        assert 'spell' in keywords
    
    def test_steal_keywords(self):
        """Test steal keywords."""
        keywords = ActionKeywords.STEAL_KEYWORDS
        assert 'steal' in keywords
        assert 'swipe' in keywords
        assert 'pocket' in keywords
    
    def test_conversation_keywords(self):
        """Test conversation keywords."""
        keywords = ActionKeywords.CONVERSATION_KEYWORDS
        assert 'talk' in keywords
        assert 'ask' in keywords


class TestItemEffects:
    """Test item effect constants."""
    
    def test_ac_bonus(self):
        """Test AC bonus constant."""
        assert ItemEffects.AC_BONUS == 'ac_bonus'
    
    def test_damage_types(self):
        """Test elemental damage constants."""
        assert ItemEffects.FIRE_DAMAGE == 'fire_damage'
        assert ItemEffects.COLD_DAMAGE == 'cold_damage'
    
    def test_resistances(self):
        """Test resistance constants."""
        assert ItemEffects.FIRE_RESISTANCE == 'fire_resistance'
        assert ItemEffects.RESISTANCE == 'resistance'


class TestEquipmentSlots:
    """Test equipment slot constants."""
    
    def test_main_slots(self):
        """Test main equipment slots."""
        assert EquipmentSlots.ARMOR == 'armor'
        assert EquipmentSlots.WEAPON == 'weapon'
        assert EquipmentSlots.SHIELD == 'shield'
    
    def test_accessory_slots(self):
        """Test accessory slots."""
        assert EquipmentSlots.HELM == 'helm'
        assert EquipmentSlots.BOOTS == 'boots'
        assert EquipmentSlots.CLOAK == 'cloak'
    
    def test_slot_aliases(self):
        """Test slot alias mappings."""
        assert EquipmentSlots.SLOT_ALIASES['helmet'] == 'helm'
        assert EquipmentSlots.SLOT_ALIASES['necklace'] == 'amulet'


class TestLocationTypes:
    """Test location type constants."""
    
    def test_settlement_types(self):
        """Test settlement locations."""
        assert LocationTypes.TAVERN == 'tavern'
        assert LocationTypes.SHOP == 'shop'
        assert LocationTypes.INN == 'inn'
    
    def test_dangerous_locations(self):
        """Test dangerous location types."""
        assert LocationTypes.DUNGEON == 'dungeon'
        assert LocationTypes.CAVE == 'cave'
        assert LocationTypes.RUINS == 'ruins'


class TestCharacterConstants:
    """Test character class and race constants."""
    
    def test_character_classes(self):
        """Test D&D 5e class constants."""
        assert CharacterClasses.FIGHTER == 'Fighter'
        assert CharacterClasses.WIZARD == 'Wizard'
        assert CharacterClasses.ROGUE == 'Rogue'
    
    def test_character_races(self):
        """Test D&D 5e race constants."""
        assert CharacterRaces.DWARF == 'Dwarf'
        assert CharacterRaces.ELF == 'Elf'
        assert CharacterRaces.HUMAN == 'Human'


class TestDamageTypes:
    """Test damage type constants."""
    
    def test_physical_damage(self):
        """Test physical damage types."""
        assert DamageTypes.BLUDGEONING == 'bludgeoning'
        assert DamageTypes.PIERCING == 'piercing'
        assert DamageTypes.SLASHING == 'slashing'
    
    def test_elemental_damage(self):
        """Test elemental damage types."""
        assert DamageTypes.FIRE == 'fire'
        assert DamageTypes.COLD == 'cold'
        assert DamageTypes.LIGHTNING == 'lightning'


class TestConditions:
    """Test condition constants."""
    
    def test_common_conditions(self):
        """Test common D&D conditions."""
        assert Conditions.UNCONSCIOUS == 'unconscious'
        assert Conditions.POISONED == 'poisoned'
        assert Conditions.PRONE == 'prone'


class TestHelperFunctions:
    """Test helper utility functions."""
    
    def test_is_command_valid(self):
        """Test is_command() with valid commands."""
        assert is_command('/help')
        assert is_command('/start_combat')
        assert is_command('/map')
    
    def test_is_command_invalid(self):
        """Test is_command() with invalid input."""
        assert not is_command('attack the goblin')
        assert not is_command('/notacommand')
        assert not is_command('')
        assert not is_command(None)
    
    def test_is_command_case_insensitive(self):
        """Test is_command() is case-insensitive."""
        assert is_command('/HELP')
        assert is_command('/HeLp')
    
    def test_normalize_slot_canonical(self):
        """Test normalize_slot() with canonical slot names."""
        assert normalize_slot('helm') == 'helm'
        assert normalize_slot('boots') == 'boots'
    
    def test_normalize_slot_alias(self):
        """Test normalize_slot() with alias names."""
        assert normalize_slot('helmet') == 'helm'
        assert normalize_slot('necklace') == 'amulet'
        assert normalize_slot('girdle') == 'belt'
    
    def test_normalize_slot_case_insensitive(self):
        """Test normalize_slot() is case-insensitive."""
        assert normalize_slot('HELMET') == 'helm'
        assert normalize_slot('Necklace') == 'amulet'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
