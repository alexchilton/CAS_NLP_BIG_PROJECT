"""
Magic Item Manager

Handles magic item lookups, effects, and integration with character state.
"""

from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.data.magic_items import (
    get_magic_item,
    get_items_by_rarity,
    get_items_by_type,
    requires_attunement,
    get_all_item_names,
    MagicItem
)


class MagicItemManager:
    """Manages magic items and their effects on characters."""

    def __init__(self):
        """Initialize the magic item manager."""
        pass

    def lookup_item(self, item_name: str) -> Optional[MagicItem]:
        """
        Look up a magic item by name.

        Args:
            item_name: Name of the item to look up

        Returns:
            Magic item dictionary or None if not found
        """
        return get_magic_item(item_name)

    def get_by_rarity(self, rarity: str) -> List[MagicItem]:
        """
        Get all items of a specific rarity.

        Args:
            rarity: Item rarity (common, uncommon, rare, very rare, legendary)

        Returns:
            List of magic items
        """
        return get_items_by_rarity(rarity)

    def get_by_type(self, item_type: str) -> List[MagicItem]:
        """
        Get all items of a specific type.

        Args:
            item_type: Item type (ring, armor, weapon, wondrous, potion)

        Returns:
            List of magic items
        """
        return get_items_by_type(item_type)

    def requires_attunement(self, item_name: str) -> bool:
        """
        Check if an item requires attunement.

        Args:
            item_name: Name of the item

        Returns:
            True if attunement required, False otherwise
        """
        return requires_attunement(item_name)

    def get_all_items(self) -> List[str]:
        """
        Get list of all available magic item names.

        Returns:
            List of item names
        """
        return get_all_item_names()

    def apply_item_effects(self, character_state: Any, item: MagicItem) -> Dict[str, Any]:
        """
        Calculate the effects of a magic item on a character.

        Args:
            character_state: Character state object
            item: Magic item dictionary

        Returns:
            Dictionary of effects applied
        """
        effects_applied = {}
        item_effects = item.get("effects", {})

        # AC bonus
        if "ac_bonus" in item_effects:
            effects_applied["ac_bonus"] = item_effects["ac_bonus"]

        # Saving throw bonus
        if "saving_throw_bonus" in item_effects:
            effects_applied["saving_throw_bonus"] = item_effects["saving_throw_bonus"]

        # Attack bonus (weapons)
        if "attack_bonus" in item_effects:
            effects_applied["attack_bonus"] = item_effects["attack_bonus"]

        # Damage bonus (weapons)
        if "damage_bonus" in item_effects:
            effects_applied["damage_bonus"] = item_effects["damage_bonus"]

        # Additional damage (elemental weapons)
        if "fire_damage" in item_effects:
            effects_applied["extra_damage"] = {
                "type": "fire",
                "dice": item_effects["fire_damage"]
            }
        elif "cold_damage" in item_effects:
            effects_applied["extra_damage"] = {
                "type": "cold",
                "dice": item_effects["cold_damage"]
            }

        # Resistance
        if "resistance" in item_effects:
            effects_applied["resistance"] = item_effects["resistance"]

        # Fire resistance (from specific items like Frost Brand)
        if "fire_resistance" in item_effects:
            effects_applied["fire_resistance"] = True

        # Stealth advantage
        if "stealth_advantage" in item_effects:
            effects_applied["stealth_advantage"] = True

        # Speed modifiers
        if "speed_double" in item_effects:
            effects_applied["speed_double"] = True

        # Flying speed
        if "flying_speed" in item_effects:
            effects_applied["flying_speed"] = item_effects["flying_speed"]

        # Invisibility
        if "invisibility" in item_effects:
            effects_applied["invisibility"] = True

        # Temp HP (potions)
        if "temp_hp" in item_effects:
            effects_applied["temp_hp"] = item_effects["temp_hp"]

        # Healing (potions)
        if "healing" in item_effects:
            effects_applied["healing"] = item_effects["healing"]

        return effects_applied

    def can_equip_item(self, character_state: Any, item: MagicItem, equipped_items: List[str]) -> tuple[bool, str]:
        """
        Check if a character can equip an item.

        Args:
            character_state: Character state object
            item: Magic item to equip
            equipped_items: List of currently equipped item names

        Returns:
            Tuple of (can_equip: bool, reason: str)
        """
        # Check attunement limit
        if item.get("attunement", False):
            # Count currently attuned items
            attuned_count = 0
            for equipped_name in equipped_items:
                equipped_item = get_magic_item(equipped_name)
                if equipped_item and equipped_item.get("attunement", False):
                    attuned_count += 1

            if attuned_count >= 3:
                return False, "You can only attune to 3 items at a time. Unequip an attuned item first."

        # Check item type conflicts (can't wear two rings on same hand, etc.)
        item_type = item.get("type", "")

        if item_type == "ring":
            # Count rings
            ring_count = sum(1 for name in equipped_items if get_magic_item(name) and get_magic_item(name).get("type") == "ring")
            if ring_count >= 2:
                return False, "You can only wear 2 rings at a time."

        elif item_type == "armor":
            # Check if already wearing armor
            for equipped_name in equipped_items:
                equipped = get_magic_item(equipped_name)
                if equipped and equipped.get("type") == "armor":
                    return False, f"You are already wearing {equipped_name}. Unequip it first."

        elif item_type == "wondrous":
            # Check for slot conflicts (boots, cloak, gloves)
            item_name_lower = item["name"].lower()
            for equipped_name in equipped_items:
                equipped_lower = equipped_name.lower()

                # Boots conflict
                if "boots" in item_name_lower and "boots" in equipped_lower:
                    return False, f"You are already wearing {equipped_name}."

                # Cloak conflict
                if "cloak" in item_name_lower and "cloak" in equipped_lower:
                    return False, f"You are already wearing {equipped_name}."

                # Gloves conflict
                if "gloves" in item_name_lower and "gloves" in equipped_lower:
                    return False, f"You are already wearing {equipped_name}."

        return True, "OK"

    def get_total_bonuses(self, equipped_items: List[str]) -> Dict[str, Any]:
        """
        Calculate total bonuses from all equipped items.

        Args:
            equipped_items: List of equipped item names

        Returns:
            Dictionary of total bonuses
        """
        total_bonuses = {
            "ac_bonus": 0,
            "saving_throw_bonus": 0,
            "attack_bonus": 0,
            "damage_bonus": 0,
            "resistances": [],
            "advantages": [],
            "extra_damage": []
        }

        for item_name in equipped_items:
            item = get_magic_item(item_name)
            if not item:
                continue

            effects = item.get("effects", {})

            # AC bonus (these stack from different items)
            if "ac_bonus" in effects:
                total_bonuses["ac_bonus"] += effects["ac_bonus"]

            # Saving throw bonus (these stack)
            if "saving_throw_bonus" in effects:
                total_bonuses["saving_throw_bonus"] += effects["saving_throw_bonus"]

            # Attack bonus (only highest applies, typically from weapon)
            if "attack_bonus" in effects:
                total_bonuses["attack_bonus"] = max(total_bonuses["attack_bonus"], effects["attack_bonus"])

            # Damage bonus (only highest applies)
            if "damage_bonus" in effects:
                total_bonuses["damage_bonus"] = max(total_bonuses["damage_bonus"], effects["damage_bonus"])

            # Resistances
            if "resistance" in effects:
                res_type = effects["resistance"]
                if res_type not in total_bonuses["resistances"]:
                    total_bonuses["resistances"].append(res_type)

            if "fire_resistance" in effects:
                if "fire" not in total_bonuses["resistances"]:
                    total_bonuses["resistances"].append("fire")

            # Advantages
            if "stealth_advantage" in effects:
                if "stealth" not in total_bonuses["advantages"]:
                    total_bonuses["advantages"].append("stealth")

            # Extra damage (from weapons like Flametongue)
            if "fire_damage" in effects:
                total_bonuses["extra_damage"].append({
                    "type": "fire",
                    "dice": effects["fire_damage"]
                })
            elif "cold_damage" in effects:
                total_bonuses["extra_damage"].append({
                    "type": "cold",
                    "dice": effects["cold_damage"]
                })

        return total_bonuses

    def consume_potion(self, potion_name: str) -> Optional[Dict[str, Any]]:
        """
        Use a potion and get its effects.

        Args:
            potion_name: Name of the potion

        Returns:
            Dictionary of effects, or None if not a potion
        """
        item = get_magic_item(potion_name)
        if not item or item.get("type") != "potion":
            return None

        effects = item.get("effects", {})
        result = {
            "name": potion_name,
            "effects": effects,
            "description": item.get("description", "")
        }

        return result


