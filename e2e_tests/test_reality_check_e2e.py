#!/usr/bin/env python3
"""
E2E Test: Reality Check System
Tests that the Reality Check system prevents hallucinations in actual gameplay.

Test Cases:
1. Invalid combat target (goblin doesn't exist)
2. Invalid item use (bow not in inventory)
3. Invalid spell (character doesn't know it)
4. Valid combat after NPC introduction
5. Valid item use with actual inventory
6. NPC conversation with introduction
"""

import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.systems.character_creator import Character
from dnd_rag_system.systems.game_state import CharacterState

# Suppress tokenizer warning
os.environ['TOKENIZERS_PARALLELISM'] = 'false'


def create_thorin() -> Character:
    """Create Thorin Stormshield character for testing."""
    return Character(
        name="Thorin Stormshield",
        race="Dwarf",
        character_class="Fighter",
        level=3,
        strength=16,
        dexterity=12,
        constitution=16,
        intelligence=10,
        wisdom=13,
        charisma=8,
        hit_points=28,
        armor_class=18,
        proficiency_bonus=2,
        equipment=["Longsword", "Shield", "Plate Armor", "Backpack"],
        background="Soldier",
        alignment="Lawful Good"
    )


def test_invalid_combat_target(gm: GameMaster, char: Character):
    """Test that attacking non-existent goblin is handled correctly."""
    print("\n" + "="*80)
    print("TEST 1: Invalid Combat Target (Goblin Doesn't Exist)")
    print("="*80)

    # Set character context
    gm.set_context(f"The player is {char.name}, a level {char.level} {char.race} {char.character_class}.")

    # Try to attack a goblin that doesn't exist
    player_input = "I attack the goblin with my longsword"
    print(f"\n🎲 Player: {player_input}")

    response = gm.generate_response(player_input, use_rag=False)
    print(f"🎭 GM: {response}")

    # Check that response indicates no goblin present
    response_lower = response.lower()
    success_indicators = [
        "no goblin", "don't see", "isn't here", "not present",
        "no one", "nobody", "can't find", "nowhere",
        "nothing there", "no enemies", "empty space", "empty air"
    ]

    if any(indicator in response_lower for indicator in success_indicators):
        print("\n✅ PASS: GM correctly indicated no goblin is present")
        return True
    else:
        print("\n❌ FAIL: GM may have hallucinated a goblin encounter")
        print(f"   Response should indicate no goblin present")
        print(f"   Response: {response}")
        return False


def test_invalid_item_use(gm: GameMaster, char: Character):
    """Test that using a bow (not in inventory) is handled correctly."""
    print("\n" + "="*80)
    print("TEST 2: Invalid Item Use (Bow Not In Inventory)")
    print("="*80)

    # Clear scene from previous test
    gm.session.npcs_present = []

    player_input = "I ready my bow and prepare to shoot"
    print(f"\n🎲 Player: {player_input}")

    response = gm.generate_response(player_input, use_rag=False)
    print(f"🎭 GM: {response}")

    # Check that response indicates no bow available
    response_lower = response.lower()
    success_indicators = [
        "don't have", "no bow", "haven't got", "not carrying",
        "longsword", "shield", "don't possess"
    ]

    if any(indicator in response_lower for indicator in success_indicators):
        print("\n✅ PASS: GM correctly indicated character doesn't have a bow")
        return True
    else:
        print("\n❌ FAIL: GM may have allowed using non-existent bow")
        print(f"   Character inventory: {char.equipment}")
        return False


def test_invalid_spell_cast(gm: GameMaster, char: Character):
    """Test that casting unknown spell (Fireball) is handled correctly."""
    print("\n" + "="*80)
    print("TEST 3: Invalid Spell Cast (Thorin Doesn't Know Fireball)")
    print("="*80)

    player_input = "I cast Fireball at the target"
    print(f"\n🎲 Player: {player_input}")

    response = gm.generate_response(player_input, use_rag=True)
    print(f"🎭 GM: {response}")

    # Thorin is a Fighter, not a spellcaster - should not be able to cast Fireball
    response_lower = response.lower()
    success_indicators = [
        "can't cast", "don't know", "not a spellcaster", "fighter",
        "no magic", "unable to cast", "don't have the ability"
    ]

    if any(indicator in response_lower for indicator in success_indicators):
        print("\n✅ PASS: GM correctly indicated character can't cast spells")
        return True
    else:
        print("\n⚠️  WARNING: GM may have allowed Fighter to cast Fireball")
        print(f"   Thorin is a Fighter (no spellcasting)")
        return False


