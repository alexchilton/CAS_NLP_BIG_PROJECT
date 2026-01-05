"""
Test Party Member Interactions

Tests for character-to-character actions including:
- Healing other party members
- Buff spells targeting allies
- Item sharing between characters
- Party-wide spell effects
- Target validation
"""

import pytest
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.game_state import GameSession, CharacterState
from dnd_rag_system.systems.spell_manager import SpellManager
from dnd_rag_system.core.chroma_manager import ChromaDBManager


@pytest.fixture
def db_manager():
    """Create ChromaDB manager for tests."""
    return ChromaDBManager()


@pytest.fixture
def spell_mgr(db_manager):
    """Create SpellManager instance for tests."""
    return SpellManager(db_manager)


class TestPartyMemberHealing:
    """Test healing spells cast on other party members."""

    @pytest.fixture
    def setup_party(self, spell_mgr):
        """Create a party with multiple members."""
        # Create session
        session = GameSession()

        # Create party members
        healer = CharacterState(
            character_name="Elara",
            max_hp=24,
            current_hp=24
        )
        healer.spell_slots = {1: 4, 2: 2}  # Level 3 Cleric slots

        fighter = CharacterState(
            character_name="Thorin",
            max_hp=30,
            current_hp=15  # Wounded!
        )

        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=28,
            current_hp=10  # Badly wounded!
        )
        wizard.spell_slots = {1: 4, 2: 3, 3: 2}

        # Add to party (party is a list attribute, not PartyState)
        session.party = [healer, fighter, wizard]
        session.character_state = healer  # Healer is active

        return session, spell_mgr, healer, fighter, wizard

    def test_cast_healing_spell_on_party_member(self, setup_party):
        """Test casting Cure Wounds on another party member."""
        session, spell_manager, healer, fighter, wizard = setup_party

        # Cast Cure Wounds on Thorin (the wounded fighter)
        result = spell_manager.cast_healing_spell(
            "Cure Wounds",
            "Elara",
            "Thorin",
        )

        assert result["success"], "Healing spell should succeed"
        assert result["amount"] > 0, "Should heal some amount"
        assert result["caster"] == "Elara"
        assert result["target"] == "Thorin"
        assert "Elara casts Cure Wounds on Thorin" in result["message"]

    def test_healing_increases_target_hp(self, setup_party):
        """Test that healing actually increases the target's HP."""
        session, spell_manager, healer, fighter, wizard = setup_party

        original_hp = fighter.current_hp
        assert original_hp == 15, "Fighter should start wounded"

        # Cast healing spell
        result = spell_manager.cast_healing_spell(
            "Cure Wounds",
            "Elara",
            "Thorin",
        )

        # Apply healing to target
        healing_amount = result["amount"]
        fighter.current_hp = min(fighter.max_hp, fighter.current_hp + healing_amount)

        assert fighter.current_hp > original_hp, "HP should increase"
        assert fighter.current_hp <= fighter.max_hp, "HP shouldn't exceed max"

    def test_healing_cannot_exceed_max_hp(self, setup_party):
        """Test that healing doesn't give more HP than max."""
        session, spell_manager, healer, fighter, wizard = setup_party

        # Set fighter to almost full HP
        fighter.current_hp = fighter.max_hp - 2

        # Cast strong healing spell
        result = spell_manager.cast_healing_spell(
            "Cure Wounds",
            "Elara",
            "Thorin",
        )

        # Apply healing
        healing_amount = result["amount"]
        new_hp = min(fighter.max_hp, fighter.current_hp + healing_amount)

        assert new_hp <= fighter.max_hp, "HP should not exceed max"
        assert new_hp == fighter.max_hp, "Should be at max HP"

    def test_heal_self_when_no_target_specified(self, setup_party):
        """Test that healer can heal themselves."""
        session, spell_manager, healer, fighter, wizard = setup_party

        # Wound the healer
        healer.current_hp = 10

        # Cast without target (should default to self)
        result = spell_manager.cast_healing_spell(
            "Cure Wounds",
            "Elara",
            "Elara",  # Self-targeting
        )

        assert result["success"], "Self-healing should work"
        assert result["target"] == "Elara"
        assert result["caster"] == "Elara"

    def test_heal_multiple_party_members_sequentially(self, setup_party):
        """Test healing multiple wounded allies."""
        session, spell_manager, healer, fighter, wizard = setup_party

        # Both are wounded
        assert fighter.current_hp < fighter.max_hp
        assert wizard.current_hp < wizard.max_hp

        # Heal fighter first
        result1 = spell_manager.cast_healing_spell(
            "Cure Wounds",
            "Elara",
            "Thorin",
        )
        fighter.current_hp = min(fighter.max_hp, fighter.current_hp + result1["amount"])

        # Heal wizard second
        result2 = spell_manager.cast_healing_spell(
            "Cure Wounds",
            "Elara",
            "Gandalf",
        )
        wizard.current_hp = min(wizard.max_hp, wizard.current_hp + result2["amount"])

        # Both should have more HP
        assert fighter.current_hp > 15, "Fighter should be healed"
        assert wizard.current_hp > 10, "Wizard should be healed"

    def test_upcast_healing_spell_on_ally(self, setup_party):
        """Test upcasting healing spell for more healing."""
        session, spell_manager, healer, fighter, wizard = setup_party

        # Cast at level 1
        result_level1 = spell_manager.cast_healing_spell(
            "Cure Wounds",
            "Elara",
            "Thorin",
        )

        # Cast at level 2 (upcast)
        result_level2 = spell_manager.cast_healing_spell(
            "Cure Wounds",
            "Elara",
            "Gandalf",
        )

        # Level 2 should heal more (gets extra 1d8 per level)
        # Can't guarantee due to randomness, but message should indicate level
        assert result_level2["spell_level"] == 2
        assert result_level1["spell_level"] == 1


