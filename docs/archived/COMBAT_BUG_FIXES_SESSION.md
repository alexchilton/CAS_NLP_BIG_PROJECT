# Combat Bug Fixes - Session Summary

## Bugs Fixed

### 1. ✅ Unconscious State Validation (FIXED)
**Bug**: Player could act (attack, cast spells) while unconscious  
**Fix**: Added validation at start of `generate_response()` in `gm_dialogue_unified.py`
- Checks for `Condition.UNCONSCIOUS` in character conditions
- Blocks ALL actions except `/help`, `/stats`, `/character`, `/context`, `/death_save`, `/initiative`
- Returns helpful message explaining unconscious state and D&D 5e rules

**Code**: Lines 228-248 in `dnd_rag_system/systems/gm_dialogue_unified.py`

### 2. ✅ NPCs Continue Attacking Unconscious Players (FIXED)
**Bug**: NPCs stopped taking turns when player was unconscious  
**Root Cause**: Turn only advanced if player took a combat action, but unconscious player was blocked from acting → turn never advanced → NPCs never got to attack

**Fix**: Modified turn advancement logic (lines 640-664 in `gm_dialogue_unified.py`)
- Turn now advances if player took combat action **OR** player is unconscious
- Unconscious players' turns are auto-skipped
- NPCs then process their consecutive turns normally
- Damage is applied to unconscious player
- This follows D&D 5e rules (unconscious = auto-crit from melee, can cause death)

**Code**: Lines 640-664 in `dnd_rag_system/systems/gm_dialogue_unified.py`

### 3. ✅ Encounter Spam Fixed (FIXED)
**Bug**: Random encounters triggered EVERY turn when exploring (goblin → owlbear → manticore in 3 turns)  
**Root Cause**: Encounter check ran on every exploration keyword with no cooldown

**Fix**: Added encounter cooldown system
- Added `turns_since_last_encounter` and `last_encounter_location` to `GameSession` (game_state.py line 1015-1016)
- Encounter only rolls if:
  - 5+ turns since last encounter, OR
  - Player changed locations
- Counter increments each non-combat turn
- Resets to 0 when encounter spawns

**Code**:
- game_state.py lines 1015-1016 (new fields)
- gm_dialogue_unified.py lines 518-552 (encounter cooldown logic)

### 4. ✅ Added Goblin Wolf Rider Test Scenario
**Request**: Multi-enemy combat test scenario for items and multiple NPCs

**Added**: "Goblin Wolf Rider" scenario to DEBUG_SCENARIOS
- Location: Forest Ambush Site
- NPCs: Goblin + Wolf (tests multi-enemy combat and initiative)
- Items: Rope, Torch (tests item spawning in scenarios)

**Code**: web/app_gradio.py line 75

## Manual Testing Required
1. Enable DEBUG_MODE in settings.py
2. Start Gradio: `python web/app_gradio.py`
3. Load "Goblin Wolf Rider" scenario
4. Attack goblin until unconscious (0 HP)
5. Verify:
   - ✅ Cannot attack/cast spells (blocked with message)
   - ✅ Can still use `/stats`, `/help`
   - ✅ Goblin and Wolf continue attacking each turn
   - ✅ HP continues to decrease (can die)

## Additional Fixes (Same Session)

### 5. ✅ NPCs Attack Every Turn in Combat
**Bug**: NPCs only attacked when player took combat actions (attack/spell)  
**Problem**: If player tried to run away, drink potion, or talk → NPCs didn't attack

**Fix**: Changed turn advancement to **always** advance in combat, regardless of action type
- Running away? NPCs attack
- Drinking potion? NPCs attack  
- Talking? NPCs attack
- Unconscious? NPCs attack

**Code**: Lines 640-662 in `gm_dialogue_unified.py`

### 6. ✅ Item Persistence System
**Bug**: Items spawned in scenarios would be there forever, even after being picked up

**Fix**: Added full item persistence system
- Added `available_items` list to `Location` class
- Added `add_item()`, `remove_item()`, `has_item()` methods
- Items removed from location when picked up
- Tracked in `moved_items` dict (item → destination)
- Mechanics extractor now detects item pickups ("You pick up the rope")
- Applicator adds to inventory AND removes from location

**Code**:
- `game_state.py` lines 57-117: Location item tracking
- `mechanics_extractor.py`: Added `items_acquired` field
- `mechanics_applicator.py` lines 168-186: Item pickup handling
- `web/app_gradio.py` lines 418-431: Debug scenario item spawning

**How It Works**:
1. GM says "You pick up the rope"
2. Mechanics extractor detects: `{"items_acquired": [{"character": "Player", "item": "rope"}]}`
3. Applicator adds rope to character inventory
4. Applicator removes rope from location's `available_items`
5. Location tracks in `moved_items`: `{"rope": "Player's inventory"}`
6. If player returns, rope is gone

## Files Modified (Total)
1. `dnd_rag_system/systems/gm_dialogue_unified.py` - Unconscious validation, NPC attacks, encounter cooldown
2. `dnd_rag_system/systems/game_state.py` - Encounter tracking, item persistence
3. `dnd_rag_system/systems/mechanics_extractor.py` - Item acquisition detection
4. `dnd_rag_system/systems/mechanics_applicator.py` - Item pickup handling
5. `web/app_gradio.py` - Debug scenario, item spawning
6. `docs/COMBAT_BUG_FIXES_SESSION.md` - This documentation

## Testing Checklist
- [ ] NPCs attack when player tries to run away
- [ ] NPCs attack when player uses item/potion
- [ ] NPCs attack when player is unconscious
- [ ] Items disappear from location after pickup
- [ ] Items appear in character inventory
- [ ] Items don't respawn on revisit
- [ ] Encounter cooldown works (5 turns between spawns)
- [ ] Goblin Wolf Rider scenario has Rope and Torch
- [ ] Rope/Torch can be picked up
- [ ] Rope/Torch gone after pickup
