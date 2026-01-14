"""
D&D 5e Magic Items Database

Curated magic items organized by rarity.
Source: D&D 5e Dungeon Master's Guide

Each magic item has:
- name: Item name
- rarity: uncommon, rare, very rare, legendary
- attunement: Whether attunement is required
- type: Item type (ring, armor, weapon, wondrous, potion)
- effects: Mechanical effects (AC bonus, damage bonus, etc.)
- description: Full item description
- notes: Additional mechanics or restrictions
"""

from typing import Dict, List, Any

# Magic item type
MagicItem = Dict[str, Any]

MAGIC_ITEMS: Dict[str, MagicItem] = {
    # ========================================================================
    # RINGS
    # ========================================================================
    "Ring of Protection": {
        "name": "Ring of Protection",
        "rarity": "rare",
        "attunement": True,
        "type": "ring",
        "effects": {
            "ac_bonus": 1,
            "saving_throw_bonus": 1
        },
        "description": "You gain a +1 bonus to AC and saving throws while wearing this ring.",
        "notes": "One of the most versatile defensive items"
    },

    "Ring of Invisibility": {
        "name": "Ring of Invisibility",
        "rarity": "legendary",
        "attunement": True,
        "type": "ring",
        "effects": {
            "invisibility": True
        },
        "description": "While wearing this ring, you can turn invisible as an action. Anything you are wearing or carrying is invisible with you. You remain invisible until the ring is removed, until you attack or cast a spell, or until you use a bonus action to become visible again.",
        "notes": "Action to activate, bonus action to deactivate"
    },

    "Ring of Spell Storing": {
        "name": "Ring of Spell Storing",
        "rarity": "rare",
        "attunement": True,
        "type": "ring",
        "effects": {
            "spell_levels": 5
        },
        "description": "This ring stores spells cast into it, holding them until the attuned wearer uses them. The ring can store up to 5 levels worth of spells at a time. Any creature can cast a spell of 1st through 5th level into the ring by touching the ring as the spell is cast. The spell has no effect, other than to be stored in the ring.",
        "notes": "Can cast stored spells using original caster's spell save DC and attack bonus"
    },

    "Ring of Resistance": {
        "name": "Ring of Resistance",
        "rarity": "rare",
        "attunement": True,
        "type": "ring",
        "effects": {
            "resistance": "varies"  # acid, cold, fire, force, lightning, necrotic, poison, psychic, radiant, or thunder
        },
        "description": "You have resistance to one damage type while wearing this ring. The gem in the ring indicates the type, which the DM chooses or determines randomly.",
        "notes": "Type determined when found: acid, cold, fire, lightning, poison, etc."
    },

    "Ring of Feather Falling": {
        "name": "Ring of Feather Falling",
        "rarity": "rare",
        "attunement": True,
        "type": "ring",
        "effects": {
            "feather_fall": True
        },
        "description": "When you fall while wearing this ring, you descend 60 feet per round and take no damage from falling.",
        "notes": "Always active when worn"
    },

    # ========================================================================
    # WONDROUS ITEMS
    # ========================================================================
    "Bag of Holding": {
        "name": "Bag of Holding",
        "rarity": "uncommon",
        "attunement": False,
        "type": "wondrous",
        "effects": {
            "capacity_pounds": 500,
            "capacity_cubic_feet": 64
        },
        "description": "This bag has an interior space considerably larger than its outside dimensions, roughly 2 feet in diameter at the mouth and 4 feet deep. The bag can hold up to 500 pounds, not exceeding a volume of 64 cubic feet. The bag weighs 15 pounds, regardless of its contents. Retrieving an item from the bag requires an action.",
        "notes": "Placing bag inside another extradimensional space destroys both and opens gate to Astral Plane"
    },

    "Immovable Rod": {
        "name": "Immovable Rod",
        "rarity": "uncommon",
        "attunement": False,
        "type": "wondrous",
        "effects": {
            "dc_to_move": 30
        },
        "description": "This flat iron rod has a button on one end. You can use an action to press the button, which causes the rod to become magically fixed in place. Until you or another creature uses an action to push the button again, the rod doesn't move, even if it is defying gravity. The rod can hold up to 8,000 pounds of weight. More weight causes the rod to deactivate and fall. A creature can use an action to make a DC 30 Strength check, moving the fixed rod up to 10 feet on a success.",
        "notes": "Can support up to 8,000 pounds"
    },

    "Boots of Speed": {
        "name": "Boots of Speed",
        "rarity": "rare",
        "attunement": True,
        "type": "wondrous",
        "effects": {
            "speed_double": True,
            "duration": 10
        },
        "description": "While you wear these boots, you can use a bonus action and click the boots' heels together. If you do, the boots double your walking speed, and any creature that makes an opportunity attack against you has disadvantage on the attack roll. If you click your heels together again, you end the effect. When the boots' property has been used for a total of 10 minutes, the magic ceases to function until you finish a long rest.",
        "notes": "10 minutes per long rest, bonus action to activate"
    },

    "Boots of Elvenkind": {
        "name": "Boots of Elvenkind",
        "rarity": "uncommon",
        "attunement": False,
        "type": "wondrous",
        "effects": {
            "stealth_advantage": True
        },
        "description": "While you wear these boots, your steps make no sound, regardless of the surface you are moving across. You also have advantage on Dexterity (Stealth) checks that rely on moving silently.",
        "notes": "Always active when worn"
    },

    "Cloak of Elvenkind": {
        "name": "Cloak of Elvenkind",
        "rarity": "uncommon",
        "attunement": True,
        "type": "wondrous",
        "effects": {
            "stealth_advantage": True,
            "perception_disadvantage_vs_you": True
        },
        "description": "While you wear this cloak with its hood up, Wisdom (Perception) checks made to see you have disadvantage, and you have advantage on Dexterity (Stealth) checks made to hide, as the cloak's color shifts to camouflage you. Pulling the hood up or down requires an action.",
        "notes": "Must have hood up, action to activate"
    },

    "Cloak of Protection": {
        "name": "Cloak of Protection",
        "rarity": "uncommon",
        "attunement": True,
        "type": "wondrous",
        "effects": {
            "ac_bonus": 1,
            "saving_throw_bonus": 1
        },
        "description": "You gain a +1 bonus to AC and saving throws while you wear this cloak.",
        "notes": "Does not stack with Ring of Protection (both provide same bonus type)"
    },

    "Rope of Climbing": {
        "name": "Rope of Climbing",
        "rarity": "uncommon",
        "attunement": False,
        "type": "wondrous",
        "effects": {
            "length": 60,
            "animated": True
        },
        "description": "This 60-foot length of silk rope weighs 3 pounds and can hold up to 3,000 pounds. If you hold one end of the rope and use an action to speak the command word, the rope animates. As a bonus action, you can command the other end to move toward a destination you choose. That end moves 10 feet on your turn when you first command it and 10 feet on each of your turns until reaching its destination, up to its maximum length away, or until you tell it to stop.",
        "notes": "Can animate to climb surfaces, tie/untie itself on command"
    },

    "Gloves of Missile Snaring": {
        "name": "Gloves of Missile Snaring",
        "rarity": "uncommon",
        "attunement": True,
        "type": "wondrous",
        "effects": {
            "catch_missiles": True
        },
        "description": "These gloves seem to almost meld into your hands when you don them. When a ranged weapon attack hits you while you're wearing them, you can use your reaction to reduce the damage by 1d10 + your Dexterity modifier, provided that you have a free hand. If you reduce the damage to 0, you can catch the missile if it is small enough for you to hold in that hand.",
        "notes": "Reaction to catch projectiles"
    },

    # ========================================================================
    # MAGIC WEAPONS
    # ========================================================================
    "Weapon +1": {
        "name": "Weapon +1",
        "rarity": "uncommon",
        "attunement": False,
        "type": "weapon",
        "effects": {
            "attack_bonus": 1,
            "damage_bonus": 1
        },
        "description": "You have a +1 bonus to attack and damage rolls made with this magic weapon.",
        "notes": "Any weapon type: sword, bow, axe, etc."
    },

    "Weapon +2": {
        "name": "Weapon +2",
        "rarity": "rare",
        "attunement": False,
        "type": "weapon",
        "effects": {
            "attack_bonus": 2,
            "damage_bonus": 2
        },
        "description": "You have a +2 bonus to attack and damage rolls made with this magic weapon.",
        "notes": "Any weapon type: sword, bow, axe, etc."
    },

    "Weapon +3": {
        "name": "Weapon +3",
        "rarity": "very rare",
        "attunement": False,
        "type": "weapon",
        "effects": {
            "attack_bonus": 3,
            "damage_bonus": 3
        },
        "description": "You have a +3 bonus to attack and damage rolls made with this magic weapon.",
        "notes": "Any weapon type: sword, bow, axe, etc."
    },

    "Flametongue": {
        "name": "Flametongue",
        "rarity": "rare",
        "attunement": True,
        "type": "weapon",
        "effects": {
            "fire_damage": "2d6",
            "ignite_action": True
        },
        "description": "You can use a bonus action to speak this magic sword's command word, causing flames to erupt from the blade. These flames shed bright light in a 40-foot radius and dim light for an additional 40 feet. While the sword is ablaze, it deals an extra 2d6 fire damage to any target it hits. The flames last until you use a bonus action to speak the command word again or until you drop or sheathe the sword.",
        "notes": "Bonus action to activate/deactivate, +2d6 fire damage when active"
    },

    "Frost Brand": {
        "name": "Frost Brand",
        "rarity": "very rare",
        "attunement": True,
        "type": "weapon",
        "effects": {
            "cold_damage": "1d6",
            "fire_resistance": True,
            "cold_immunity_aura": True
        },
        "description": "When you hit with an attack using this magic sword, the target takes an extra 1d6 cold damage. In addition, while you hold the sword, you have resistance to fire damage. In freezing temperatures, the blade sheds bright light in a 10-foot radius and dim light for an additional 10 feet. When you draw this weapon, you can extinguish all nonmagical flames within 30 feet of you.",
        "notes": "Always active cold damage, grants fire resistance"
    },

    "Vorpal Sword": {
        "name": "Vorpal Sword",
        "rarity": "legendary",
        "attunement": True,
        "type": "weapon",
        "effects": {
            "attack_bonus": 3,
            "damage_bonus": 3,
            "decapitate_on_20": True
        },
        "description": "You gain a +3 bonus to attack and damage rolls made with this magic weapon. In addition, the weapon ignores resistance to slashing damage. When you attack a creature that has at least one head with this weapon and roll a 20 on the attack roll, you cut off one of the creature's heads. The creature dies if it can't survive without the lost head.",
        "notes": "Decapitates on natural 20, ignores slashing resistance"
    },

    # ========================================================================
    # MAGIC ARMOR
    # ========================================================================
    "Armor +1": {
        "name": "Armor +1",
        "rarity": "rare",
        "attunement": False,
        "type": "armor",
        "effects": {
            "ac_bonus": 1
        },
        "description": "You have a +1 bonus to AC while wearing this armor.",
        "notes": "Any armor type: leather, chain mail, plate, etc."
    },

    "Armor +2": {
        "name": "Armor +2",
        "rarity": "very rare",
        "attunement": False,
        "type": "armor",
        "effects": {
            "ac_bonus": 2
        },
        "description": "You have a +2 bonus to AC while wearing this armor.",
        "notes": "Any armor type: leather, chain mail, plate, etc."
    },

    "Armor +3": {
        "name": "Armor +3",
        "rarity": "legendary",
        "attunement": False,
        "type": "armor",
        "effects": {
            "ac_bonus": 3
        },
        "description": "You have a +3 bonus to AC while wearing this armor.",
        "notes": "Any armor type: leather, chain mail, plate, etc."
    },

    "Armor of Resistance": {
        "name": "Armor of Resistance",
        "rarity": "rare",
        "attunement": True,
        "type": "armor",
        "effects": {
            "resistance": "varies"
        },
        "description": "You have resistance to one type of damage while you wear this armor. The DM chooses the type or determines it randomly from the options below: acid, cold, fire, force, lightning, necrotic, poison, psychic, radiant, or thunder.",
        "notes": "Resistance type determined when found"
    },

    "Mithral Armor": {
        "name": "Mithral Armor",
        "rarity": "uncommon",
        "attunement": False,
        "type": "armor",
        "effects": {
            "no_stealth_disadvantage": True,
            "no_strength_requirement": True
        },
        "description": "Mithral is a light, flexible metal. A mithral chain shirt or breastplate can be worn under normal clothes. If the armor normally imposes disadvantage on Dexterity (Stealth) checks or has a Strength requirement, the mithral version of the armor doesn't.",
        "notes": "Medium or heavy armor only, removes stealth disadvantage and STR requirement"
    },

    # ========================================================================
    # POTIONS
    # ========================================================================
    "Potion of Healing": {
        "name": "Potion of Healing",
        "rarity": "common",
        "attunement": False,
        "type": "potion",
        "effects": {
            "healing": "2d4+2"
        },
        "description": "You regain 2d4 + 2 hit points when you drink this potion. The potion's red liquid glimmers when agitated.",
        "notes": "Action to drink, single use"
    },

    "Potion of Greater Healing": {
        "name": "Potion of Greater Healing",
        "rarity": "uncommon",
        "attunement": False,
        "type": "potion",
        "effects": {
            "healing": "4d4+4"
        },
        "description": "You regain 4d4 + 4 hit points when you drink this potion.",
        "notes": "Action to drink, single use"
    },

    "Potion of Invisibility": {
        "name": "Potion of Invisibility",
        "rarity": "very rare",
        "attunement": False,
        "type": "potion",
        "effects": {
            "invisibility": True,
            "duration": 60  # 1 hour in minutes
        },
        "description": "When you drink this potion, you become invisible for 1 hour. Anything you wear or carry is invisible with you. The effect ends early if you attack or cast a spell.",
        "notes": "1 hour duration, ends if you attack or cast spell"
    },

    "Potion of Flying": {
        "name": "Potion of Flying",
        "rarity": "very rare",
        "attunement": False,
        "type": "potion",
        "effects": {
            "flying_speed": 60,
            "duration": 60  # 1 hour in minutes
        },
        "description": "When you drink this potion, you gain a flying speed equal to your walking speed for 1 hour and can hover. If you're in the air when the potion wears off, you fall unless you have some other means of staying aloft.",
        "notes": "1 hour duration, flying speed = walking speed"
    },

    "Potion of Heroism": {
        "name": "Potion of Heroism",
        "rarity": "rare",
        "attunement": False,
        "type": "potion",
        "effects": {
            "temp_hp": 10,
            "bless": True,
            "duration": 60  # 1 hour in minutes
        },
        "description": "For 1 hour after drinking it, you gain 10 temporary hit points that last for 1 hour. For the same duration, you are under the effect of the bless spell (no concentration required).",
        "notes": "10 temp HP + bless effect for 1 hour, no concentration"
    },

    "Potion of Fire Breath": {
        "name": "Potion of Fire Breath",
        "rarity": "uncommon",
        "attunement": False,
        "type": "potion",
        "effects": {
            "breath_weapon_uses": 3,
            "breath_damage": "4d6",
            "breath_dc": 13
        },
        "description": "After drinking this potion, you can use a bonus action to exhale fire at a target within 30 feet of you. The target must make a DC 13 Dexterity saving throw, taking 4d6 fire damage on a failed save, or half as much damage on a successful one. The effect ends after you exhale the fire three times or when 1 hour has passed.",
        "notes": "3 uses or 1 hour, bonus action, DC 13 DEX save, 4d6 fire damage"
    },
}