# Convenience function for quick lookups
def lookup_magic_item(item_name: str) -> Optional[MagicItem]:
    """
    Quick lookup function for magic items.

    Args:
        item_name: Name of the item

    Returns:
        Magic item dictionary or None
    """
    return get_magic_item(item_name)


if __name__ == "__main__":
    # Quick test
    manager = MagicItemManager()

    print("🔮 Magic Item Manager Test\n")

    # Test lookup
    ring = manager.lookup_item("Ring of Protection")
    print(f"Ring of Protection: {ring['rarity']}, Attunement: {ring['attunement']}")

    # Test effects
    print(f"\nEffects: {manager.apply_item_effects(None, ring)}")

    # Test attunement check
    print(f"\nRequires attunement: {manager.requires_attunement('Ring of Protection')}")
    print(f"Bag of Holding attunement: {manager.requires_attunement('Bag of Holding')}")

    # Test can equip
    can_equip, reason = manager.can_equip_item(None, ring, [])
    print(f"\nCan equip Ring of Protection: {can_equip} ({reason})")

    # Test attunement limit
    equipped = ["Ring of Protection", "Ring of Spell Storing", "Boots of Speed"]
    cloak = manager.lookup_item("Cloak of Protection")
    can_equip, reason = manager.can_equip_item(None, cloak, equipped)
    print(f"Can equip 4th attuned item: {can_equip} ({reason})")

    # Test total bonuses
    equipped = ["Ring of Protection", "Cloak of Protection"]
    bonuses = manager.get_total_bonuses(equipped)
    print(f"\nTotal bonuses from {equipped}:")
    print(f"  AC: +{bonuses['ac_bonus']}")
    print(f"  Saves: +{bonuses['saving_throw_bonus']}")

    # Test potion
    potion_effects = manager.consume_potion("Potion of Healing")
    print(f"\nPotion of Healing: {potion_effects['effects']}")
