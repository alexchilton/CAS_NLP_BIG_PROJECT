#!/usr/bin/env python3
"""
Test Item Persistence in Locations

Tests how items work with lazy-generated locations:
1. Location gets added to map via /explore
2. Items can be "found" at locations
3. Items taken by character are tracked
4. Items stay gone when returning to location
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.systems.game_state import GameSession, Location, LocationType
from dnd_rag_system.systems.world_builder import initialize_world, generate_random_location

print("=" * 80)
print("ITEM PERSISTENCE IN LOCATIONS TEST")
print("=" * 80)

# Test 1: Lazy location gets added to map
print("\n📍 Test 1: Lazy Location Gets Added to Map")
print("-" * 80)
session = GameSession(session_name="Item Test")
initialize_world(session, starting_location="Town Square")

initial_count = len(session.world_map)
print(f"Initial world map: {initial_count} locations")

# Simulate /explore - generate new location
current_loc = session.get_current_location_obj()
new_location = generate_random_location(current_loc)
print(f"Generated: {new_location.name}")

# Add to map (this is what /explore command does)
session.add_location(new_location)
session.connect_locations(current_loc.name, new_location.name)

final_count = len(session.world_map)
print(f"✅ World map now: {final_count} locations (was {initial_count})")
assert final_count == initial_count + 1, "Should have added 1 location"

# Verify it's connected
assert new_location.name in current_loc.connections, "Should be connected"
assert current_loc.name in new_location.connections, "Should be bidirectional"
print(f"✅ Connections: {current_loc.name} ↔ {new_location.name}")

# Test 2: Location has items structure
print("\n📦 Test 2: Location Has Item Tracking Structure")
print("-" * 80)
print(f"moved_items dict: {new_location.moved_items}")
print(f"Type: {type(new_location.moved_items)}")
assert isinstance(new_location.moved_items, dict), "Should be a dict"
print("✅ Location has moved_items structure")

# Test 3: Simulate item spawning at location
print("\n🎁 Test 3: Spawn Items at Location")
print("-" * 80)

# In a real implementation, we'd have a system that decides what items spawn
# For now, let's manually add some items to test the tracking
class LocationItems:
    """Helper to track items at a location."""
    def __init__(self):
        self.items_present = {}  # {item_name: quantity}
    
    def add_item(self, item_name, quantity=1):
        self.items_present[item_name] = self.items_present.get(item_name, 0) + quantity
    
    def remove_item(self, item_name, quantity=1):
        if item_name in self.items_present:
            self.items_present[item_name] -= quantity
            if self.items_present[item_name] <= 0:
                del self.items_present[item_name]
            return True
        return False
    
    def has_item(self, item_name):
        return item_name in self.items_present and self.items_present[item_name] > 0

# Create item tracker for the new location
location_items = LocationItems()
location_items.add_item("Ancient Sword", 1)
location_items.add_item("Gold Coins", 50)
location_items.add_item("Health Potion", 2)

print(f"Items at {new_location.name}:")
for item, qty in location_items.items_present.items():
    print(f"  - {item} x{qty}")
print("✅ Items spawned at location")

# Test 4: Character picks up item
print("\n🎒 Test 4: Character Picks Up Item")
print("-" * 80)

# Simulate character picking up the sword
item_to_take = "Ancient Sword"
print(f"Character takes: {item_to_take}")

# Remove from location
if location_items.remove_item(item_to_take):
    # Track that it was moved
    new_location.moved_items[item_to_take] = "Thorin's Inventory"
    print(f"✅ Removed from location")
    print(f"✅ Tracked in moved_items: {new_location.moved_items}")
else:
    print("❌ Failed to remove item")

# Verify item is gone from location
assert not location_items.has_item(item_to_take), "Item should be gone"
print(f"✅ '{item_to_take}' no longer at location")

# Remaining items
print(f"\nRemaining items at {new_location.name}:")
for item, qty in location_items.items_present.items():
    print(f"  - {item} x{qty}")

# Test 5: Travel away and back - item should stay gone
print("\n🔄 Test 5: Return to Location - Item Stays Gone")
print("-" * 80)

# Travel to another location
session.travel_to(current_loc.name)
print(f"Traveled to {current_loc.name}")

# Travel back
session.travel_to(new_location.name)
print(f"Returned to {new_location.name}")

# Check moved_items persisted
print(f"moved_items: {new_location.moved_items}")
assert item_to_take in new_location.moved_items, "Should remember item was taken"
print(f"✅ System remembers '{item_to_take}' was taken")

# Check item is still gone
assert not location_items.has_item(item_to_take), "Item should still be gone"
print(f"✅ '{item_to_take}' still not at location")

# Test 6: Pick up another item
print("\n🎒 Test 6: Pick Up Second Item")
print("-" * 80)

item_to_take_2 = "Health Potion"
print(f"Character takes 1x {item_to_take_2}")

if location_items.remove_item(item_to_take_2, 1):
    new_location.moved_items[item_to_take_2] = "Thorin's Inventory"
    print(f"✅ Removed 1x potion")

print(f"\nRemaining items:")
for item, qty in location_items.items_present.items():
    print(f"  - {item} x{qty}")

print(f"\nmoved_items: {new_location.moved_items}")
assert len(new_location.moved_items) == 2, "Should track both items"
print(f"✅ Tracking {len(new_location.moved_items)} moved items")

# Test 7: Multiple visits - all changes persist
print("\n🔄 Test 7: Multiple Visits - Changes Persist")
print("-" * 80)

# Leave and return multiple times
for i in range(3):
    session.travel_to(current_loc.name)
    session.travel_to(new_location.name)

print(f"After {3} round trips:")
print(f"  Visit count: {new_location.visit_count}")
print(f"  moved_items: {new_location.moved_items}")
print(f"  Items still at location: {list(location_items.items_present.keys())}")

assert len(new_location.moved_items) == 2, "Should still track both items"
assert "Ancient Sword" in new_location.moved_items, "Sword still tracked"
assert "Health Potion" in new_location.moved_items, "Potion still tracked"
print("✅ All changes persisted across multiple visits")

# Test 8: Integration with session
print("\n🗺️  Test 8: Location in Session World Map")
print("-" * 80)

retrieved_loc = session.get_location(new_location.name)
assert retrieved_loc is not None, "Should be in world map"
assert retrieved_loc.name == new_location.name, "Should be same location"
assert retrieved_loc.moved_items == new_location.moved_items, "Should have same moved_items"
print(f"✅ Location properly stored in session.world_map")
print(f"✅ moved_items accessible via session: {retrieved_loc.moved_items}")

print("\n" + "=" * 80)
print("ANALYSIS & FINDINGS")
print("=" * 80)

print("""
CURRENT STATE:
=============

