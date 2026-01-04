"""
Tests for Player Attack Damage Calculation System (Fix #14)

Tests the _calculate_player_attack method that pre-calculates
attack rolls and damage for player attacks against NPCs.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import random

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.systems.character_creator import Character
from dnd_rag_system.systems.game_state import GameSession, CharacterState
from dnd_rag_system.systems.monster_stat_system import MonsterInstance
from dnd_rag_system.core.chroma_manager import ChromaDBManager


@pytest.fixture
def thorin_character():
    """Thorin Stormshield - Fighter with STR 16, Longsword"""
    return Character(
        name="Thorin Stormshield",
        race="Dwarf",
        character_class="Fighter",
        level=3,
        strength=16,  # +3 modifier
        dexterity=12,
        constitution=16,
        intelligence=10,
        wisdom=13,
        charisma=8,
        hit_points=28,
        armor_class=18,
        proficiency_bonus=2,
        background="Soldier",
        alignment="Lawful Good",
        equipment=["Longsword", "Shield", "Plate Armor", "Backpack"],
        spells=[],
    )


@pytest.fixture
def elara_character():
    """Elara Moonwhisper - Wizard with STR 8, Dagger"""
    return Character(
        name="Elara Moonwhisper",
        race="Elf",
        character_class="Wizard",
        level=3,
        strength=8,  # -1 modifier
        dexterity=16,
        constitution=12,
        intelligence=18,
        wisdom=14,
        charisma=10,
        hit_points=18,
        armor_class=12,
        proficiency_bonus=2,
        background="Sage",
        alignment="Neutral Good",
        equipment=["Dagger", "Spellbook", "Staff"],
        spells=["Magic Missile", "Fireball"],
    )


@pytest.fixture
def barbarian_character():
    """Grok the Destroyer - Barbarian with Greataxe, no weapon in equipment"""
    return Character(
        name="Grok",
        race="Half-Orc",
        character_class="Barbarian",
        level=5,
        strength=18,  # +4 modifier
        dexterity=14,
        constitution=16,
        intelligence=8,
        wisdom=10,
        charisma=8,
        hit_points=55,
        armor_class=14,
        proficiency_bonus=3,
        background="Outlander",
        alignment="Chaotic Neutral",
        equipment=["Greataxe", "Javelin", "Explorer's Pack"],
        spells=[],
    )


@pytest.fixture
def unarmed_character():
    """Character with no weapons - should default to unarmed"""
    return Character(
        name="Monk Steve",
        race="Human",
        character_class="Monk",
        level=2,
        strength=12,  # +1 modifier
        dexterity=16,
        constitution=14,
        intelligence=10,
        wisdom=15,
        charisma=8,
        hit_points=20,
        armor_class=15,
        proficiency_bonus=2,
        background="Hermit",
        alignment="Lawful Neutral",
        equipment=["Rope", "Backpack", "Waterskin"],  # No weapons
        spells=[],
    )


@pytest.fixture
def goblin_npc():
    """Standard goblin - AC 15, HP 15"""
    return MonsterInstance(
        name="Goblin",
        cr=0.25,
        size="Small",
        type="humanoid",
        ac=15,
        max_hp=15,
        current_hp=15,
        speed=30,
        str=8,
        dex=14,
        con=10,
        int=10,
        wis=8,
        cha=8,
        attacks=[{"name": "Scimitar", "to_hit": 4, "damage": "1d6+2", "damage_type": "slashing"}],
        traits=[],
        description="A small goblin",
    )


@pytest.fixture
def armored_knight_npc():
    """Heavily armored knight - AC 20, HP 50"""
    return MonsterInstance(
        name="Knight",
        cr=3,
        size="Medium",
        type="humanoid",
        ac=20,
        max_hp=50,
        current_hp=50,
        speed=30,
        str=16,
        dex=11,
        con=14,
        int=11,
        wis=11,
        cha=15,
        attacks=[{"name": "Greatsword", "to_hit": 5, "damage": "2d6+3", "damage_type": "slashing"}],
        traits=["Brave"],
        description="An armored knight",
    )


@pytest.fixture
def mock_db_manager():
    """Mock ChromaDB manager to avoid initialization"""
    mock = MagicMock(spec=ChromaDBManager)
    return mock


@pytest.fixture
def gm(mock_db_manager):
    """GameMaster instance with mocked DB"""
    gm = GameMaster(mock_db_manager)
    return gm


class TestBasicAttackCalculation:
    """Test basic attack roll and damage calculation"""

    def test_attack_hit_against_low_ac(self, gm, thorin_character, goblin_npc):
        """Test successful attack when roll + mods >= AC"""
        # Setup
        char_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        # Force a good roll
        with patch('random.randint', return_value=14):
            result = gm._calculate_player_attack("Goblin", char_state)

        # Verify: 14 + 3 (STR) + 2 (prof) = 19 vs AC 15 → HIT
        assert "HITS" in result
        assert "Thorin Stormshield" in result
        assert "Goblin" in result
        assert "longsword" in result.lower()
        assert "19 vs AC 15" in result
        assert "slashing damage" in result

    def test_attack_miss_against_high_ac(self, gm, thorin_character, armored_knight_npc):
        """Test missed attack when roll + mods < AC"""
        # Setup
        char_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Knight"] = armored_knight_npc

        # Force a low roll
        with patch('random.randint', return_value=5):
            result = gm._calculate_player_attack("Knight", char_state)

        # Verify: 5 + 3 (STR) + 2 (prof) = 10 vs AC 20 → MISS
        assert "MISSES" in result
        assert "10 vs AC 20" in result
        assert "NO DAMAGE" in result

    def test_attack_exactly_meets_ac(self, gm, thorin_character, goblin_npc):
        """Test that roll + mods == AC is a hit"""
        # Setup
        char_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        # Force roll that exactly meets AC: need 10 to hit (10 + 5 = 15 vs AC 15)
        with patch('random.randint', return_value=10):
            result = gm._calculate_player_attack("Goblin", char_state)

        # Verify: Exactly meeting AC is a hit
        assert "HITS" in result
        assert "15 vs AC 15" in result


class TestCriticalHitsAndMisses:
    """Test critical hit and critical miss mechanics"""

    def test_critical_hit_natural_20(self, gm, thorin_character, goblin_npc):
        """Test natural 20 always hits and doubles damage"""
        # Setup
        char_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        # Force natural 20
        with patch('random.randint', return_value=20):
            result = gm._calculate_player_attack("Goblin", char_state)

        # Verify
        assert "CRITICAL HIT" in result
        assert "natural 20" in result.lower() or "20 (critical" in result.lower()
        assert "DOUBLE DAMAGE" in result or "critical" in result.lower()

    def test_critical_miss_natural_1(self, gm, thorin_character, goblin_npc):
        """Test natural 1 always misses even if mods would hit"""
        # Setup
        char_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.character_state = char_state
        # Give goblin AC 5 - even with mods (1 + 5 = 6), nat 1 should miss
        goblin_npc.ac = 5
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        # Force natural 1
        with patch('random.randint', return_value=1):
            result = gm._calculate_player_attack("Goblin", char_state)

        # Verify
        assert "CRITICALLY MISSES" in result or "CRITICAL MISS" in result
        assert "natural 1" in result.lower()
        assert "NO DAMAGE" in result


class TestWeaponDetection:
    """Test weapon detection from equipment list"""

    def test_longsword_detection(self, gm, thorin_character, goblin_npc):
        """Test longsword is detected and uses 1d8 damage"""
        # Setup
        char_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        with patch('random.randint', return_value=15):
            result = gm._calculate_player_attack("Goblin", char_state)

        assert "longsword" in result.lower()
        assert "slashing" in result.lower()

    def test_greataxe_detection(self, gm, barbarian_character, goblin_npc):
        """Test greataxe is detected (1d12 damage)"""
        # Setup
        char_state = CharacterState(character_name=barbarian_character.name, max_hp=55, current_hp=55)
        gm.session.base_character_stats[barbarian_character.name] = barbarian_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        with patch('random.randint', return_value=15):
            result = gm._calculate_player_attack("Goblin", char_state)

        assert "greataxe" in result.lower()
        assert "slashing" in result.lower()

    def test_dagger_detection(self, gm, elara_character, goblin_npc):
        """Test dagger is detected (1d4 damage)"""
        # Setup
        char_state = CharacterState(character_name=elara_character.name, max_hp=18, current_hp=18)
        gm.session.base_character_stats[elara_character.name] = elara_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        with patch('random.randint', return_value=15):
            result = gm._calculate_player_attack("Goblin", char_state)

        assert "dagger" in result.lower()
        assert "piercing" in result.lower()

    def test_unarmed_fallback(self, gm, unarmed_character, goblin_npc):
        """Test character with no weapons defaults to unarmed (1d4 bludgeoning)"""
        # Setup
        char_state = CharacterState(character_name=unarmed_character.name, max_hp=20, current_hp=20)
        gm.session.base_character_stats[unarmed_character.name] = unarmed_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        with patch('random.randint', return_value=15):
            result = gm._calculate_player_attack("Goblin", char_state)

        assert "unarmed" in result.lower()
        assert "bludgeoning" in result.lower()


class TestDamageCalculation:
    """Test damage dice rolling and modifiers"""

    def test_damage_includes_strength_modifier(self, gm, thorin_character, goblin_npc):
        """Test damage includes STR modifier (+3 for Thorin)"""
        # Setup
        char_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        # Force hit with specific damage roll (1d8 = 5, +3 STR = 8 total)
        with patch('random.randint', side_effect=[15, 5]):  # [attack roll, damage roll]
            result = gm._calculate_player_attack("Goblin", char_state)

        # Should have 8 damage (5 from d8, +3 from STR)
        assert "damage" in result.lower()
        # Damage should be in 4-11 range for longsword (1d8+3)

    def test_weak_character_lower_damage(self, gm, elara_character, goblin_npc):
        """Test character with low STR (8, -1 mod) does less damage"""
        # Setup
        char_state = CharacterState(character_name=elara_character.name, max_hp=18, current_hp=18)
        gm.session.base_character_stats[elara_character.name] = elara_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        # Elara: STR 8 (-1 mod), Dagger (1d4), so damage = 1d4 - 1 (min 0)
        with patch('random.randint', side_effect=[15, 3]):  # Hit, damage die = 3
            result = gm._calculate_player_attack("Goblin", char_state)

        # Should hit but with low damage (3 - 1 = 2)
        assert "HITS" in result


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_no_base_character_stats(self, gm, goblin_npc):
        """Test graceful failure when character not in base_character_stats"""
        # Setup - character_state exists but no base stats
        char_state = CharacterState(character_name="Unknown", max_hp=20, current_hp=20)
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        result = gm._calculate_player_attack("Goblin", char_state)

        # Should return empty string, not crash
        assert result == ""

    def test_no_character_state(self, gm, thorin_character, goblin_npc):
        """Test graceful failure when character_state is None"""
        # Setup - base stats exist but no character_state
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        result = gm._calculate_player_attack("Goblin", None)

        # Should return empty string
        assert result == ""

    def test_npc_not_in_combat_manager(self, gm, thorin_character):
        """Test default AC (12) when NPC not loaded in combat manager"""
        # Setup
        char_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.character_state = char_state
        # Don't add NPC to combat manager

        with patch('random.randint', return_value=15):
            result = gm._calculate_player_attack("UnknownOrc", char_state)

        # Should use default AC 12
        assert "vs AC 12" in result

    def test_empty_equipment_list(self, gm, goblin_npc):
        """Test character with empty equipment list defaults to unarmed"""
        char_with_no_equipment = Character(
            name="Bob",
            race="Human",
            character_class="Commoner",
            strength=10,
            proficiency_bonus=2,
            equipment=[],  # Empty
        )

        char_state = CharacterState(character_name="Bob", max_hp=10, current_hp=10)
        gm.session.base_character_stats["Bob"] = char_with_no_equipment
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        with patch('random.randint', return_value=15):
            result = gm._calculate_player_attack("Goblin", char_state)

        assert "unarmed" in result.lower()


class TestPartyMode:
    """Test attack calculation works with multiple characters (party mode)"""

    def test_multiple_characters_stored(self, gm, thorin_character, elara_character, goblin_npc):
        """Test both characters can be stored and retrieved"""
        # Setup party
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.base_character_stats[elara_character.name] = elara_character
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        # Test Thorin attacks
        thorin_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        with patch('random.randint', return_value=15):
            thorin_result = gm._calculate_player_attack("Goblin", thorin_state)

        assert "Thorin Stormshield" in thorin_result
        assert "longsword" in thorin_result.lower()

        # Test Elara attacks
        elara_state = CharacterState(character_name=elara_character.name, max_hp=18, current_hp=18)
        with patch('random.randint', return_value=15):
            elara_result = gm._calculate_player_attack("Goblin", elara_state)

        assert "Elara Moonwhisper" in elara_result
        assert "dagger" in elara_result.lower()

    def test_correct_character_stats_used(self, gm, thorin_character, elara_character, goblin_npc):
        """Test that each character uses their own stats, not mixed"""
        # Setup
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.base_character_stats[elara_character.name] = elara_character
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        # Thorin: STR 16 (+3), Prof +2 = +5 to hit
        thorin_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        with patch('random.randint', return_value=10):
            thorin_result = gm._calculate_player_attack("Goblin", thorin_state)
        # 10 + 5 = 15
        assert "15 vs AC" in thorin_result

        # Elara: STR 8 (-1), Prof +2 = +1 to hit
        elara_state = CharacterState(character_name=elara_character.name, max_hp=18, current_hp=18)
        with patch('random.randint', return_value=10):
            elara_result = gm._calculate_player_attack("Goblin", elara_state)
        # 10 + 1 = 11
        assert "11 vs AC" in elara_result


class TestInstructionFormat:
    """Test that instruction format is correct for GM"""

    def test_instruction_format_on_hit(self, gm, thorin_character, goblin_npc):
        """Test instruction format contains all required elements on hit"""
        char_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Goblin"] = goblin_npc

        with patch('random.randint', return_value=15):
            result = gm._calculate_player_attack("Goblin", char_state)

        # Check all required elements
        assert "COMBAT INSTRUCTION:" in result
        assert "Thorin Stormshield" in result
        assert "Goblin" in result
        assert "HITS" in result
        assert "vs AC" in result
        assert "damage" in result.lower()
        assert "Narrate" in result

    def test_instruction_format_on_miss(self, gm, thorin_character, armored_knight_npc):
        """Test instruction format on miss"""
        char_state = CharacterState(character_name=thorin_character.name, max_hp=28, current_hp=28)
        gm.session.base_character_stats[thorin_character.name] = thorin_character
        gm.session.character_state = char_state
        gm.combat_manager.npc_monsters["Knight"] = armored_knight_npc

        with patch('random.randint', return_value=5):
            result = gm._calculate_player_attack("Knight", char_state)

        assert "COMBAT INSTRUCTION:" in result
        assert "MISSES" in result
        assert "NO DAMAGE" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
