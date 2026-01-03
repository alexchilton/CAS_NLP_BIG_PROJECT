"""
D&D 5e Monster Stat Blocks

Curated stat blocks for common monsters, organized by Challenge Rating.
Source: D&D 5e Monster Manual

Each monster has:
- name: Monster name
- cr: Challenge rating
- type: Monster type (humanoid, beast, undead, etc.)
- size: Size category (tiny, small, medium, large, huge, gargantuan)
- ac: Armor class
- hp: Hit points (average)
- hp_dice: Hit dice formula (e.g., "2d6")
- speed: Movement speed in feet
- str, dex, con, int, wis, cha: Ability scores
- attacks: List of attack dictionaries with to_hit, reach, damage
- traits: Special abilities
- description: Flavor text
"""

from typing import Dict, List, Any

# Monster stat block type
MonsterStat = Dict[str, Any]

MONSTER_STATS: Dict[str, MonsterStat] = {
    # ========================================================================
    # CR 0 - Trivial Threats
    # ========================================================================
    "Giant Rat": {
        "name": "Giant Rat",
        "cr": 0,
        "type": "beast",
        "size": "small",
        "ac": 12,
        "hp": 7,
        "hp_dice": "2d6",
        "speed": 30,
        "str": 7, "dex": 15, "con": 11, "int": 2, "wis": 10, "cha": 4,
        "attacks": [
            {
                "name": "Bite",
                "to_hit": 4,
                "reach": 5,
                "damage": "1d4+2",
                "damage_type": "piercing"
            }
        ],
        "traits": ["Keen Smell", "Pack Tactics"],
        "description": "A diseased rat the size of a small dog, with matted fur and sharp teeth."
    },

    # ========================================================================
    # CR 1/4 - Easy Encounters
    # ========================================================================
    "Goblin": {
        "name": "Goblin",
        "cr": 0.25,
        "type": "humanoid",
        "size": "small",
        "ac": 15,
        "hp": 7,
        "hp_dice": "2d6",
        "speed": 30,
        "str": 8, "dex": 14, "con": 10, "int": 10, "wis": 8, "cha": 8,
        "attacks": [
            {
                "name": "Scimitar",
                "to_hit": 4,
                "reach": 5,
                "damage": "1d6+2",
                "damage_type": "slashing"
            },
            {
                "name": "Shortbow",
                "to_hit": 4,
                "reach": 80,  # range
                "damage": "1d6+2",
                "damage_type": "piercing"
            }
        ],
        "traits": ["Nimble Escape"],
        "description": "A small, green-skinned humanoid with sharp teeth and a cunning glint in its yellow eyes."
    },

    "Wolf": {
        "name": "Wolf",
        "cr": 0.25,
        "type": "beast",
        "size": "medium",
        "ac": 13,
        "hp": 11,
        "hp_dice": "2d8+2",
        "speed": 40,
        "str": 12, "dex": 15, "con": 12, "int": 3, "wis": 12, "cha": 6,
        "attacks": [
            {
                "name": "Bite",
                "to_hit": 4,
                "reach": 5,
                "damage": "2d4+2",
                "damage_type": "piercing",
                "special": "Target must succeed DC 11 STR save or be knocked prone"
            }
        ],
        "traits": ["Keen Hearing and Smell", "Pack Tactics"],
        "description": "A fierce predator with gray fur and piercing eyes that hunts in packs."
    },

    "Skeleton": {
        "name": "Skeleton",
        "cr": 0.25,
        "type": "undead",
        "size": "medium",
        "ac": 13,
        "hp": 13,
        "hp_dice": "2d8+4",
        "speed": 30,
        "str": 10, "dex": 14, "con": 15, "int": 6, "wis": 8, "cha": 5,
        "attacks": [
            {
                "name": "Shortsword",
                "to_hit": 4,
                "reach": 5,
                "damage": "1d6+2",
                "damage_type": "piercing"
            },
            {
                "name": "Shortbow",
                "to_hit": 4,
                "reach": 80,
                "damage": "1d6+2",
                "damage_type": "piercing"
            }
        ],
        "traits": ["Vulnerable to bludgeoning damage", "Immune to poison"],
        "description": "An animated skeleton of humanoid bones, eyes glowing with unnatural green light."
    },

    # ========================================================================
    # CR 1/2 - Moderate Low-Level Encounters
    # ========================================================================
    "Orc": {
        "name": "Orc",
        "cr": 0.5,
        "type": "humanoid",
        "size": "medium",
        "ac": 13,
        "hp": 15,
        "hp_dice": "2d8+6",
        "speed": 30,
        "str": 16, "dex": 12, "con": 16, "int": 7, "wis": 11, "cha": 10,
        "attacks": [
            {
                "name": "Greataxe",
                "to_hit": 5,
                "reach": 5,
                "damage": "1d12+3",
                "damage_type": "slashing"
            },
            {
                "name": "Javelin",
                "to_hit": 5,
                "reach": 30,
                "damage": "1d6+3",
                "damage_type": "piercing"
            }
        ],
        "traits": ["Aggressive (bonus action to move toward enemy)"],
        "description": "A muscular, gray-skinned humanoid with tusks and a fierce battle cry."
    },

    "Hobgoblin": {
        "name": "Hobgoblin",
        "cr": 0.5,
        "type": "humanoid",
        "size": "medium",
        "ac": 18,
        "hp": 11,
        "hp_dice": "2d8+2",
        "speed": 30,
        "str": 13, "dex": 12, "con": 12, "int": 10, "wis": 10, "cha": 9,
        "attacks": [
            {
                "name": "Longsword",
                "to_hit": 3,
                "reach": 5,
                "damage": "1d8+1",
                "damage_type": "slashing"
            },
            {
                "name": "Longbow",
                "to_hit": 3,
                "reach": 150,
                "damage": "1d8+1",
                "damage_type": "piercing"
            }
        ],
        "traits": ["Martial Advantage (+2d6 damage with ally nearby)"],
        "description": "A disciplined goblinoid soldier in well-maintained armor, tactical and organized."
    },

    # ========================================================================
    # CR 1 - Challenging for Level 1-2 Characters
    # ========================================================================
    "Dire Wolf": {
        "name": "Dire Wolf",
        "cr": 1,
        "type": "beast",
        "size": "large",
        "ac": 14,
        "hp": 37,
        "hp_dice": "5d10+10",
        "speed": 50,
        "str": 17, "dex": 15, "con": 15, "int": 3, "wis": 12, "cha": 7,
        "attacks": [
            {
                "name": "Bite",
                "to_hit": 5,
                "reach": 5,
                "damage": "2d6+3",
                "damage_type": "piercing",
                "special": "Target must succeed DC 13 STR save or be knocked prone"
            }
        ],
        "traits": ["Keen Hearing and Smell", "Pack Tactics"],
        "description": "A massive wolf with black fur, standing as tall as a horse, with fangs like daggers."
    },

    "Bugbear": {
        "name": "Bugbear",
        "cr": 1,
        "type": "humanoid",
        "size": "medium",
        "ac": 16,
        "hp": 27,
        "hp_dice": "5d8+5",
        "speed": 30,
        "str": 15, "dex": 14, "con": 13, "int": 8, "wis": 11, "cha": 9,
        "attacks": [
            {
                "name": "Morningstar",
                "to_hit": 4,
                "reach": 5,
                "damage": "2d8+2",
                "damage_type": "piercing"
            },
            {
                "name": "Javelin",
                "to_hit": 4,
                "reach": 30,
                "damage": "2d6+2",
                "damage_type": "piercing"
            }
        ],
        "traits": ["Brute (+1 die of damage)", "Surprise Attack (+2d6 if surprised)", "Sneaky"],
        "description": "A hulking, hairy goblinoid that excels at ambush tactics and brutish strength."
    },

    # ========================================================================
    # CR 2 - Moderate Challenge
    # ========================================================================
    "Ogre": {
        "name": "Ogre",
        "cr": 2,
        "type": "giant",
        "size": "large",
        "ac": 11,
        "hp": 59,
        "hp_dice": "7d10+21",
        "speed": 40,
        "str": 19, "dex": 8, "con": 16, "int": 5, "wis": 7, "cha": 7,
        "attacks": [
            {
                "name": "Greatclub",
                "to_hit": 6,
                "reach": 5,
                "damage": "2d8+4",
                "damage_type": "bludgeoning"
            },
            {
                "name": "Javelin",
                "to_hit": 6,
                "reach": 30,
                "damage": "2d6+4",
                "damage_type": "piercing"
            }
        ],
        "traits": [],
        "description": "A brutish, dim-witted giant standing 9 feet tall with a crude club and stench of unwashed flesh."
    },

    "Werewolf": {
        "name": "Werewolf",
        "cr": 3,
        "type": "humanoid_shapechanger",
        "size": "medium",
        "ac": 12,
        "hp": 58,
        "hp_dice": "9d8+18",
        "speed": 30,
        "str": 15, "dex": 13, "con": 14, "int": 10, "wis": 11, "cha": 10,
        "attacks": [
            {
                "name": "Bite (Wolf or Hybrid Form)",
                "to_hit": 4,
                "reach": 5,
                "damage": "1d8+2",
                "damage_type": "piercing",
                "special": "Target must succeed DC 12 CON save or be cursed with werewolf lycanthropy"
            },
            {
                "name": "Claws (Hybrid Form)",
                "to_hit": 4,
                "reach": 5,
                "damage": "2d4+2",
                "damage_type": "slashing"
            }
        ],
        "traits": ["Shapechanger", "Immune to non-silvered weapons", "Keen Hearing and Smell"],
        "description": "A cursed humanoid that transforms into a savage wolf-human hybrid under the full moon."
    },

    # ========================================================================
    # CR 5 - Deadly for Low Levels
    # ========================================================================
    "Hill Giant": {
        "name": "Hill Giant",
        "cr": 5,
        "type": "giant",
        "size": "huge",
        "ac": 13,
        "hp": 105,
        "hp_dice": "10d12+40",
        "speed": 40,
        "str": 21, "dex": 8, "con": 19, "int": 5, "wis": 9, "cha": 6,
        "attacks": [
            {
                "name": "Greatclub",
                "to_hit": 8,
                "reach": 10,
                "damage": "3d8+5",
                "damage_type": "bludgeoning"
            },
            {
                "name": "Rock",
                "to_hit": 8,
                "reach": 60,
                "damage": "3d10+5",
                "damage_type": "bludgeoning"
            }
        ],
        "traits": [],
        "description": "A 16-foot-tall giant with a crude appearance, covered in hides and wielding an enormous club."
    },

    "Troll": {
        "name": "Troll",
        "cr": 5,
        "type": "giant",
        "size": "large",
        "ac": 15,
        "hp": 84,
        "hp_dice": "8d10+40",
        "speed": 30,
        "str": 18, "dex": 13, "con": 20, "int": 7, "wis": 9, "cha": 7,
        "attacks": [
            {
                "name": "Bite",
                "to_hit": 7,
                "reach": 5,
                "damage": "1d6+4",
                "damage_type": "piercing"
            },
            {
                "name": "Claw",
                "to_hit": 7,
                "reach": 5,
                "damage": "2d6+4",
                "damage_type": "slashing"
            }
        ],
        "traits": ["Regeneration (10 HP per turn, disabled by fire/acid)", "Keen Smell"],
        "description": "A hunched, green-skinned monstrosity with long arms and incredible regenerative abilities."
    },

    # ========================================================================
    # CR 6+ - High Level Threats
    # ========================================================================
    "Young White Dragon": {
        "name": "Young White Dragon",
        "cr": 6,
        "type": "dragon",
        "size": "large",
        "ac": 17,
        "hp": 133,
        "hp_dice": "14d10+56",
        "speed": 40,
        "str": 18, "dex": 10, "con": 18, "int": 6, "wis": 11, "cha": 12,
        "attacks": [
            {
                "name": "Bite",
                "to_hit": 7,
                "reach": 10,
                "damage": "2d10+4",
                "damage_type": "piercing",
                "special": "+1d8 cold damage"
            },
            {
                "name": "Claw",
                "to_hit": 7,
                "reach": 5,
                "damage": "2d6+4",
                "damage_type": "slashing"
            },
            {
                "name": "Cold Breath (Recharge 5-6)",
                "to_hit": "auto",
                "reach": 30,
                "damage": "10d8",
                "damage_type": "cold",
                "special": "60-foot cone, DC 15 CON save for half damage"
            }
        ],
        "traits": ["Ice Walk", "Immune to cold", "Darkvision 120 ft", "Blindsight 30 ft"],
        "description": "A fearsome dragon with scales like ice and breath that freezes flesh solid."
    },

    "Chimera": {
        "name": "Chimera",
        "cr": 6,
        "type": "monstrosity",
        "size": "large",
        "ac": 14,
        "hp": 114,
        "hp_dice": "12d10+48",
        "speed": 30,
        "str": 19, "dex": 11, "con": 19, "int": 3, "wis": 14, "cha": 10,
        "attacks": [
            {
                "name": "Bite (Lion)",
                "to_hit": 7,
                "reach": 5,
                "damage": "2d6+4",
                "damage_type": "piercing"
            },
            {
                "name": "Horns (Goat)",
                "to_hit": 7,
                "reach": 5,
                "damage": "2d8+4",
                "damage_type": "bludgeoning"
            },
            {
                "name": "Fire Breath (Dragon Head, Recharge 5-6)",
                "to_hit": "auto",
                "reach": 15,
                "damage": "7d8",
                "damage_type": "fire",
                "special": "15-foot cone, DC 15 DEX save for half"
            }
        ],
        "traits": ["Three heads (advantage on Perception)", "Flying speed 60 ft"],
        "description": "A horrific fusion of lion, goat, and dragon - a three-headed monstrosity breathing fire."
    },

    # ========================================================================
    # CR 13+ - Epic Threats
    # ========================================================================
    "Adult Red Dragon": {
        "name": "Adult Red Dragon",
        "cr": 17,
        "type": "dragon",
        "size": "huge",
        "ac": 19,
        "hp": 256,
        "hp_dice": "19d12+133",
        "speed": 40,
        "str": 27, "dex": 10, "con": 25, "int": 16, "wis": 13, "cha": 21,
        "attacks": [
            {
                "name": "Bite",
                "to_hit": 14,
                "reach": 10,
                "damage": "2d10+8",
                "damage_type": "piercing",
                "special": "+2d6 fire damage"
            },
            {
                "name": "Claw",
                "to_hit": 14,
                "reach": 5,
                "damage": "2d6+8",
                "damage_type": "slashing"
            },
            {
                "name": "Tail",
                "to_hit": 14,
                "reach": 15,
                "damage": "2d8+8",
                "damage_type": "bludgeoning"
            },
            {
                "name": "Fire Breath (Recharge 5-6)",
                "to_hit": "auto",
                "reach": 60,
                "damage": "18d6",
                "damage_type": "fire",
                "special": "60-foot cone, DC 21 DEX save for half"
            }
        ],
        "traits": ["Legendary Resistance (3/day)", "Frightful Presence (DC 19 WIS save)", "Immune to fire", "Legendary Actions"],
        "description": "A colossal dragon with crimson scales like molten metal, greed burning in its ancient eyes."
    },

    "Vampire": {
        "name": "Vampire",
        "cr": 13,
        "type": "undead",
        "size": "medium",
        "ac": 16,
        "hp": 144,
        "hp_dice": "17d8+68",
        "speed": 30,
        "str": 18, "dex": 18, "con": 18, "int": 17, "wis": 15, "cha": 18,
        "attacks": [
            {
                "name": "Unarmed Strike",
                "to_hit": 9,
                "reach": 5,
                "damage": "1d8+4",
                "damage_type": "bludgeoning",
                "special": "+4d6 necrotic damage, grapple"
            },
            {
                "name": "Bite",
                "to_hit": 9,
                "reach": 5,
                "damage": "1d6+4",
                "damage_type": "piercing",
                "special": "+3d6 necrotic damage, reduces max HP"
            }
        ],
        "traits": ["Shapechanger", "Legendary Resistance (3/day)", "Regeneration (20 HP/turn)", "Spider Climb", "Charm", "Misty Escape"],
        "description": "An undead aristocrat with pale skin, hypnotic eyes, and an insatiable thirst for blood."
    },
}


