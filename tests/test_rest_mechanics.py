"""
Test suite for rest mechanics (short rest and long rest).

Tests HP restoration, hit dice usage, and spell slot restoration.
"""

import pytest
from dnd_rag_system.systems.game_state import CharacterState, SpellSlots


class TestShortRest:
    """Test short rest mechanics."""

    def test_short_rest_heals_with_hit_dice(self):
        """Test that short rest spends hit dice and heals HP."""
        char = CharacterState(
            character_name="Test Fighter",
            max_hp=30,
            current_hp=15,  # Damaged
            level=3,
            hit_dice_max=3,
            hit_dice_current=3
        )

        # Take short rest and spend 1 hit die
        result = char.short_rest(hit_dice_spent=1)

        # Should heal some HP
        assert result["hit_dice_spent"] == 1
        assert result["hit_dice_remaining"] == 2
        assert result["hp_restored"] > 0
        assert char.current_hp > 15  # HP increased
        assert char.hit_dice_current == 2  # Used 1 hit die

        print(f"✓ Short rest: {result['hit_dice_spent']} hit die spent, {result['hp_restored']} HP restored")

    def test_short_rest_no_hit_dice(self):
        """Test that short rest handles having no hit dice gracefully."""
        # Note: CharacterState.__post_init__ sets hit_dice_current = hit_dice_max if == 0
        # So we need to manually spend all hit dice after creation
        char = CharacterState(
            character_name="Exhausted Fighter",
            max_hp=30,
            current_hp=15,
            level=3,
            hit_dice_max=3
        )

        # Manually spend all hit dice to deplete them
        char.hit_dice_current = 0

        # Try to rest with no hit dice
        result = char.short_rest(hit_dice_spent=1)

        # Should return early with no healing
        assert result["hit_dice_spent"] == 0
        assert result["hp_restored"] == 0
        assert char.current_hp == 15  # No healing possible without hit dice
        assert char.hit_dice_current == 0  # Still at 0

        print(f"✓ Short rest with no hit dice: HP remains {char.current_hp}/{char.max_hp}")

    def test_short_rest_caps_at_max_hp(self):
        """Test that short rest doesn't exceed max HP."""
        char = CharacterState(
            character_name="Nearly Healed Fighter",
            max_hp=30,
            current_hp=28,  # Almost full
            level=3,
            hit_dice_max=3,
            hit_dice_current=3
        )

        # Take short rest - should heal but not exceed max
        result = char.short_rest(hit_dice_spent=2)

        assert char.current_hp <= char.max_hp
        assert char.current_hp == 30  # Capped at max

        print(f"✓ Short rest capped at max HP: {char.current_hp}/{char.max_hp}")

    def test_short_rest_multiple_hit_dice(self):
        """Test spending multiple hit dice in one rest."""
        char = CharacterState(
            character_name="Badly Wounded Fighter",
            max_hp=50,
            current_hp=10,  # Badly damaged
            level=5,
            hit_dice_max=5,
            hit_dice_current=5
        )

        # Spend 3 hit dice
        result = char.short_rest(hit_dice_spent=3)

        assert result["hit_dice_spent"] == 3
        assert char.hit_dice_current == 2
        assert result["hp_restored"] > 0
        assert char.current_hp > 10

        print(f"✓ Short rest with 3 hit dice: {result['hp_restored']} HP restored")


