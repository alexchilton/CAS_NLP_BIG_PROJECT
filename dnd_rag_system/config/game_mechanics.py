"""
Game Mechanics Constants

Centralized D&D 5e game mechanics tables and constants.
Extracted from multiple files to avoid duplication and make updates easier.

Sources:
- D&D 5e Player's Handbook (spell slot progression)
- D&D 5e Dungeon Master's Guide (CR/XP tables, p.274)
"""

from typing import Dict

# ============================================================================
# SPELL SLOT PROGRESSION TABLES
# ============================================================================

# Full casters: Wizard, Sorcerer, Cleric, Druid, Bard
# {character_level: {spell_level: num_slots}}
SPELL_SLOTS_FULL_CASTER: Dict[int, Dict[int, int]] = {
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

# Half casters: Paladin, Ranger
# {character_level: {spell_level: num_slots}}
SPELL_SLOTS_HALF_CASTER: Dict[int, Dict[int, int]] = {
    1: {},  # No spells at level 1
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

# Third casters: Eldritch Knight, Arcane Trickster
# {character_level: {spell_level: num_slots}}
SPELL_SLOTS_THIRD_CASTER: Dict[int, Dict[int, int]] = {
    1: {},
    2: {},
    3: {1: 2},
    4: {1: 3},
    5: {1: 3},
    6: {1: 3},
    7: {1: 4, 2: 2},
    8: {1: 4, 2: 2},
    9: {1: 4, 2: 2},
    10: {1: 4, 2: 3},
    11: {1: 4, 2: 3},
    12: {1: 4, 2: 3},
    13: {1: 4, 2: 3, 3: 2},
    14: {1: 4, 2: 3, 3: 2},
    15: {1: 4, 2: 3, 3: 2},
    16: {1: 4, 2: 3, 3: 3},
    17: {1: 4, 2: 3, 3: 3},
    18: {1: 4, 2: 3, 3: 3},
    19: {1: 4, 2: 3, 3: 3, 4: 1},
    20: {1: 4, 2: 3, 3: 3, 4: 1},
}

# Warlock pact magic (different progression)
# Warlocks have fewer slots but they're all cast at the highest level
SPELL_SLOTS_WARLOCK: Dict[int, Dict[int, int]] = {
    1: {1: 1},
    2: {1: 2},
    3: {2: 2},  # 2 slots, cast at 2nd level
    4: {2: 2},
    5: {3: 2},  # 2 slots, cast at 3rd level
    6: {3: 2},
    7: {4: 2},  # 2 slots, cast at 4th level
    8: {4: 2},
    9: {5: 2},  # 2 slots, cast at 5th level
    10: {5: 2},
    11: {5: 3},  # 3 slots, cast at 5th level
    12: {5: 3},
    13: {5: 3},
    14: {5: 3},
    15: {5: 3},
    16: {5: 3},
    17: {5: 4},  # 4 slots, cast at 5th level
    18: {5: 4},
    19: {5: 4},
    20: {5: 4},
}

# ============================================================================
# CHALLENGE RATING & EXPERIENCE POINTS
# ============================================================================

# XP awards by Challenge Rating (DMG p.274)
CR_TO_XP: Dict[float, int] = {
    0: 10,
    0.125: 25,     # 1/8
    0.25: 50,      # 1/4
    0.5: 100,      # 1/2
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

# ============================================================================
# CHARACTER PROGRESSION
# ============================================================================

# XP thresholds for leveling up (PHB p.15)
XP_TO_LEVEL: Dict[int, int] = {
    1: 0,
    2: 300,
    3: 900,
    4: 2700,
    5: 6500,
    6: 14000,
    7: 23000,
    8: 34000,
    9: 48000,
    10: 64000,
    11: 85000,
    12: 100000,
    13: 120000,
    14: 140000,
    15: 165000,
    16: 195000,
    17: 225000,
    18: 265000,
    19: 305000,
    20: 355000,
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_spell_slots(character_class: str, character_level: int) -> Dict[int, int]:
    """
    Get spell slots for a character class and level.
    
    Args:
        character_class: Class name (e.g., "Wizard", "Paladin", "Warlock")
        character_level: Character level (1-20)
        
    Returns:
        Dictionary of {spell_level: num_slots}
    """
    class_lower = character_class.lower()
    
    # Full casters
    if class_lower in ["wizard", "sorcerer", "cleric", "druid", "bard"]:
        return SPELL_SLOTS_FULL_CASTER.get(character_level, {})
    
    # Half casters
    elif class_lower in ["paladin", "ranger"]:
        return SPELL_SLOTS_HALF_CASTER.get(character_level, {})
    
    # Third casters
    elif class_lower in ["eldritch knight", "arcane trickster"]:
        return SPELL_SLOTS_THIRD_CASTER.get(character_level, {})
    
    # Warlock
    elif class_lower == "warlock":
        return SPELL_SLOTS_WARLOCK.get(character_level, {})
    
    # Non-spellcaster
    else:
        return {}


def get_xp_for_cr(challenge_rating: float) -> int:
    """
    Get XP award for defeating a creature of given CR.
    
    Args:
        challenge_rating: CR value (e.g., 0.125, 1, 5, 20)
        
    Returns:
        XP value, or 0 if CR not found
    """
    return CR_TO_XP.get(challenge_rating, 0)


def get_level_for_xp(total_xp: int) -> int:
    """
    Get character level based on total XP.
    
    Args:
        total_xp: Total experience points
        
    Returns:
        Character level (1-20)
    """
    for level in range(20, 0, -1):  # Check from high to low
        if total_xp >= XP_TO_LEVEL[level]:
            return level
    return 1


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("D&D 5e Game Mechanics Constants")
    print("=" * 60)
    
    # Test spell slots
    print("\nWizard Level 5 Spell Slots:")
    slots = get_spell_slots("Wizard", 5)
    for level, count in sorted(slots.items()):
        print(f"  Level {level}: {count} slots")
    
    # Test XP
    print("\nCR to XP Conversion:")
    for cr in [0.25, 1, 5, 10, 20]:
        xp = get_xp_for_cr(cr)
        print(f"  CR {cr}: {xp} XP")
    
    # Test leveling
    print("\nXP to Level:")
    for xp in [0, 300, 900, 6500, 64000]:
        level = get_level_for_xp(xp)
        print(f"  {xp} XP = Level {level}")
