"""
D&D 5e Class Features Database

Core class features for Rogue, Fighter, Wizard, and Cleric (levels 1-20).
Source: D&D 5e Player's Handbook

Each class has:
- hit_dice: Hit die type (d6, d8, d10, d12)
- primary_ability: Main ability score
- saving_throw_proficiencies: Proficient saves
- features_by_level: Dictionary of features gained at each level
"""

from typing import Dict, List, Any

# Class feature type
ClassData = Dict[str, Any]

CLASS_FEATURES: Dict[str, ClassData] = {
    # ========================================================================
    # ROGUE - The Cunning Striker
    # ========================================================================
    "Rogue": {
        "hit_dice": "d8",
        "primary_ability": "dexterity",
        "saving_throw_proficiencies": ["dexterity", "intelligence"],
        "features_by_level": {
            1: [
                {
                    "name": "Sneak Attack",
                    "damage_by_level": {
                        1: "1d6", 3: "2d6", 5: "3d6", 7: "4d6", 9: "5d6",
                        11: "6d6", 13: "7d6", 15: "8d6", 17: "9d6", 19: "10d6"
                    },
                    "trigger": "advantage on attack roll OR ally within 5 feet of target",
                    "frequency": "once per turn",
                    "weapon_restriction": "finesse or ranged weapon",
                    "description": "Once per turn, deal extra damage to one creature you hit with an attack if you have advantage on the attack roll. The attack must use a finesse or ranged weapon. You don't need advantage if another enemy of the target is within 5 feet of it, that enemy isn't incapacitated, and you don't have disadvantage on the attack roll."
                },
                {
                    "name": "Expertise",
                    "count": 2,
                    "level_upgrade": {1: 2, 6: 4},
                    "description": "Choose two of your skill proficiencies. Your proficiency bonus is doubled for any ability check you make that uses either of the chosen proficiencies. At 6th level, you can choose two more."
                },
                {
                    "name": "Thieves' Cant",
                    "description": "You know thieves' cant, a secret mix of dialect, jargon, and code that allows you to hide messages in seemingly normal conversation."
                }
            ],
            2: [
                {
                    "name": "Cunning Action",
                    "usage": "bonus action",
                    "options": ["Dash", "Disengage", "Hide"],
                    "description": "Your quick thinking and agility allow you to move and act quickly. You can take a bonus action on each of your turns in combat. This action can be used only to take the Dash, Disengage, or Hide action."
                }
            ],
            3: [
                {
                    "name": "Roguish Archetype",
                    "description": "Choose an archetype: Thief, Assassin, or Arcane Trickster"
                }
            ],
            5: [
                {
                    "name": "Uncanny Dodge",
                    "usage": "reaction",
                    "trigger": "when attacker you can see hits you",
                    "effect": "halve damage",
                    "description": "When an attacker that you can see hits you with an attack, you can use your reaction to halve the attack's damage against you."
                }
            ],
            7: [
                {
                    "name": "Evasion",
                    "trigger": "Dexterity saving throw",
                    "effect": "take no damage on success, half on failure",
                    "description": "When you are subjected to an effect that allows you to make a Dexterity saving throw to take only half damage, you instead take no damage if you succeed on the saving throw, and only half damage if you fail."
                }
            ],
            11: [
                {
                    "name": "Reliable Talent",
                    "description": "Whenever you make an ability check that lets you add your proficiency bonus, you can treat a d20 roll of 9 or lower as a 10."
                }
            ]
        }
    },

    # ========================================================================
    # FIGHTER - The Master of Combat
    # ========================================================================
    "Fighter": {
        "hit_dice": "d10",
        "primary_ability": "strength or dexterity",
        "saving_throw_proficiencies": ["strength", "constitution"],
        "features_by_level": {
            1: [
                {
                    "name": "Fighting Style",
                    "options": ["Archery", "Defense", "Dueling", "Great Weapon Fighting", "Protection", "Two-Weapon Fighting"],
                    "description": "You adopt a particular style of fighting as your specialty. Choose one fighting style."
                },
                {
                    "name": "Second Wind",
                    "usage": "bonus action",
                    "uses": "1 per short or long rest",
                    "healing": "1d10 + fighter_level",
                    "description": "You have a limited well of stamina that you can draw on to protect yourself from harm. On your turn, you can use a bonus action to regain hit points equal to 1d10 + your fighter level. Once you use this feature, you must finish a short or long rest before you can use it again."
                }
            ],
            2: [
                {
                    "name": "Action Surge",
                    "usage": "once per turn",
                    "uses_by_level": {2: 1, 17: 2},
                    "recharge": "short or long rest",
                    "description": "You can push yourself beyond your normal limits for a moment. On your turn, you can take one additional action. Once you use this feature, you must finish a short or long rest before you can use it again. Starting at 17th level, you can use it twice before a rest, but only once on the same turn."
                }
            ],
            3: [
                {
                    "name": "Martial Archetype",
                    "description": "Choose an archetype: Champion, Battle Master, or Eldritch Knight"
                }
            ],
            5: [
                {
                    "name": "Extra Attack",
                    "attacks_by_level": {5: 2, 11: 3, 20: 4},
                    "description": "You can attack twice, instead of once, whenever you take the Attack action on your turn. The number of attacks increases to three when you reach 11th level and to four when you reach 20th level."
                }
            ],
            9: [
                {
                    "name": "Indomitable",
                    "usage": "reroll failed saving throw",
                    "uses_by_level": {9: 1, 13: 2, 17: 3},
                    "recharge": "long rest",
                    "description": "You can reroll a saving throw that you fail. If you do so, you must use the new roll, and you can't use this feature again until you finish a long rest. You can use this feature twice between long rests starting at 13th level and three times between long rests starting at 17th level."
                }
            ]
        }
    },

    # ========================================================================
    # WIZARD - The Master of the Arcane
    # ========================================================================
    "Wizard": {
        "hit_dice": "d6",
        "primary_ability": "intelligence",
        "saving_throw_proficiencies": ["intelligence", "wisdom"],
        "spellcasting_ability": "intelligence",
        "spell_slots_by_level": {
            1: {"1st": 2},
            2: {"1st": 3},
            3: {"1st": 4, "2nd": 2},
            4: {"1st": 4, "2nd": 3},
            5: {"1st": 4, "2nd": 3, "3rd": 2},
            6: {"1st": 4, "2nd": 3, "3rd": 3},
            7: {"1st": 4, "2nd": 3, "3rd": 3, "4th": 1},
            8: {"1st": 4, "2nd": 3, "3rd": 3, "4th": 2},
            9: {"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 1},
            10: {"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2},
        },
        "features_by_level": {
            1: [
                {
                    "name": "Spellcasting",
                    "spellcasting_ability": "Intelligence",
                    "spell_save_dc": "8 + proficiency_bonus + Intelligence_modifier",
                    "spell_attack_bonus": "proficiency_bonus + Intelligence_modifier",
                    "description": "As a student of arcane magic, you have a spellbook containing spells that show the first glimmerings of your true power."
                },
                {
                    "name": "Arcane Recovery",
                    "usage": "once per day during short rest",
                    "slots_recovered": "combined level <= half wizard level (rounded up)",
                    "restriction": "6th level or lower spell slots",
                    "description": "Once per day when you finish a short rest, you can recover some expended spell slots. The spell slots can have a combined level that is equal to or less than half your wizard level (rounded up), and none of the slots can be 6th level or higher."
                }
            ],
            2: [
                {
                    "name": "Arcane Tradition",
                    "description": "Choose an arcane tradition: School of Evocation, School of Abjuration, etc."
                }
            ],
            18: [
                {
                    "name": "Spell Mastery",
                    "description": "Choose one 1st-level and one 2nd-level wizard spell from your spellbook. You can cast those spells at their lowest level without expending a spell slot."
                }
            ],
            20: [
                {
                    "name": "Signature Spells",
                    "description": "Choose two 3rd-level wizard spells as your signature spells. You always have these spells prepared and can each cast once at 3rd level without expending a spell slot. You regain the ability to do so when you finish a short or long rest."
                }
            ]
        }
    },

    # ========================================================================
    # CLERIC - The Divine Champion
    # ========================================================================
    "Cleric": {
        "hit_dice": "d8",
        "primary_ability": "wisdom",
        "saving_throw_proficiencies": ["wisdom", "charisma"],
        "spellcasting_ability": "wisdom",
        "spell_slots_by_level": {
            1: {"1st": 2},
            2: {"1st": 3},
            3: {"1st": 4, "2nd": 2},
            4: {"1st": 4, "2nd": 3},
            5: {"1st": 4, "2nd": 3, "3rd": 2},
            6: {"1st": 4, "2nd": 3, "3rd": 3},
            7: {"1st": 4, "2nd": 3, "3rd": 3, "4th": 1},
            8: {"1st": 4, "2nd": 3, "3rd": 3, "4th": 2},
            9: {"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 1},
            10: {"1st": 4, "2nd": 3, "3rd": 3, "4th": 3, "5th": 2},
        },
        "features_by_level": {
            1: [
                {
                    "name": "Spellcasting",
                    "spellcasting_ability": "Wisdom",
                    "spell_save_dc": "8 + proficiency_bonus + Wisdom_modifier",
                    "spell_attack_bonus": "proficiency_bonus + Wisdom_modifier",
                    "ritual_casting": True,
                    "description": "As a conduit for divine power, you can cast cleric spells."
                },
                {
                    "name": "Divine Domain",
                    "description": "Choose one domain: Life, Knowledge, Light, Nature, Tempest, Trickery, or War. Your choice grants you domain spells and other features."
                }
            ],
            2: [
                {
                    "name": "Channel Divinity",
                    "uses_by_level": {2: 1, 6: 2, 18: 3},
                    "recharge": "short or long rest",
                    "options": ["Turn Undead", "domain-specific options"],
                    "description": "You gain the ability to channel divine energy directly from your deity, using that energy to fuel magical effects."
                },
                {
                    "name": "Turn Undead",
                    "usage": "action, Channel Divinity",
                    "save": "Wisdom",
                    "dc": "spell save DC",
                    "duration": "1 minute or until damaged",
                    "description": "As an action, you present your holy symbol and speak a prayer. Each undead that can see or hear you within 30 feet must make a Wisdom saving throw. If the creature fails, it is turned for 1 minute or until it takes any damage."
                }
            ],
            5: [
                {
                    "name": "Destroy Undead",
                    "cr_destroyed_by_level": {5: "1/2", 8: "1", 11: "2", 14: "3", 17: "4"},
                    "trigger": "Turn Undead",
                    "description": "When an undead fails its saving throw against your Turn Undead feature, the creature is instantly destroyed if its challenge rating is at or below a certain threshold."
                }
            ],
            10: [
                {
                    "name": "Divine Intervention",
                    "usage": "action",
                    "success_chance": "percentile <= cleric_level",
                    "cooldown": "7 days on failure, none on success",
                    "description": "You can call on your deity to intervene on your behalf. Describe the assistance you seek, and roll percentile dice. If you roll a number equal to or lower than your cleric level, your deity intervenes."
                }
            ]
        }
    },

    # ========================================================================
    # BARBARIAN - The Furious Warrior
    # ========================================================================
    "Barbarian": {
        "hit_dice": "d12",
        "primary_ability": "strength",
        "saving_throw_proficiencies": ["strength", "constitution"],
        "features_by_level": {
            1: [
                {
                    "name": "Rage",
                    "usage": "bonus action",
                    "uses_by_level": {1: 2, 3: 3, 6: 4, 12: 5, 17: 6, 20: "unlimited"},
                    "damage_bonus_by_level": {1: 2, 9: 3, 16: 4},
                    "recharge": "long rest",
                    "duration": "1 minute",
                    "benefits": [
                        "Advantage on Strength checks and saves",
                        "Melee weapon damage bonus using Strength",
                        "Resistance to bludgeoning, piercing, slashing damage"
                    ],
                    "restrictions": [
                        "Can't cast spells",
                        "Can't concentrate on spells",
                        "Ends early if knocked unconscious or if you don't attack or take damage since last turn"
                    ],
                    "description": "In battle, you fight with primal ferocity. On your turn, you can enter a rage as a bonus action."
                },
                {
                    "name": "Unarmored Defense",
                    "ac_formula": "10 + Dexterity_modifier + Constitution_modifier",
                    "restriction": "not wearing armor, no shield restriction",
                    "description": "While you are not wearing armor, your Armor Class equals 10 + your Dexterity modifier + your Constitution modifier. You can use a shield and still gain this benefit."
                }
            ],
            2: [
                {
                    "name": "Reckless Attack",
                    "usage": "first attack on turn with Strength",
                    "benefit": "advantage on melee attack rolls using Strength",
                    "drawback": "attack rolls against you have advantage until next turn",
                    "description": "You can throw aside all concern for defense to attack with fierce desperation. When you make your first attack on your turn, you can decide to attack recklessly, giving you advantage on melee weapon attack rolls using Strength during this turn, but attack rolls against you have advantage until your next turn."
                },
                {
                    "name": "Danger Sense",
                    "trigger": "Dexterity saving throw against effect you can see",
                    "benefit": "advantage on save",
                    "restriction": "not blinded, deafened, or incapacitated",
                    "description": "You gain an uncanny sense of when things nearby aren't as they should be, giving you an edge when you dodge away from danger. You have advantage on Dexterity saving throws against effects that you can see."
                }
            ],
            5: [
                {
                    "name": "Extra Attack",
                    "attacks": 2,
                    "description": "You can attack twice, instead of once, whenever you take the Attack action on your turn."
                },
                {
                    "name": "Fast Movement",
                    "speed_bonus": 10,
                    "restriction": "not wearing heavy armor",
                    "description": "Your speed increases by 10 feet while you aren't wearing heavy armor."
                }
            ]
        }
    },

    # ========================================================================
    # PALADIN - The Holy Warrior
    # ========================================================================
    "Paladin": {
        "hit_dice": "d10",
        "primary_ability": "strength and charisma",
        "saving_throw_proficiencies": ["wisdom", "charisma"],
        "spellcasting_ability": "charisma",
        "spell_slots_by_level": {
            2: {"1st": 2},
            3: {"1st": 3},
            4: {"1st": 3},
            5: {"1st": 4, "2nd": 2},
            6: {"1st": 4, "2nd": 2},
            7: {"1st": 4, "2nd": 3},
            8: {"1st": 4, "2nd": 3},
            9: {"1st": 4, "2nd": 3, "3rd": 2},
            10: {"1st": 4, "2nd": 3, "3rd": 2},
        },
        "features_by_level": {
            1: [
                {
                    "name": "Divine Sense",
                    "usage": "action",
                    "uses": "1 + Charisma_modifier per long rest",
                    "range": "60 feet",
                    "duration": "until end of next turn",
                    "detects": ["celestials", "fiends", "undead", "consecrated/desecrated places"],
                    "description": "You can detect the presence of strong evil or good. Until the end of your next turn, you know the location of any celestial, fiend, or undead within 60 feet of you that is not behind total cover."
                },
                {
                    "name": "Lay on Hands",
                    "healing_pool": "paladin_level * 5",
                    "usage": "action, touch",
                    "recharge": "long rest",
                    "special": "can cure disease/poison for 5 HP",
                    "description": "You have a pool of healing power that replenishes when you take a long rest. With that pool, you can restore a total number of hit points equal to your paladin level × 5."
                }
            ],
            2: [
                {
                    "name": "Fighting Style",
                    "options": ["Defense", "Dueling", "Great Weapon Fighting", "Protection"],
                    "description": "You adopt a fighting style as your specialty."
                },
                {
                    "name": "Divine Smite",
                    "usage": "when you hit with melee weapon",
                    "cost": "spell slot (any level)",
                    "damage": "2d8 + 1d8 per spell level above 1st (max 5d8)",
                    "extra_damage": "+1d8 vs undead/fiends",
                    "description": "When you hit a creature with a melee weapon attack, you can expend one spell slot to deal radiant damage to the target, in addition to the weapon's damage. The extra damage is 2d8 for a 1st-level spell slot, plus 1d8 for each spell level higher than 1st, to a maximum of 5d8."
                }
            ],
            3: [
                {
                    "name": "Sacred Oath",
                    "description": "Choose an oath: Oath of Devotion, Oath of the Ancients, or Oath of Vengeance"
                },
                {
                    "name": "Channel Divinity",
                    "uses": "1 per short or long rest",
                    "description": "Your oath allows you to channel divine energy to fuel magical effects."
                }
            ],
            6: [
                {
                    "name": "Aura of Protection",
                    "range_by_level": {6: "10 feet", 18: "30 feet"},
                    "bonus": "Charisma_modifier to saves",
                    "description": "Whenever you or a friendly creature within 10 feet of you must make a saving throw, the creature gains a bonus to the saving throw equal to your Charisma modifier."
                }
            ]
        }
    }
}


def get_class_data(class_name: str) -> ClassData:
    """
    Get class data by name (case-insensitive).

    Args:
        class_name: Name of the class

    Returns:
        Class data dictionary, or None if not found
    """
    for name, data in CLASS_FEATURES.items():
        if name.lower() == class_name.lower():
            return data.copy()

    return None


def get_class_features_at_level(class_name: str, level: int) -> List[Dict]:
    """
    Get all features for a class at a specific level.

    Args:
        class_name: Name of the class
        level: Character level

    Returns:
        List of features gained at that level
    """
    class_data = get_class_data(class_name)
    if not class_data:
        return []

    features_by_level = class_data.get("features_by_level", {})
    return features_by_level.get(level, [])


def get_all_class_features(class_name: str, up_to_level: int = 20) -> Dict[int, List[Dict]]:
    """
    Get all features for a class up to a certain level.

    Args:
        class_name: Name of the class
        up_to_level: Maximum level to include (default 20)

    Returns:
        Dictionary mapping level to list of features
    """
    class_data = get_class_data(class_name)
    if not class_data:
        return {}

    features_by_level = class_data.get("features_by_level", {})
    return {
        level: features
        for level, features in features_by_level.items()
        if level <= up_to_level
    }


def get_available_classes() -> List[str]:
    """Get list of all available class names."""
    return list(CLASS_FEATURES.keys())


# Quick test
if __name__ == "__main__":
    print("⚔️  D&D 5e Class Features Database\n")
    print(f"Total classes: {len(CLASS_FEATURES)}\n")

    # Test each class
    for class_name in get_available_classes():
        class_data = get_class_data(class_name)
        print(f"📖 {class_name}:")
        print(f"   Hit Die: {class_data['hit_dice']}")
        print(f"   Primary: {class_data['primary_ability']}")
        print(f"   Saves: {', '.join(class_data['saving_throw_proficiencies'])}")

        # Level 1 features
        lvl1_features = get_class_features_at_level(class_name, 1)
        print(f"   Level 1: {', '.join([f['name'] for f in lvl1_features])}")
        print()

    # Test Rogue Sneak Attack scaling
    print("🗡️  Rogue Sneak Attack Damage:")
    rogue_data = get_class_data("Rogue")
    sneak_attack = rogue_data["features_by_level"][1][0]
    for level in [1, 3, 5, 7, 9, 11]:
        damage = sneak_attack["damage_by_level"].get(level, "N/A")
        print(f"   Level {level}: {damage}")
