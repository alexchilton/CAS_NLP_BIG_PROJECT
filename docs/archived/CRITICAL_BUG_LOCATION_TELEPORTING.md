# CRITICAL BUGS FOUND IN SELENIUM TEST OUTPUT

## 🚨 Location Teleporting During Combat

**Severity**: CRITICAL - Breaks core gameplay

### Evidence from logs/test_adventure_simulation_20260104_104404.log

#### Example 1 - Turn 3:
```
Line 123: ⚔️  Turn 3: COMBAT - Attacking Goblin!
Line 124: Combat started: ... in Dark Forest Clearing
Line 128: Attack: ... in The Prancing Pony Inn
```
**Problem**: Player starts combat in Dark Forest but teleports to The Prancing Pony Inn mid-attack!

#### Example 2 - Turn 4:
```
Line 174: ⚔️  Turn 4: COMBAT - Attacking Goblin!  
Line 176: Combat started: ... in Dark Forest Clearing
Line 179: Attack: ... in The Market Square
```
**Problem**: Player starts combat in Dark Forest but teleports to The Market Square mid-attack!

## 🚨 Location Doesn't Match Player Intent

#### Example - Turn 1:
```
Line 44: 🚶 Turn 1: Traveling to Town Gates...
Line 46: GM: ... in Goblin Cave Entrance
```
**Problem**: Player says "travel to Town Gates" but GM puts them in "Goblin Cave Entrance"

## Root Cause Analysis

### Hypothesis:
The GM LLM is **not maintaining location context** between responses. Each GM response might be:
1. Regenerating location randomly
2. Ignoring the current location state
3. Not reading the session's current_location properly

### Where to investigate:
1. `web/app_gradio.py` - How is location passed to GM in prompt?
2. `dnd_rag_system/systems/gm_dialogue_unified.py` - How does GM maintain state?
3. Is `gm.session.current_location` being updated correctly?
4. Is the prompt including current location context?

## Impact

**This makes the game unplayable:**
- Player cannot strategically choose locations
- Combat happens in random places
- Narrative makes no sense (fighting goblin → teleports to tavern mid-fight)
- Completely breaks immersion

## Required Fixes

1. **Location must be sticky** - Once set, it shouldn't change unless player explicitly travels
2. **GM prompt must clearly show current location** - Make it impossible for LLM to ignore
3. **Validate GM response** - Check if GM mentioned a different location, reject and retry
4. **Lock location during combat** - Absolute requirement: NO location changes during combat

## Testing Requirements

After fixes, verify:
- [ ] Player travels to location X → GM confirms they're in location X
- [ ] Combat starts in location X → All combat rounds stay in location X
- [ ] Location only changes when player says "travel to Y"
- [ ] GM cannot randomly generate new locations unless player explores
