# Location & World Map System

## Overview

The D&D RAG system uses a **hybrid approach** combining **fixed starter locations** with **LLM-enhanced procedural generation** for endless exploration.

## ✅ LLM-Enhanced Location Generation (IMPLEMENTED!)

**New implementation** (`/explore` command):

### How It Works:

```python
Player: /explore

1. Python determines structure:
   - Location type (weighted random based on current location)
   - Safety level (safe/dangerous)
   - Connections (bidirectional link to current location)

2. LLM generates flavor (ONCE per location):
   Prompt includes:
   - Current location context
   - Recent battles (defeated enemies)
   - Time of day
   - NPCs present
   - Weather/day
   
   LLM Response:
   NAME: Shadowfang Grotto
   DESCRIPTION: A damp cavern where goblin corpses still litter the floor...

3. Location CACHED in world_map:
   session.world_map["Shadowfang Grotto"] = Location(...)
   
4. On revisit:
   - Load from cache (no regeneration!)
   - LLM only narrates travel
   - Can reference state changes (defeated_enemies, moved_items)
```

### Key Features:

✅ **Generated ONCE** - LLM creates name + description on first `/explore`  
✅ **CACHED forever** - Stored in `world_map`, never regenerated  
✅ **Context-aware** - LLM sees game state (battles, NPCs, time, weather)  
✅ **Graceful fallback** - If LLM fails, falls back to template generation  
✅ **Unique names** - No more "Dark Cavern #3" duplicates  
✅ **Rich descriptions** - Atmospheric, specific to your adventure

### Code Location:

- **LLM enhancement**: `world_builder.py::generate_llm_enhanced_location()` (lines 329-434)
- **Integration**: `gm_dialogue_unified.py` `/explore` command (lines 365-416)
- **Template fallback**: `world_builder.py::generate_random_location()` (still available)

### Testing:

```bash
pytest tests/test_llm_location_generation.py  # 5/5 passing ✅
pytest tests/test_location_generation.py      # 11/11 passing ✅
```

## How It Works

### 1. **Fixed Starting World** 
`dnd_rag_system/systems/world_builder.py::create_starting_world()`

**Pre-built locations:**
- **Town Square** (hub) → connects to everything
- **The Prancing Pony Inn** (safe, has inn)
- **Market Square** (safe, has shop)
- **Temple District** (safe, healing)
- **Adventurer's Guild Hall** (safe, has shop)
- **Town Gates** (safe, transition point)
- **Forest Path** (dangerous)
- **Mountain Road** (dangerous)
- **Dark Cave** (dangerous, undiscovered initially)
- **Old Ruins** (dangerous, undiscovered)
- **Dragon's Lair** (dangerous, undiscovered)
- **Mürren** (dangerous mountain village with shop/inn)

All locations are **pre-connected** with bidirectional paths defined in the `connections` field.

### 2. **Procedural Location Generation**
`dnd_rag_system/systems/world_builder.py::generate_random_location()`

**How `/explore` works:**

1. Player types `/explore` or `/search`
2. System checks current location
3. Checks if location already has 6+ connections (max explored)
4. If space available:
   - Generates new location based on current location type
   - Creates procedural name (e.g., "Dark Cavern", "Ancient Ruins")
   - Adds procedural description
   - Creates **bidirectional connection**
   - Adds to world map

**Generation Rules:**

From **TOWN/TAVERN/SHOP**:
- 40% Forest
- 40% Wilderness  
- 20% Mountain

From **FOREST/WILDERNESS**:
- 30% Cave
- 20% Ruins
- 25% More Forest
- 25% More Wilderness

From **MOUNTAIN**:
- 50% Cave
- 20% Castle
- 30% Ruins

From **DUNGEON/CAVE**:
- 40% Cave
- 30% Ruins
- 30% Dungeon (deeper)

### 3. **World Map Storage**

**In GameSession (`game_state.py`):**

```python
world_map: Dict[str, Location] = {}  # location_name -> Location object
```

