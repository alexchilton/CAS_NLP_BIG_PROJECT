"""
Comprehensive test suite for character creation with all classes and races.

Tests that each class/race combination creates valid characters at various levels,
with correct HP, spell slots, proficiencies, and racial bonuses.
"""

import pytest
from dnd_rag_system.systems.character_creator import Character
from dnd_rag_system.systems.rag_character_enhancer import enhance_character_with_rag
from dnd_rag_system.constants import CharacterClasses, CharacterRaces


# All D&D 5e classes
ALL_CLASSES = [
    CharacterClasses.BARBARIAN,
    CharacterClasses.BARD,
    CharacterClasses.CLERIC,
    CharacterClasses.DRUID,
    CharacterClasses.FIGHTER,
    CharacterClasses.MONK,
    CharacterClasses.PALADIN,
    CharacterClasses.RANGER,
    CharacterClasses.ROGUE,
    CharacterClasses.SORCERER,
    CharacterClasses.WARLOCK,
    CharacterClasses.WIZARD
]

# All D&D 5e races
ALL_RACES = [
    CharacterRaces.DWARF,
    CharacterRaces.ELF,
    CharacterRaces.HALFLING,
    CharacterRaces.HUMAN,
    CharacterRaces.DRAGONBORN,
    CharacterRaces.GNOME,
    CharacterRaces.HALF_ELF,
    CharacterRaces.HALF_ORC,
    CharacterRaces.TIEFLING
]

# Expected hit dice for each class
EXPECTED_HIT_DICE = {
    CharacterClasses.BARBARIAN: 12,
    CharacterClasses.FIGHTER: 10,
    CharacterClasses.PALADIN: 10,
    CharacterClasses.RANGER: 10,
    CharacterClasses.BARD: 8,
    CharacterClasses.CLERIC: 8,
    CharacterClasses.DRUID: 8,
    CharacterClasses.MONK: 8,
    CharacterClasses.ROGUE: 8,
    CharacterClasses.WARLOCK: 8,
    CharacterClasses.SORCERER: 6,
    CharacterClasses.WIZARD: 6
}

# Spellcasting classes
FULL_CASTERS = [
    CharacterClasses.BARD,
    CharacterClasses.CLERIC,
    CharacterClasses.DRUID,
    CharacterClasses.SORCERER,
    CharacterClasses.WIZARD
]

HALF_CASTERS = [
    CharacterClasses.PALADIN,
    CharacterClasses.RANGER
]

# Expected racial bonuses (primary stat)
RACIAL_BONUSES = {
    CharacterRaces.DWARF: 'constitution',
    CharacterRaces.ELF: 'dexterity',
    CharacterRaces.HALFLING: 'dexterity',
    CharacterRaces.HUMAN: 'strength',  # Gets +1 to all
    CharacterRaces.DRAGONBORN: 'strength',
    CharacterRaces.GNOME: 'intelligence',
    CharacterRaces.HALF_ELF: 'charisma',
    CharacterRaces.HALF_ORC: 'strength',
    CharacterRaces.TIEFLING: 'charisma'
}


