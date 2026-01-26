"""
Tests for centralized game mechanics constants
"""

import pytest
from dnd_rag_system.config.game_mechanics import (
    SPELL_SLOTS_FULL_CASTER,
    SPELL_SLOTS_HALF_CASTER,
    SPELL_SLOTS_THIRD_CASTER,
    SPELL_SLOTS_WARLOCK,
    CR_TO_XP,
    XP_TO_LEVEL,
    get_spell_slots,
    get_xp_for_cr,
    get_level_for_xp
)


class TestSpellSlotConstants:
    """Test spell slot progression constants."""
    
    def test_full_caster_level_1_slots(self):
        """Full casters at level 1 should have 2 level-1 slots."""
        slots = SPELL_SLOTS_FULL_CASTER[1]
        assert slots[1] == 2
        assert 2 not in slots  # No level 2 slots yet
    
    def test_full_caster_level_5_slots(self):
        """Full casters at level 5 should have 4/3/2 slots."""
        slots = SPELL_SLOTS_FULL_CASTER[5]
        assert slots[1] == 4
        assert slots[2] == 3
        assert slots[3] == 2
        assert 4 not in slots  # No level 4 slots yet
    
    def test_full_caster_level_20_slots(self):
        """Full casters at level 20 should have max slots."""
        slots = SPELL_SLOTS_FULL_CASTER[20]
        assert 1 in slots
        assert 9 in slots  # Should have 9th level slots
        assert slots[9] == 1  # One 9th level slot
    
    def test_half_caster_level_2_slots(self):
        """Half casters get spells at level 2."""
        slots = SPELL_SLOTS_HALF_CASTER[2]
        assert slots[1] == 2
    
    def test_half_caster_no_spells_at_level_1(self):
        """Half casters don't get spells at level 1."""
        slots = SPELL_SLOTS_HALF_CASTER.get(1, {})
        assert slots == {}, "Half casters should have no spell slots at level 1"
    
    def test_half_caster_max_level_5_spells(self):
        """Half casters max out at 5th level spells."""
        slots = SPELL_SLOTS_HALF_CASTER[20]
        assert 5 in slots
        assert 6 not in slots  # No 6th level slots
    
    def test_third_caster_level_3_slots(self):
        """Third casters get spells at level 3."""
        slots = SPELL_SLOTS_THIRD_CASTER[3]
        assert 1 in slots
    
    def test_third_caster_max_level_4_spells(self):
        """Third casters max out at 4th level spells."""
        slots = SPELL_SLOTS_THIRD_CASTER[20]
        assert 4 in slots
        assert 5 not in slots  # No 5th level slots
    
    def test_warlock_pact_magic_level_1(self):
        """Warlocks have pact magic slots at level 1."""
        slots = SPELL_SLOTS_WARLOCK[1]
        assert slots[1] == 1  # 1 spell slot
    
    def test_warlock_pact_magic_level_11(self):
        """Warlocks get 3 slots and 5th level spells at level 11."""
        slots = SPELL_SLOTS_WARLOCK[11]
        assert slots[5] == 3  # 3 fifth-level slots
    
    def test_warlock_max_slot_level(self):
        """Warlocks max out at 5th level spell slots."""
        slots = SPELL_SLOTS_WARLOCK[20]
        assert 5 in slots
        assert 6 not in slots


class TestCRToXP:
    """Test CR to XP conversion constants."""
    
    def test_cr_0_xp(self):
        """CR 0 should give specific XP values."""
        assert CR_TO_XP[0] in [0, 10]  # CR 0 can be 0 or 10 XP
    
    def test_cr_1_xp(self):
        """CR 1 should give 200 XP."""
        assert CR_TO_XP[1] == 200
    
    def test_cr_5_xp(self):
        """CR 5 should give 1,800 XP."""
        assert CR_TO_XP[5] == 1800
    
    def test_cr_10_xp(self):
        """CR 10 should give 5,900 XP."""
        assert CR_TO_XP[10] == 5900
    
    def test_cr_20_xp(self):
        """CR 20 should give 25,000 XP."""
        assert CR_TO_XP[20] == 25000
    
    def test_cr_30_xp(self):
        """CR 30 should give 155,000 XP."""
        assert CR_TO_XP[30] == 155000
    
    def test_fractional_cr_values(self):
        """Should have fractional CR values."""
        assert 0.125 in CR_TO_XP  # CR 1/8
        assert 0.25 in CR_TO_XP   # CR 1/4
        assert 0.5 in CR_TO_XP    # CR 1/2