def get_magic_item(item_name: str) -> MagicItem:
    """
    Get magic item by name (case-insensitive).

    Args:
        item_name: Name of the magic item

    Returns:
        Magic item dictionary, or None if not found
    """
    # Case-insensitive lookup
    for name, item in MAGIC_ITEMS.items():
        if name.lower() == item_name.lower():
            return item.copy()  # Return a copy to avoid mutations

    return None


def get_items_by_rarity(rarity: str) -> List[MagicItem]:
    """
    Get all magic items of a specific rarity.

    Args:
        rarity: Item rarity (common, uncommon, rare, very rare, legendary)

    Returns:
        List of magic item dictionaries
    """
    items = []
    for name, item in MAGIC_ITEMS.items():
        if item["rarity"].lower() == rarity.lower():
            items.append(item.copy())

    return items


def get_items_by_type(item_type: str) -> List[MagicItem]:
    """
    Get all magic items of a specific type.

    Args:
        item_type: Item type (ring, armor, weapon, wondrous, potion)

    Returns:
        List of magic item dictionaries
    """
    items = []
    for name, item in MAGIC_ITEMS.items():
        if item["type"].lower() == item_type.lower():
            items.append(item.copy())

    return items


def requires_attunement(item_name: str) -> bool:
    """
    Check if an item requires attunement.

    Args:
        item_name: Name of the magic item

    Returns:
        True if attunement required, False otherwise
    """
    item = get_magic_item(item_name)
    if item:
        return item.get("attunement", False)
    return False


def get_all_item_names() -> List[str]:
    """Get list of all available magic item names."""
    return list(MAGIC_ITEMS.keys())


# Quick test
if __name__ == "__main__":
    print("✨ D&D 5e Magic Items Database\n")
    print(f"Total items: {len(MAGIC_ITEMS)}\n")

    # Test by rarity
    for rarity in ["common", "uncommon", "rare", "very rare", "legendary"]:
        items = get_items_by_rarity(rarity)
        if items:
            print(f"{rarity.title()}: {len(items)} items")
            print(f"  {', '.join([i['name'] for i in items])}")

    # Test by type
    print("\n📦 By Type:")
    for item_type in ["ring", "wondrous", "weapon", "armor", "potion"]:
        items = get_items_by_type(item_type)
        print(f"  {item_type.title()}: {len(items)} items")

    # Test lookup
    print("\n💍 Ring of Protection:")
    ring = get_magic_item("Ring of Protection")
    if ring:
        print(f"  Rarity: {ring['rarity']}")
        print(f"  Attunement: {ring['attunement']}")
        print(f"  Effects: {ring['effects']}")
