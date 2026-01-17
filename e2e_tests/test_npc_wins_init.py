#!/usr/bin/env python3
"""Quick test to show NPC winning initiative"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.systems.game_state import CharacterState

def test_npc_wins():
    db = ChromaDBManager()
    gm = GameMaster(db)

    # Setup character
    char_state = CharacterState(character_name="Thorin Stormshield", max_hp=30, level=3, gold=50)
    char_state.current_hp = 30
    char_state.armor_class = 18
    gm.session.character_state = char_state
    gm.set_context("Test character")
    gm.set_location("Cave", "A dark cave with a goblin!")
    gm.session.npcs_present = ["goblin"]

    # Attack the goblin (might win or lose initiative)
    print("\n" + "="*80)
    print("Player: 'attack the goblin'")
    print("="*80)

    for attempt in range(5):  # Try 5 times to get NPC winning initiative
        # Reset combat
        if gm.combat_manager.is_in_combat():
            gm.combat_manager.end_combat()

        response = gm.generate_response("attack the goblin", use_rag=False)

        if "goblin's turn!" in response and "**🐉 NPC ACTIONS:**" in response:
            print(f"\n✅ Attempt {attempt + 1}: NPC WON INITIATIVE!\n")
            print(response)
            return True

    # If we didn't get NPC winning, show last attempt anyway
    print(f"\n⚠️  Tried 5 times, showing last result (player may have won):\n")
    print(response)
    return False

if __name__ == "__main__":
    test_npc_wins()