✅ Lazy locations ARE added to map:
   - session.add_location(new_loc)
   - session.connect_locations(current, new)
   - Accessible via session.world_map[name]

✅ Item tracking structure EXISTS:
   - location.moved_items = {item: destination}
   - Persists across visits
   - Can be queried

❌ Item tracking NOT INTEGRATED:
   - No automatic item spawning
   - No automatic pickup tracking
   - Items tracked in character.inventory only
   - Location doesn't know about its items

WHAT'S NEEDED:
=============

1. Location Item System:
   - Add items_present to Location (or separate system)
   - Spawn items at generation time
   - Track quantities

2. Pickup Integration:
   - When character picks up item
   - Remove from location.items_present
   - Add to character.inventory
   - Record in location.moved_items

3. GM Integration:
   - GM should mention items when describing location
   - Skip items that are in moved_items
   - "You see a glinting sword" (first visit)
   - "The sword you took is gone" (return visit)

WORKAROUND (Current):
====================

For now, items can be:
- Described by GM narratively
- Tracked manually in moved_items
- Added to character inventory via commands

The infrastructure is there, just needs connection!
""")

print("\n" + "=" * 80)
print("✅ ALL ITEM PERSISTENCE TESTS PASSED!")
print("=" * 80)
print("\nConclusion:")
print("  ✅ Lazy locations get added to map correctly")
print("  ✅ moved_items structure exists and persists")
print("  ⚠️  Need to integrate item spawning/pickup system")
print("  ⚠️  Need to connect location items with GM descriptions")
