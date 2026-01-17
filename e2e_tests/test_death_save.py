#!/usr/bin/env python3
"""Test /death_save command"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.systems.game_state import CharacterState, Condition

def test_death_save():
    """Test that /death_save command works"""
    print("\n" + "="*80)
    print("🧪 TEST: /death_save Command")
    print("="*80)

    db = ChromaDBManager()
    gm = GameMaster(db)

    # Setup character at 0 HP (unconscious)
    char_state = CharacterState(character_name="Thorin", max_hp=30, level=3, gold=50)
    char_state.current_hp = 0  # Unconscious
    char_state.conditions.append(Condition.UNCONSCIOUS.value)
    gm.session.character_state = char_state
    gm.set_context("Test character")

    print(f"\n📊 Character state:")
    print(f"   HP: {char_state.current_hp}/{char_state.max_hp}")
    print(f"   Conditions: {char_state.conditions}")
    print(f"   Unconscious: {not char_state.is_conscious()}")

    # Try death save command
    print("\n💬 Player: '/death_save'")

    try:
        response = gm.generate_response("/death_save", use_rag=False)

        print("\n" + "="*80)
        print("GM Response:")
        print("="*80)
        print(response)
        print("="*80)

        # Check that it worked
        has_roll = "Rolled" in response or "rolled" in response
        has_result = any(word in response for word in ["Success", "Failure", "Natural"])

        print(f"\n🔍 ANALYSIS:")
        print(f"   Contains dice roll: {'✅' if has_roll else '❌'}")
        print(f"   Contains result: {'✅' if has_result else '❌'}")

        if has_roll and has_result:
            print("\n✅ TEST PASSED: /death_save command works!")
            return True
        else:
            print("\n❌ TEST FAILED: Response doesn't look like a death save")
            return False

    except Exception as e:
        print(f"\n❌ TEST FAILED: Exception raised: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_death_save()
    sys.exit(0 if success else 1)