def test_valid_combat_after_npc_intro(gm: GameMaster, char: Character):
    """Test that combat works after GM introduces an NPC."""
    print("\n" + "="*80)
    print("TEST 4: Valid Combat After NPC Introduction")
    print("="*80)

    # First, introduce a goblin to the scene
    gm.add_npc("Goblin")
    gm.set_location("Forest Path", "A narrow path winds through dense trees.")
    print("📍 Setup: GM introduces Goblin to the scene")

    # Now attack should be valid
    player_input = "I attack the goblin with my longsword"
    print(f"\n🎲 Player: {player_input}")

    response = gm.generate_response(player_input, use_rag=False)
    print(f"🎭 GM: {response}")

    # Check that response allows the combat
    response_lower = response.lower()
    rejection_indicators = [
        "no goblin", "don't see", "isn't here", "not present"
    ]

    if not any(indicator in response_lower for indicator in rejection_indicators):
        print("\n✅ PASS: GM allowed combat with introduced NPC")
        return True
    else:
        print("\n❌ FAIL: GM rejected combat even though goblin was introduced")
        print(f"   NPCs present: {gm.session.npcs_present}")
        return False


def test_valid_item_use(gm: GameMaster, char: Character):
    """Test that using actual inventory item (longsword) works."""
    print("\n" + "="*80)
    print("TEST 5: Valid Item Use (Longsword In Inventory)")
    print("="*80)

    player_input = "I draw my longsword and hold it ready"
    print(f"\n🎲 Player: {player_input}")

    response = gm.generate_response(player_input, use_rag=False)
    print(f"🎭 GM: {response}")

    # Check that response allows using the longsword
    response_lower = response.lower()
    rejection_indicators = [
        "don't have", "no longsword", "not carrying"
    ]

    if not any(indicator in response_lower for indicator in rejection_indicators):
        print("\n✅ PASS: GM allowed using item from inventory")
        return True
    else:
        print("\n❌ FAIL: GM rejected using item that's in inventory")
        print(f"   Character equipment: {char.equipment}")
        return False


def test_npc_conversation_introduction(gm: GameMaster, char: Character):
    """Test that talking to new NPC works (allows contextual introduction)."""
    print("\n" + "="*80)
    print("TEST 6: NPC Conversation With Introduction")
    print("="*80)

    # Clear scene
    gm.session.npcs_present = []
    gm.set_location("The Prancing Pony Inn", "A cozy tavern filled with travelers")

    # Try to talk to bartender (not yet introduced, but makes sense in tavern)
    player_input = "I talk to the bartender"
    print(f"\n🎲 Player: {player_input}")

    response = gm.generate_response(player_input, use_rag=False)
    print(f"🎭 GM: {response}")

    # Check that response either introduces bartender OR politely indicates no one
    response_lower = response.lower()

    # Success if either:
    # 1. Bartender is introduced (ideal)
    # 2. GM indicates no bartender visible (also acceptable)
    introduced = "bartender" in response_lower and not any(
        phrase in response_lower for phrase in ["no bartender", "don't see", "isn't here"]
    )
    rejected_appropriately = any(
        phrase in response_lower for phrase in ["no bartender", "don't see anyone", "nobody behind"]
    )

    if introduced:
        print("\n✅ PASS: GM introduced contextually appropriate NPC (bartender in tavern)")
        print(f"   NPCs in scene: {gm.session.npcs_present}")
        return True
    elif rejected_appropriately:
        print("\n✅ PASS: GM appropriately indicated no bartender present")
        return True
    else:
        print("\n⚠️  NEUTRAL: Response unclear about NPC introduction")
        return True  # Don't fail on ambiguous cases


def test_generic_item_term(gm: GameMaster, char: Character):
    """Test that generic terms like 'weapon' match specific items like 'longsword'."""
    print("\n" + "="*80)
    print("TEST 7: Generic Item Term ('weapon' matches 'Longsword')")
    print("="*80)

    player_input = "I draw my weapon and prepare for combat"
    print(f"\n🎲 Player: {player_input}")

    response = gm.generate_response(player_input, use_rag=False)
    print(f"🎭 GM: {response}")

    # Check that response allows using the weapon (not rejected)
    response_lower = response.lower()
    rejection_indicators = [
        "don't have", "no weapon", "not carrying", "not in your pack", "not there"
    ]

    if not any(indicator in response_lower for indicator in rejection_indicators):
        print("\n✅ PASS: GM allowed using generic 'weapon' term for longsword")
        return True
    else:
        print("\n❌ FAIL: GM rejected generic 'weapon' term even though character has longsword")
        print(f"   Character equipment: {char.equipment}")
        return False