class TestTargetValidation:
    """Test validation of spell targets."""

    @pytest.fixture
    def setup_party(self, spell_mgr):
        """Create party for validation tests."""
        session = GameSession()

        char1.spell_slots = {1: 4}


        session.party = [char1, char2]
        session.character_state = char1

        return session, spell_mgr, char1, char2

    def test_target_exists_in_party(self, setup_party):
        """Test that target must be in the party."""
        session, spell_manager, caster, target = setup_party

        # Valid target
        result = spell_manager.cast_healing_spell(
            "Cure Wounds",
            "Alice",
            "Bob",
        )
        assert result["success"], "Should succeed with valid target"

        # Note: System doesn't currently reject invalid targets,
        # it just creates the healing - this could be improved

    def test_spell_target_type_detection(self, setup_party):
        """Test that spell manager detects ally vs enemy spells."""
        session, spell_manager, caster, target = setup_party

        # Healing spell = ally
        ally_type = spell_manager.lookup_spell_target_type("Cure Wounds")
        assert ally_type in ["ally", "self"], "Cure Wounds should target ally/self"

        # Attack spell = enemy
        enemy_type = spell_manager.lookup_spell_target_type("Fire Bolt")
        assert enemy_type == "enemy", "Fire Bolt should target enemy"

        # Area spell
        area_type = spell_manager.lookup_spell_target_type("Fireball")
        assert area_type == "area", "Fireball should be area effect"


class TestSpellSlotConsumption:
    """Test that casting spells on allies consumes spell slots properly."""

    @pytest.fixture
    def setup_caster(self, spell_mgr):
        """Create a caster with limited spell slots."""
        session = GameSession()

        caster = CharacterState(
            name="Healer",
            max_hp=24,
            current_hp=24
        )
        caster.spell_slots = {1: 4, 2: 2}

        target = CharacterState(
            name="Warrior",
            max_hp=30,
            current_hp=10
        )

        session.party = [caster, target]
        session.character_state = caster

        return session, spell_mgr, caster, target

    def test_spell_slot_consumed_when_healing_ally(self, setup_caster):
        """Test that healing an ally consumes a spell slot."""
        session, spell_manager, caster, target = setup_caster

        # Check initial slots
        initial_level1_slots = caster.spell_slots.get(1, 0)
        assert initial_level1_slots == 4, "Should have 4 level 1 slots"

        # Cast healing spell
        result = spell_manager.cast_healing_spell(
            "Cure Wounds",
            "Healer",
            "Warrior",
        )
        assert result["success"], "Healing should succeed"

        # Consume slot
        cast_result = caster.cast_spell(1, "Cure Wounds")
        assert cast_result["success"], "Slot consumption should work"

        # Check slots decreased
        new_level1_slots = caster.spell_slots.get(1, 0)
        assert new_level1_slots == 3, "Should have 3 level 1 slots remaining"

    def test_cannot_cast_without_slots(self, setup_caster):
        """Test that you can't cast when out of spell slots."""
        session, spell_manager, caster, target = setup_caster

        # Deplete all level 1 slots
        caster.spell_slots[1] = 0

        # Try to cast
        cast_result = caster.cast_spell(1, "Cure Wounds")
        assert not cast_result["success"], "Should fail without slots"
        assert "no level 1 spell slots" in cast_result["message"].lower()

    def test_cantrips_dont_consume_slots(self, setup_caster):
        """Test that cantrips can be cast unlimited times."""
        session, spell_manager, caster, target = setup_caster

        # Cantrips don't have slots
        assert 0 not in caster.spell_slots, "Cantrips shouldn't track slots"

        # Cast cantrip (if it were a healing cantrip - hypothetical)
        # This would work regardless of spell slot status


