"""
Test Round Order When New Round Starts with NPC Turn

Verifies that when a new round begins with an NPC's turn, the announcement
order is:
1. Round X begins!
2. NPC attacks
3. Next combatant's turn

Initiative: Ogre (15), Goblin (12), Hero (10)
Round 2 starts with Ogre's turn, so we should see:
  - Round 2 begins!
  - Ogre attacks!
  - Goblin attacks!
  - Hero's turn!
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.combat_manager import CombatManager
from dnd_rag_system.systems.game_state import CombatState
from dnd_rag_system.systems.monster_stat_system import MonsterInstance


def create_goblin():
    return MonsterInstance(
        name="Goblin",
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
        attacks=[{"name": "Scimitar", "to_hit": 4, "damage": "1d6+2", "damage_type": "slashing"}],
        traits=[],
        description="A goblin"
    )


def create_ogre():
    return MonsterInstance(
        name="Ogre",
        cr=2,
        size="Large",
        type="giant",
        ac=11,
        max_hp=59,
        current_hp=59,
        speed=40,
        str=19,
        dex=8,
        con=16,
        int=5,
        wis=7,
        cha=7,
        attacks=[{"name": "Greatclub", "to_hit": 6, "damage": "2d8+4", "damage_type": "bludgeoning"}],
        traits=[],
        description="An ogre"
    )


def test_npc_round_start():
    """Test that round announcement appears before NPC actions when round starts with NPC."""
    print("\n" + "="*80)
    print("🧪 TEST: Round Starting with NPC Turn")
    print("="*80)

    combat_state = CombatState()
    combat_manager = CombatManager(combat_state, debug=True)

    # Initiative order: Ogre (15), Goblin (12), Hero (10)
    combat_state.start_combat({
        'Ogre': 15,
        'Goblin': 12,
        'Hero': 10
    })

    combat_manager.npc_monsters['Ogre'] = create_ogre()
    combat_manager.npc_monsters['Goblin'] = create_goblin()

    print("\n✅ Combat started (Round 1, Ogre's turn)")
    print(f"   Initiative: Ogre (15), Goblin (12), Hero (10)")

    # === Round 1: Ogre -> Goblin -> Hero ===
    # NPCs auto-process, should end on Hero's turn
    npc_actions = combat_manager.process_npc_turns(target_ac=15)
    npc_msg = "\n".join(npc_actions)

    print(f"\n💬 Round 1 NPC processing:\n{npc_msg}\n")

    assert "Ogre" in npc_msg, "Ogre should have attacked"
    assert "Goblin" in npc_msg, "Goblin should have attacked"
    assert "Hero's turn" in npc_msg, "Should announce Hero's turn"
    assert "Round 2 begins" not in npc_msg, "Should NOT start Round 2 yet"

    current = combat_state.get_current_turn()
    assert current == "Hero", f"Should be Hero's turn, got {current}"
    assert combat_state.round_number == 1, "Should still be Round 1"

    print("✅ Round 1 complete: Ogre attacked, Goblin attacked, now Hero's turn")

    # === Hero's turn in Round 1 ===
    print("\n📖 Hero attacks...")

    # Advance past Hero (should move to Ogre and start Round 2)
    turn_msg = combat_manager.advance_turn()
    print(f"💬 advance_turn(): {repr(turn_msg)}")

    # advance_turn() should announce the round change
    assert "Round 2 begins" in turn_msg, "advance_turn() should announce round change"

    # Process NPC turns for Round 2
    npc_actions = combat_manager.process_npc_turns(target_ac=15)
    npc_msg = "\n".join(npc_actions)

    print(f"\n💬 Round 2 NPC processing:\n{npc_msg}\n")

    # Find positions
    ogre_idx = npc_msg.find("Ogre attacks")
    goblin_idx = npc_msg.find("Goblin attacks")
    hero_idx = npc_msg.find("Hero's turn")

    print("🔍 Message order analysis:")
    print(f"   'Ogre attacks' at: {ogre_idx}")
    print(f"   'Goblin attacks' at: {goblin_idx}")
    print(f"   'Hero's turn' at: {hero_idx}")

    # Verify correct order (Round 2 was already announced by advance_turn())
    assert ogre_idx != -1, "Ogre must attack"
    assert goblin_idx != -1, "Goblin must attack"
    assert hero_idx != -1, "Hero's turn must be announced"

    assert ogre_idx < goblin_idx, "Ogre should attack before Goblin"
    assert goblin_idx < hero_idx, "Goblin's attack should come before Hero's turn announcement"

    # Round 2 should NOT be announced again by process_npc_turns (advance_turn already did it)
    assert "Round 2 begins" not in npc_msg, "Round 2 should not be announced twice"

    print("\n" + "="*80)
    print("✅ TEST PASSED!")
    print("   Correct order:")
    print("   1. advance_turn() announces: Round 2 begins")
    print("   2. process_npc_turns() shows: Ogre → Goblin → Hero's turn")
    print("="*80)


if __name__ == "__main__":
    test_npc_round_start()