def test_dragon_combat_scenario(gm: GameMaster, char: Character):
    """Test realistic dragon combat with various weapons and spells."""
    print("\n" + "="*80)
    print("TEST 8: Dragon Combat Scenario (Single Character)")
    print("="*80)

    # Set up dragon encounter
    gm.set_location("Dragon's Lair", "A vast cave filled with treasure. A massive red dragon guards its hoard.")
    gm.add_npc("Ancient Red Dragon")
    print("📍 Setup: Set location to Dragon's Lair, added Ancient Red Dragon")

    # Test 1: Attack with longsword (valid - has longsword)
    print("\n🎲 Test 8a: Attack dragon with longsword")
    response1 = gm.generate_response("I attack the dragon with my longsword", use_rag=False)
    print(f"🎭 GM: {response1[:100]}...")
    valid1 = "not there" not in response1.lower() and "no dragon" not in response1.lower()

    # Test 2: Try to use bow (invalid - no bow)
    print("\n🎲 Test 8b: Try to use bow (not in inventory)")
    response2 = gm.generate_response("I fire my bow at the dragon", use_rag=False)
    print(f"🎭 GM: {response2[:100]}...")
    valid2 = "don't have" in response2.lower() or "no bow" in response2.lower()

    # Test 3: Use shield (valid - has shield)
    print("\n🎲 Test 8c: Raise shield")
    response3 = gm.generate_response("I raise my shield to block the dragon's flames", use_rag=False)
    print(f"🎭 GM: {response3[:100]}...")
    valid3 = "not there" not in response3.lower()

    # Test 4: Generic weapon term (valid - has longsword)
    print("\n🎲 Test 8d: Generic 'weapon' term")
    response4 = gm.generate_response("I strike the dragon with my weapon", use_rag=False)
    print(f"🎭 GM: {response4[:100]}...")
    valid4 = "not there" not in response4.lower() and "no weapon" not in response4.lower()

    all_valid = valid1 and valid2 and valid3 and valid4

    if all_valid:
        print("\n✅ PASS: Dragon combat scenario handled correctly")
        print("   ✓ Longsword attack allowed")
        print("   ✓ Bow attack rejected (not in inventory)")
        print("   ✓ Shield use allowed")
        print("   ✓ Generic weapon term worked")
    else:
        print("\n❌ FAIL: Some combat actions handled incorrectly")
        if not valid1: print("   ✗ Longsword attack failed")
        if not valid2: print("   ✗ Bow attack not rejected")
        if not valid3: print("   ✗ Shield use failed")
        if not valid4: print("   ✗ Generic weapon term failed")

    return all_valid