class TestXPToLevel:
    """Test XP to level progression constants."""
    
    def test_level_1_xp(self):
        """Level 1 starts at 0 XP."""
        assert XP_TO_LEVEL[1] == 0
    
    def test_level_2_xp(self):
        """Level 2 requires 300 XP."""
        assert XP_TO_LEVEL[2] == 300
    
    def test_level_5_xp(self):
        """Level 5 requires 6,500 XP."""
        assert XP_TO_LEVEL[5] == 6500
    
    def test_level_10_xp(self):
        """Level 10 requires 64,000 XP."""
        assert XP_TO_LEVEL[10] == 64000
    
    def test_level_20_xp(self):
        """Level 20 requires 355,000 XP."""
        assert XP_TO_LEVEL[20] == 355000
    
    def test_all_levels_present(self):
        """Should have all levels 1-20."""
        for level in range(1, 21):
            assert level in XP_TO_LEVEL


class TestGetSpellSlotsHelper:
    """Test get_spell_slots() helper function."""
    
    def test_get_wizard_level_5_slots(self):
        """Should return Wizard level 5 slots."""
        slots = get_spell_slots("Wizard", 5)
        assert slots[1] == 4
        assert slots[2] == 3
        assert slots[3] == 2
    
    def test_get_paladin_level_5_slots(self):
        """Should return Paladin (half caster) level 5 slots."""
        slots = get_spell_slots("Paladin", 5)
        assert 1 in slots
        assert 2 in slots
    
    def test_get_warlock_slots(self):
        """Should return Warlock pact magic slots."""
        slots = get_spell_slots("Warlock", 5)
        assert 3 in slots  # Gets 3rd level slots
    
    def test_get_fighter_no_slots(self):
        """Fighter (non-caster) should have no slots."""
        slots = get_spell_slots("Fighter", 10)
        assert slots == {}
    
    def test_get_unknown_class_returns_empty(self):
        """Unknown class should return empty dict."""
        slots = get_spell_slots("UnknownClass", 5)
        assert slots == {}
    
    def test_level_out_of_range_returns_empty(self):
        """Out of range level should return empty dict."""
        slots = get_spell_slots("Wizard", 25)
        assert slots == {}


class TestGetXPForCRHelper:
    """Test get_xp_for_cr() helper function."""
    
    def test_cr_1_returns_200_xp(self):
        """CR 1 should return 200 XP."""
        assert get_xp_for_cr(1) == 200
    
    def test_cr_5_returns_1800_xp(self):
        """CR 5 should return 1,800 XP."""
        assert get_xp_for_cr(5) == 1800
    
    def test_fractional_cr(self):
        """Should handle fractional CR values."""
        xp = get_xp_for_cr(0.5)  # CR 1/2
        assert xp == 100
    
    def test_cr_quarter(self):
        """CR 1/4 should return 50 XP."""
        assert get_xp_for_cr(0.25) == 50
    
    def test_unknown_cr_returns_0(self):
        """Unknown CR should return 0."""
        assert get_xp_for_cr(999) == 0
    
    def test_negative_cr_returns_0(self):
        """Negative CR should return 0."""
        assert get_xp_for_cr(-1) == 0


class TestGetLevelForXPHelper:
    """Test get_level_for_xp() helper function."""
    
    def test_xp_0_is_level_1(self):
        """0 XP should be level 1."""
        assert get_level_for_xp(0) == 1
    
    def test_xp_300_is_level_2(self):
        """300 XP should be level 2."""
        assert get_level_for_xp(300) == 2
    
    def test_xp_350_is_level_2(self):
        """350 XP (between thresholds) should be level 2."""
        assert get_level_for_xp(350) == 2
    
    def test_xp_6500_is_level_5(self):
        """6,500 XP should be level 5."""
        assert get_level_for_xp(6500) == 5
    
    def test_xp_355000_is_level_20(self):
        """355,000 XP should be level 20."""
        assert get_level_for_xp(355000) == 20
    
    def test_xp_1000000_is_level_20(self):
        """XP beyond max should cap at level 20."""
        assert get_level_for_xp(1000000) == 20


class TestConstantsIntegrity:
    """Test that constants are internally consistent."""
    
    def test_spell_slot_progression_is_increasing(self):
        """Higher levels should have more spell slots."""
        for level in range(1, 19):
            if level in SPELL_SLOTS_FULL_CASTER and level + 1 in SPELL_SLOTS_FULL_CASTER:
                # Total slots should generally increase
                current_total = sum(SPELL_SLOTS_FULL_CASTER[level].values())
                next_total = sum(SPELL_SLOTS_FULL_CASTER[level + 1].values())
                assert next_total >= current_total
    
    def test_cr_xp_is_increasing(self):
        """Higher CR should give more XP."""
        previous_xp = 0
        for cr in sorted([k for k in CR_TO_XP.keys() if isinstance(k, (int, float)) and k >= 1]):
            current_xp = CR_TO_XP[cr]
            assert current_xp > previous_xp, f"CR {cr} XP should be > CR {cr-1} XP"
            previous_xp = current_xp
    
    def test_level_xp_is_increasing(self):
        """Higher levels require more XP."""
        for level in range(1, 20):
            assert XP_TO_LEVEL[level + 1] > XP_TO_LEVEL[level]
