"""
Character Equipment Integration

Integrates magic items with character state, handling equipping/unequipping
and automatic application of item bonuses.
"""

from typing import Dict, List, Optional, Tuple, Any
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.systems.magic_item_manager import MagicItemManager
from dnd_rag_system.systems.game_state import CharacterState


class CharacterEquipment:
    """Manages character equipment and magic item integration."""

    def __init__(self, character_state: CharacterState):
        """
        Initialize character equipment manager.

        Args:
            character_state: The character's game state
        """
        self.character = character_state
        self.item_manager = MagicItemManager()

    def equip_item(self, item_name: str) -> Tuple[bool, str]:
        """
        Equip a magic item from inventory.

        Args:
            item_name: Name of the item to equip

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Look up item data
        item = self.item_manager.lookup_item(item_name)
        if not item:
            return False, f"Item '{item_name}' not found in magic item database"

        # Check if item is in inventory (case-insensitive)
        # Find actual item name in inventory (may have different casing)
        actual_item_name = None
        for inv_item in self.character.inventory.keys():
            if inv_item.lower() == item_name.lower():
                actual_item_name = inv_item
                break

        if not actual_item_name:
            return False, f"You don't have '{item_name}' in your inventory"

        # Use actual item name from inventory for the rest of the function
        item_name = actual_item_name

        # Get currently equipped item names for validation
        equipped_item_names = list(self.character.equipped.values())

        # Check if can equip (attunement limit, slot conflicts, etc.)
        can_equip, reason = self.item_manager.can_equip_item(
            self.character,
            item,
            equipped_item_names
        )

        if not can_equip:
            return False, reason

        # Determine equipment slot
        slot = self._determine_slot(item)

        # If slot is occupied, unequip current item first
        if slot in self.character.equipped:
            old_item = self.character.equipped[slot]
            success, msg = self.unequip_item(slot)
            if not success:
                return False, f"Could not unequip {old_item}: {msg}"

        # Equip the item
        self.character.equip_item(slot, item_name)

        # Apply item effects
        self._apply_item_effects(item, apply=True)

        # Build success message
        message = f"✅ Equipped {item_name}"
        if item.get('attunement', False):
            message += " (attuned)"

        # Show effects
        effects_msg = self._format_item_effects(item)
        if effects_msg:
            message += f"\n{effects_msg}"

        return True, message

    def unequip_item(self, slot: str) -> Tuple[bool, str]:
        """
        Unequip an item from a slot.

        Args:
            slot: Equipment slot name

        Returns:
            Tuple of (success: bool, message: str)
        """
        if slot not in self.character.equipped:
            return False, f"No item equipped in slot '{slot}'"

        item_name = self.character.equipped[slot]
        item = self.item_manager.lookup_item(item_name)

        if not item:
            # Item not in database, just remove from equipped
            self.character.unequip_item(slot)
            return True, f"Unequipped {item_name}"

        # Remove item effects
        self._apply_item_effects(item, apply=False)

        # Unequip
        self.character.unequip_item(slot)

        return True, f"🔓 Unequipped {item_name}"

    def get_total_bonuses(self) -> Dict[str, Any]:
        """
        Calculate total bonuses from all equipped magic items.

        Returns:
            Dictionary of bonus types and values
        """
        equipped_item_names = list(self.character.equipped.values())
        return self.item_manager.get_total_bonuses(equipped_item_names)

    def get_equipment_summary(self) -> str:
        """
        Get a formatted summary of equipped items and bonuses.

        Returns:
            Formatted text summary
        """
        if not self.character.equipped:
            return "No items equipped"

        lines = ["**Equipped Items:**\n"]

        attuned_count = 0

        for slot, item_name in sorted(self.character.equipped.items()):
            item = self.item_manager.lookup_item(item_name)
            if item:
                line = f"• {slot.title()}: {item_name}"
                if item.get('attunement', False):
                    line += " ⭐ (attuned)"
                    attuned_count += 1
                lines.append(line)
            else:
                lines.append(f"• {slot.title()}: {item_name}")

        # Add attunement status
        lines.append(f"\n**Attunement:** {attuned_count}/3")

        # Add bonuses
        bonuses = self.get_total_bonuses()
        if bonuses:
            lines.append("\n**Total Bonuses:**")
            for bonus_type, value in sorted(bonuses.items()):
                bonus_name = bonus_type.replace('_', ' ').title()
                if isinstance(value, (int, float)) and value > 0:
                    lines.append(f"  +{value} {bonus_name}")
                else:
                    lines.append(f"  {value} {bonus_name}")

        return "\n".join(lines)

    def list_equippable_items(self) -> List[str]:
        """
        List all magic items in inventory that can be equipped.

        Returns:
            List of item names
        """
        equippable = []

        for item_name in self.character.inventory:
            item = self.item_manager.lookup_item(item_name)
            if item:
                # Check if it's an equippable item (not a potion)
                item_type = item.get('type', '')
                if item_type != 'potion':
                    equippable.append(item_name)

        return equippable

    def use_potion(self, potion_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Use a potion from inventory.

        Args:
            potion_name: Name of the potion

        Returns:
            Tuple of (success: bool, message: str, effects: Optional[Dict])
        """
        # Check if item is in inventory
        if potion_name not in self.character.inventory:
            return False, f"You don't have '{potion_name}' in your inventory", None

        # Look up potion
        potion = self.item_manager.lookup_item(potion_name)
        if not potion:
            return False, f"'{potion_name}' is not a recognized magic item", None

        if potion.get('type') != 'potion':
            return False, f"'{potion_name}' is not a potion", None

        # Get effects from the item (consume_potion returns full item dict)
        potion_data = self.item_manager.consume_potion(potion_name)
        if not potion_data or 'effects' not in potion_data:
            return False, f"Potion '{potion_name}' has no effects", None

        effects = potion_data['effects']

        # Remove from inventory
        self.character.remove_item(potion_name, 1)

        # Build message
        message = f"🧪 Used {potion_name}"

        # Apply healing if present
        if 'healing' in effects:
            healing_dice = effects['healing']
            # For now, we'll just show the dice - actual rolling would happen elsewhere
            message += f"\n  Heals: {healing_dice}"

        # Show other effects
        for effect_name, effect_value in effects.items():
            if effect_name != 'healing':
                effect_str = effect_name.replace('_', ' ').title()
                message += f"\n  {effect_str}: {effect_value}"

        return True, message, effects

    def check_attunement_slots(self) -> Tuple[int, int]:
        """
        Check how many attunement slots are used.

        Returns:
            Tuple of (used_slots: int, max_slots: int)
        """
        equipped_items = self._get_equipped_items_data()
        attuned_count = sum(
            1 for item in equipped_items
            if item.get('attunement', False)
        )
        return attuned_count, 3

    def _get_equipped_items_data(self) -> List[Dict]:
        """
        Get full data for all equipped items.

        Returns:
            List of item dictionaries
        """
        items = []
        for item_name in self.character.equipped.values():
            item = self.item_manager.lookup_item(item_name)
            if item:
                items.append(item)
        return items

    def _determine_slot(self, item: Dict) -> str:
        """
        Determine the equipment slot for an item.

        Args:
            item: Item dictionary

        Returns:
            Slot name
        """
        item_type = item.get('type', 'unknown').lower()
        item_name = item.get('name', '').lower()

        # Check name for specific slot types (some wondrous items)
        if 'cloak' in item_name:
            return 'back'
        elif 'boots' in item_name:
            return 'feet'
        elif 'gloves' in item_name or 'gauntlets' in item_name:
            return 'hands'
        elif 'helm' in item_name or 'helmet' in item_name:
            return 'head'
        elif 'amulet' in item_name or 'necklace' in item_name:
            return 'neck'
        elif 'belt' in item_name or 'girdle' in item_name:
            return 'waist'
        elif 'bracers' in item_name:
            return 'arms'

        # Map item types to slots
        slot_map = {
            'armor': 'armor',
            'weapon': 'main_hand',
            'shield': 'off_hand',
            'ring': self._next_ring_slot(),
            'amulet': 'neck',
            'boots': 'feet',
            'cloak': 'back',
            'gloves': 'hands',
            'helm': 'head',
            'belt': 'waist',
            'wand': 'main_hand',
            'staff': 'main_hand',
            'rod': 'main_hand',
            'wondrous': 'misc',  # Changed from 'wondrous item'
        }

        return slot_map.get(item_type, 'misc')

    def _next_ring_slot(self) -> str:
        """
        Find next available ring slot.

        Returns:
            'ring_left' or 'ring_right'
        """
        if 'ring_left' not in self.character.equipped:
            return 'ring_left'
        elif 'ring_right' not in self.character.equipped:
            return 'ring_right'
        else:
            return 'ring_left'  # Will trigger unequip

    def _apply_item_effects(self, item: Dict, apply: bool = True):
        """
        Apply or remove item effects to character.

        Args:
            item: Item dictionary
            apply: True to apply effects, False to remove
        """
        effects = item.get('effects', {})
        multiplier = 1 if apply else -1

        # AC bonus
        if 'ac_bonus' in effects:
            self.character.armor_class += effects['ac_bonus'] * multiplier

        # Saving throw bonus (applies to all saves)
        if 'saving_throw_bonus' in effects:
            bonus = effects['saving_throw_bonus'] * multiplier
            # In actual game, this would be tracked separately
            # For now, we don't modify ability scores directly
            pass

        # Attack bonus
        if 'attack_bonus' in effects:
            # Would be applied during attack rolls
            pass

        # Damage bonus
        if 'damage_bonus' in effects:
            # Would be applied during damage rolls
            pass

        # Speed bonus
        if 'speed_bonus' in effects:
            self.character.speed += effects['speed_bonus'] * multiplier

    def _format_item_effects(self, item: Dict) -> str:
        """
        Format item effects as a readable string.

        Args:
            item: Item dictionary

        Returns:
            Formatted effects string
        """
        effects = item.get('effects', {})
        if not effects:
            return ""

        lines = ["Effects:"]

        effect_names = {
            'ac_bonus': 'AC',
            'saving_throw_bonus': 'Saving Throws',
            'attack_bonus': 'Attack Rolls',
            'damage_bonus': 'Damage',
            'speed_bonus': 'Speed',
            'strength_bonus': 'Strength',
            'dexterity_bonus': 'Dexterity',
            'constitution_bonus': 'Constitution',
        }

        for effect_key, effect_value in effects.items():
            effect_name = effect_names.get(effect_key, effect_key.replace('_', ' ').title())
            if isinstance(effect_value, (int, float)) and effect_value > 0:
                lines.append(f"  +{effect_value} {effect_name}")
            else:
                lines.append(f"  {effect_value} {effect_name}")

        return "\n".join(lines)