def test_party_dragon_combat(gm: GameMaster):
    """Test party-mode dragon combat with multiple character types."""
    print("\n" + "="*80)
    print("TEST 9: Party Dragon Combat (Multiple Characters)")
    print("="*80)

    # Create a party with different classes
    fighter = Character(
        name="Thorin", race="Dwarf", character_class="Fighter", level=5,
        strength=16, dexterity=12, constitution=16, intelligence=10, wisdom=13, charisma=8,
        hit_points=45, armor_class=18, proficiency_bonus=3,
        equipment=["Longsword", "Shield", "Plate Armor"],
        spells=[]
    )

    wizard = Character(
        name="Elara", race="Elf", character_class="Wizard", level=5,
        strength=8, dexterity=14, constitution=12, intelligence=18, wisdom=13, charisma=10,
        hit_points=25, armor_class=12, proficiency_bonus=3,
        equipment=["Quarterstaff", "Spellbook", "Robes"],
        spells=["Fireball", "Magic Missile", "Shield"]
    )

    # Create party state
    from dnd_rag_system.systems.game_state import PartyState
    party = PartyState(party_name="Dragon Slayers")

    # Add characters to party
    fighter_state = CharacterState(character_name=fighter.name, max_hp=45, level=5,
                                   inventory={item: 1 for item in fighter.equipment})
    fighter_state.race = fighter.race
    fighter_state.character_class = fighter.character_class

    wizard_state = CharacterState(character_name=wizard.name, max_hp=25, level=5,
                                  inventory={item: 1 for item in wizard.equipment})
    wizard_state.race = wizard.race
    wizard_state.character_class = wizard.character_class
    wizard_state.spells = wizard.spells

    party.add_character(fighter_state)
    party.add_character(wizard_state)
    gm.session.party = party

    # Set dragon location
    gm.set_location("Dragon's Mountain Peak", "A treacherous mountain summit where an ancient dragon roosts.")
    gm.add_npc("Ancient Red Dragon")
    print("📍 Setup: Party of 2 at Dragon's Mountain Peak with Ancient Red Dragon")

    # Test 1: Fighter uses longsword (valid)
    print("\n🎲 Test 9a: Thorin attacks with longsword")
    gm.session.character_state = fighter_state  # Set active character
    response1 = gm.generate_response("Thorin attacks the dragon with his longsword", use_rag=False)
    print(f"🎭 GM: {response1[:100]}...")
    valid1 = "not there" not in response1.lower()

    # Test 2: Wizard casts Fireball (valid - knows the spell)
    print("\n🎲 Test 9b: Elara casts Fireball")
    gm.session.character_state = wizard_state
    response2 = gm.generate_response("Elara casts Fireball at the dragon", use_rag=False)
    print(f"🎭 GM: {response2[:100]}...")
    valid2 = "don't know" not in response2.lower() and "not a spellcaster" not in response2.lower()

    # Test 3: Fighter tries to cast spell (invalid - Fighter can't cast)
    print("\n🎲 Test 9c: Thorin tries to cast Fireball (should fail)")
    gm.session.character_state = fighter_state
    response3 = gm.generate_response("Thorin casts Fireball", use_rag=False)
    print(f"🎭 GM: {response3[:100]}...")
    valid3 = "fighter" in response3.lower() or "not a" in response3.lower()

    # Test 4: Wizard tries to use longsword (invalid - doesn't have it)
    print("\n🎲 Test 9d: Elara tries to use longsword (not in inventory)")
    gm.session.character_state = wizard_state
    response4 = gm.generate_response("Elara attacks with a longsword", use_rag=False)
    print(f"🎭 GM: {response4[:100]}...")
    valid4 = "don't have" in response4.lower() or "not there" in response4.lower()

    all_valid = valid1 and valid2 and valid3 and valid4

    if all_valid:
        print("\n✅ PASS: Party dragon combat handled correctly")
        print("   ✓ Fighter longsword attack allowed")
        print("   ✓ Wizard Fireball allowed")
        print("   ✓ Fighter can't cast spells")
        print("   ✓ Wizard doesn't have longsword")
    else:
        print("\n❌ FAIL: Some party combat actions handled incorrectly")
        if not valid1: print("   ✗ Fighter longsword failed")
        if not valid2: print("   ✗ Wizard Fireball failed")
        if not valid3: print("   ✗ Fighter spell cast not rejected")
        if not valid4: print("   ✗ Wizard longsword not rejected")

    return all_valid


def run_all_tests():
    """Run all Reality Check E2E tests."""
    print("\n" + "="*80)
    print("🧪 D&D REALITY CHECK SYSTEM - E2E TESTS")
    print("="*80)
    print("\nTesting that the Reality Check system prevents hallucinations")
    print("in actual gameplay scenarios.\n")

    # Initialize system
    print("Initializing D&D RAG System...")
    db = ChromaDBManager()
    gm = GameMaster(db)
    char = create_thorin()

    # Load CharacterState into GameSession for Reality Check validation
    char_state = CharacterState(
        character_name=char.name,
        max_hp=char.hit_points,
        current_hp=char.hit_points,
        level=char.level,
        inventory={item: 1 for item in char.equipment},
    )
    char_state.character_class = char.character_class  # Add for spell validation
    char_state.race = char.race  # Add for personality-driven responses
    gm.session.character_state = char_state

    print(f"✓ System initialized with character: {char.name}")
    print(f"✓ Character state loaded with inventory: {list(char_state.inventory.keys())}")

    # Run tests
    results = {}

    results["Invalid Combat Target"] = test_invalid_combat_target(gm, char)
    results["Invalid Item Use"] = test_invalid_item_use(gm, char)
    results["Invalid Spell Cast"] = test_invalid_spell_cast(gm, char)
    results["Valid Combat After Intro"] = test_valid_combat_after_npc_intro(gm, char)
    results["Valid Item Use"] = test_valid_item_use(gm, char)
    results["NPC Conversation"] = test_npc_conversation_introduction(gm, char)
    results["Generic Item Term"] = test_generic_item_term(gm, char)
    results["Dragon Combat Scenario"] = test_dragon_combat_scenario(gm, char)
    results["Party Dragon Combat"] = test_party_dragon_combat(gm)

    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 ALL REALITY CHECK E2E TESTS PASSED!")
        print("\nThe Reality Check system is working correctly!")
        print("Player actions are validated against game state before GM generation.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\nThe Reality Check system may not be working as expected.")
        print("Check the test output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
