# Item Persistence in Lazy-Generated Locations

## Your Questions Answered

### 1. How do lazy-generated locations get added to the map?

**Answer:** Via the `/explore` command:

```python
# When player uses /explore:
current_loc = session.get_current_location_obj()

# Generate new location (lazy generation)
new_location = generate_random_location(current_loc)

# Add to world map
session.add_location(new_location)

# Create bidirectional connection
session.connect_locations(current_loc.name, new_location.name)
```

**Result:**
- New location is in `session.world_map` dictionary
- Connections are bidirectional (A→B and B→A)
- Can be accessed via `session.get_location(name)`
- Persists for entire session (in-memory)

### 2. How are items tracked when found and taken?

**Current State:**

```python
# Location has the structure:
location.moved_items = {
    "Ancient Sword": "Thorin's Inventory",
    "Health Potion": "Elara's Inventory"
}
```

**What Works:** ✅
- `moved_items` dictionary exists
- Persists across visits
- Can be queried

**What Doesn't Work Yet:** ⚠️
- No automatic item spawning at locations
- No automatic pickup integration
- Items only tracked in `character.inventory`
- GM doesn't know about location items

### 3. Complete Item Lifecycle (With Tests)

See `test_location_items.py` for comprehensive tests:

```python
# Test 1: Location added to map ✅
session.add_location(new_location)
assert new_location.name in session.world_map

# Test 2: Item tracking structure exists ✅
assert isinstance(new_location.moved_items, dict)

# Test 3: Spawn items at location ✅
location_items.add_item("Ancient Sword", 1)

# Test 4: Character picks up item ✅
location_items.remove_item("Ancient Sword")
location.moved_items["Ancient Sword"] = "Thorin's Inventory"

# Test 5: Return to location - item stays gone ✅
session.travel_to(other_location)
session.travel_to(original_location)
assert "Ancient Sword" in location.moved_items  # Still tracked!
assert not location_items.has_item("Ancient Sword")  # Still gone!

# Test 6: Multiple items tracked ✅
# Test 7: Persists across multiple visits ✅
# Test 8: Accessible via session.world_map ✅
```

**All 8 tests pass!**

### 4. Visit Count Mentions

**You said:** "It doesn't really need to mention the visit count"

**You're absolutely right!** I've updated the system:

**Before:**
```
RETURN VISIT: This is the party's 2nd time at Dark Forest.
```

**After:**
```
NOTE: The party has been here before. Describe naturally.
```

**Result:**
- GM won't say "2nd visit" or count explicitly
- Will naturally acknowledge familiarity
- More immersive narrative

## What's Implemented vs. What's Missing

### ✅ **Implemented & Tested:**

1. **Lazy Location Generation**
   - `/explore` generates new locations
   - Added to `session.world_map`
   - Bidirectional connections
   - Persists across visits

2. **Location Persistence**
   - `location.visit_count` tracks visits
   - `location.defeated_enemies` set (enemies stay dead!)
   - `location.moved_items` dict (infrastructure exists)
   - `location.completed_events` set

3. **Travel System**
   - `/travel <location>` validates connections
   - `/map` shows destinations
   - `/locations` shows discovered areas
   - Travel updates location state

4. **GM Context**
   - Knows about return visits (without counting)
   - Knows about defeated enemies
   - Can mention aftermath naturally

### ⚠️ **Missing (Infrastructure Exists, Not Connected):**

1. **Automatic Item Spawning**
   - Need to decide what items spawn where
   - Based on location type?
   - Random generation?

2. **Item Pickup Integration**
   - Need to connect player commands to item removal
   - Track in both `character.inventory` AND `location.moved_items`
   - Update GM descriptions

3. **GM Item Descriptions**
   - GM should mention items at locations
   - Skip items that are in `moved_items`
   - "You see a glinting sword" vs "The sword is gone"

## How to Implement Full Item System (Future)

```python
# 1. Add items to Location
class Location:
    items_present: Dict[str, int] = field(default_factory=dict)
    
# 2. Spawn items at generation
def generate_random_location(from_loc):
    # ... existing code ...
    
    # Add location-appropriate items
    if location_type == LocationType.CAVE:
        new_location.items_present = {
            "Gold Coins": random.randint(10, 50),
            "Ancient Artifact": 1
        }
    
    return new_location

# 3. Pickup command
def handle_pickup(item_name, location, character):
    if item_name in location.items_present:
        # Remove from location
        location.items_present[item_name] -= 1
        if location.items_present[item_name] <= 0:
            del location.items_present[item_name]
        
        # Track in moved_items
        location.moved_items[item_name] = f"{character.name}'s Inventory"
        
        # Add to character
        character.inventory.append(item_name)
        
        return f"You take the {item_name}."

# 4. GM description integration
def build_location_description(location):
    desc = location.description
    
    # Add items if present
    if location.items_present:
        items = ", ".join(location.items_present.keys())
        desc += f"\n\nYou notice: {items}"
    
    # Mention taken items
    if location.moved_items:
        desc += f"\n(Items taken: {', '.join(location.moved_items.keys())})"
    
    return desc
```

## Summary

**Your Questions:**

1. ✅ **How are locations added to map?**
   → Via `session.add_location()` + `connect_locations()`

2. ✅ **How are items tracked?**
   → `location.moved_items` dict (exists, partially used)

3. ✅ **What happens when items are taken?**
   → Infrastructure exists, needs integration with pickup system

4. ✅ **Visit count mentions?**
   → Removed! GM now describes naturally without counting

**Tests Written:** 8/8 passing in `test_location_items.py`

**Status:** Infrastructure complete, just needs item system connection!
