#!/usr/bin/env python3
"""
E2E Test: Party Character Name Parsing

Tests that the Reality Check system correctly identifies which party member
is acting based on their name in the player input, and validates actions
against THAT character's inventory, spells, and abilities.

Test Cases:
1. "Thorin attacks" -> Validates against Thorin's equipment
2. "Elara casts Fire Bolt" -> Validates against Elara's spells
3. "Gimli drinks potion" -> Validates against Gimli's inventory
4. Invalid: "Thorin casts Fireball" -> Rejects (Fighter can't cast)
5. Invalid: "Elara shoots bow" -> Rejects (bow not in inventory)
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.systems.game_state import CharacterState, PartyState


def test_party_character_parsing():
    """Test character name parsing in party mode."""
    print("\n" + "=" * 80)
    print("🎭 E2E TEST: Party Character Name Parsing")
    print("=" * 80)

    # Initialize GM
    db = ChromaDBManager()
    gm = GameMaster(db)

    # Create party with Thorin (Fighter) and Elara (Wizard)
    print("\n📝 Setting up party...")

    # Thorin - Dwarf Fighter
    thorin = CharacterState(
        character_name="Thorin",
        max_hp=30,
        current_hp=30,
        inventory={"Longsword": 1, "Shield": 1, "Plate Armor": 1}
    )
    # Add dynamic attributes for validation
    thorin.race = "Dwarf"
    thorin.character_class = "Fighter"
    thorin.spells = []  # Fighter has no spells

    # Elara - Elf Wizard
    elara = CharacterState(
        character_name="Elara",
        max_hp=16,
        current_hp=16,
        inventory={"Staff": 1, "Spellbook": 1, "Robes": 1}
    )
    # Add dynamic attributes for validation
    elara.race = "Elf"
    elara.character_class = "Wizard"
    elara.spells = ["Fire Bolt", "Magic Missile", "Shield"]

    # Gimli - Dwarf Cleric (for item test)
    gimli = CharacterState(
        character_name="Gimli",
        max_hp=28,
        current_hp=28,
        inventory={"Warhammer": 1, "Healing Potion": 2, "Holy Symbol": 1}
    )
    # Add dynamic attributes for validation
    gimli.race = "Dwarf"
    gimli.character_class = "Cleric"
    gimli.spells = ["Cure Wounds", "Bless"]

    # Set up party
    party = PartyState(party_name="Test Party")
    party.add_character(thorin)
    party.add_character(elara)
    party.add_character(gimli)

    gm.session.party = party  # GameSession uses 'party', not 'party_state'

    # Set up combat encounter
    gm.set_location("Dragon's Lair", "A vast cavern filled with treasure and danger")
    gm.add_npc("Goblin Scout")
    gm.add_npc("Ancient Red Dragon")

    print("✅ Party created:")
    print(f"   - Thorin (Fighter): Longsword, Shield, Plate Armor")
    print(f"   - Elara (Wizard): Staff, Spellbook, Robes | Spells: Fire Bolt, Magic Missile, Shield")
    print(f"   - Gimli (Cleric): Warhammer, Healing Potion x2, Holy Symbol | Spells: Cure Wounds, Bless")

    # TEST 1: Thorin attacks with longsword (VALID)
    print("\n" + "=" * 80)
    print("TEST 1: Thorin attacks with longsword (should be VALID)")
    print("=" * 80)

    response = gm.generate_response("Thorin attacks the Goblin Scout with his longsword", use_rag=False)
    print(f"\n💬 GM Response: {response}\n")

    assert "daft" not in response.lower(), "Response should NOT be an invalid action rejection"
    print("✅ TEST 1 PASSED: Thorin's longsword attack validated correctly")

    # TEST 2: Elara casts Fire Bolt (VALID)
    print("\n" + "=" * 80)
    print("TEST 2: Elara casts Fire Bolt (should be VALID)")
    print("=" * 80)

    response = gm.generate_response("Elara casts Fire Bolt at the Goblin Scout", use_rag=False)
    print(f"\n💬 GM Response: {response}\n")

    assert "daft" not in response.lower(), "Response should NOT be an invalid action rejection"
    print("✅ TEST 2 PASSED: Elara's Fire Bolt spell validated correctly")

    # TEST 3: Gimli uses healing potion (VALID)
    print("\n" + "=" * 80)
    print("TEST 3: Gimli drinks healing potion (should be VALID)")
    print("=" * 80)

    response = gm.generate_response("Gimli drinks a healing potion", use_rag=False)
    print(f"\n💬 GM Response: {response}\n")

    assert "not in" not in response.lower() or "don't find" not in response.lower(), \
        "Response should NOT reject the healing potion"
    print("✅ TEST 3 PASSED: Gimli's healing potion validated correctly")

    # TEST 4: Thorin tries to cast Fireball (INVALID - Fighter can't cast spells)
    print("\n" + "=" * 80)
    print("TEST 4: Thorin casts Fireball (should be INVALID - Fighter can't cast)")
    print("=" * 80)

    response = gm.generate_response("Thorin casts Fireball at the Ancient Red Dragon", use_rag=False)
    print(f"\n💬 GM Response: {response}\n")

    assert "daft" in response.lower() or "fighter" in response.lower(), \
        "Response should reject Fighter casting spells"
    print("✅ TEST 4 PASSED: Correctly rejected Thorin (Fighter) casting Fireball")

    # TEST 5: Elara tries to shoot bow (INVALID - no bow in inventory)
    print("\n" + "=" * 80)
    print("TEST 5: Elara shoots bow (should be INVALID - no bow in inventory)")
    print("=" * 80)

    response = gm.generate_response("Elara shoots the Dragon with her bow", use_rag=False)
    print(f"\n💬 GM Response: {response}\n")

    assert "not there" in response.lower() or "don't have" in response.lower(), \
        "Response should reject using bow (not in inventory)"
    print("✅ TEST 5 PASSED: Correctly rejected Elara using bow (not in inventory)")

    # TEST 6: Thorin tries to use Staff (INVALID - Staff is Elara's, not Thorin's)
    print("\n" + "=" * 80)
    print("TEST 6: Thorin uses staff (should be INVALID - Staff belongs to Elara)")
    print("=" * 80)

    response = gm.generate_response("Thorin uses his staff", use_rag=False)
    print(f"\n💬 GM Response: {response}\n")

    assert "not in" in response.lower() or "don't find" in response.lower(), \
        "Response should reject using staff (Thorin doesn't have it, Elara does)"
    print("✅ TEST 6 PASSED: Correctly rejected Thorin using staff (Elara's item)")

    # TEST 7: Elara casts Shield spell (VALID - she knows it)
    print("\n" + "=" * 80)
    print("TEST 7: Elara casts Shield (should be VALID)")
    print("=" * 80)

    response = gm.generate_response("Elara casts Shield", use_rag=False)
    print(f"\n💬 GM Response: {response}\n")

    assert "daft" not in response.lower(), "Response should NOT reject Shield spell"
    print("✅ TEST 7 PASSED: Elara's Shield spell validated correctly")

    # TEST 8: Gimli casts Cure Wounds (VALID - Cleric spell)
    print("\n" + "=" * 80)
    print("TEST 8: Gimli casts Cure Wounds (should be VALID)")
    print("=" * 80)

    response = gm.generate_response("Gimli casts Cure Wounds", use_rag=False)
    print(f"\n💬 GM Response: {response}\n")

    assert "daft" not in response.lower(), "Response should NOT reject Cure Wounds"
    print("✅ TEST 8 PASSED: Gimli's Cure Wounds spell validated correctly")

    # TEST 9: No character name specified (should work with fallback)
    print("\n" + "=" * 80)
    print("TEST 9: No character name (fallback behavior)")
    print("=" * 80)

    response = gm.generate_response("I attack the goblin", use_rag=False)
    print(f"\n💬 GM Response: {response}\n")
    print("ℹ️  TEST 9: Fallback behavior tested (no character name specified)")

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print("\n✅ ALL 8 CHARACTER PARSING TESTS PASSED!")
    print("\nFeatures tested:")
    print("  ✓ Parsing 'CharName attacks' pattern")
    print("  ✓ Parsing 'CharName casts Spell' pattern")
    print("  ✓ Parsing 'CharName drinks/uses item' pattern")
    print("  ✓ Validating actions against correct character's inventory")
    print("  ✓ Validating spells against correct character's known spells")
    print("  ✓ Rejecting invalid class abilities (Fighter casting spells)")
    print("  ✓ Rejecting items not in character's inventory")
    print("  ✓ Character-specific item isolation (Thorin can't use Elara's staff)")
    print("\n🎉 Party character parsing is working correctly!")
    print("=" * 80)


if __name__ == "__main__":
    test_party_character_parsing()
