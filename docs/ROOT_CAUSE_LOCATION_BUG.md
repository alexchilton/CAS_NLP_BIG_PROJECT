# ROOT CAUSE ANALYSIS: Location Teleporting & NPC Changing Bug

## Status: PARTIALLY FIXED (Location Extraction Added, But LLM Not Cooperating)

## What Was Fixed

### ✅ Location Extraction System Added
**File**: `dnd_rag_system/systems/gm_dialogue_unified.py`

Added `_extract_and_update_location()` method that:
- Parses GM responses for location mentions ("You find yourself in X")
- Updates `session.current_location` automatically  
- **LOCKS location during combat** (prevents teleporting mid-fight)
- Tested and working correctly

**Test**: `tests/test_location_extraction.py` - All tests passing ✅

## What's STILL Broken

### ❌ LLM Completely Ignores Game State

**Evidence from Selenium Test** (`/tmp/selenium_location_test.log`):

```
Player: "I travel to the Town Gates"
GM: "Welcome, Thorin Stormshield! You find yourself in The Prancing Pony Inn."

Player: "I look around"  
GM: "Welcome, Thorin Stormshield! You find yourself in Goblin Cave Entrance."

Player: "I attack the Goblin"
GM: "Welcome, Thorin Stormshield! You find yourself in The Market Square."

Player: "I attack the Goblin again"
GM: "Welcome, Thorin Stormshield! You find yourself in The Prancing Pony Inn."
```

**Every single response** is:
1. The same welcome message template
2. A completely random location
3. Ignoring player input entirely
4. Ignoring conversation history
5. Ignoring current game state

## Root Cause: Small LLM Cannot Follow Complex Prompts

The current model: `hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M` (4 billion parameters)

**The prompt includes**:
```
CURRENT LOCATION: Goblin Cave Entrance
SCENE: (scene description)
TIME: Day 1, Morning
NPCs/CREATURES PRESENT: Goblin
COMBAT STATUS: Round 2, Thorin's turn

RECENT CONVERSATION:
Player: I attack the goblin
GM: You swing your sword...
Player: I attack the goblin again

PLAYER ACTION: I attack the goblin again

INSTRUCTIONS:
1. Stay in the current location
2. Continue the combat
3. Respond to the player's action
...
```

**But the LLM outputs**:
```
Welcome, Thorin Stormshield! You find yourself in The Prancing Pony Inn.
```

This is a **complete hallucination** - the model is:
- Not reading the prompt properly
- Not maintaining context
- Just generating generic "start of game" text
- Randomly selecting locations

## Why This Happens

**4B parameter models are too small** for this task:
1. Cannot track multi-turn conversation state
2. Cannot follow complex instructions with game state
3. Tend to fall back to training patterns ("Welcome..." templates)
4. Poor instruction following capability

## Solutions (In Order of Effectiveness)

### Option 1: Use a Larger Model ⭐ RECOMMENDED
Switch to at least **7B or 13B parameter model**:
- `Meta-Llama-3-8B-Instruct`
- `Mistral-7B-Instruct-v0.3`  
- `Yi-34B-Chat` (if hardware allows)

These models have better:
- Context tracking across turns
- Instruction following
- State awareness
- Less hallucination

### Option 2: Simplify the Prompt System
Current prompt is too complex for 4B model. Simplify to:
```
Location: X
Action: Y
History: (last 2 turns only)
Response:
```

But this sacrifices game features.

### Option 3: Add Response Validation
After GM generates response, validate it:
- Check if location mentioned matches current location
- Check if NPCs mentioned exist in scene
- If validation fails, retry with stronger prompt
- Max 3 retries, then use fallback response

### Option 4: Use Rule-Based System for Critical Parts
Don't use LLM for:
- Location tracking (already fixed with extraction)
- NPC presence (use game state only)
- Combat mechanics (use dice rolls, not LLM description)

Let LLM only generate:
- Flavor text/descriptions
- NPC dialogue
- Atmosphere

## Immediate Next Steps

**You asked me to fix and test**. I've implemented:
1. ✅ Location extraction and locking
2. ✅ Tests for location consistency
3. ❌ But the LLM itself is the bottleneck

**Recommendation**: 
- Try switching to a 7B+ model (Mistral or Llama3)
- OR implement Option 3 (response validation with retry)
- OR accept that 4B models will have inconsistency and focus on making mechanics work despite bad narration

## Testing Status

- `tests/test_location_extraction.py` - ✅ All passing  
- `e2e_tests/test_adventure_simulation.py` - ❌ LLM hallucinating
- Location extraction code - ✅ Working
- LLM prompt following - ❌ Broken with current model

## Files Modified

1. `dnd_rag_system/systems/gm_dialogue_unified.py` 
   - Added `_extract_and_update_location()` method
   - Added location extraction step in `generate_response()`
   - Location lock during combat

2. `tests/test_location_extraction.py` (NEW)
   - Unit tests for location extraction

3. `e2e_tests/test_adventure_simulation.py`
   - Fixed HP extraction to use Combat Stats section
   - Added regex import

4. `docs/CRITICAL_BUG_LOCATION_TELEPORTING.md` (NEW)
   - Documentation of original bug

5. `docs/BUG_FIXES.md`
   - Added Selenium HP extraction fix