**Location object fields:**
- `name: str` - Location name
- `location_type: LocationType` - TOWN, CAVE, FOREST, etc.
- `description: str` - Text description
- `connections: List[str]` - Connected location names
- `is_safe: bool` - Safe for resting?
- `is_discovered: bool` - Has player found it?
- `has_shop: bool` - Can buy/sell items?
- `has_inn: bool` - Can rest here?
- `resident_npcs: List[str]` - NPCs that live here
- `items: List[str]` - Items available to take
- `visit_count: int` - Times visited
- `last_visit_day: int` - Game day of last visit

### 4. **Map Commands**

**`/map`** - Show current location + discovered areas
```
🗺️ WORLD MAP

📍 Current Location: Town Square
   The heart of the town, bustling with activity...

🧭 You can travel to:
  ✅ The Prancing Pony Inn (tavern)
  ✅ Market Square (shop)
  ⚔️ Forest Path (forest)
  ❓ ??? (undiscovered area)

🌍 All Discovered Locations (8):
👉 ✅ Town Square (town) [3x]
   ✅ Market Square (shop)
   ⚔️ Dark Cavern (cave)
   ...

💡 Use `/travel <location>` to move, `/explore` to discover new areas.
```

**`/locations`** - Simple list of discovered locations
```
🗺️ Discovered Locations:
  - Town Square (town) (visited 3x)
  - Market Square (shop)
  - Dark Cavern (cave)
  ...
```

**`/travel <location>`** - Move to connected location
```python
# In gm_dialogue_unified.py (lines 249-262)
if lower_input.startswith('/travel '):
    destination = player_input[8:].strip()
    success, message = self.session.travel_to(destination)
    # Returns success/failure message
```

**`/explore` or `/search`** - Generate new random location
```python
# In gm_dialogue_unified.py (lines 365-394)
new_location = generate_random_location(current_loc)
self.session.add_location(new_location)
self.session.connect_locations(current_loc.name, new_location.name)
```

### 5. **Connection Management**

**Bidirectional connections:**
```python
# When connecting locations
self.session.connect_locations("Town Square", "Forest Path")

# This updates BOTH locations:
# - Town Square.connections includes "Forest Path"
# - Forest Path.connections includes "Town Square"
```

**Max connections:** 6 per location (prevents infinite branching)

**Travel validation:**
```python
def travel_to(self, destination: str) -> Tuple[bool, str]:
    # Check if destination is in current location's connections
    # Check if destination exists in world_map
    # If valid: update current_location, record visit, return description
```

### 6. **Discovery System**

**Locations have `is_discovered` flag:**
- Fixed locations start as `discovered=True` (except caves/dungeons)
- Generated locations start as `discovered=False`
- Becomes discovered when:
  - Player travels there
  - Location is mentioned in narrative
  - Player uses `/explore` to create it

**In map display:**
- Discovered: Shows full name and type
- Undiscovered: Shows "❓ ??? (undiscovered area)"

### 7. **Key Files**

**Core Implementation:**
- `dnd_rag_system/systems/world_builder.py` - Location generation
- `dnd_rag_system/systems/game_state.py` - Location storage, travel logic
- `dnd_rag_system/systems/gm_dialogue_unified.py` - Map commands (lines 249-394)

**Location Types (enum):**
```python
class LocationType(Enum):
    TOWN = "town"
    TAVERN = "tavern"
    SHOP = "shop"
    TEMPLE = "temple"
    GUILD_HALL = "guild_hall"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    CAVE = "cave"
    RUINS = "ruins"
    CASTLE = "castle"
    DUNGEON = "dungeon"
    WILDERNESS = "wilderness"
```

## Summary

**Locations are:**
- ✅ **Fixed** for the starting world (12 hand-crafted locations)
- ✅ **Procedurally generated** via `/explore` command (unlimited)
- ✅ **Fully connected** via bidirectional graph
- ✅ **Stored in world_map** dictionary in GameSession
- ✅ **Tracked** with visit counts, discovery status, connections
- ✅ **Displayed** via `/map` and `/locations` commands
- ✅ **Navigable** via `/travel <location>` command

**The mapping is dynamic and grows as players explore!** 🗺️
