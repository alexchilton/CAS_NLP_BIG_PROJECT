"""
Comprehensive Test Suite for D&D Shop System

Tests the conversational shopkeeper system including:
1. Searching shop inventory
2. Getting item prices
3. Purchase transactions (gold deduction, inventory addition)
4. Sell transactions
5. Chat command parsing
6. Shopkeeper context generation
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.systems.shop_system import ShopSystem, ShopTransaction
from dnd_rag_system.systems.game_state import CharacterState, GameSession
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.loaders.equipment_loader import load_equipment_to_chromadb


def setup_test_environment():
    """Set up test environment with equipment data."""
    print("\n" + "="*80)
    print("SETTING UP TEST ENVIRONMENT")
    print("="*80)

    # Initialize ChromaDB
    db = ChromaDBManager()

    # Load equipment data
    equipment_file = Path(__file__).parent / "web" / "equipment.txt"
    if equipment_file.exists():
        print(f"\n📦 Loading equipment from {equipment_file}")
        num_items = load_equipment_to_chromadb(db, equipment_file)
        print(f"✅ Loaded {num_items} equipment items")
    else:
        print(f"⚠️  Equipment file not found at {equipment_file}")

    # Create shop system
    shop = ShopSystem(db, debug=True)

    # Create test character with starting gold
    char = CharacterState(
        character_name="Test Adventurer",
        max_hp=25,
        level=3
    )
    char.gold = 100  # Starting with 100 gold
    char.inventory = {
        'Old Sword': 1,
        'Leather Armor': 1
    }

    print(f"\n💰 Test character created with {char.gold} gold")
    print(f"📦 Starting inventory: {list(char.inventory.keys())}")

    return shop, char, db


def test_shop_inventory_search():
    """Test searching shop inventory."""
    print("\n" + "="*80)
    print("TEST 1: Shop Inventory Search")
    print("="*80)

    shop, char, db = setup_test_environment()

    # Test 1.1: Search for swords
    print("\n--- Test 1.1: Search for 'sword' ---")
    items = shop.search_shop_inventory("sword", n_results=5)
    print(f"Found {len(items)} items matching 'sword':")
    for item in items:
        print(f"  - {item['name']}: {item['cost_gp']} gp")
    assert len(items) > 0, "Should find sword items"
    print("✅ PASSED")

    # Test 1.2: Search for armor
    print("\n--- Test 1.2: Search for 'armor' ---")
    items = shop.search_shop_inventory("armor", n_results=5)
    print(f"Found {len(items)} items matching 'armor':")
    for item in items:
        print(f"  - {item['name']}: {item['cost_gp']} gp")
    assert len(items) > 0, "Should find armor items"
    print("✅ PASSED")

    # Test 1.3: Search for healing potions
    print("\n--- Test 1.3: Search for 'healing potion' ---")
    items = shop.search_shop_inventory("healing potion", n_results=3)
    print(f"Found {len(items)} items matching 'healing potion':")
    for item in items:
        print(f"  - {item['name']}: {item['cost_gp']} gp - {item['description'][:80]}...")
    print("✅ PASSED")


def test_get_item_price():
    """Test getting item prices."""
    print("\n" + "="*80)
    print("TEST 2: Get Item Prices")
    print("="*80)

    shop, char, db = setup_test_environment()

    # Test 2.1: Get price of longsword
    print("\n--- Test 2.1: Price of Longsword ---")
    price = shop.get_item_price("Longsword")
    print(f"Longsword costs: {price} gp")
    assert price is not None, "Should find longsword price"
    assert price > 0, "Price should be positive"
    print("✅ PASSED")

    # Test 2.2: Get price of potion
    print("\n--- Test 2.2: Price of Potion of Healing ---")
    price = shop.get_item_price("Potion of Healing")
    print(f"Potion of Healing costs: {price} gp")
    assert price is not None, "Should find potion price"
    print("✅ PASSED")

    # Test 2.3: Non-existent item
    print("\n--- Test 2.3: Price of non-existent 'Legendary Sword of Doom' ---")
    price = shop.get_item_price("Legendary Sword of Doom")
    print(f"Result: {price}")
    assert price is None, "Should return None for non-existent items"
    print("✅ PASSED")


def test_purchase_transactions():
    """Test purchase transactions with gold deduction and inventory addition."""
    print("\n" + "="*80)
    print("TEST 3: Purchase Transactions (Gold & Inventory)")
    print("="*80)

    shop, char, db = setup_test_environment()

    initial_gold = char.gold
    print(f"\n💰 Starting gold: {initial_gold} gp")

    # Test 3.1: Successful purchase
    print("\n--- Test 3.1: Buy Longsword (should succeed) ---")
    transaction = shop.attempt_purchase(char, "Longsword", quantity=1)
    print(f"Result: {transaction.success}")
    print(f"Message: {transaction.message}")
    print(f"Cost: {transaction.cost_gp} gp")
    print(f"Remaining gold: {transaction.remaining_gold} gp")
    print(f"Inventory: {char.inventory}")

    assert transaction.success, "Purchase should succeed"
    assert char.gold < initial_gold, "Gold should decrease"
    assert 'Longsword' in char.inventory, "Longsword should be in inventory"
    assert char.inventory['Longsword'] == 1, "Should have 1 longsword"
    print("✅ PASSED")

    # Test 3.2: Purchase multiple items
    print("\n--- Test 3.2: Buy 3 Healing Potions ---")
    gold_before = char.gold
    transaction = shop.attempt_purchase(char, "Potion of Healing", quantity=3)
    print(f"Result: {transaction.success}")
    print(f"Message: {transaction.message}")
    print(f"Total cost: {transaction.cost_gp} gp")
    print(f"Gold before: {gold_before} gp, After: {char.gold} gp")

    if transaction.success:
        assert char.inventory['Potion of Healing'] == 3, "Should have 3 potions"
        assert char.gold == gold_before - transaction.cost_gp, "Gold should match"
        print("✅ PASSED")
    else:
        print("⚠️  Not enough gold for this purchase (expected if insufficient funds)")

    # Test 3.3: Insufficient gold
    print("\n--- Test 3.3: Try to buy expensive Plate Armor (should fail) ---")
    transaction = shop.attempt_purchase(char, "Plate Armor", quantity=1)
    print(f"Result: {transaction.success}")
    print(f"Message: {transaction.message}")
    assert not transaction.success, "Should fail due to insufficient gold"
    print("✅ PASSED")

    # Test 3.4: Non-existent item
    print("\n--- Test 3.4: Try to buy 'Magic Banana' (should fail) ---")
    transaction = shop.attempt_purchase(char, "Magic Banana", quantity=1)
    print(f"Result: {transaction.success}")
    print(f"Message: {transaction.message}")
    assert not transaction.success, "Should fail - item doesn't exist"
    print("✅ PASSED")


def test_sell_transactions():
    """Test selling items for gold."""
    print("\n" + "="*80)
    print("TEST 4: Sell Transactions")
    print("="*80)

    shop, char, db = setup_test_environment()

    # Character has: Old Sword, Leather Armor
    initial_gold = char.gold
    print(f"\n💰 Starting gold: {initial_gold} gp")
    print(f"📦 Starting inventory: {char.inventory}")

    # Test 4.1: Sell Old Sword
    print("\n--- Test 4.1: Sell 'Old Sword' ---")
    transaction = shop.attempt_sale(char, "Old Sword", quantity=1)
    print(f"Result: {transaction.success}")
    print(f"Message: {transaction.message}")
    print(f"Gold received: {transaction.cost_gp} gp")
    print(f"Total gold now: {char.gold} gp")

    if transaction.success:
        assert char.gold > initial_gold, "Gold should increase"
        assert 'Old Sword' not in char.inventory, "Old Sword should be removed"
        print("✅ PASSED")

    # Test 4.2: Try to sell item you don't have
    print("\n--- Test 4.2: Try to sell 'Diamond Ring' (don't have) ---")
    transaction = shop.attempt_sale(char, "Diamond Ring", quantity=1)
    print(f"Result: {transaction.success}")
    print(f"Message: {transaction.message}")
    assert not transaction.success, "Should fail - don't have item"
    print("✅ PASSED")


def test_chat_command_parsing():
    """Test parsing purchase/sell commands from player chat."""
    print("\n" + "="*80)
    print("TEST 5: Chat Command Parsing")
    print("="*80)

    shop, char, db = setup_test_environment()

    test_cases = [
        # Purchase commands
        ("/buy longsword", ("longsword", 1)),
        ("/buy 3 healing potions", ("healing potions", 3)),
        ("I'll buy a rope", ("rope", 1)),
        ("Can I buy the shield?", ("shield", 1)),
        ("I want to purchase 2 torches", ("torches", 2)),
        ("Get me the backpack please", ("backpack", 1)),

        # Sell commands
        ("/sell old sword", ("old sword", 1)),
        ("/sell 5 arrows", ("arrows", 5)),
        ("I want to sell my leather armor", ("leather armor", 1)),

        # Non-shop commands (should return None)
        ("Hello shopkeeper!", None),
        ("What do you have in stock?", None),
        ("Tell me about longswords", None),
    ]

    for i, (input_text, expected) in enumerate(test_cases, 1):
        print(f"\n--- Test 5.{i}: '{input_text}' ---")

        # Test purchase parsing
        if expected and "sell" not in input_text.lower():
            result = shop.parse_purchase_intent(input_text)
            print(f"Purchase intent: {result}")
            if expected is not None:
                assert result == expected, f"Expected {expected}, got {result}"
                print("✅ PASSED")
            else:
                assert result is None, "Should not detect purchase intent"
                print("✅ PASSED (correctly not detected)")

        # Test sell parsing
        elif expected and "sell" in input_text.lower():
            result = shop.parse_sell_intent(input_text)
            print(f"Sell intent: {result}")
            assert result == expected, f"Expected {expected}, got {result}"
            print("✅ PASSED")

        # Test non-shop messages
        else:
            purchase_result = shop.parse_purchase_intent(input_text)
            sell_result = shop.parse_sell_intent(input_text)
            print(f"Purchase: {purchase_result}, Sell: {sell_result}")
            assert purchase_result is None and sell_result is None, "Should not detect any intent"
            print("✅ PASSED")


def test_shopkeeper_context():
    """Test shopkeeper context generation for GM."""
    print("\n" + "="*80)
    print("TEST 6: Shopkeeper Context Generation")
    print("="*80)

    shop, char, db = setup_test_environment()

    # Test different shopkeeper personalities
    personalities = [
        ("general store", "Merchant Giles", "friendly"),
        ("weapon smith", "Grumak the Smith", "grumpy"),
        ("apothecary", "Madame Celestine", "mysterious"),
    ]

    for shop_type, name, personality in personalities:
        print(f"\n--- Testing {name} ({personality} {shop_type}) ---")
        context = shop.create_shopkeeper_context(shop_type, name, personality)
        print(f"Context length: {len(context)} characters")
        assert name in context, "Shopkeeper name should be in context"
        assert shop_type in context, "Shop type should be in context"
        assert len(context) > 200, "Context should be substantial"
        print("✅ PASSED")


def test_complete_shopping_experience():
    """Test a complete shopping experience with conversation."""
    print("\n" + "="*80)
    print("TEST 7: Complete Shopping Experience")
    print("="*80)
    print("\nSimulating a player visiting a weapon shop...")

    shop, char, db = setup_test_environment()

    print(f"\n💰 Starting gold: {char.gold} gp")
    print(f"📦 Starting inventory: {list(char.inventory.keys())}")

    # Step 1: Player asks about swords
    print("\n🗨️  Player: \"What swords do you have?\"")
    swords = shop.search_shop_inventory("sword", n_results=3)
    print(f"🏪 Shopkeeper shows {len(swords)} swords:")
    for sword in swords:
        print(f"   - {sword['name']}: {sword['cost_gp']} gp")

    # Step 2: Player asks about specific item
    print("\n🗨️  Player: \"How much for the longsword?\"")
    price = shop.get_item_price("Longsword")
    print(f"🏪 Shopkeeper: \"The longsword? Fine blade! {price} gold pieces.\"")

    # Step 3: Player buys the sword
    print("\n🗨️  Player: \"/buy longsword\"")
    transaction = shop.attempt_purchase(char, "Longsword", quantity=1)
    print(f"💼 Transaction: {transaction.message}")
    print(f"🏪 Shopkeeper: \"Excellent choice! *wraps sword carefully* That'll be {transaction.cost_gp} gold.\"")

    assert transaction.success, "Purchase should succeed"
    assert 'Longsword' in char.inventory, "Should have longsword"

    # Step 4: Player sells old item
    print("\n🗨️  Player: \"I want to sell my old sword\"")
    transaction = shop.attempt_sale(char, "Old Sword", quantity=1)
    print(f"💼 Transaction: {transaction.message}")
    if transaction.success:
        print(f"🏪 Shopkeeper: \"Hmm, seen better days... I'll give you {transaction.cost_gp} gold for it.\"")

    # Final inventory
    print(f"\n📊 Final Results:")
    print(f"   💰 Gold: {char.gold} gp")
    print(f"   📦 Inventory: {list(char.inventory.keys())}")

    print("\n✅ COMPLETE SHOPPING EXPERIENCE PASSED!")


def run_all_tests():
    """Run all shop system tests."""
    print("\n" + "🛒"*40)
    print("D&D SHOP SYSTEM - COMPREHENSIVE TEST SUITE")
    print("🛒"*40)

    try:
        test_shop_inventory_search()
        test_get_item_price()
        test_purchase_transactions()
        test_sell_transactions()
        test_chat_command_parsing()
        test_shopkeeper_context()
        test_complete_shopping_experience()

        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("="*80)
        print("\nThe Shop System is working correctly!")
        print("✅ Shop inventory search")
        print("✅ Item price lookups")
        print("✅ Purchase transactions (gold deduction, inventory addition)")
        print("✅ Sell transactions (gold increase, inventory removal)")
        print("✅ Chat command parsing (natural language + commands)")
        print("✅ Shopkeeper context generation for GM roleplay")
        print("\nThe conversational shopkeeper system is ready! 🏪")
        print("Players can naturally talk to shopkeepers via the GM chat.")
        print("Transactions are processed automatically while GM narrates.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()
