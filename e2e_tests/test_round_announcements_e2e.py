#!/usr/bin/env python3
"""
E2E Test: Round Announcement Order in GM Dialogue

Tests that the GM properly announces rounds in the correct order:
1. Round 1 begins! (at combat start)
2. Combat actions happen
3. Round 2 begins! (only when actually starting round 2)

Scenarios:
A. Player initiates combat: "attack the goblin"
B. Explicit combat start: "/start_combat ogre"
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.systems.game_state import CharacterState


def setup_test_character(gm, spawn_goblin=False):
    """Create a minimal test character (Thorin) in the GM session."""
    # Create minimal character state
    char_state = CharacterState(
        character_name="Thorin Stormshield",
        max_hp=30,
        level=3,
        gold=50
    )
    char_state.current_hp = 30
    char_state.armor_class = 18
    char_state.race = "Dwarf"
    char_state.character_class = "Fighter"

    # Set in session
    gm.session.character_state = char_state

    # Set GM context
    context = """The player is Thorin Stormshield, a level 3 Dwarf Fighter.

PLAYER CHARACTER STATS:
- HP: 30/30  |  AC: 18  |  Prof Bonus: +2
- STR: 16 (+3)  |  DEX: 12 (+1)  |  CON: 14 (+2)

EQUIPMENT: Battleaxe, Shield, Chain Mail"""

    gm.set_context(context)

    # Set location and optionally spawn a goblin
    if spawn_goblin:
        gm.set_location("Goblin Cave", "A dark cave. You see a goblin lurking in the shadows!")
        gm.session.npcs_present = ["goblin"]
    else:
        gm.set_location("Test Arena", "A combat testing area.")


def test_attack_goblin_scenario():
    """Test: Player says 'attack the goblin'"""
    print("\n" + "="*80)
    print("🧪 TEST A: Player says 'attack the goblin'")
    print("="*80)

    # Create fresh GM instance
    db = ChromaDBManager()
    gm = GameMaster(db)

    # Setup test character with goblin in location
    setup_test_character(gm, spawn_goblin=True)

    # Player attacks goblin
    print("\n💬 Player: 'attack the goblin'")
    response = gm.generate_response("attack the goblin", use_rag=False)

    print("\n" + "="*80)
    print("🎭 GM RESPONSE:")
    print("="*80)
    print(response)
    print("="*80)

    # Analyze response
    lines = response.split('\n')

    # Find key phrases
    round_1_idx = None
    round_2_idx = None
    goblin_attack_idx = None
    thorin_turn_idx = None

    for i, line in enumerate(lines):
        if "Round 1 begins" in line:
            round_1_idx = i
        if "Round 2 begins" in line:
            round_2_idx = i
        if "Goblin" in line and ("attack" in line.lower() or "swings" in line.lower() or "strikes" in line.lower()):
            if goblin_attack_idx is None:  # Only record first attack
                goblin_attack_idx = i
        if "Thorin's turn" in line or "Your turn" in line:
            thorin_turn_idx = i

    print("\n🔍 ANALYSIS:")
    print(f"   'Round 1 begins' found at line: {round_1_idx}")
    print(f"   'Round 2 begins' found at line: {round_2_idx}")
    print(f"   'Goblin attack' found at line: {goblin_attack_idx}")
    print(f"   'Thorin's turn' found at line: {thorin_turn_idx}")

    # Assertions
    errors = []

    # MUST announce Round 1
    if round_1_idx is None:
        errors.append("❌ FAIL: Round 1 was never announced!")
    else:
        print("   ✅ Round 1 was announced")

    # If Round 1 exists, it should be BEFORE any combat actions
    if round_1_idx is not None and goblin_attack_idx is not None:
        if round_1_idx > goblin_attack_idx:
            errors.append(f"❌ FAIL: Round 1 announced at line {round_1_idx} AFTER Goblin attacked at line {goblin_attack_idx}!")
        else:
            print("   ✅ Round 1 announced before combat actions")

    # Round 2 should NOT appear in first response (unless combat actually wrapped - which is unlikely)
    # In most cases, player attacks, goblin counterattacks, still Round 1
    if round_2_idx is not None:
        errors.append(f"⚠️  WARNING: Round 2 appeared at line {round_2_idx} - did combat wrap already? This may be valid if both combatants acted.")

    # Print results
    print("\n" + "="*80)
    if errors:
        print("❌ TEST A FAILED:")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print("✅ TEST A PASSED: Round announcements in correct order!")
    print("="*80)

    return True


def test_start_combat_ogre_scenario():
    """Test: Player uses '/start_combat ogre'"""
    print("\n" + "="*80)
    print("🧪 TEST B: Player uses '/start_combat ogre'")
    print("="*80)

    # Create fresh GM instance
    db = ChromaDBManager()
    gm = GameMaster(db)

    # Setup test character
    setup_test_character(gm)

    # Start combat with ogre
    print("\n💬 Player: '/start_combat ogre'")
    response = gm.generate_response("/start_combat ogre", use_rag=False)

    print("\n" + "="*80)
    print("🎭 GM RESPONSE:")
    print("="*80)
    print(response)
    print("="*80)

    # Analyze response
    lines = response.split('\n')

    # Find key phrases
    round_1_idx = None
    round_2_idx = None
    ogre_attack_idx = None
    thorin_turn_idx = None
    initiative_idx = None

    for i, line in enumerate(lines):
        if "Round 1 begins" in line:
            round_1_idx = i
        if "Round 2 begins" in line:
            round_2_idx = i
        if "Ogre" in line and ("attack" in line.lower() or "swings" in line.lower() or "strikes" in line.lower()):
            if ogre_attack_idx is None:  # Only record first attack
                ogre_attack_idx = i
        if "Thorin's turn" in line or "Your turn" in line:
            thorin_turn_idx = i
        if "Initiative Order" in line:
            initiative_idx = i

    print("\n🔍 ANALYSIS:")
    print(f"   'Initiative Order' found at line: {initiative_idx}")
    print(f"   'Round 1 begins' found at line: {round_1_idx}")
    print(f"   'Round 2 begins' found at line: {round_2_idx}")
    print(f"   'Ogre attack' found at line: {ogre_attack_idx}")
    print(f"   'Thorin's turn' found at line: {thorin_turn_idx}")

    # Assertions
    errors = []

    # MUST announce Round 1
    if round_1_idx is None:
        errors.append("❌ FAIL: Round 1 was never announced!")
    else:
        print("   ✅ Round 1 was announced")

    # Round 1 should come AFTER initiative order
    if round_1_idx is not None and initiative_idx is not None:
        if round_1_idx < initiative_idx:
            errors.append(f"❌ FAIL: Round 1 announced at line {round_1_idx} BEFORE Initiative Order at line {initiative_idx}!")
        else:
            print("   ✅ Round 1 announced after Initiative Order")

    # If Ogre attacks (won initiative), Round 1 should be BEFORE the attack
    if round_1_idx is not None and ogre_attack_idx is not None:
        if round_1_idx > ogre_attack_idx:
            errors.append(f"❌ FAIL: Round 1 announced at line {round_1_idx} AFTER Ogre attacked at line {ogre_attack_idx}!")
        else:
            print("   ✅ Round 1 announced before Ogre attack")

    # Round 2 should NOT appear in the initial combat start
    if round_2_idx is not None:
        errors.append(f"❌ FAIL: Round 2 should NOT appear in initial combat start (found at line {round_2_idx})!")
    else:
        print("   ✅ Round 2 did not appear (correct)")

    # Print results
    print("\n" + "="*80)
    if errors:
        print("❌ TEST B FAILED:")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print("✅ TEST B PASSED: Round announcements in correct order!")
    print("="*80)

    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 E2E: Round Announcement Order in GM Dialogue")
    print("="*80)

    test_a_passed = test_attack_goblin_scenario()
    test_b_passed = test_start_combat_ogre_scenario()

    print("\n" + "="*80)
    print("📊 FINAL RESULTS")
    print("="*80)
    print(f"Test A (attack goblin): {'✅ PASSED' if test_a_passed else '❌ FAILED'}")
    print(f"Test B (/start_combat ogre): {'✅ PASSED' if test_b_passed else '❌ FAILED'}")
    print("="*80)

    if test_a_passed and test_b_passed:
        print("\n✅ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED!")
        sys.exit(1)