class TestAllClassesCreation:
    """Test character creation for all classes at various levels."""
    
    @pytest.mark.parametrize("character_class", ALL_CLASSES)
    def test_level_1_creation(self, character_class):
        """Test that all classes can be created at level 1."""
        char = Character(
            name=f"Test{character_class}",
            race=CharacterRaces.HUMAN,
            character_class=character_class,
            level=1,
            strength=10,
            dexterity=10,
            constitution=14,  # +2 modifier
            intelligence=10,
            wisdom=10,
            charisma=10
        )
        
        enhance_character_with_rag(char)
        
        # Should have HP (at least 1)
        assert char.hit_points > 0, f"{character_class} should have HP"
        
        # HP should be reasonable for level 1
        expected_min = EXPECTED_HIT_DICE[character_class] + 2  # +2 CON mod
        assert char.hit_points >= expected_min, \
            f"{character_class} should have at least {expected_min} HP (got {char.hit_points})"
        
        # Should have class features
        assert len(char.class_features) > 0, f"{character_class} should have class features"
        assert '(SRD-enhanced)' in char.class_features, "Should be SRD-enhanced"
        
        # Casters should have spells
        if character_class in FULL_CASTERS:
            assert len(char.spells) > 0, f"{character_class} should have starting spells"
    
    @pytest.mark.parametrize("character_class", ALL_CLASSES)
    def test_level_5_creation(self, character_class):
        """Test all classes at level 5 (key milestone with extra attack/3rd level spells)."""
        char = Character(
            name=f"Test{character_class}5",
            race=CharacterRaces.HUMAN,
            character_class=character_class,
            level=5,
            strength=10,
            dexterity=10,
            constitution=14,
            intelligence=10,
            wisdom=10,
            charisma=10
        )
        
        enhance_character_with_rag(char)
        
        # HP should scale with level
        hit_die = EXPECTED_HIT_DICE[character_class]
        avg_per_level = (hit_die // 2) + 1
        expected_min_hp = hit_die + 2 + (4 * (avg_per_level + 2))  # Level 1 + 4 more levels
        
        assert char.hit_points >= expected_min_hp, \
            f"{character_class} level 5 should have at least {expected_min_hp} HP (got {char.hit_points})"
        
        # Should have more HP than level 1
        char_level_1 = Character(
            name="Temp",
            race=CharacterRaces.HUMAN,
            character_class=character_class,
            level=1,
            constitution=14
        )
        enhance_character_with_rag(char_level_1)
        assert char.hit_points > char_level_1.hit_points, \
            f"Level 5 should have more HP than level 1"
    
    @pytest.mark.parametrize("character_class", ALL_CLASSES)
    def test_level_10_creation(self, character_class):
        """Test all classes at level 10 (mid-tier play)."""
        char = Character(
            name=f"Test{character_class}10",
            race=CharacterRaces.HUMAN,
            character_class=character_class,
            level=10,
            strength=12,
            dexterity=12,
            constitution=16,  # +3 modifier
            intelligence=12,
            wisdom=12,
            charisma=12
        )
        
        enhance_character_with_rag(char)
        
        # HP should be substantial at level 10
        hit_die = EXPECTED_HIT_DICE[character_class]
        avg_per_level = (hit_die // 2) + 1
        # Level 1: hit_die + 3, then 9 more levels of (avg + 3)
        expected_min_hp = hit_die + 3 + (9 * (avg_per_level + 3))
        
        assert char.hit_points >= expected_min_hp, \
            f"{character_class} level 10 should have at least {expected_min_hp} HP (got {char.hit_points})"
        
        # Barbarian should have highest HP
        if character_class == CharacterClasses.BARBARIAN:
            assert char.hit_points >= 100, "Barbarian should have 100+ HP at level 10"
        
        # Wizard should have lower HP but still reasonable
        if character_class == CharacterClasses.WIZARD:
            assert char.hit_points >= 40, "Wizard should have 40+ HP at level 10"
            assert char.hit_points < 80, "Wizard shouldn't have more HP than fighters"
        
        # Spellcasters should have high-level spell slots
        if character_class in FULL_CASTERS:
            assert len(char.spells) > 0, f"{character_class} should have spells"
            # Should mention 5th level slots in class features
            spell_slot_feature = [f for f in char.class_features if 'Spell Slots' in f]
            assert len(spell_slot_feature) > 0, "Should have spell slot info"
            assert '5st: 2' in spell_slot_feature[0], "Level 10 full caster should have 5th level slots"


class TestAllRacesCreation:
    """Test character creation for all races."""
    
    @pytest.mark.parametrize("race", ALL_RACES)
    def test_race_creation_wizard(self, race):
        """Test each race creates a valid Wizard character."""
        char = Character(
            name=f"Test{race}Wizard",
            race=race,
            character_class=CharacterClasses.WIZARD,
            level=3,
            strength=8,
            dexterity=12,
            constitution=12,
            intelligence=16,
            wisdom=10,
            charisma=10
        )
        
        # Apply racial bonuses (manual for now - normally done in GUI)
        from dnd_rag_system.systems.racial_bonuses import load_racial_traits
        racial_traits = load_racial_traits(None, race)
        
        base_stats = {
            'strength': 8,
            'dexterity': 12,
            'constitution': 12,
            'intelligence': 16,
            'wisdom': 10,
            'charisma': 10
        }
        
        if racial_traits:
            for ability, bonus in racial_traits.ability_increases.items():
                current = getattr(char, ability)
                setattr(char, ability, current + bonus)
        
        enhance_character_with_rag(char)
        
        # Should have HP
        assert char.hit_points > 0, f"{race} Wizard should have HP"
        
        # Should have enhanced stats from racial bonus
        if racial_traits and racial_traits.ability_increases:
            primary_bonus_stat = RACIAL_BONUSES.get(race)
            if primary_bonus_stat and race != CharacterRaces.HUMAN:  # Human gets +1 to all
                final_stat = getattr(char, primary_bonus_stat)
                base_stat = base_stats[primary_bonus_stat]
                assert final_stat > base_stat, \
                    f"{race} should have bonus to {primary_bonus_stat}"
    
    @pytest.mark.parametrize("race", ALL_RACES)
    def test_race_creation_fighter(self, race):
        """Test each race creates a valid Fighter character."""
        char = Character(
            name=f"Test{race}Fighter",
            race=race,
            character_class=CharacterClasses.FIGHTER,
            level=5,
            strength=16,
            dexterity=14,
            constitution=14,
            intelligence=10,
            wisdom=10,
            charisma=10
        )
        
        enhance_character_with_rag(char)
        
        # Fighters should have good HP
        assert char.hit_points >= 40, f"{race} Fighter level 5 should have 40+ HP"
        
        # Should have class features
        assert 'Second Wind' in char.class_features or \
               any('Second Wind' in f for f in char.class_features), \
               "Fighter should have Second Wind"


class TestClassRaceCombinations:
    """Test specific class/race combinations that are common in D&D."""
    
    def test_elf_wizard_classic(self):
        """Elf Wizard - classic combination."""
        char = Character(
            name="Elara Classic Test",
            race=CharacterRaces.ELF,
            character_class=CharacterClasses.WIZARD,
            level=7,
            strength=8,
            dexterity=14,  # Base
            constitution=12,
            intelligence=17,
            wisdom=12,
            charisma=10
        )
        
        # Apply Elf racial bonus (+2 DEX)
        char.dexterity = 16  # 14 + 2
        
        enhance_character_with_rag(char)
        
        # Should have good HP for a wizard
        assert char.hit_points >= 30, "Level 7 wizard should have 30+ HP"
        
        # Should have 4th level spell slots
        spell_slot_info = [f for f in char.class_features if 'Spell Slots' in f]
        assert len(spell_slot_info) > 0
        assert '4st:' in spell_slot_info[0], "Level 7 wizard should have 4th level slots"
        
        # Should have spells
        assert len(char.spells) > 0, "Wizard should have spells"
    
    def test_half_orc_barbarian_classic(self):
        """Half-Orc Barbarian - classic bruiser."""
        char = Character(
            name="Grok Test",
            race=CharacterRaces.HALF_ORC,
            character_class=CharacterClasses.BARBARIAN,
            level=8,
            strength=18,  # Base 16 + 2 racial
            dexterity=12,
            constitution=16,  # Base 14 + 2 racial
            intelligence=8,
            wisdom=10,
            charisma=8
        )
        
        enhance_character_with_rag(char)
        
        # Barbarian should have LOTS of HP
        assert char.hit_points >= 80, "Level 8 Half-Orc Barbarian should have 80+ HP"
        
        # Should have Rage
        assert any('Rage' in f for f in char.class_features), "Barbarian should have Rage"
    
    def test_human_cleric_versatile(self):
        """Human Cleric - well-rounded support."""
        char = Character(
            name="Aelwyn Test",
            race=CharacterRaces.HUMAN,
            character_class=CharacterClasses.CLERIC,
            level=6,
            strength=11,  # 10 + 1 human
            dexterity=11,  # 10 + 1 human
            constitution=13,  # 12 + 1 human
            intelligence=11,  # 10 + 1 human
            wisdom=17,  # 16 + 1 human
            charisma=11   # 10 + 1 human
        )
        
        enhance_character_with_rag(char)
        
        # Should have decent HP
        assert char.hit_points >= 35, "Level 6 Cleric should have 35+ HP"
        
        # Should have spells (full caster)
        assert len(char.spells) > 0, "Cleric should have spells"
        
        # Should have 3rd level spell slots
        spell_slot_info = [f for f in char.class_features if 'Spell Slots' in f]
        assert '3st:' in spell_slot_info[0], "Level 6 cleric should have 3rd level slots"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_level_20_character(self):
        """Test max level character."""
        char = Character(
            name="Epic Wizard",
            race=CharacterRaces.HUMAN,
            character_class=CharacterClasses.WIZARD,
            level=20,
            strength=10,
            dexterity=14,
            constitution=16,
            intelligence=20,
            wisdom=12,
            charisma=10
        )
        
        enhance_character_with_rag(char)
        
        # Should have substantial HP even for a wizard
        assert char.hit_points >= 80, "Level 20 wizard should have 80+ HP"
        
        # Should have 9th level spell slots
        spell_slot_info = [f for f in char.class_features if 'Spell Slots' in f]
        assert '9st:' in spell_slot_info[0], "Level 20 wizard should have 9th level slots"
    
    def test_low_constitution_character(self):
        """Test character with very low CON survives."""
        char = Character(
            name="Frail Wizard",
            race=CharacterRaces.GNOME,
            character_class=CharacterClasses.WIZARD,
            level=5,
            strength=8,
            dexterity=14,
            constitution=6,  # -2 modifier!
            intelligence=18,
            wisdom=10,
            charisma=8
        )
        
        enhance_character_with_rag(char)
        
        # Should still have at least 1 HP per level (minimum)
        assert char.hit_points >= 5, "Even with CON 6, should have minimum 1 HP/level"
    
    def test_non_caster_has_no_spells(self):
        """Test that martial classes don't get spells."""
        char = Character(
            name="Fighter Test",
            race=CharacterRaces.HUMAN,
            character_class=CharacterClasses.FIGHTER,
            level=10
        )
        
        enhance_character_with_rag(char)
        
        # Fighter should NOT have spells (unless they're an Eldritch Knight, which we don't model)
        assert len(char.spells) == 0, "Fighter should not have spells"
        
        # Should not have spell slot info
        spell_slot_info = [f for f in char.class_features if 'Spell Slots' in f]
        assert len(spell_slot_info) == 0, "Fighter should not have spell slots"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
