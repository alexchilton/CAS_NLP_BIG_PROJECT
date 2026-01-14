#!/usr/bin/env python3
"""
Quick integration test for equipment commands.

Tests that the equipment system can be integrated with the game without errors.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.systems.character_equipment import CharacterEquipment
from dnd_rag_system.systems.game_state import CharacterState

def test_equipment_integration():
    """Test that equipment commands work with character state."""
    print("🧪 Testing Equipment Integration\n")
    print("=" * 80)

    # Create a test character
    print("\n1. Creating test character...")
    char_state = CharacterState(
        character_name="Test Fighter",
        max_hp=45,
        current_hp=45,
        level=5
    )
    char_state.armor_class = 16
    char_state.speed = 30
    print("✅ Character created")

    # Add magic items to inventory
    print("\n2. Adding magic items to inventory...")
    char_state.add_item("Ring of Protection", 1)
    char_state.add_item("Cloak of Protection", 1)
    char_state.add_item("Potion of Healing", 2)
    char_state.add_item("+1 Longsword", 1)
    print(f"✅ Items added: {list(char_state.inventory.keys())}")

    # Create equipment manager
    print("\n3. Creating equipment manager...")
    equipment_manager = CharacterEquipment(char_state)
    print("✅ Equipment manager created")

    # Test /equipment command (when no items equipped)
    print("\n4. Testing /equipment command (no items equipped)...")
    summary = equipment_manager.get_equipment_summary()
    print(f"Result: {summary}")
    assert "No items equipped" in summary
    print("✅ /equipment works when no items equipped")

    # Test /equip command
    print("\n5. Testing /equip Ring of Protection...")
    initial_ac = char_state.armor_class
    success, msg = equipment_manager.equip_item("Ring of Protection")
    print(f"Success: {success}")
    print(f"Message: {msg}")
    assert success, f"Failed to equip: {msg}"
    assert char_state.armor_class == initial_ac + 1, f"AC didn't increase! Was {initial_ac}, now {char_state.armor_class}"
    print(f"✅ /equip works! AC increased from {initial_ac} to {char_state.armor_class}")

    # Test /equipment command (with items)
    print("\n6. Testing /equipment command (with items)...")
    summary = equipment_manager.get_equipment_summary()
    print(f"Result:\n{summary}")
    assert "Ring of Protection" in summary
    assert "1/3" in summary  # Check attunement count (format may vary)
    print("✅ /equipment shows equipped items")

    # Test equipping another item
    print("\n7. Testing /equip Cloak of Protection...")
    success, msg = equipment_manager.equip_item("Cloak of Protection")
    print(f"Success: {success}")
    print(f"Message: {msg}")
    assert success, f"Failed to equip: {msg}"
    print(f"✅ Equipped second item! AC now {char_state.armor_class}")

    # Test /unequip command
    print("\n8. Testing /unequip ring_left...")
    success, msg = equipment_manager.unequip_item("ring_left")
    print(f"Success: {success}")
    print(f"Message: {msg}")
    assert success, f"Failed to unequip: {msg}"
    print(f"✅ /unequip works! AC now {char_state.armor_class}")

    # Test using a potion
    print("\n9. Testing /use Potion of Healing...")
    success, msg, effects = equipment_manager.use_potion("Potion of Healing")
    print(f"Success: {success}")
    print(f"Message: {msg}")
    print(f"Effects: {effects}")
    assert success, f"Failed to use potion: {msg}"
    assert char_state.inventory.get("Potion of Healing", 0) == 1, "Potion not removed from inventory"
    print("✅ Potion usage works!")

    # Test error handling
    print("\n10. Testing error handling...")

    # Try to equip item not in inventory
    success, msg = equipment_manager.equip_item("Ring of Invisibility")
    print(f"Equip non-existent item: {success} - {msg}")
    assert not success, "Should fail when item not in inventory"
    print("✅ Error handling works for missing items")

    # Try to unequip empty slot
    success, msg = equipment_manager.unequip_item("ring_left")
    print(f"Unequip empty slot: {success} - {msg}")
    assert not success, "Should fail when slot is empty"
    print("✅ Error handling works for empty slots")

    print("\n" + "=" * 80)
    print("🎉 ALL INTEGRATION TESTS PASSED!")
    print("=" * 80)
    print("\nEquipment commands are ready to use in the game!")
    print("Next step: Run e2e tests with actual Gradio server")

if __name__ == "__main__":
    try:
        test_equipment_integration()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
