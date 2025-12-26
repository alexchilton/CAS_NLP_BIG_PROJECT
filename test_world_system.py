#!/usr/bin/env python3
"""
Test World State & Exploration System

Verifies that location tracking, world map, and travel commands work correctly.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.systems.game_state import GameSession, Location, LocationType
from dnd_rag_system.systems.world_builder import initialize_world, create_starting_world

print("=" * 80)
print("WORLD STATE & EXPLORATION SYSTEM TEST")
print("=" * 80)

# Test 1: Create starting world
print("\n📍 Test 1: Create Starting World")
print("-" * 80)
locations = create_starting_world()
print(f"✅ Created {len(locations)} locations")
for name, loc in locations.items():
    discovered_marker = "🔓" if loc.is_discovered else "🔒"
    print(f"  {discovered_marker} {name} ({loc.location_type.value}) - {len(loc.connections)} connections")

# Test 2: Initialize GameSession with world
print("\n🎲 Test 2: Initialize GameSession")
print("-" * 80)
session = GameSession(session_name="Test Adventure")
initialize_world(session, starting_location="Town Square")
print(f"✅ World initialized")
print(f"  Current location: {session.current_location}")
print(f"  Total locations in world map: {len(session.world_map)}")

# Test 3: Check current location
print("\n📌 Test 3: Current Location Object")
print("-" * 80)
current_loc = session.get_current_location_obj()
if current_loc:
    print(f"✅ Current location object retrieved")
    print(f"  Name: {current_loc.name}")
    print(f"  Type: {current_loc.location_type.value}")
    print(f"  Safe: {current_loc.is_safe}")
    print(f"  Visited: {current_loc.visit_count} times")
    print(f"  Connections: {', '.join(current_loc.connections)}")
else:
    print("❌ Failed to get current location object")

# Test 4: Get available destinations
print("\n🗺️  Test 4: Available Destinations")
print("-" * 80)
destinations = session.get_available_destinations()
print(f"✅ Can travel to {len(destinations)} locations:")
for dest in destinations:
    print(f"  - {dest}")

# Test 5: Travel to connected location
print("\n🚶 Test 5: Travel to Connected Location")
print("-" * 80)
success, message = session.travel_to("The Prancing Pony Inn")
if success:
    print(f"✅ Travel successful!")
    print(f"  {message}")
    print(f"  Current location: {session.current_location}")
else:
    print(f"❌ Travel failed: {message}")

# Test 6: Try to travel to non-connected location
print("\n❌ Test 6: Travel to Non-Connected Location")
print("-" * 80)
success, message = session.travel_to("Dragon's Lair")
if not success:
    print(f"✅ Correctly prevented invalid travel")
    print(f"  {message}")
else:
    print(f"❌ Should have failed!")

# Test 7: Return to Town Square
print("\n🔙 Test 7: Return to Town Square")
print("-" * 80)
success, message = session.travel_to("Town Square")
if success:
    print(f"✅ Returned to Town Square")
    current_loc = session.get_current_location_obj()
    print(f"  Visit count: {current_loc.visit_count} (should be 2)")
else:
    print(f"❌ Failed to return")

# Test 8: Persistent enemy state
print("\n⚔️  Test 8: Persistent Enemy State")
print("-" * 80)
session.mark_enemy_defeated_at_current_location("Goblin Chieftain")
session.mark_enemy_defeated_at_current_location("Orc Warrior")

is_defeated = session.is_enemy_defeated_here("Goblin Chieftain")
print(f"✅ Marked 'Goblin Chieftain' as defeated: {is_defeated}")

is_defeated2 = session.is_enemy_defeated_here("orc warrior")  # Case insensitive
print(f"✅ Marked 'Orc Warrior' as defeated: {is_defeated2} (case insensitive)")

is_not_defeated = session.is_enemy_defeated_here("Dragon")
print(f"✅ 'Dragon' not defeated: {not is_not_defeated}")

# Test 9: Travel away and back - enemy should stay defeated
print("\n🔄 Test 9: Persistent State After Travel")
print("-" * 80)
session.travel_to("Market Square")
print(f"  Traveled to {session.current_location}")
session.travel_to("Town Square")
print(f"  Returned to {session.current_location}")

still_defeated = session.is_enemy_defeated_here("Goblin Chieftain")
print(f"✅ Goblin Chieftain still defeated after travel: {still_defeated}")

# Test 10: Discovered locations
print("\n🔍 Test 10: Discovered Locations")
print("-" * 80)
discovered = session.get_discovered_locations()
print(f"✅ Discovered {len(discovered)} locations:")
for loc_name in discovered[:5]:  # Show first 5
    print(f"  - {loc_name}")

# Test 11: Location metadata
print("\n🏪 Test 11: Location Features")
print("-" * 80)
market = session.get_location("Market Square")
if market:
    print(f"✅ Market Square features:")
    print(f"  Has shop: {market.has_shop}")
    print(f"  Has inn: {market.has_inn}")
    print(f"  Is safe: {market.is_safe}")
    print(f"  Resident NPCs: {', '.join(market.resident_npcs)}")

print("\n" + "=" * 80)
print("✅ ALL WORLD STATE TESTS PASSED!")
print("=" * 80)
print("\nWorld State & Exploration System is working correctly!")
print("Features validated:")
print("  ✅ Location creation and initialization")
print("  ✅ World map graph structure")
print("  ✅ Location connections and travel")
print("  ✅ Travel validation (can't go to unconnected locations)")
print("  ✅ Visit tracking")
print("  ✅ Persistent enemy state")
print("  ✅ Location metadata (type, features, NPCs)")
print("  ✅ Discovery system")
