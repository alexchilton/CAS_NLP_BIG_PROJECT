#!/usr/bin/env python3
"""Test that prompt leakage and duplicate mechanics are fixed"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.systems.game_state import CharacterState

def test_no_duplicate_mechanics():
    """Test that damage mechanics don't appear multiple times"""
    print("\n" + "="*80)
    print("🧪 TEST: No Duplicate Mechanics Messages")
    print("="*80)

    db = ChromaDBManager()
    gm = GameMaster(db)

    # Setup character
    char_state = CharacterState(character_name="Thorin", max_hp=30, level=3, gold=50)
    char_state.current_hp = 30
    char_state.armor_class = 15
    gm.session.character_state = char_state
    gm.set_context("Test character")
    gm.set_location("Arena", "A combat arena")
    gm.session.npcs_present = []

    # Start combat explicitly
    print("\n💬 Player: '/start_combat ogre'")
    response1 = gm.generate_response("/start_combat ogre", use_rag=False)
    print("\n" + "="*80)
    print("Combat Start Response:")
    print("="*80)
    print(response1)

    # Attack the ogre
    print("\n💬 Player: 'attack the ogre'")
    response2 = gm.generate_response("attack the ogre", use_rag=False)

    print("\n" + "="*80)
    print("Attack Response:")
    print("="*80)
    print(response2)
    print("="*80)

    # Count how many times damage mechanics appear
    mechanics_count = response2.count("⚙️ MECHANICS:")
    ogre_damage_count = response2.lower().count("ogre takes")

    print(f"\n🔍 ANALYSIS:")
    print(f"   '⚙️ MECHANICS:' sections: {mechanics_count}")
    print(f"   'ogre takes' phrases: {ogre_damage_count}")

    # Check for prompt leakage patterns
    leakage_patterns = [
        "Narrate the",
        "Taking the above information into consideration",
        "you must engage in a roleplay conversation"
    ]

    leakage_found = []
    for pattern in leakage_patterns:
        if pattern.lower() in response2.lower():
            leakage_found.append(pattern)

    if leakage_found:
        print(f"\n❌ PROMPT LEAKAGE FOUND:")
        for pattern in leakage_found:
            print(f"   - '{pattern}'")
    else:
        print(f"\n✅ No prompt leakage detected")

    # Verdict
    errors = []

    if mechanics_count > 1:
        errors.append(f"❌ Multiple MECHANICS sections ({mechanics_count})")

    if ogre_damage_count > 2:  # Allow up to 2 (one from player attack, one from mechanics)
        errors.append(f"❌ Duplicate damage messages ({ogre_damage_count} instances)")

    if leakage_found:
        errors.append(f"❌ Prompt leakage detected: {leakage_found}")

    print("\n" + "="*80)
    if errors:
        print("❌ TEST FAILED:")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print("✅ TEST PASSED: No duplicates or prompt leakage!")
    print("="*80)

    return True


if __name__ == "__main__":
    success = test_no_duplicate_mechanics()
    sys.exit(0 if success else 1)
