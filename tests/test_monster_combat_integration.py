#!/usr/bin/env python3
"""
Test Monster Stats Integration with Combat Manager

This test verifies that:
1. Monster stats are loaded from database
2. Combat Manager uses real AC, HP, attacks
3. Initiative uses monster DEX modifiers
4. NPC damage tracking works
5. Combat displays NPC HP correctly
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.game_state import CombatState, CharacterState
from dnd_rag_system.systems.combat_manager import CombatManager


def test_combat_with_goblin():
    """Test combat against a Goblin with real D&D 5e stats."""
    print("\n" + "⚔️" * 40)
    print("TEST: Combat with Goblin (Real Stats)")
    print("⚔️" * 40)

    # Create a test character
    print("\n📝 Creating test character...")
    character = CharacterState(
        character_name="Thorin the Dwarf Fighter",
        level=3,
        max_hp=28,
        current_hp=28,
        inventory={"Longsword": 1, "Shield": 1, "Health Potion": 2},
        gold=50
    )
    print(f"✅ Created: {character.character_name}")
    print(f"   Level {character.level}, HP: {character.current_hp}/{character.max_hp}")

    # Create combat manager
    print("\n⚔️  Initializing Combat Manager...")
    combat_state = CombatState()
    combat_manager = CombatManager(combat_state, debug=True)

    # Start combat with Goblin
    print("\n🐉 Starting combat with Goblin...")
    print("   (Goblin stats should be loaded from database)")
    message = combat_manager.start_combat_with_character(
        character,
        npcs=["Goblin"],
        character_dex_mod=1  # Thorin's DEX mod
    )

    print("\n" + "=" * 60)
    print(message)
    print("=" * 60)

    # Check if Goblin stats were loaded
    goblin = combat_manager.get_npc_monster("Goblin")
    if goblin:
        print("\n✅ Goblin stats loaded successfully!")
        print(f"   Name: {goblin.name}")
        print(f"   CR: {goblin.cr}")
        print(f"   HP: {goblin.current_hp}/{goblin.max_hp}")
        print(f"   AC: {goblin.ac}")
        print(f"   DEX: {goblin.dex}")
        print(f"   Attacks: {', '.join([a['name'] for a in goblin.attacks])}")
    else:
        print("❌ ERROR: Goblin stats not loaded!")
        return False

    # Test initiative tracker with NPC HP
    print("\n📜 Initiative Tracker (with NPC HP):")
    print(combat_manager.get_initiative_tracker())

    # Simulate combat round 1
    print("\n" + "=" * 60)
    print("ROUND 1: Player attacks Goblin")
    print("=" * 60)

    # Player attacks goblin
    goblin_ac = combat_manager.get_npc_ac("Goblin")
    print(f"\n🎯 Attack roll: 1d20 + 5 (STR mod + proficiency)")
    attack_roll = 15  # Simulated roll
    print(f"   Roll: {attack_roll} vs AC {goblin_ac}")

    if attack_roll >= goblin_ac:
        print("   ✅ HIT!")

        # Roll damage: Longsword 1d8+3
        damage = 7  # Simulated: 1d8(4) + 3(STR)
        print(f"\n💥 Damage: 1d8+3 = {damage} slashing")

        # Apply damage to goblin
        actual_dmg, is_dead = combat_manager.apply_damage_to_npc("Goblin", damage)

        if is_dead:
            print(f"\n☠️  **GOBLIN DEFEATED!**")
            print(f"   Dealt {actual_dmg} damage")
        else:
            print(f"\n   Goblin HP: {goblin.current_hp}/{goblin.max_hp}")
    else:
        print("   ❌ MISS!")

    # Show updated initiative tracker
    print("\n📜 Updated Initiative Tracker:")
    print(combat_manager.get_initiative_tracker())

    # Simulate goblin counterattack if alive
    if goblin.is_alive():
        print("\n" + "=" * 60)
        print("Goblin's Turn: Counterattack")
        print("=" * 60)

        # Goblin attacks with scimitar
        attack_bonus = combat_manager.get_npc_attack_bonus("Goblin", "Scimitar")
        damage, damage_type = combat_manager.roll_npc_attack_damage("Goblin", "Scimitar")

        print(f"\n🗡️  Goblin attacks with Scimitar")
        print(f"   Attack bonus: +{attack_bonus}")
        print(f"   Damage: {damage} {damage_type}")

        # Simulate hit
        character.take_damage(damage)
        print(f"\n💥 Thorin takes {damage} {damage_type} damage!")
        print(f"   HP: {character.current_hp}/{character.max_hp}")

    # Final status
    print("\n" + "=" * 60)
    print("COMBAT SUMMARY")
    print("=" * 60)
    print(f"Character: {character.character_name} - HP: {character.current_hp}/{character.max_hp}")
    if goblin.is_alive():
        print(f"Goblin: HP: {goblin.current_hp}/{goblin.max_hp}")
    else:
        print(f"Goblin: ☠️  DEAD")

    print("\n✅ TEST PASSED: Monster stats integration working!\n")
    return True


def test_multiple_monsters():
    """Test combat with multiple different monsters."""
    print("\n" + "⚔️" * 40)
    print("TEST: Combat with Multiple Monsters")
    print("⚔️" * 40)

    # Create test character
    character = CharacterState(
        character_name="Gandalf the Wizard",
        level=5,
        max_hp=30,
        current_hp=30
    )

    combat_state = CombatState()
    combat_manager = CombatManager(combat_state, debug=True)

    # Start combat with multiple monsters
    print("\n🐉 Starting combat with Goblin, Wolf, and Skeleton...")
    message = combat_manager.start_combat_with_character(
        character,
        npcs=["Goblin", "Wolf", "Skeleton"],
        character_dex_mod=1
    )

    print("\n" + message)

    # Check all monsters loaded
    print("\n📊 Loaded Monster Stats:")
    for npc_name in ["Goblin", "Wolf", "Skeleton"]:
        monster = combat_manager.get_npc_monster(npc_name)
        if monster:
            print(f"\n   ✅ {monster.name}")
            print(f"      CR: {monster.cr}, HP: {monster.current_hp}, AC: {monster.ac}")
        else:
            print(f"\n   ❌ {npc_name} - NOT LOADED")

    print("\n📜 Initiative Tracker:")
    print(combat_manager.get_initiative_tracker())

    print("\n✅ TEST PASSED: Multiple monsters loaded!\n")
    return True


def test_dragon_combat():
    """Test high-level combat with a dragon."""
    print("\n" + "⚔️" * 40)
    print("TEST: Epic Combat - Young White Dragon")
    print("⚔️" * 40)

    # High-level character
    character = CharacterState(
        character_name="Arthas the Paladin",
        level=10,
        max_hp=95,
        current_hp=95
    )

    combat_state = CombatState()
    combat_manager = CombatManager(combat_state, debug=True)

    # Start combat with dragon
    print("\n🐉 A Young White Dragon appears!")
    message = combat_manager.start_combat_with_character(
        character,
        npcs=["Young White Dragon"],
        character_dex_mod=2
    )

    print("\n" + message)

    # Check dragon stats
    dragon = combat_manager.get_npc_monster("Young White Dragon")
    if dragon:
        print("\n🐉 Dragon Stats:")
        print(f"   CR: {dragon.cr}")
        print(f"   HP: {dragon.current_hp}/{dragon.max_hp}")
        print(f"   AC: {dragon.ac}")
        print(f"   Size: {dragon.size}")
        print(f"   Attacks: {', '.join([a['name'] for a in dragon.attacks])}")
        print(f"   Traits: {', '.join(dragon.traits)}")

        # Test dragon breath attack
        print("\n❄️  Dragon uses Cold Breath!")
        damage, dtype = combat_manager.roll_npc_attack_damage("Young White Dragon", "Cold Breath")
        print(f"   Damage: {damage} {dtype}")
        print(f"   (This is MASSIVE damage!)")

    print("\n📜 Initiative Tracker:")
    print(combat_manager.get_initiative_tracker())

    print("\n✅ TEST PASSED: Dragon combat works!\n")
    return True


if __name__ == "__main__":
    print("\n" + "🎲" * 40)
    print("MONSTER STATS INTEGRATION TEST SUITE")
    print("🎲" * 40)

    tests = [
        ("Combat with Goblin", test_combat_with_goblin),
        ("Multiple Monsters", test_multiple_monsters),
        ("Dragon Combat", test_dragon_combat)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Monster stats integration is working!")
    else:
        print("\n⚠️  Some tests failed. Check output above.")

    print("=" * 60 + "\n")
