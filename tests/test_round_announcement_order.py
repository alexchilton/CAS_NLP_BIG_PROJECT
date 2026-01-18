"""
Test Round Announcement Order Fix

This test verifies that round announcements happen in the correct order:
1. Round X begins!
2. NPC attacks (if any)
3. Player's turn!

Bug: Previously, the order was:
1. NPC's turn!
2. Round X begins!
3. Player's turn!

The fix ensures that:
- advance_turn() does NOT announce NPC turns (since they're auto-processed)
- process_npc_turns() announces round changes during NPC processing
- process_npc_turns() announces the player's turn after all NPCs are done
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.combat_manager import CombatManager
from dnd_rag_system.systems.game_state import CombatState, CharacterState
from dnd_rag_system.systems.monster_stat_system import MonsterInstance


def create_test_character(name="Hero"):
    """Create a test character."""
    char = CharacterState(
        character_name=name,
        max_hp=30,
        level=3
    )
    return char


def create_test_goblin(name="Goblin"):
    """Create a test goblin."""
    goblin = MonsterInstance(
        name=name,
        cr=0.25,
        size="Small",
        type="humanoid",
        ac=15,
        max_hp=7,
        current_hp=7,
        speed=30,
        str=8,
        dex=14,
        con=10,
        int=10,
        wis=8,
        cha=8,
        attacks=[{
            "name": "Scimitar",
            "to_hit": 4,
            "damage": "1d6+2",
            "damage_type": "slashing"
        }],
        traits=[],
        description="A small goblin"
    )
    return goblin


def test_round_announcement_order():
    """Test that round changes are announced before NPC actions."""
    print("\n" + "="*80)
    print("🧪 TEST: Round Announcement Order")
    print("="*80)

    # Setup combat with Hero (15) and Goblin (12)
    # Turn order: Hero -> Goblin -> Hero -> Goblin -> ...
    combat_state = CombatState()
    combat_manager = CombatManager(combat_state, debug=True)

    # Add combatants
    char = create_test_character("Hero")
    goblin = create_test_goblin("Goblin")

    # Start combat (Round 1)
    combat_state.start_combat({
        'Hero': 15,
        'Goblin': 12
    })
    combat_manager.npc_monsters['Goblin'] = goblin

    print("\n✅ Combat started (Round 1, Hero's turn)")

    # === Round 1, Hero's turn ===
    current = combat_state.get_current_turn()
    print(f"   Current turn: {current} (Round {combat_state.round_number})")
    assert current == "Hero", "Should be Hero's turn"
    assert combat_state.round_number == 1, "Should be Round 1"

    # Hero attacks (simulated)
    print("\n📖 Hero attacks...")

    # Advance turn (should move to Goblin, Round 1)
    turn_msg = combat_manager.advance_turn()
    print(f"\n💬 advance_turn() returned: {repr(turn_msg)}")

    # Should be empty or minimal because Goblin is an NPC
    assert "Goblin's turn" not in turn_msg, "❌ FAIL: Should NOT announce Goblin's turn in advance_turn()"

    # Process NPC turns (Goblin attacks, advances to Hero, still Round 1)
    npc_actions = combat_manager.process_npc_turns(target_ac=15)
    npc_msg = "\n".join(npc_actions)
    print(f"\n💬 process_npc_turns() returned:\n{npc_msg}")

    # Goblin should attack
    assert len(npc_actions) > 0, "Goblin should have attacked"
    assert "Goblin" in npc_msg, "Goblin's attack should be in NPC actions"

    # Should announce Hero's turn after Goblin
    assert "Hero's turn" in npc_msg, "Should announce Hero's turn after Goblin's attack"

    # Actually WITH only 2 combatants, round wraps here! So Round 2 SHOULD be announced
    assert "Round 2 begins" in npc_msg, "Round 2 should be announced when wrapping"

    # Check order: Round announcement should come BEFORE Hero's turn announcement
    if "Round 2 begins" in npc_msg:
        round_idx = npc_msg.find("Round 2 begins")
        hero_turn_idx = npc_msg.find("Hero's turn")
        print(f"\n🔍 First round wrap analysis:")
        print(f"   'Round 2 begins' at index: {round_idx}")
        print(f"   'Hero's turn' at index: {hero_turn_idx}")
        assert round_idx < hero_turn_idx, "❌ FAIL: Round announcement must come BEFORE turn announcement!"

    current = combat_state.get_current_turn()
    print(f"\n✅ After NPC processing: {current}'s turn (Round {combat_state.round_number})")
    assert current == "Hero", "Should be Hero's turn"
    assert combat_state.round_number == 2, "Should be Round 2 after wrapping"

    # === Round 2, Hero's turn ===
    print("\n📖 Hero attacks again (Round 2)...")

    # Advance turn (should move to Goblin, still Round 2)
    turn_msg = combat_manager.advance_turn()
    print(f"\n💬 advance_turn() returned: {repr(turn_msg)}")

    # Should NOT announce round change here (Goblin is NPC, so process_npc_turns will handle it)
    assert "Round 3 begins" not in turn_msg, "❌ FAIL: Should NOT announce Round 3 in advance_turn() when next turn is NPC"

    # Process NPC turns (Goblin attacks, advances to Hero, NOW Round 3)
    npc_actions = combat_manager.process_npc_turns(target_ac=15)
    npc_msg = "\n".join(npc_actions)
    print(f"\n💬 process_npc_turns() returned:\n{npc_msg}")

    # Check order: Round announcement should come BEFORE Hero's turn announcement
    round_idx = npc_msg.find("Round 3 begins")
    hero_turn_idx = npc_msg.find("Hero's turn")

    print(f"\n🔍 Second round wrap analysis:")
    print(f"   'Round 3 begins' at index: {round_idx}")
    print(f"   'Hero's turn' at index: {hero_turn_idx}")

    assert round_idx != -1, "❌ FAIL: Round 3 announcement missing!"
    assert hero_turn_idx != -1, "❌ FAIL: Hero's turn announcement missing!"
    assert round_idx < hero_turn_idx, "❌ FAIL: Round announcement must come BEFORE turn announcement!"

    current = combat_state.get_current_turn()
    print(f"\n✅ After NPC processing: {current}'s turn (Round {combat_state.round_number})")
    assert current == "Hero", "Should be Hero's turn"
    assert combat_state.round_number == 3, "Should be Round 3 now"

    print("\n" + "="*80)
    print("✅ TEST PASSED: Round announcements happen in correct order!")
    print("   Order: Round X begins → NPC actions → Player's turn")
    print("="*80)


if __name__ == "__main__":
    test_round_announcement_order()
