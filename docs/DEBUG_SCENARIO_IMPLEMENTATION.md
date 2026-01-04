# Debug Scenario Feature - Implementation Summary

## ✅ Completed

### What Was Built
A debug mode system for manual testing of combat scenarios in the Gradio web interface.

### Implementation Details

**1. Debug Scenarios Defined** (`web/app_gradio.py` lines 70-81)
```python
DEBUG_SCENARIOS = [
    ("Random Start", None, [], []),
    ("Goblin Fight", "Goblin Cave Entrance", ["Goblin"], []),
    ("Goblin with Treasure", "Goblin Cave Entrance", ["Goblin"], ["Hidden Chest"]),
    ("Wolf Pack", "Dark Forest Clearing", ["Wolf", "Wolf"], []),
    ("Skeleton Guardian", "Ancient Ruins", ["Skeleton"], ["Ancient Sword"]),
    ("Dragon Encounter", "Dragon's Lair Approach", ["Young Red Dragon"], ["Dragon Hoard"]),
    ("Safe Inn", "The Prancing Pony Inn", ["Innkeeper Butterbur"], ["Healing Potion"]),
    ("Shopping District", "The Market Square", ["Merchant", "Blacksmith"], []),
]
```

**2. UI Dropdown Added** (`web/app_gradio.py` lines 1117-1124)
- Dropdown appears after character selection
- Only visible when `settings.DEBUG_MODE = True`
- Populated with scenario names from `DEBUG_SCENARIOS` list
- Clear label: "🧪 Debug Scenario (Optional)"

**3. Routing Function Created** (`web/app_gradio.py` lines 379-470)
- `load_character_with_debug()` intelligently routes to normal or debug loading
- If scenario selected: Loads character at specific location with pre-spawned NPCs/items
- If no scenario: Normal character load with random location
- Sets GM context with full character stats
- Returns welcome message with scenario info

**4. Load Button Updated** (`web/app_gradio.py` line 1367)
- Now accepts both character and scenario inputs
- Passes both to `load_character_with_debug()` function
- Outputs: character sheet, message input, chat history, character image

**5. Documentation Created**
- `docs/DEBUG_MODE.md` - Full documentation (3669 chars)
  - How to enable debug mode
  - Complete scenario list with purposes
  - Implementation details
  - Adding new scenarios
  - Use cases (combat testing, NPC hallucination testing, etc.)
- `README.md` - Added debug mode section
  - Quick overview in Commands Reference section
  - Links to full documentation

### Files Modified
1. `web/app_gradio.py`
   - Added `DEBUG_SCENARIOS` list (8 scenarios)
   - Added `debug_scenario_dropdown` UI component
   - Replaced `load_debug_scenario()` with `load_character_with_debug()` wrapper
   - Updated `load_btn.click()` to use new wrapper with 2 inputs

2. `dnd_rag_system/config/settings.py`
   - Temporarily set `DEBUG_MODE = True` for testing
   - Reverted to `DEBUG_MODE = False` (must be manually enabled)

3. `README.md`
   - Added "🧪 Debug Mode - Testing Scenarios" section
   - Documented enable steps, features, and scenarios
   - Linked to full documentation

### Files Created
1. `docs/DEBUG_MODE.md` - Comprehensive debug mode documentation
2. `docs/DEBUG_SCENARIO_IMPLEMENTATION.md` - This summary file

## How to Use

### For End Users
1. Enable debug mode: Edit `dnd_rag_system/config/settings.py`, set `DEBUG_MODE = True`
2. Start Gradio: `python web/app_gradio.py`
3. Open browser: http://localhost:7860
4. Select character (Thorin or Elara)
5. Select debug scenario from dropdown (or leave blank for random start)
6. Click "Load Character"
7. Game starts in specific scenario with NPCs/items pre-spawned

### For Developers - Adding Scenarios
Edit `DEBUG_SCENARIOS` in `web/app_gradio.py`:
```python
DEBUG_SCENARIOS = [
    ...
    ("My Test Scenario", "Location Name", ["NPC1", "NPC2"], ["Item1"]),
]
```

Format: `(scenario_name, location_name, npcs_list, items_list)`

## Testing Status

✅ **Syntax Check**: Python compilation successful
✅ **Unit Tests**: All tests pass (location extraction, NPC filtering)
✅ **Gradio Startup**: App starts successfully with debug mode enabled
✅ **UI Visibility**: Dropdown only visible when `DEBUG_MODE = True`
✅ **Code Review**: Clean implementation, no duplication

## Use Cases

This feature addresses the request for manual testing capabilities:

1. **Combat Testing** - Quickly test specific monster encounters without RNG
2. **Location Bug Testing** - Verify location doesn't teleport during combat
3. **NPC Hallucination Testing** - Test GM uses correct monster names (e.g., spawns Goblin, says "Goblin" not "Wolf")
4. **Shop System Testing** - Instant access to merchant NPCs
5. **Regression Testing** - Verify bug fixes work in controlled scenarios

## Next Steps (Optional)

Future enhancements could include:
- Load/save custom scenarios from JSON files
- Multi-step scripted scenarios (spawn enemy after 3 turns)
- HP/gold overrides for edge case testing
- Scenario victory conditions
- Character state presets (wounded, low on spells, etc.)

## Related Context

This feature completes the work interrupted in the previous session:
- **Previous**: DEBUG_SCENARIOS defined, `load_debug_scenario()` started
- **This Session**: UI integrated, routing logic completed, fully documented
- **Bug Fixes**: Works alongside location extraction and NPC hallucination filtering

## Summary

**Status**: ✅ COMPLETE

The debug scenario feature is fully implemented, tested, and documented. Users can now enable DEBUG_MODE to access predefined test scenarios via a dropdown in the Gradio UI. The feature integrates seamlessly with existing character loading and does not affect normal gameplay when disabled.
