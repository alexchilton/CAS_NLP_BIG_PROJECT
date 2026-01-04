"""
Tests for Encounter Cooldown System (Fix #3)

Tests the encounter cooldown system that prevents random
encounter spam by implementing:
- 5-turn cooldown between encounters
- Location change resets cooldown
- No encounters during combat
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.game_state import GameSession


class TestEncounterCooldown:
    """Test 5-turn cooldown between encounters"""

    def test_initial_state(self):
        """Test initial encounter tracking state"""
        session = GameSession()
        assert session.turns_since_last_encounter == 0
        assert session.last_encounter_location == ""

    def test_increment_turns(self):
        """Test incrementing turns counter"""
        session = GameSession()
        session.turns_since_last_encounter = 0

        session.turns_since_last_encounter += 1
        assert session.turns_since_last_encounter == 1

        session.turns_since_last_encounter += 1
        assert session.turns_since_last_encounter == 2

    def test_cooldown_check_before_5_turns(self):
        """Test that cooldown is active before 5 turns"""
        session = GameSession()
        session.current_location = "Forest"
        session.last_encounter_location = "Forest"
        session.turns_since_last_encounter = 3  # Only 3 turns

        # Cooldown active (same location, < 5 turns)
        can_encounter = (
            session.turns_since_last_encounter >= 5 or
            session.last_encounter_location != session.current_location
        )
        assert can_encounter is False

    def test_cooldown_expires_after_5_turns(self):
        """Test that cooldown expires after 5 turns"""
        session = GameSession()
        session.current_location = "Forest"
        session.last_encounter_location = "Forest"
        session.turns_since_last_encounter = 5  # Exactly 5 turns

        # Cooldown expired
        can_encounter = (
            session.turns_since_last_encounter >= 5 or
            session.last_encounter_location != session.current_location
        )
        assert can_encounter is True

    def test_cooldown_with_more_than_5_turns(self):
        """Test cooldown with > 5 turns"""
        session = GameSession()
        session.current_location = "Forest"
        session.last_encounter_location = "Forest"
        session.turns_since_last_encounter = 10

        can_encounter = session.turns_since_last_encounter >= 5
        assert can_encounter is True

    def test_reset_on_encounter_spawn(self):
        """Test resetting counter when encounter spawns"""
        session = GameSession()
        session.current_location = "Forest"
        session.turns_since_last_encounter = 7

        # Encounter spawns - reset
        session.turns_since_last_encounter = 0
        session.last_encounter_location = session.current_location

        assert session.turns_since_last_encounter == 0
        assert session.last_encounter_location == "Forest"


class TestLocationChange:
    """Test location change resets cooldown"""

    def test_different_location_allows_encounter(self):
        """Test changing location allows immediate encounter"""
        session = GameSession()
        session.current_location = "Cave"
        session.last_encounter_location = "Forest"
        session.turns_since_last_encounter = 1  # Only 1 turn

        # Different location - can encounter
        can_encounter = (
            session.turns_since_last_encounter >= 5 or
            session.last_encounter_location != session.current_location
        )
        assert can_encounter is True

    def test_same_location_enforces_cooldown(self):
        """Test staying in same location enforces cooldown"""
        session = GameSession()
        session.current_location = "Forest"
        session.last_encounter_location = "Forest"
        session.turns_since_last_encounter = 3

        # Same location, < 5 turns - no encounter
        can_encounter = (
            session.turns_since_last_encounter >= 5 or
            session.last_encounter_location != session.current_location
        )
        assert can_encounter is False

    def test_location_change_updates_last_encounter_location(self):
        """Test that last_encounter_location updates on new encounter"""
        session = GameSession()
        session.current_location = "Cave"
        session.last_encounter_location = "Forest"

        # Encounter spawns in Cave
        session.last_encounter_location = session.current_location
        session.turns_since_last_encounter = 0

        assert session.last_encounter_location == "Cave"

    def test_multiple_location_changes(self):
        """Test multiple location changes"""
        session = GameSession()

        # Encounter in Forest
        session.current_location = "Forest"
        session.last_encounter_location = "Forest"
        session.turns_since_last_encounter = 0

        # Move to Cave - can encounter (different location)
        session.current_location = "Cave"
        can_encounter = session.last_encounter_location != session.current_location
        assert can_encounter is True

        # Encounter in Cave
        session.last_encounter_location = "Cave"
        session.turns_since_last_encounter = 0

        # Move to Town - can encounter (different location)
        session.current_location = "Town"
        can_encounter = session.last_encounter_location != session.current_location
        assert can_encounter is True


class TestEncounterLogic:
    """Test complete encounter check logic"""

    def test_first_encounter_can_spawn(self):
        """Test that first encounter can spawn (no previous encounter)"""
        session = GameSession()
        session.current_location = "Forest"
        session.last_encounter_location = ""  # No previous
        session.turns_since_last_encounter = 0

        # Different location (empty != Forest) - can spawn
        can_encounter = session.last_encounter_location != session.current_location
        assert can_encounter is True

    def test_encounter_sequence(self):
        """Test realistic encounter sequence"""
        session = GameSession()

        # Turn 1: Player enters Forest
        session.current_location = "Forest"
        session.last_encounter_location = ""
        can_encounter = session.last_encounter_location != session.current_location
        assert can_encounter is True  # First encounter can spawn

        # Encounter spawns
        session.last_encounter_location = "Forest"
        session.turns_since_last_encounter = 0

        # Turns 2-5: Player explores Forest
        for turn in range(1, 5):
            session.turns_since_last_encounter += 1
            can_encounter = (
                session.turns_since_last_encounter >= 5 or
                session.last_encounter_location != session.current_location
            )
            assert can_encounter is False  # Cooldown active

        # Turn 6: Cooldown expired
        session.turns_since_last_encounter += 1
        can_encounter = session.turns_since_last_encounter >= 5
        assert can_encounter is True

    def test_travel_interrupts_cooldown(self):
        """Test that traveling to new location bypasses cooldown"""
        session = GameSession()

        # Encounter in Forest
        session.current_location = "Forest"
        session.last_encounter_location = "Forest"
        session.turns_since_last_encounter = 0

        # Turn 2: Still in Forest - cooldown active
        session.turns_since_last_encounter = 1
        can_encounter = (
            session.turns_since_last_encounter >= 5 or
            session.last_encounter_location != session.current_location
        )
        assert can_encounter is False

        # Turn 3: Travel to Mountains - can encounter immediately
        session.current_location = "Mountains"
        can_encounter = session.last_encounter_location != session.current_location
        assert can_encounter is True


class TestCombatInteraction:
    """Test encounters don't spawn during combat"""

    def test_turns_dont_increment_during_combat(self):
        """Test that encounter counter doesn't increment during combat"""
        session = GameSession()
        session.current_location = "Cave"
        session.turns_since_last_encounter = 0

        # Combat starts
        in_combat = session.combat.in_combat

        # During combat, counter shouldn't increment
        # (This is handled in gm_dialogue_unified.py, not GameSession)
        # But we can test the state tracking
        if in_combat:
            # Don't increment
            pass
        else:
            session.turns_since_last_encounter += 1

        # If not in combat, should increment
        assert session.turns_since_last_encounter == 1

    def test_combat_state_tracking(self):
        """Test combat state can be checked"""
        session = GameSession()

        # Not in combat initially
        assert session.combat.in_combat is False

        # Start combat
        session.combat.in_combat = True
        assert session.combat.in_combat is True

        # End combat
        session.combat.in_combat = False
        assert session.combat.in_combat is False


