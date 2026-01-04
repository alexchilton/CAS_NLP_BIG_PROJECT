# Debug Mode - Scenario Testing

## Overview
Debug mode provides predefined test scenarios for manually testing combat, NPCs, and game features without having to trigger random encounters or navigate to specific locations.

## Enabling Debug Mode

Edit `dnd_rag_system/config/settings.py`:
```python
DEBUG_MODE = True
```

When enabled, a "🧪 Debug Scenario (Optional)" dropdown appears in the Gradio UI after character selection.

## Available Scenarios

| Scenario | Location | NPCs | Items | Purpose |
|----------|----------|------|-------|---------|
| Random Start | Random | None | None | Normal game start |
| Goblin Fight | Goblin Cave Entrance | Goblin | None | Test basic combat |
| Goblin with Treasure | Goblin Cave Entrance | Goblin | Hidden Chest | Test combat + looting |
| Goblin Wolf Rider | Forest Ambush Site | Goblin, Wolf | Rope, Torch | **Multi-enemy combat test** |
| Wolf Pack | Dark Forest Clearing | 2x Wolf | None | Test multi-enemy combat |
| Skeleton Guardian | Ancient Ruins | Skeleton | Ancient Sword | Test undead combat |
| Dragon Encounter | Dragon's Lair Approach | Young Red Dragon | Dragon Hoard | Test high-CR encounter |
| Safe Inn | The Prancing Pony Inn | Innkeeper Butterbur | Healing Potion | Test NPC dialogue |
| Shopping District | The Market Square | Merchant, Blacksmith | None | Test shop system |

## Usage

1. Enable `DEBUG_MODE = True` in settings
2. Start Gradio interface: `python web/app_gradio.py`
3. Select a character (Thorin or Elara)
4. Select a debug scenario from dropdown
5. Click "Load Character"
6. Game starts in the specified scenario with NPCs and items pre-spawned

## Implementation Details

### Scenario Format
```python
DEBUG_SCENARIOS = [
    (scenario_name, location_name, npcs_to_spawn, items_to_add),
    ...
]
```

### How It Works
1. `load_character_with_debug()` checks if scenario is selected
2. If yes: Loads character at specific location and injects NPCs/items
3. If no: Normal character load with random location
4. NPCs are added to `gm.session.npcs_present`
5. Items are added to `gm.session.location_items`

### Code Location
- UI: `web/app_gradio.py` lines ~72-81 (scenario definitions), ~1117-1124 (dropdown UI)
- Logic: `web/app_gradio.py` lines ~379-470 (`load_character_with_debug()`)
- Settings: `dnd_rag_system/config/settings.py` line 188

## Adding New Scenarios

Edit `DEBUG_SCENARIOS` list in `web/app_gradio.py`:
```python
DEBUG_SCENARIOS = [
    ...
    ("My Custom Scenario", "Location Name", ["NPC1", "NPC2"], ["Item1", "Item2"]),
]
```

**Note:** Location must exist in `STARTING_LOCATIONS` or `COMBAT_LOCATIONS` lists, or use custom name with generic description.

## Use Cases

1. **Combat Testing** - Test specific monster types without triggering random encounters
2. **NPC Hallucination Testing** - Verify GM uses correct monster names (e.g., "Goblin Fight" scenario)
3. **Location Stability Testing** - Verify location doesn't teleport during combat
4. **Item/Loot Testing** - Test item discovery and inventory systems
5. **Shop Testing** - Quickly access merchant NPCs
6. **Regression Testing** - Verify bug fixes work in specific scenarios

## Related Files

- `docs/BUG_FIXES.md` - Documents location/NPC hallucination fixes that debug mode helps test
- `docs/FLEXIBLE_TESTING_SYSTEM.md` - Environment variable testing (different approach)
- `tests/test_location_extraction.py` - Automated tests for location extraction
- `tests/test_encounter_hallucination_fix.py` - Automated tests for NPC filtering

## Future Enhancements

Potential additions:
- Save/load custom scenarios from JSON
- Multi-step scenario scripting (e.g., "spawn goblin after 3 turns")
- Scenario victory conditions
- Scenario-specific objectives
- HP/gold overrides for testing edge cases
