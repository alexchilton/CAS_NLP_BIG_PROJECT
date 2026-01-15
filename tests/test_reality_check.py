"""
Test suite for the Reality Check / Action Validator system.

Tests various scenarios:
1. Combat actions (valid, invalid, fuzzy match)
2. NPC conversations (existing, new introduction, rejection)
3. Spell casting (valid, invalid spell)
4. Item usage (valid, invalid item)
5. Exploration (always valid)
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.systems.action_validator import (
    ActionValidator, ActionType, ValidationResult
)
from dnd_rag_system.systems.game_state import GameSession, CharacterState


def test_combat_actions():
    """Test combat action validation"""
    print("\n" + "="*80)
    print("TEST 1: Combat Actions")
    print("="*80)

    # Use keyword classifier for consistent test results
    validator = ActionValidator(debug=True, classifier_type="keyword")
    session = GameSession(session_name="Test Combat")

    # Add some NPCs
    session.npcs_present = ["Goblin", "Bandit Captain"]

    # Test 1.1: Valid combat action
    print("\n--- Test 1.1: Attack existing enemy ---")
    intent = validator.analyze_intent("I attack the Goblin with my sword")
    print(f"Intent: {intent}")
    validation = validator.validate_action(intent, session)
    print(f"Result: {validation.result.value}")
    print(f"Message: {validation.message}")
    assert validation.result in [ValidationResult.VALID, ValidationResult.FUZZY_MATCH], "Should be valid or fuzzy match"
    print("✅ PASSED")

    # Test 1.2: Invalid combat action (enemy doesn't exist)
    print("\n--- Test 1.2: Attack non-existent enemy ---")
    intent = validator.analyze_intent("I attack the Dragon")
    print(f"Intent: {intent}")
    validation = validator.validate_action(intent, session)
    print(f"Result: {validation.result.value}")
    print(f"Message: {validation.message}")
    assert validation.result == ValidationResult.INVALID, "Should be invalid"
    print("✅ PASSED")

    # Test 1.3: Fuzzy match (partial name)
    print("\n--- Test 1.3: Fuzzy match (bandit → Bandit Captain) ---")
    intent = validator.analyze_intent("I strike the bandit")
    print(f"Intent: {intent}")
    validation = validator.validate_action(intent, session)
    print(f"Result: {validation.result.value}")
    print(f"Matched: {validation.matched_entity}")
    print(f"Message: {validation.message}")
    assert validation.result in [ValidationResult.FUZZY_MATCH, ValidationResult.VALID], "Should fuzzy match"
    print("✅ PASSED")


def test_npc_conversations():
    """Test NPC conversation validation"""
    print("\n" + "="*80)
    print("TEST 2: NPC Conversations")
    print("="*80)

    # Use keyword classifier for consistent test results
    validator = ActionValidator(debug=True, classifier_type="keyword")
    session = GameSession(session_name="Test Conversation")
    session.set_location("Rusty Dragon Inn", "A warm tavern filled with patrons.")

    # Add existing NPC
    session.npcs_present = ["Innkeeper"]

    # Test 2.1: Talk to existing NPC
    print("\n--- Test 2.1: Talk to existing NPC ---")
    intent = validator.analyze_intent("I talk to the Innkeeper")
    print(f"Intent: {intent}")
    validation = validator.validate_action(intent, session)
    print(f"Result: {validation.result.value}")
    print(f"Message: {validation.message}")
    assert validation.result == ValidationResult.VALID, "Should be valid"
    print("✅ PASSED")

    # Test 2.2: Talk to new NPC (should allow introduction)
    print("\n--- Test 2.2: Talk to new NPC (bartender in tavern) ---")
    intent = validator.analyze_intent("I ask the bartender about rumors")
    print(f"Intent: {intent}")
    validation = validator.validate_action(intent, session)
    print(f"Result: {validation.result.value}")
    print(f"Message: {validation.message}")
    assert validation.result == ValidationResult.NPC_INTRODUCTION, "Should allow introduction"
    print("✅ PASSED")

    # Test 2.3: Quoted speech
    print("\n--- Test 2.3: Quoted speech to NPC ---")
    intent = validator.analyze_intent('"Hello there!" I say to the guard')
    print(f"Intent: {intent}")
    print(f"Target detected: {intent.target}")
    assert intent.action_type == ActionType.CONVERSATION, "Should detect conversation"
    print("✅ PASSED")


def test_spell_casting():
    """Test spell casting validation"""
    print("\n" + "="*80)
    print("TEST 3: Spell Casting")
    print("="*80)

    # Use keyword classifier for consistent test results
    validator = ActionValidator(debug=True, classifier_type="keyword")
    session = GameSession(session_name="Test Spells")

    # Create character with known spells
    # Note: CharacterState doesn't have a spells attribute by default
    # For testing, we'll add it dynamically
    char_state = CharacterState(
        character_name="Gandalf",
        max_hp=28,
        level=5
    )
    # Add spells attribute for testing
    char_state.spells = ["Magic Missile", "Fireball", "Shield"]
    session.character_state = char_state

    session.npcs_present = ["Goblin"]

    # Test 3.1: Cast known spell
    print("\n--- Test 3.1: Cast known spell ---")
    intent = validator.analyze_intent("I cast Magic Missile at the Goblin")
    print(f"Intent: {intent}")
    validation = validator.validate_action(intent, session)
    print(f"Result: {validation.result.value}")
    print(f"Message: {validation.message}")
    assert validation.result == ValidationResult.VALID, "Should be valid"
    print("✅ PASSED")

    # Test 3.2: Cast unknown spell
    print("\n--- Test 3.2: Cast unknown spell ---")
    intent = validator.analyze_intent("I cast Wish")
    print(f"Intent: {intent}")
    validation = validator.validate_action(intent, session)
    print(f"Result: {validation.result.value}")
    print(f"Message: {validation.message}")
    assert validation.result == ValidationResult.INVALID, "Should be invalid"
    print("✅ PASSED")


def test_item_usage():
    """Test item usage validation"""
    print("\n" + "="*80)
    print("TEST 4: Item Usage")
    print("="*80)

    # Use keyword classifier for consistent test results (LLM can be flaky)
    validator = ActionValidator(debug=True, classifier_type="keyword")
    session = GameSession(session_name="Test Items")

    # Create character with inventory
    # Note: CharacterState.inventory is Dict[str, int] not List[str]
    char_state = CharacterState(
        character_name="Frodo",
        max_hp=20,
        level=3
    )
    char_state.inventory = {
        "Healing Potion": 2,
        "Rope": 1,
        "Lockpicks": 1
    }
    session.character_state = char_state

    # Test 4.1: Use item in inventory
    print("\n--- Test 4.1: Use item in inventory ---")
    intent = validator.analyze_intent("I drink the Healing Potion")
    print(f"Intent: {intent}")
    validation = validator.validate_action(intent, session)
    print(f"Result: {validation.result.value}")
    print(f"Message: {validation.message}")
    assert validation.result == ValidationResult.VALID, "Should be valid"
    print("✅ PASSED")

    # Test 4.2: Use item not in inventory
    print("\n--- Test 4.2: Use item not in inventory ---")
    intent = validator.analyze_intent("I use my Flaming Sword")
    print(f"Intent: {intent}")
    validation = validator.validate_action(intent, session)
    print(f"Result: {validation.result.value}")
    print(f"Message: {validation.message}")
    assert validation.result == ValidationResult.INVALID, "Should be invalid"
    print("✅ PASSED")


def test_exploration():
    """Test exploration actions (always valid)"""
    print("\n" + "="*80)
    print("TEST 5: Exploration Actions")
    print("="*80)

    # Use keyword classifier for consistent test results
    validator = ActionValidator(debug=True, classifier_type="keyword")
    session = GameSession(session_name="Test Exploration")

    # Test 5.1: Look around
    print("\n--- Test 5.1: Look around ---")
    intent = validator.analyze_intent("I look around the room")
    print(f"Intent: {intent}")
    validation = validator.validate_action(intent, session)
    print(f"Result: {validation.result.value}")
    assert validation.result == ValidationResult.VALID, "Should be valid"
    print("✅ PASSED")

    # Test 5.2: Search
    print("\n--- Test 5.2: Search for traps ---")
    intent = validator.analyze_intent("I search for traps")
    print(f"Intent: {intent}")
    validation = validator.validate_action(intent, session)
    print(f"Result: {validation.result.value}")
    assert validation.result == ValidationResult.VALID, "Should be valid"
    print("✅ PASSED")


def test_intent_analysis():
    """Test intent parsing accuracy"""
    print("\n" + "="*80)
    print("TEST 6: Intent Analysis")
    print("="*80)

    # Use keyword classifier for consistent test results
    validator = ActionValidator(debug=True, classifier_type="keyword")

    test_cases = [
        ("I attack the goblin", ActionType.COMBAT, "goblin"),
        ("I swing my sword at the orc", ActionType.COMBAT, "the orc"),
        ("I cast fireball at the enemies", ActionType.SPELL_CAST, "the enemies"),
        ("I talk to the bartender", ActionType.CONVERSATION, "bartender"),
        ('"Hello!" I say to the guard', ActionType.CONVERSATION, "guard"),
        ("I drink a healing potion", ActionType.ITEM_USE, None),
        ("I look around", ActionType.EXPLORATION, None),
    ]

    for i, (text, expected_type, expected_target) in enumerate(test_cases, 1):
        print(f"\n--- Test 6.{i}: {text[:50]}... ---")
        intent = validator.analyze_intent(text)
        print(f"Expected type: {expected_type.value}, Got: {intent.action_type.value}")
        print(f"Expected target: {expected_target}, Got: {intent.target}")
        assert intent.action_type == expected_type, f"Wrong action type for: {text}"
        if expected_target:
            assert intent.target is not None, f"Should detect target for: {text}"
        print("✅ PASSED")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "🎲"*40)
    print("D&D REALITY CHECK SYSTEM - COMPREHENSIVE TEST SUITE")
    print("🎲"*40)

    try:
        test_intent_analysis()
        test_combat_actions()
        test_npc_conversations()
        test_spell_casting()
        test_item_usage()
        test_exploration()

        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("="*80)
        print("\nThe Reality Check system is working correctly!")
        print("✅ Combat validation prevents attacking non-existent enemies")
        print("✅ NPC conversations encourage dynamic introductions")
        print("✅ Spell casting validates known spells")
        print("✅ Item usage checks inventory")
        print("✅ Exploration actions are always allowed")
        print("\nThe hybrid approach successfully balances:")
        print("  - Strict validation for game-critical entities")
        print("  - Flexible narrative freedom for descriptions")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