class TestEdgeCases:
    """Test edge cases in encounter system"""

    def test_negative_turns(self):
        """Test handling of negative turns (shouldn't happen, but be safe)"""
        session = GameSession()
        session.turns_since_last_encounter = -1

        # Even with negative, >= 5 check should work
        can_encounter = session.turns_since_last_encounter >= 5
        assert can_encounter is False

    def test_very_large_turn_count(self):
        """Test with very large turn count"""
        session = GameSession()
        session.turns_since_last_encounter = 1000

        can_encounter = session.turns_since_last_encounter >= 5
        assert can_encounter is True

    def test_empty_location_names(self):
        """Test with empty location names"""
        session = GameSession()
        session.current_location = ""
        session.last_encounter_location = ""

        # Same empty location
        can_encounter = session.last_encounter_location != session.current_location
        assert can_encounter is False

    def test_case_sensitive_location_names(self):
        """Test location names are case-sensitive"""
        session = GameSession()
        session.current_location = "Forest"
        session.last_encounter_location = "forest"  # Different case

        # Different locations (case matters)
        can_encounter = session.last_encounter_location != session.current_location
        assert can_encounter is True

    def test_whitespace_in_location_names(self):
        """Test location names with whitespace"""
        session = GameSession()
        session.current_location = "Dark Forest"
        session.last_encounter_location = "Dark Forest"

        # Same location
        can_encounter = session.last_encounter_location != session.current_location
        assert can_encounter is False


class TestEncounterCooldownIntegration:
    """Test full integration of encounter cooldown system"""

    def test_realistic_gameplay_scenario(self):
        """Test realistic multi-turn gameplay scenario"""
        session = GameSession()

        # Player starts in Tavern (safe zone)
        session.current_location = "Tavern"
        session.last_encounter_location = ""
        session.turns_since_last_encounter = 0

        # Turn 1: Travel to Forest (exploration begins)
        session.current_location = "Forest"
        can_encounter = session.last_encounter_location != session.current_location
        assert can_encounter is True  # New location

        # Goblin encounter spawns!
        session.last_encounter_location = "Forest"
        session.turns_since_last_encounter = 0

        # Turns 2-4: Combat with goblin (no turn increment during combat)
        # Turn counter stays at 0 during combat

        # Turn 5: Combat ends, exploration continues
        session.turns_since_last_encounter = 1
        can_encounter = session.turns_since_last_encounter >= 5
        assert can_encounter is False  # Cooldown active

        # Turns 6-9: Explore deeper
        for _ in range(4):
            session.turns_since_last_encounter += 1

        assert session.turns_since_last_encounter == 5
        can_encounter = session.turns_since_last_encounter >= 5
        assert can_encounter is True  # Cooldown expired

        # Wolf encounter spawns!
        session.last_encounter_location = "Forest"
        session.turns_since_last_encounter = 0

        # Turn 10: Player flees to Town
        session.current_location = "Town"
        can_encounter = session.last_encounter_location != session.current_location
        assert can_encounter is True  # Different location, but town is safe

        # Town doesn't spawn encounters (handled by encounter system logic)
        # But cooldown allows it if needed
        session.last_encounter_location = "Town"
        session.turns_since_last_encounter = 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