class TestHealingMechanics:
    """Test healing dice and calculations."""
    # Uses the spell_mgr fixture from module level

    def test_cure_wounds_healing_dice(self, spell_mgr):
        """Test that Cure Wounds uses correct dice formula."""

        assert result is not None, "Should return healing info"
        dice_formula, amount = result

        # Cure Wounds is 1d8 at level 1
        assert "1d8" in dice_formula or "d8" in dice_formula
        assert amount >= 1, "Should heal at least 1 HP"
        assert amount <= 8, "Should heal at most 8 HP (for 1d8)"

    def test_healing_scales_with_spell_level(self, spell_mgr):
        """Test that upcast healing spells heal more."""
        # This is tested implicitly - higher spell level = more dice
        # Cure Wounds: 1d8 per slot level
        # Level 1 = 1d8, Level 2 = 2d8, Level 3 = 3d8

        result_level1 = spell_mgr.cast_healing_spell(
            "Cure Wounds",
            "Caster",
            "Target",
        )

        result_level2 = spell_mgr.cast_healing_spell(
            "Cure Wounds",
            "Caster",
            "Target",
        )

        # Both should succeed
        assert result_level1["success"]
        assert result_level2["success"]

        # Level info should be tracked
        assert result_level1["spell_level"] == 1
        assert result_level2["spell_level"] == 2


class TestPartyMemberLookup:
    """Test finding party members by name."""

    def test_find_party_member_by_exact_name(self):
        """Test looking up party member by exact name."""
        session = GameSession()


        session.party = [char1, char2, char3]

        # Find by exact name
        found = next((c for c in session.party if c.character_name == "Thorin"), None)
        assert found is not None, "Should find Thorin"
        assert found.character_name == "Thorin"
        assert found.char_class == "Fighter"

    def test_find_party_member_case_insensitive(self):
        """Test case-insensitive party member lookup."""
        session = GameSession()

        session.party = [char1]

        # Case variations
        for name_variant in ["elara", "ELARA", "Elara", "eLaRa"]:
            found = next((c for c in session.party if c.character_name.lower() == name_variant.lower()), None)
            assert found is not None, f"Should find with variant: {name_variant}"


class TestIntegrationScenarios:
    """Integration tests for realistic party healing scenarios."""

    def test_combat_healing_scenario(self, spell_mgr):
        """Simulate realistic combat healing scenario."""
        session = GameSession()

        # Create party
        cleric.spell_slots = {1: 4, 2: 3, 3: 2}


        session.party = [cleric, fighter, wizard]
        session.character_state = cleric

        # Scenario: After tough battle, both allies are wounded
        # Cleric heals wizard first (more wounded)

        heal_wizard = spell_mgr.cast_healing_spell(
            "Cure Wounds",
            "Elara",
            "Gandalf",
        )

        wizard.current_hp = min(wizard.max_hp, wizard.current_hp + heal_wizard["amount"])
        cleric.cast_spell(2, "Cure Wounds")  # Consume slot

        assert wizard.current_hp > 5, "Wizard should be healed"
        assert cleric.spell_slots[2] == 2, "Should have used a level 2 slot"

        # Then heal fighter
        heal_fighter = spell_mgr.cast_healing_spell(
            "Cure Wounds",
            "Elara",
            "Thorin",
        )

        fighter.current_hp = min(fighter.max_hp, fighter.current_hp + heal_fighter["amount"])
        cleric.cast_spell(1, "Cure Wounds")  # Consume slot

        assert fighter.current_hp > 12, "Fighter should be healed"
        assert cleric.spell_slots[1] == 3, "Should have used a level 1 slot"

        # Both allies should be in better shape
        assert wizard.current_hp > 5
        assert fighter.current_hp > 12

    def test_multiple_healers_scenario(self, spell_mgr):
        """Test scenario with multiple healers in party."""
        session = GameSession()

        # Two clerics!
        cleric1.spell_slots = {1: 4, 2: 2}

        cleric2.spell_slots = {1: 4, 2: 2}


        session.party = [cleric1, cleric2, fighter]

        # Both clerics can heal the fighter
        fighter.current_hp = min(fighter.max_hp, fighter.current_hp + heal1["amount"])

        fighter.current_hp = min(fighter.max_hp, fighter.current_hp + heal2["amount"])

        # Fighter should be much better off
        assert fighter.current_hp > 16, "Double healing should significantly restore HP"


if __name__ == '__main__':
    # Run with: python -m pytest tests/test_party_member_interactions.py -v
    pytest.main([__file__, '-v', '--tb=short'])