def get_monster_stat(monster_name: str) -> MonsterStat:
    """
    Get monster stat block by name (case-insensitive).

    Args:
        monster_name: Name of the monster

    Returns:
        Monster stat dictionary, or None if not found
    """
    # Case-insensitive lookup
    for name, stats in MONSTER_STATS.items():
        if name.lower() == monster_name.lower():
            return stats.copy()  # Return a copy to avoid mutations

    return None


def get_monsters_by_cr(min_cr: float = 0, max_cr: float = 30) -> List[MonsterStat]:
    """
    Get all monsters within a CR range.

    Args:
        min_cr: Minimum challenge rating
        max_cr: Maximum challenge rating

    Returns:
        List of monster stat dictionaries
    """
    monsters = []
    for name, stats in MONSTER_STATS.items():
        if min_cr <= stats["cr"] <= max_cr:
            monsters.append(stats.copy())

    return monsters


def get_all_monster_names() -> List[str]:
    """Get list of all available monster names."""
    return list(MONSTER_STATS.keys())


# Quick test
if __name__ == "__main__":
    print("🎲 D&D 5e Monster Stats Database\n")
    print(f"Total monsters: {len(MONSTER_STATS)}\n")

    # Test CR grouping
    for cr in [0, 0.25, 0.5, 1, 2, 5, 6, 13]:
        monsters = get_monsters_by_cr(cr, cr)
        if monsters:
            print(f"CR {cr}: {', '.join([m['name'] for m in monsters])}")

    # Test lookup
    print("\n🐺 Goblin Stats:")
    goblin = get_monster_stat("Goblin")
    if goblin:
        print(f"  HP: {goblin['hp']} ({goblin['hp_dice']})")
        print(f"  AC: {goblin['ac']}")
        print(f"  Attacks: {[a['name'] for a in goblin['attacks']]}")
