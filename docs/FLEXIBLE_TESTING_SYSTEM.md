# Flexible Testing System for E2E Tests

## Overview

The game now supports **completely flexible E2E testing** via environment variables. You can create any scenario you want for testing: custom locations, specific NPCs, hidden items, etc.

## Environment Variables

### `TEST_START_LOCATION`
**Set starting location for tests**

```bash
TEST_START_LOCATION="Goblin Cave"
TEST_START_LOCATION="Dragon's Lair"
TEST_START_LOCATION="Underwater Temple"  # Custom location
```

- If location exists in predefined list → uses that description
- If location is custom → creates it with generic or custom description

### `TEST_LOCATION_DESC`
**Optional custom description for location**

```bash
TEST_START_LOCATION="Haunted Mansion" \
TEST_LOCATION_DESC="An old manor shrouded in mist. Ghostly wails echo through the halls." \
python3 test.py
```

### `TEST_NPCS`
**Deterministic NPC spawning for tests**

```bash
TEST_NPCS="Goblin"                    # Single NPC
TEST_NPCS="Goblin, Orc"              # Multiple NPCs
TEST_NPCS="Ancient Red Dragon"        # Boss monster
```

**Behavior:**
- `TEST_NPCS` set → Uses those NPCs (overrides everything)
- `TEST_NPCS` not set:
  - Towns/Inns → Friendly NPCs (merchants, shopkeepers)
  - Combat locations → No NPCs (player explores naturally)

### `TEST_ITEMS`
**Add items to location for testing**

```bash
# Simple items on ground
TEST_ITEMS="Healing Potion, Gold Coins"

# Items in container (for hidden treasure scenarios)
TEST_ITEMS="Hidden Chest:Magic Ring of Protection, 100 Gold"
TEST_ITEMS="Ancient Urn:Potion of Invisibility"
```

## Complete Example: Your Goblin Treasure Scenario

```bash
# Set up: Goblin Cave with goblin and hidden chest containing magic ring
TEST_START_LOCATION="Goblin Cave" \
TEST_LOCATION_DESC="A dark cave filled with goblin markings. The air is thick with danger." \
TEST_NPCS="Goblin" \
TEST_ITEMS="Hidden Chest:Magic Ring of Protection" \
HEADLESS=true python3 e2e_tests/test_goblin_treasure_persistence.py
```

**What this test does:**
1. ✅ Starts in Goblin Cave with goblin and hidden chest
2. ✅ Kills the goblin in combat
3. ✅ Searches and finds the hidden chest
4. ✅ Takes the magic ring (adds to inventory)
5. ✅ Leaves the location
6. ✅ Returns to Goblin Cave
7. ✅ Verifies state persistence:
   - Dead goblin still there
   - Chest still there (but empty)
   - Ring NOT in chest (already taken)
   - Ring IN inventory

## NPC Spawning Logic

### Normal Gameplay (no `TEST_NPCS`)

**Towns/Shops/Inns:**
```
The Prancing Pony Inn → Innkeeper Butterbur, Traveling Merchant
The Market Square → Merchant, Blacksmith, Potion Seller
The Town Gates → Town Guard, General Store Shopkeeper
```

**Combat Locations:**
```
Goblin Cave → No NPCs (player discovers through exploration)
Dragon's Lair → No NPCs (player discovers through exploration)
Ancient Ruins → No NPCs (player discovers through exploration)
```

### Testing Mode (`TEST_NPCS` set)

**Overrides everything:**
```bash
# Even in towns, TEST_NPCS overrides friendly NPCs
TEST_START_LOCATION="The Prancing Pony Inn" \
TEST_NPCS="Evil Assassin" \
python3 test.py

# Result: Inn has Evil Assassin, not Innkeeper
```

## Use Cases

### 1. Combat Test with Specific Monster
```bash
TEST_START_LOCATION="Ancient Ruins" \
TEST_NPCS="Skeleton, Skeleton" \
python3 e2e_tests/test_skeleton_combat.py
```

### 2. Shopping Test
```bash
TEST_START_LOCATION="The Market Square" \
# No TEST_NPCS → friendly merchants spawn automatically
python3 e2e_tests/test_shopping.py
```

### 3. Hidden Treasure Discovery
```bash
TEST_START_LOCATION="Sunken Temple" \
TEST_ITEMS="Hidden Altar:Artifact of Power, Ancient Scroll" \
python3 e2e_tests/test_treasure_discovery.py
```

### 4. Boss Fight
```bash
TEST_START_LOCATION="Dragon's Lair" \
TEST_NPCS="Ancient Red Dragon" \
TEST_ITEMS="Hoard Pile:Magic Sword, 1000 Gold, Dragon Scale Armor" \
python3 e2e_tests/test_dragon_fight.py
```

### 5. Multi-NPC Combat
```bash
TEST_START_LOCATION="Goblin Camp" \
TEST_NPCS="Goblin Chief, Goblin, Goblin, Wolf" \
python3 e2e_tests/test_multi_npc_combat.py
```

## Benefits

### ✅ Deterministic Testing
- No random encounters in tests
- Reproducible scenarios
- Consistent test results

### ✅ Flexible Scenario Creation
- Any location + any NPCs
- Custom descriptions
- Hidden items and containers

### ✅ State Persistence Testing
- Item tracking across location changes
- Dead NPCs remain after combat
- Inventory persistence

### ✅ Normal Gameplay Preserved
- Towns have friendly NPCs
- Combat locations allow natural exploration
- No forced random encounters

## Running Tests

### Run specific test
```bash
HEADLESS=true python3 e2e_tests/test_goblin_cave_combat.py
```

### Run with custom environment
```bash
TEST_START_LOCATION="Custom Location" \
TEST_NPCS="Custom Monster" \
HEADLESS=true python3 e2e_tests/test_custom.py
```

### Run all E2E tests
```bash
HEADLESS=true python3 -m pytest e2e_tests/ -v
```

## Files Created

- `e2e_tests/test_goblin_cave_combat.py` - Goblin combat test
- `e2e_tests/test_goblin_treasure_persistence.py` - State persistence test
- `demo_npc_spawning.py` - NPC spawning logic demo
- `test_custom_location_npcs.py` - Custom location/NPC demo
- `FLEXIBLE_TESTING_SYSTEM.md` - This documentation

## Implementation Details

**Location in code:** `web/app_gradio.py:210-282`

**Key functions:**
- `load_character_with_location()` - Sets up location, NPCs, and items
- `gm.set_location()` - Sets location description
- `gm.session.npcs_present` - Tracks NPCs in location
- `gm.session.location_items` - Tracks items in location

**Environment variable priority:**
1. `TEST_START_LOCATION` → Location name
2. `TEST_LOCATION_DESC` → Custom description (optional)
3. `TEST_NPCS` → NPCs (overrides friendly NPCs)
4. `TEST_ITEMS` → Items in location

## Future Enhancements

Potential additions:
- `TEST_WEATHER` - Weather conditions
- `TEST_TIME` - Time of day
- `TEST_QUEST` - Active quest
- `TEST_PARTY` - Multiple characters
