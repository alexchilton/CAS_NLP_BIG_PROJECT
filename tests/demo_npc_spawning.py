#!/usr/bin/env python3
"""
Demo: NPC Spawning Logic

Shows the three different NPC spawning modes:
1. Friendly NPCs in towns/shops (normal gameplay)
2. No NPCs in combat locations (player explores naturally)
3. Deterministic NPCs via TEST_NPCS (testing)
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from web.app_gradio import load_character_with_location, gm

print("\n" + "🎭" * 40)
print("NPC SPAWNING LOGIC DEMO")
print("🎭" * 40)

# Test 1: Town with friendly NPCs (normal gameplay)
print("\n" + "=" * 80)
print("SCENARIO 1: Town/Shop - Friendly NPCs (NORMAL GAMEPLAY)")
print("=" * 80)

# Clear TEST_NPCS to simulate normal gameplay
if 'TEST_NPCS' in os.environ:
    del os.environ['TEST_NPCS']

os.environ['TEST_START_LOCATION'] = 'The Prancing Pony Inn'

print(f"\n🎮 Normal Gameplay Mode:")
print(f"   Location: The Prancing Pony Inn")
print(f"   TEST_NPCS: (not set)")

gm.session.npcs_present = []  # Reset
loc_name, loc_desc, char_name = load_character_with_location("Thorin")

print(f"\n✅ Loaded at: {loc_name}")
print(f"👥 NPCs Present: {gm.session.npcs_present}")

if gm.session.npcs_present:
    print("\n✅ SUCCESS: Friendly NPCs auto-spawned in town!")
else:
    print("\n❌ FAIL: Expected friendly NPCs in town")

# Test 2: Combat location with NO NPCs (normal gameplay)
print("\n" + "=" * 80)
print("SCENARIO 2: Goblin Cave - No Automatic NPCs (EXPLORATION)")
print("=" * 80)

if 'TEST_NPCS' in os.environ:
    del os.environ['TEST_NPCS']

os.environ['TEST_START_LOCATION'] = 'Goblin Cave Entrance'

print(f"\n🎮 Normal Gameplay Mode:")
print(f"   Location: Goblin Cave Entrance")
print(f"   TEST_NPCS: (not set)")

gm.session.npcs_present = []  # Reset
loc_name, loc_desc, char_name = load_character_with_location("Thorin")

print(f"\n✅ Loaded at: {loc_name}")
print(f"👥 NPCs Present: {gm.session.npcs_present}")

if not gm.session.npcs_present:
    print("\n✅ SUCCESS: No forced combat encounters!")
    print("   Player will discover goblins through exploration/LLM")
else:
    print(f"\n❌ FAIL: Expected no NPCs, got {gm.session.npcs_present}")

# Test 3: Deterministic NPCs via TEST_NPCS (testing mode)
print("\n" + "=" * 80)
print("SCENARIO 3: Any Location with TEST_NPCS (TESTING MODE)")
print("=" * 80)

os.environ['TEST_START_LOCATION'] = 'Dragon Lair'
os.environ['TEST_NPCS'] = 'Ancient Red Dragon, Kobold Servant'

print(f"\n🧪 Test Mode:")
print(f"   Location: Dragon Lair")
print(f"   TEST_NPCS: Ancient Red Dragon, Kobold Servant")

gm.session.npcs_present = []  # Reset
loc_name, loc_desc, char_name = load_character_with_location("Thorin")

print(f"\n✅ Loaded at: {loc_name}")
print(f"👥 NPCs Present: {gm.session.npcs_present}")

if "Ancient Red Dragon" in gm.session.npcs_present and "Kobold Servant" in gm.session.npcs_present:
    print("\n✅ SUCCESS: Deterministic NPCs for testing!")
else:
    print(f"\n❌ FAIL: Expected ['Ancient Red Dragon', 'Kobold Servant'], got {gm.session.npcs_present}")

# Test 4: TEST_NPCS overrides town NPCs
print("\n" + "=" * 80)
print("SCENARIO 4: TEST_NPCS Overrides Town NPCs")
print("=" * 80)

os.environ['TEST_START_LOCATION'] = 'The Prancing Pony Inn'
os.environ['TEST_NPCS'] = 'Evil Assassin'  # Override friendly NPCs with test NPC

print(f"\n🧪 Test Mode (overriding town NPCs):")
print(f"   Location: The Prancing Pony Inn (normally has friendly NPCs)")
print(f"   TEST_NPCS: Evil Assassin (test override)")

gm.session.npcs_present = []  # Reset
loc_name, loc_desc, char_name = load_character_with_location("Thorin")

print(f"\n✅ Loaded at: {loc_name}")
print(f"👥 NPCs Present: {gm.session.npcs_present}")

if gm.session.npcs_present == ["Evil Assassin"]:
    print("\n✅ SUCCESS: TEST_NPCS overrides friendly town NPCs!")
else:
    print(f"\n❌ FAIL: Expected ['Evil Assassin'], got {gm.session.npcs_present}")

print("\n" + "=" * 80)
print("✅ DEMO COMPLETE!")
print("=" * 80)
print("\n📊 Summary:")
print("   ✅ Towns/shops have friendly NPCs (normal gameplay)")
print("   ✅ Combat locations have NO forced NPCs (exploration)")
print("   ✅ TEST_NPCS provides deterministic NPCs (testing)")
print("   ✅ TEST_NPCS overrides everything (full control)")
print("=" * 80 + "\n")
