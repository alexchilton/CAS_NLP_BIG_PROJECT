# World Exploration E2E Test Documentation

## Purpose

This test demonstrates the complete world state and exploration system with persistence across location changes.

## What It Tests

### 1. Lazy Location Generation
- `/explore` generates new locations procedurally
- Each new location is unique with contextual type
- New locations are immediately added to world map
- Connections are created automatically

### 2. Location Travel
- `/map` shows available destinations
- `/travel <location>` moves between connected locations
- Cannot travel to unconnected locations
- Travel updates current_location in GameSession

### 3. Persistence - How It Works

#### Location Persistence
**Q: How does lazy generation get saved?**
**A:** Locations are added to `GameSession.world_map` dictionary:
```python
# In /explore command:
new_location = generate_random_location(current_loc)
self.session.add_location(new_location)  # Adds to world_map
self.session.connect_locations(current, new)  # Updates connections
```

**Q: Can we go back to explored locations?**
**A:** Yes! The connections persist in the Location objects:
```python
# Location has connections list
location.connections = ["Town Square", "Dark Forest", ...]

# travel_to() checks connections:
if destination in current_loc.connections:
    # Travel allowed
```

#### Enemy Persistence
**Q: Do dead creatures stay dead?**
**A:** Yes! Via `location.defeated_enemies` set:
```python
# When enemy is defeated:
session.mark_enemy_defeated_at_current_location("Cave Goblin")

# Adds to current location's set:
location.defeated_enemies.add("cave goblin")  # lowercase

# When returning:
if session.is_enemy_defeated_here("Cave Goblin"):
    # Enemy already dead - don't spawn again
```

#### Item Persistence
**Q: Do picked up items stay gone?**
**A:** Partially implemented via `location.moved_items`:
```python
# Structure exists:
location.moved_items = {"Sword": "Thorin's Inventory"}

# But needs integration with item pickup system
# Currently items are tracked in character inventory
# Location-specific item spawning needs work
```

### 4. GM Responses on Return Visits

**Q: Does GM answer similarly when returning?**
**A:** The GM gets the same location description:
```python
# On travel:
self.current_location = destination
self.scene_description = dest_loc.description

# GM prompt includes:
"SCENE: {self.session.scene_description}"
```

However, the GM LLM may add variety. The system could be enhanced to:
- Mention defeated enemies: "Goblin corpses litter the ground"
- Note taken items: "The chest you looted stands empty"
- Track other events via `location.completed_events`

## Test Flow

1. **Load Character** (Thorin)
2. **Check Starting Location** - Verify we're somewhere
3. **/map** - See available destinations
4. **/explore** - Generate first new location
5. **/travel** - Move to first location
6. **Verify GM Response** - Location description shown
7. **/explore again** - Generate second location from first
8. **/travel** - Move to second location
9. **Combat** - Fight "Cave Goblin"
10. **Defeat Enemy** - Goblin marked as defeated
11. **/travel back** - Return to first location
12. **Verify Return** - Can go back
13. **/travel forward** - Go to second location again
14. **Check Persistence** - Goblin still dead!
15. **/locations** - See all discovered locations
16. **Travel to Shop** - Test shop integration
17. **Buy Item** - Verify shopping works

## Running the Test

```bash
# Terminal 1: Start Gradio
python web/app_gradio.py

# Terminal 2: Run test
python e2e_tests/test_world_exploration.py
```

## Expected Results

✅ Character loads
✅ Can explore and discover new locations
✅ Can travel between locations
✅ Generated locations appear in world map
✅ Can return to previous locations
✅ Defeated enemies stay defeated
✅ /locations shows all discovered areas
✅ Shop integration works

## Persistence Limitations (Current)

### What Persists:
- ✅ Generated locations (in world_map)
- ✅ Location connections
- ✅ Defeated enemies (per location)
- ✅ Discovery status
- ✅ Visit counts

### What Doesn't Fully Persist:
- ⚠️ Session state is memory-only (lost on app restart)
- ⚠️ Location-specific item spawns (structure exists, not fully used)
- ⚠️ Dynamic NPC positions (npcs_present is session-level, not location-level)
- ⚠️ Time-based events (day/night doesn't affect locations yet)

### To Add Full Persistence:
```python
# Save world state to disk
session.save_to_json("save_game.json")

# Load on startup
session = GameSession.load_from_json("save_game.json")

# This would require implementing to_dict() for Location, GameSession
```

## Code References

- **Location Class**: `dnd_rag_system/systems/game_state.py` (lines 1-150)
- **World Builder**: `dnd_rag_system/systems/world_builder.py`
- **Navigation Commands**: `dnd_rag_system/systems/gm_dialogue_unified.py` (lines 274-325)
- **Lazy Generation**: `world_builder.py::generate_random_location()`

## Success Criteria

The test passes if:
1. New locations are generated via /explore
2. Can travel to and from generated locations
3. /locations shows all discovered areas
4. Defeated enemy doesn't respawn on return visit
5. Shop commands work in shop locations
6. No crashes or errors during navigation
