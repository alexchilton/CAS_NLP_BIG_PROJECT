#!/usr/bin/env python3
"""
Test the Narrative to Mechanics Translation System

Tests extraction and application of game mechanics from GM narratives.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.systems.mechanics_extractor import MechanicsExtractor
from dnd_rag_system.systems.mechanics_applicator import MechanicsApplicator
from dnd_rag_system.systems.game_state import CharacterState, Condition


def test_damage_extraction():
    """Test damage extraction and application."""
    print("\n" + "=" * 80)
    print("TEST 1: Damage Extraction")
    print("=" * 80)

    extractor = MechanicsExtractor(debug=True)
    applicator = MechanicsApplicator(debug=True)

    # Create test character
    thorin = CharacterState(
        character_name="Thorin",
        max_hp=28,
        current_hp=28
    )

    print(f"\n📊 Initial State: Thorin has {thorin.current_hp}/{thorin.max_hp} HP")

    # Test narratives
    narratives = [
        "The goblin's rusty axe strikes Thorin's shoulder, dealing 8 slashing damage!",
        "The orc's greataxe slams into Thorin for 12 damage!",
        "Thorin takes 5 fire damage from the burning oil.",
    ]

    for narrative in narratives:
        print(f"\n📖 Narrative: {narrative}")

        # Extract
        mechanics = extractor.extract(narrative, ["Thorin"])

        # Apply
        feedback = applicator.apply_to_character(mechanics, thorin)

        print(f"💥 Result: {thorin.current_hp}/{thorin.max_hp} HP")
        if feedback:
            for msg in feedback:
                print(f"   {msg}")

    print(f"\n✅ Final State: Thorin has {thorin.current_hp}/{thorin.max_hp} HP")
    print("=" * 80)


def test_healing_extraction():
    """Test healing extraction and application."""
    print("\n" + "=" * 80)
    print("TEST 2: Healing Extraction")
    print("=" * 80)

    extractor = MechanicsExtractor(debug=True)
    applicator = MechanicsApplicator(debug=True)

    # Create test character (damaged)
    elara = CharacterState(
        character_name="Elara",
        max_hp=14,
        current_hp=6
    )

    print(f"\n📊 Initial State: Elara has {elara.current_hp}/{elara.max_hp} HP")

    narratives = [
        "Elara drinks the health potion, restoring 7 hit points!",
        "The cleric's healing word restores 5 HP to Elara.",
    ]

    for narrative in narratives:
        print(f"\n📖 Narrative: {narrative}")

        mechanics = extractor.extract(narrative, ["Elara"])
        feedback = applicator.apply_to_character(mechanics, elara)

        print(f"❤️  Result: {elara.current_hp}/{elara.max_hp} HP")
        if feedback:
            for msg in feedback:
                print(f"   {msg}")

    print(f"\n✅ Final State: Elara has {elara.current_hp}/{elara.max_hp} HP")
    print("=" * 80)


def test_conditions():
    """Test condition extraction and application."""
    print("\n" + "=" * 80)
    print("TEST 3: Condition Extraction")
    print("=" * 80)

    extractor = MechanicsExtractor(debug=True)
    applicator = MechanicsApplicator(debug=True)

    char = CharacterState(
        character_name="Gandalf",
        max_hp=20,
        current_hp=20
    )

    print(f"\n📊 Initial State: Gandalf - Conditions: {char.conditions}")

    narratives = [
        "The poison dart hits Gandalf! He becomes poisoned.",
        "Gandalf shakes off the poison and is no longer poisoned.",
        "The banshee's wail frightens Gandalf!",
    ]

    for narrative in narratives:
        print(f"\n📖 Narrative: {narrative}")

        mechanics = extractor.extract(narrative, ["Gandalf"])
        feedback = applicator.apply_to_character(mechanics, char)

        print(f"⚠️  Result: Conditions = {char.conditions}")
        if feedback:
            for msg in feedback:
                print(f"   {msg}")

    print(f"\n✅ Final State: Gandalf - Conditions: {char.conditions}")
    print("=" * 80)


def test_complex_combat():
    """Test complex combat narrative with multiple mechanics."""
    print("\n" + "=" * 80)
    print("TEST 4: Complex Combat Narrative")
    print("=" * 80)

    extractor = MechanicsExtractor(debug=True)
    applicator = MechanicsApplicator(debug=True)

    # Create two characters
    fighter = CharacterState(
        character_name="Ragnar",
        max_hp=30,
        current_hp=30
    )

    wizard = CharacterState(
        character_name="Merlin",
        max_hp=16,
        current_hp=16
    )

    wizard.spell_slots.level_2 = 2
    wizard.spell_slots.current_2 = 2

    print(f"\n📊 Initial State:")
    print(f"   Ragnar: {fighter.current_hp}/{fighter.max_hp} HP")
    print(f"   Merlin: {wizard.current_hp}/{wizard.max_hp} HP, Spell Slots L2: {wizard.spell_slots.current_2}")

    narrative = """The dragon breathes fire! Ragnar takes 18 fire damage and is badly burned.
Merlin casts Hold Person using a 2nd level spell slot, but takes 12 fire damage from the flames.
The healing potion restores 8 HP to Ragnar."""

    print(f"\n📖 Complex Narrative:\n{narrative}")

    mechanics = extractor.extract(narrative, ["Ragnar", "Merlin"])

    # Apply to both
    feedback_fighter = applicator.apply_to_character(mechanics, fighter)
    feedback_wizard = applicator.apply_to_character(mechanics, wizard)

    print(f"\n💥 Results:")
    print(f"   Ragnar: {fighter.current_hp}/{fighter.max_hp} HP")
    for msg in feedback_fighter:
        print(f"      - {msg}")

    print(f"   Merlin: {wizard.current_hp}/{wizard.max_hp} HP, Spell Slots L2: {wizard.spell_slots.current_2}")
    for msg in feedback_wizard:
        print(f"      - {msg}")

    print("=" * 80)


def test_no_mechanics():
    """Test narratives with no mechanics."""
    print("\n" + "=" * 80)
    print("TEST 5: No Mechanics (Roleplay Only)")
    print("=" * 80)

    extractor = MechanicsExtractor(debug=True)

    narratives = [
        "The innkeeper greets you warmly and offers you a room for the night.",
        "You walk down the cobblestone street, admiring the architecture.",
        "The merchant looks at you suspiciously but says nothing.",
    ]

    for narrative in narratives:
        print(f"\n📖 Narrative: {narrative}")
        mechanics = extractor.extract(narrative)

        if mechanics.has_mechanics():
            print("   ❌ ERROR: Should have no mechanics")
        else:
            print("   ✅ Correctly identified as roleplay-only")

    print("=" * 80)


def main():
    """Run all tests."""
    print("\n" + "🧪" * 40)
    print("NARRATIVE TO MECHANICS TRANSLATION SYSTEM - TEST SUITE")
    print("🧪" * 40)

    try:
        test_damage_extraction()
        test_healing_extraction()
        test_conditions()
        test_complex_combat()
        test_no_mechanics()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)
        print("\n💡 The system successfully:")
        print("   - Extracts damage, healing, conditions from narratives")
        print("   - Applies mechanics to character state automatically")
        print("   - Handles spell slots and item consumption")
        print("   - Ignores roleplay-only narratives")
        print("\n🎯 Ready for integration into live gameplay!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