# Convenience functions
def equip_magic_item(character: CharacterState, item_name: str) -> Tuple[bool, str]:
    """
    Quick function to equip an item.

    Args:
        character: Character state
        item_name: Name of item to equip

    Returns:
        Tuple of (success: bool, message: str)
    """
    equipment = CharacterEquipment(character)
    return equipment.equip_item(item_name)


def get_equipment_summary(character: CharacterState) -> str:
    """
    Quick function to get equipment summary.

    Args:
        character: Character state

    Returns:
        Formatted summary string
    """
    equipment = CharacterEquipment(character)
    return equipment.get_equipment_summary()


if __name__ == "__main__":
    # Quick test
    from dnd_rag_system.systems.game_state import CharacterState

    print("⚔️  Character Equipment Integration Test\n")

    # Create test character
    character = CharacterState(
        character_name="Test Fighter"
    )
    character.level = 5
    character.max_hp = 45
    character.current_hp = 45
    character.armor_class = 16
    character.speed = 30

    # Add some magic items to inventory
    character.add_item("Ring of Protection", 1)
    character.add_item("Cloak of Protection", 1)
    character.add_item("Potion of Healing", 2)
    character.add_item("+1 Longsword", 1)

    equipment = CharacterEquipment(character)

    print(f"Initial AC: {character.armor_class}")
    print(f"Initial Inventory: {list(character.inventory.keys())}\n")

    # Equip some items
    print("🎒 Equipping items...\n")

    success, msg = equipment.equip_item("Ring of Protection")
    print(f"{msg}\n")

    success, msg = equipment.equip_item("Cloak of Protection")
    print(f"{msg}\n")

    success, msg = equipment.equip_item("+1 Longsword")
    print(f"{msg}\n")

    # Show equipment summary
    print(equipment.get_equipment_summary())
    print()

    print(f"New AC: {character.armor_class}\n")

    # Check bonuses
    bonuses = equipment.get_total_bonuses()
    print("📊 Total Bonuses:")
    for bonus_type, value in bonuses.items():
        print(f"  {bonus_type}: +{value}")
    print()

    # Check attunement
    used, max_slots = equipment.check_attunement_slots()
    print(f"⭐ Attunement: {used}/{max_slots}\n")

    # Use a potion
    success, msg, effects = equipment.use_potion("Potion of Healing")
    print(f"{msg}")
    print(f"  Remaining in inventory: {character.inventory.get('Potion of Healing', 0)}\n")

    # Unequip an item
    success, msg = equipment.unequip_item("neck")
    print(f"{msg}")
    print(f"New AC: {character.armor_class}")
