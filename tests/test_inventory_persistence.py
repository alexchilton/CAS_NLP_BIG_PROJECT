"""
Test inventory persistence across multiple commands.

This test verifies that items added to character_state.inventory
are properly maintained between multiple GM interactions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.systems.game_state import CharacterState


def test_inventory_persistence_across_commands():
    """
    Test that inventory persists correctly across multiple GM commands.

    Simulates:
    1. Create character with initial inventory
    2. Buy rope (adds to inventory)
    3. Verify rope is in inventory
    4. Sell rope (removes from inventory)
    5. Verify rope is NOT in inventory
    """
    print("\n" + "=" * 80)
    print("TEST: Inventory Persistence Across Commands")
    print("=" * 80)

    # Initialize systems
    db = ChromaDBManager()
    gm = GameMaster(db)

    # Create character state with initial inventory
    char_state = CharacterState(
        character_name="Test Hero",
        max_hp=30,
        level=3,
        gold=100
    )
    char_state.armor_class = 15

    # Set initial equipment (simulating Thorin's setup)
    char_state.inventory = {
        'Longsword': 1,
        'Shield': 1,
        'Plate Armor': 1,
        'Backpack': 1
    }

    # Attach character to GM session
    gm.session.character_state = char_state
    gm.set_context("Test Hero is in a marketplace")
    gm.set_location("The Market Square", "A bustling marketplace")

    # CRITICAL: Add merchant NPCs to enable shop transactions
    # The shop system requires either has_shop=True on location OR merchant NPCs present
    gm.session.npcs_present = ['Merchant', 'Shopkeeper']
    print(f"   Added NPCs for shop: {gm.session.npcs_present}")

    print(f"\n1️⃣ Initial Setup:")
    print(f"   Character: {char_state.character_name}")
    print(f"   Gold: {char_state.gold} GP")
    print(f"   Inventory: {char_state.inventory}")
    print(f"   Session character_state ID: {id(char_state)}")
    print(f"   GM session character_state ID: {id(gm.session.character_state)}")

    # Verify they're the same object
    assert gm.session.character_state is char_state, "Session character_state should be same object"
    print("   ✅ Character state attached correctly")

    # Step 2: Buy rope
    print(f"\n2️⃣ Buying rope...")
    buy_response = gm.generate_response("/buy rope", use_rag=False)

    print(f"   Response: {buy_response[:200]}...")
    print(f"   Gold after buy: {gm.session.character_state.gold} GP")
    print(f"   Inventory after buy: {gm.session.character_state.inventory}")

    # Verify purchase
    assert "rope" in gm.session.character_state.inventory, "Rope should be in inventory after purchase"
    assert gm.session.character_state.inventory["rope"] == 1, "Should have 1 rope"
    assert gm.session.character_state.gold == 99, f"Expected 99 GP, got {gm.session.character_state.gold}"
    print("   ✅ Rope successfully purchased and added to inventory")

    # CRITICAL: Check if character_state object changed
    print(f"   Session character_state ID after buy: {id(gm.session.character_state)}")
    if id(gm.session.character_state) != id(char_state):
        print("   ⚠️  WARNING: character_state object was replaced!")
        char_state = gm.session.character_state  # Update reference

    # Step 3: Verify rope persists before selling
    print(f"\n3️⃣ Checking inventory before sell:")
    print(f"   Inventory: {gm.session.character_state.inventory}")
    assert "rope" in gm.session.character_state.inventory, "Rope should still be in inventory"
    print("   ✅ Rope persisted in inventory")

    # Step 4: Sell rope
    print(f"\n4️⃣ Selling rope...")
    sell_response = gm.generate_response("/sell rope", use_rag=False)

    print(f"   Response: {sell_response[:200]}...")
    print(f"   Gold after sell: {gm.session.character_state.gold} GP")
    print(f"   Inventory after sell: {gm.session.character_state.inventory}")

    # Verify sale
    assert "rope" not in gm.session.character_state.inventory, "Rope should NOT be in inventory after sale"
    assert gm.session.character_state.gold == 99.5, f"Expected 99.5 GP (sold for 0.5), got {gm.session.character_state.gold}"
    print("   ✅ Rope successfully sold and removed from inventory")

    # Step 5: Final verification
    print(f"\n5️⃣ Final State:")
    print(f"   Gold: {gm.session.character_state.gold} GP")
    print(f"   Inventory: {gm.session.character_state.inventory}")
    print(f"   Session character_state ID: {id(gm.session.character_state)}")

    print("\n" + "=" * 80)
    print("✅ ALL INVENTORY PERSISTENCE TESTS PASSED!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        test_inventory_persistence_across_commands()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
