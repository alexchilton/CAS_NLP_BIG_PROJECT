#!/usr/bin/env python3
"""
Quick test for NPC extraction from GM narrative.

Tests that when GM says "The goblin attacks you", the mechanics extractor:
1. Extracts the goblin as an NPC
2. Auto-adds it to npcs_present
3. Logs the JSON output for debugging
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Enable debug mode
os.environ['GM_DEBUG'] = 'true'

from dnd_rag_system.systems.mechanics_extractor import MechanicsExtractor
from dnd_rag_system.systems.mechanics_applicator import MechanicsApplicator
from dnd_rag_system.systems.game_state import GameSession

def test_npc_extraction():
    """Test NPC extraction from GM narrative."""

    print("=" * 80)
    print("TEST: NPC EXTRACTION FROM GM NARRATIVE")
    print("=" * 80)
    print()

    # Create extractor and applicator with debug enabled
    extractor = MechanicsExtractor(debug=True)
    applicator = MechanicsApplicator(debug=True)
    session = GameSession(session_name="Test Session")

    # Test narratives that should extract NPCs
    test_cases = [
        {
            "narrative": "The goblin's rusty sword strikes you, dealing 3 points of damage!",
            "expected_npc": "Goblin"
        },
        {
            "narrative": "A fierce dragon swoops down from the sky, breathing fire!",
            "expected_npc": "Dragon"
        },
        {
            "narrative": "The orc chieftain roars and charges at you with his greataxe!",
            "expected_npc": "Orc Chieftain"
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST CASE {i}: {test['narrative'][:50]}...")
        print(f"{'=' * 80}\n")

        # Clear NPCs before test
        session.npcs_present = []

        print(f"📖 GM Narrative:")
        print(f"   \"{test['narrative']}\"\n")

        print(f"🔍 Extracting mechanics...\n")

        # Extract mechanics (debug logging will show JSON)
        mechanics = extractor.extract(test['narrative'])

        print(f"\n✅ Extraction complete!")
        print(f"   NPCs extracted: {mechanics.npcs_introduced}")

        # Apply NPCs to session
        feedback = applicator.apply_npcs_to_session(mechanics, session)

        print(f"\n📊 Session State:")
        print(f"   npcs_present: {session.npcs_present}")

        if feedback:
            print(f"\n💬 Feedback:")
            for msg in feedback:
                print(f"   {msg}")

        # Verify
        if test['expected_npc'] in session.npcs_present:
            print(f"\n✅ PASS: {test['expected_npc']} was added to npcs_present")
        else:
            print(f"\n❌ FAIL: {test['expected_npc']} was NOT added to npcs_present")
            print(f"   Expected: {test['expected_npc']}")
            print(f"   Got: {session.npcs_present}")

    print(f"\n{'=' * 80}")
    print("TEST COMPLETE")
    print(f"{'=' * 80}\n")

    print("💡 Check the logs above to see the JSON extraction output!")


if __name__ == "__main__":
    test_npc_extraction()