class TestLongRest:
    """Test long rest mechanics."""

    def test_long_rest_restores_full_hp(self):
        """Test that long rest restores full HP."""
        char = CharacterState(
            character_name="Wounded Wizard",
            max_hp=20,
            current_hp=5,  # Nearly dead
            level=3
        )

        # Take long rest
        result = char.long_rest()

        # HP should be fully restored
        assert char.current_hp == char.max_hp
        assert result["hp_restored"] == 15

        print(f"✓ Long rest: Full HP restored ({char.current_hp}/{char.max_hp})")

    def test_long_rest_restores_spell_slots(self):
        """Test that long rest restores all spell slots."""
        # Create wizard with spell slots
        # Note: SpellSlots __post_init__ automatically sets current = max
        char = CharacterState(
            character_name="Exhausted Wizard",
            max_hp=20,
            level=5,
            spell_slots=SpellSlots(
                level_1=4,
                level_2=3,
                level_3=2
            )
        )

        # Use some spell slots to deplete them
        char.spell_slots.use_slot(1)
        char.spell_slots.use_slot(1)
        char.spell_slots.use_slot(1)  # Use 3 level 1 slots
        char.spell_slots.use_slot(2)
        char.spell_slots.use_slot(2)
        char.spell_slots.use_slot(2)  # Use all level 2 slots
        char.spell_slots.use_slot(3)  # Use 1 level 3 slot

        # Verify slots are depleted
        assert char.spell_slots.current_1 == 1  # 4 - 3 = 1
        assert char.spell_slots.current_2 == 0  # 3 - 3 = 0
        assert char.spell_slots.current_3 == 1  # 2 - 1 = 1

        # Take long rest
        result = char.long_rest()

        # All spell slots should be restored
        assert char.spell_slots.current_1 == 4
        assert char.spell_slots.current_2 == 3
        assert char.spell_slots.current_3 == 2
        assert result["spell_slots_restored"] == True

        print(f"✓ Long rest: All spell slots restored")

    def test_long_rest_restores_half_hit_dice(self):
        """Test that long rest restores half of spent hit dice."""
        char = CharacterState(
            character_name="Tired Fighter",
            max_hp=40,
            current_hp=40,
            level=6,
            hit_dice_max=6,
            hit_dice_current=2  # Spent 4 hit dice
        )

        # Take long rest
        result = char.long_rest()

        # Should restore half of max hit dice (6 // 2 = 3)
        # Current is 2, so adding 3 gives 5 (or capped at max)
        # Minimum restoration is 1
        assert char.hit_dice_current >= 3  # At least got minimum + current
        assert char.hit_dice_current <= char.hit_dice_max
        assert result["hit_dice_restored"] >= 1

        print(f"✓ Long rest: {result['hit_dice_restored']} hit dice restored ({char.hit_dice_current}/{char.hit_dice_max})")

    def test_long_rest_clears_conditions(self):
        """Test that long rest clears conditions."""
        char = CharacterState(
            character_name="Poisoned Rogue",
            max_hp=25,
            current_hp=10,
            level=3,
            conditions=["poisoned", "frightened"]
        )

        # Verify conditions are present
        assert "poisoned" in char.conditions
        assert "frightened" in char.conditions

        # Take long rest
        char.long_rest()

        # Conditions should be cleared
        assert len(char.conditions) == 0

        print(f"✓ Long rest: All conditions cleared")

    def test_long_rest_resets_death_saves(self):
        """Test that long rest resets death saves."""
        from dnd_rag_system.systems.game_state import DeathSaves

        char = CharacterState(
            character_name="Near-Death Cleric",
            max_hp=22,
            current_hp=1,  # Barely alive
            level=3,
            death_saves=DeathSaves(successes=2, failures=1)
        )

        # Verify death saves are active
        assert char.death_saves.successes == 2
        assert char.death_saves.failures == 1

        # Take long rest
        char.long_rest()

        # Death saves should be reset
        assert char.death_saves.successes == 0
        assert char.death_saves.failures == 0

        print(f"✓ Long rest: Death saves reset")


class TestRestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_short_rest_at_full_hp(self):
        """Test that character can short rest even at full HP (to restore other resources)."""
        char = CharacterState(
            character_name="Healthy Fighter",
            max_hp=30,
            current_hp=30,  # Full HP
            level=3,
            hit_dice_max=3,
            hit_dice_current=3
        )

        # Short rest at full HP (shouldn't heal, but allowed)
        result = char.short_rest(hit_dice_spent=1)

        # HP stays at max, but hit die is still spent (rules as written)
        # Actually, the CharacterState.short_rest checks if healing is needed
        # But let's verify the behavior
        assert char.current_hp == 30

        print(f"✓ Short rest at full HP: HP remains {char.current_hp}/{char.max_hp}")

    def test_long_rest_at_full_resources(self):
        """Test long rest when already at full resources."""
        char = CharacterState(
            character_name="Fresh Wizard",
            max_hp=20,
            current_hp=20,
            level=3,
            hit_dice_max=3,
            hit_dice_current=3,
            spell_slots=SpellSlots(level_1=4, current_1=4, level_2=2, current_2=2)
        )

        # Long rest when already fresh
        result = char.long_rest()

        # Everything should stay at max
        assert char.current_hp == char.max_hp
        assert char.hit_dice_current == char.hit_dice_max
        assert char.spell_slots.current_1 == char.spell_slots.level_1
        assert result["hp_restored"] == 0  # No HP to restore

        print(f"✓ Long rest at full resources: No changes needed")


if __name__ == "__main__":
    print("🧪 Rest Mechanics Tests")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s"])
