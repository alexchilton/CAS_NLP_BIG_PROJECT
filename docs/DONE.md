# DONE - Completed Features

This file tracks completed and working features that have been implemented and tested.

---

## ✅ Project Organization & Documentation Consolidation ✅ COMPLETED (2026-01-15)

### Project Structure Reorganization
- **Goal**: Organize scattered files across root directory into logical structure
- **Status**: ✅ FULLY COMPLETED

**File Reorganization**:

1. **RAG Data Consolidation** (`dnd_rag_system/data/`):
   - Created `dnd_rag_system/data/reference/` for original D&D PDFs (104 MB)
   - Created `dnd_rag_system/data/extracted/` for processed text files (2.2 MB)
   - Moved all PDFs with cleaned names (players_handbook.pdf, monster_manual.pdf, dm_guide.pdf)
   - Moved all extracted text files (spells.txt, all_spells.txt, extracted_classes.txt, extracted_monsters.txt)
   - Moved equipment.txt from web/ to dnd_rag_system/data/
   - Created `dnd_rag_system/data/README.md` documenting data structure

2. **Scripts Organization**:
   - Created `scripts/rag/` for RAG ingestion scripts (5 files)
     - `initialize_rag.py`, `ingest_dm_guide.py`, `ingest_game_content.py`
     - `1_split_monsters.py`, `2_run_ingestion_v2.py`
   - Created `scripts/` for utility scripts (6 files)
     - `query_rag.py`, `create_character.py`, `play_with_character.py`
     - `rag_dialogue_test.py`, `test_dm_guide_query.py`, `generate_report_assets.py`
   - Updated all `project_root` paths from `.parent` to `.parent.parent.parent`

3. **Jupyter Notebooks Organization**:
   - Created `notebooks/` directory (5 notebooks)
   - Moved: `classes_to_rag.ipynb`, `monster_to_rag.ipynb`, `monster_to_rag_v2.ipynb`
   - Moved: `races_to_rag.ipynb`, `rag_spells2.ipynb`

4. **Documentation Consolidation** (`docs/`):
   - Created `docs/archived/` for old bug fix documentation (9 files)
   - Moved resolved bug docs: BUG_FIXES.md, COMBAT_BUG_FIXES_SESSION.md, CRITICAL_* files
   - Consolidated 9 test docs into single TESTING.md (merged RUNNING_TESTS.md content)
   - Removed redundant docs: TEST_FIXES_SUMMARY.md, TEST_STATUS_SUMMARY.md, TEST_SUMMARY.md
   - Removed outdated docs: SESSION_SUMMARY.md, rag_improvement_analysis.md
   - Remaining active docs: WORLD_SYSTEM_COMPLETE.md, SHOP_SYSTEM_GUIDE.md, EQUIPMENT_SYSTEM.md

**Files Modified**:
- `scripts/rag/ingest_dm_guide.py` - Updated PDF path to dnd_rag_system/data/reference/
- `scripts/rag/1_split_monsters.py` - Updated monster file paths
- `tests/test_shop_system.py` - Updated equipment.txt path
- All moved scripts - Fixed project_root path calculation

**Result**: Clean root directory with only essential deployment files (app.py, Dockerfile, requirements.txt, *.sh). All data, scripts, and docs organized logically.

**Commits**:
- 9f6b6cb - "refactor: Move equipment.txt to dnd_rag_system/data/"
- b7e273f - "refactor: Consolidate all RAG data into dnd_rag_system/data/"
- 76cbffa - "refactor: Organize scripts and notebooks into proper directories"
- [pending] - "docs: Consolidate documentation and archive old bug fixes"

---

## ✅ Selenium Dropdown Helpers & E2E Test Fixes ✅ COMPLETED (2026-01-15)

### Gradio Dropdown Selection Bug Fix
- **Problem**: E2E tests selecting "Elara" from dropdown, but system loaded "Thorin" instead
- **Root Cause**: Gradio dropdowns are `<input role="listbox">` with aria-label, NOT standard `<select>` elements
  - Previous code: `driver.find_elements(By.TAG_NAME, "select")` found nothing in Gradio
  - Dropdowns defaulted to first option (Thorin) when selection failed silently
- **Investigation**: Created test_character_bug.py to isolate core logic vs UI issue
- **Result**: Core application logic works correctly - bug was in Selenium dropdown selection

**Implementation**:

1. **Selenium Helpers Module** (`e2e_tests/selenium_helpers.py`):
   - Created comprehensive dropdown helper library
   - Universal `select_dropdown_option()` function for any Gradio dropdown
   - Uses correct CSS selector: `input[aria-label="..."]`
   - Finds options with `[role="option"]` selector
   - Supports partial matching for flexible selection
   - Includes verification that selection succeeded

2. **Specific Helper Functions**:
   - `select_character(driver, name)` - "Choose Your Character" dropdown
   - `select_race(driver, race)` - "Race" dropdown
   - `select_class(driver, class_name)` - "Class" dropdown
   - `select_alignment(driver, alignment)` - "Alignment" dropdown
   - `select_debug_scenario(driver, scenario)` - "🧪 Debug Scenario (Optional)" dropdown
   - `wait_for_gradio(driver, timeout=30)` - Wait for Gradio to load

3. **Updated E2E Tests**:
   - `e2e_tests/test_combat_scenarios.py` - Uses selenium_helpers
   - `e2e_tests/test_wizard_spell_combat.py` - Uses selenium_helpers
   - All character dropdown selection now reliable and verified

**Code Example**:
```python
from selenium_helpers import select_character, wait_for_gradio

# Old (broken):
dropdowns = driver.find_elements(By.TAG_NAME, "select")  # Finds nothing!

# New (works):
select_character(driver, "Elara")  # Uses correct aria-label selector
```

**Warning in selenium_helpers.py**:
```python
# ⚠️ CRITICAL: Gradio dropdowns are NOT standard <select> elements!
# They are <input role="listbox"> with aria-label attributes.
# ALWAYS use these helpers instead of find_element(By.TAG_NAME, "select")
```

**Files Created**:
- `e2e_tests/selenium_helpers.py` (150+ lines) - Universal dropdown helpers

**Files Modified**:
- `e2e_tests/test_combat_scenarios.py` - Imported and used helpers
- `e2e_tests/test_wizard_spell_combat.py` - Imported and used helpers

**Result**: All Gradio dropdown selections now work reliably! Comprehensive helper library prevents future dropdown bugs. Character selection verified working in E2E tests.

**Commits**:
- bc4fb82 - "fix: Fix Selenium character dropdown selection in E2E tests"
- cbe2992 - "docs: Create comprehensive Selenium dropdown helpers"

---

## ✅ E2E Bug Fixes - Combat and Character Validation ✅ COMPLETED (2026-01-14)

### Bug #1 Fixed: Wrong Character Stats in Error Messages (Thorin vs Elara)
- **Symptom**: When "Elara casts Magic Missile", system said "You're a FIGHTER, not a wizard!" using Thorin's class instead of Elara's
- **Root Cause**: `generate_invalid_action_response()` always used `session.character_state` for race/class instead of looking up the specific acting character
- **Impact**: Broke party mode validation - wrong character's stats used for error messages
- **Fix Applied** (`gm_dialogue_unified.py:1640-1652`):
  - Extract acting character name from input using `extract_acting_character()`
  - Look up specific character's stats from `base_character_stats` dictionary
  - Fall back to `character_state` for single-player mode
  - Now correctly uses Elara's stats when "Elara casts..." and Thorin's stats when "Thorin attacks..."
- **Testing**: Verified with party character parsing tests
- **Result**: ✅ Error messages now use correct character's race and class

### Bug #2 Fixed: /start_combat Spawning Wrong Enemies
- **Symptom**: `/start_combat Skeleton` spawned "Goblin, Skeleton and Ogre appear!" instead of just Skeleton
- **Root Cause**: `get_combat_start_message()` listed ALL monsters in `npc_monsters` dict (persistent accumulation), not just monsters in current combat
- **Impact**: Combat messages showed enemies from previous combats, confusing players
- **Fix Applied** (`combat_manager.py:216-217, 572`):
  - Changed to only list NPCs from current `initiative_order`:
    ```python
    npcs_in_combat = [name for name, init in self.combat.initiative_order
                      if name in self.npc_monsters]
    ```
  - Clear `npc_monsters` dictionary when combat ends:
    ```python
    self.npc_monsters.clear()  # Clear loaded monster instances for next combat
    ```
- **Testing**: Verified sequential combats no longer accumulate enemies
- **Result**: ✅ Combat messages now show only the requested enemies

### Bug #3 Investigated: Echo Bug When Unconscious
- **Symptom** (reported): Game echoes player input when character is unconscious
- **Investigation**: Cannot reproduce in current codebase
  - Unconscious check (lines 231-249) returns proper informative message, not an echo
  - No code path found that would echo the player's input
  - LLM response cleaning removes echoes (line 1916-1917)
- **Status**: Could not find or reproduce the bug
- **Possible Explanations**:
  - Bug may have been fixed inadvertently by other changes
  - May require specific reproduction scenario not tested
  - May have been a transient LLM behavior issue
- **Result**: ⚠️ Inconclusive - unable to reproduce or fix

**Files Modified (2 files)**:
- `dnd_rag_system/systems/combat_manager.py` - Fixed combat message generation and cleanup
- `dnd_rag_system/systems/gm_dialogue_unified.py` - Fixed character stat lookup for error messages

**Commit**: 626f14d - "fix: Resolve E2E test bugs in combat and character validation"

---

## ✅ LLM-Based Intent Classification (Optional) ✅ COMPLETED (2026-01-14)

### Optional LLM-Based Action Intent Classifier
- **Goal**: Add optional LLM-based natural language understanding for player actions while preserving the existing keyword-based system
- **Status**: ✅ FULLY IMPLEMENTED with parallel classifier support and graceful fallback

**Problem Solved**: The keyword-based action validator is fast and reliable but brittle - it fails on creative phrasings:
- ✅ Works: "attack the goblin", "fire my bow", "shoot my bow"
- ❌ Fails: "loose an arrow", "nock and release my bowstring", "let fly with my longbow"
- Required constant keyword list maintenance for every new synonym or variation

**Implemented Solution**: Optional LLM-based intent classifier using Qwen2.5-3B (same model as mechanics extractor)

**Implementation**:

1. **Configuration System** (`dnd_rag_system/config.py` - NEW):
   - `IntentClassifierConfig` class with classifier type constants
   - Default remains keyword-based (preserves existing behavior)
   - Toggle switches for LLM mode and comparison mode
   - Centralized model settings (reuses Qwen2.5-3B)

2. **Dual Classifier Architecture** (`action_validator.py`):
   - **Keyword-based classifier** (`_analyze_intent_keyword()`):
     - Original implementation (renamed, unchanged logic)
     - Fast (~0ms), reliable for standard phrases
     - Uses predefined keyword lists
   - **LLM-based classifier** (`_analyze_intent_llm()`):
     - Uses Qwen2.5-3B for natural language understanding
     - Handles creative phrasings: "loose an arrow", "nock and release"
     - Structured JSON output with intent type and extracted entities
     - ~1-2 second inference time
     - **Graceful fallback**: Automatically falls back to keyword-based on LLM errors
   - **Dispatcher** (`analyze_intent()`):
     - Routes to appropriate classifier based on configuration
     - Default: keyword-based (no breaking changes)
     - Optional: LLM-based via `classifier_type="llm"` parameter
     - Comparison mode: Runs both and logs differences

3. **Comparison Mode** (for validation):
   - Runs both classifiers in parallel
   - Logs differences when classifications disagree
   - Returns LLM result but shows keyword result for comparison
   - Useful for testing and validation

4. **LLM Prompt Engineering** (`_build_intent_prompt()`):
   - Structured prompt with clear action type definitions
   - Entity extraction rules (target, resource)
   - 7 detailed examples covering combat, spells, conversation, items, exploration, stealing
   - Party member context integration
   - Handles creative phrasings naturally

**Key Features**:
- ✅ **No Breaking Changes**: Default behavior remains keyword-based (fast, reliable)
- ✅ **100% Backward Compatible**: Existing code works unchanged
- ✅ **Model Reuse**: Shares Qwen2.5-3B with mechanics extractor (no additional model download)
- ✅ **Graceful Fallback**: LLM errors automatically fall back to keyword-based
- ✅ **Parallel Implementation**: Both classifiers available simultaneously
- ✅ **Runtime Toggle**: Switch via parameter without code changes
- ✅ **Validation Mode**: Compare both classifiers to verify accuracy

**Test Results** (All Passing):

**Keyword Classifier Tests** (`TestKeywordClassifier`):
- ✅ Standard combat actions recognized
- ✅ Standard spell casting recognized
- ✅ Creative combat phrases fail as expected (baseline)

**LLM Classifier Tests** (`TestLLMClassifier`):
- ✅ Creative combat phrases work: "loose an arrow at the dragon"
- ✅ Standard actions work: "I attack the goblin", "I cast Fireball"
- ✅ All action types supported: combat, spell_cast, conversation, item_use, exploration, steal
- ✅ Fallback works when LLM errors occur

**Comparison Mode Tests** (`TestComparisonMode`):
- ✅ Both classifiers agree on standard phrases
- ✅ LLM handles creative phrases better than keyword
- ✅ Differences logged automatically for analysis

**Edge Case Tests** (`TestEdgeCases`):
- ✅ Party member actions parsed correctly
- ✅ Ambiguous actions classified appropriately

**Example Usage**:

```python
# Default: keyword-based (fast, existing behavior)
validator = ActionValidator()
intent = validator.analyze_intent("I attack the goblin")
# → ActionIntent(type=combat, target=goblin, resource=None)

# LLM-based: handles creative phrasings
validator = ActionValidator(classifier_type="llm")
intent = validator.analyze_intent("I loose an arrow at the dragon")
# → ActionIntent(type=combat, target=dragon, resource=arrow)

# Comparison mode: run both and log differences
validator = ActionValidator(compare_classifiers=True)
intent = validator.analyze_intent("I nock and release my bowstring")
# Logs: "🔀 CLASSIFIER MISMATCH for 'I nock and release my bowstring':"
#       "  Keyword: ActionIntent(type=exploration, ...)"
#       "  LLM:     ActionIntent(type=combat, ...)"
# Returns: LLM result
```

**Performance**:
| Classifier | Speed | Accuracy (standard) | Accuracy (creative) | Maintenance |
|------------|-------|-------------------|-------------------|-------------|
| Keyword | ~0ms | High | Low | High (keyword lists) |
| LLM | ~1-2s | High | **High** ✨ | Low (model handles variants) |

**Benefits**:
- ✅ Handles creative natural language: "nock and release", "let fly with my longbow"
- ✅ No keyword maintenance required in LLM mode
- ✅ Preserves existing functionality (keyword mode still available)
- ✅ 100% backward compatible (default unchanged)
- ✅ Graceful error handling with automatic fallback
- ✅ Model reuse (no additional downloads or dependencies)

**Files Created (2 files)**:
- `dnd_rag_system/config.py` (58 lines) - Configuration system
- `tests/test_llm_intent_classifier.py` (263 lines) - Comprehensive test suite

**Files Modified (2 files)**:
- `dnd_rag_system/systems/action_validator.py`:
  - Added imports: `json`, `subprocess`, `Any` type
  - Updated `__init__()` with classifier_type and compare_classifiers parameters
  - Renamed `analyze_intent()` → `_analyze_intent_keyword()`
  - Created new dispatcher `analyze_intent()` that routes to appropriate classifier
  - Added `_analyze_intent_llm()` - LLM-based classification
  - Added `_build_intent_prompt()` - prompt engineering for LLM
  - Added `_query_ollama_intent()` - Ollama API integration
  - Added `_parse_intent_response()` - JSON response parsing
- `TODO.md` - Marked feature as completed with implementation details

**Testing**:
- All existing tests pass (no regressions)
- 12 new tests covering keyword, LLM, comparison, and edge cases
- All tests passing ✅

**Integration Points** (Future Work):
- Can be integrated into `GameMaster.__init__()` with toggle parameter
- Gradio UI can add radio button for user to choose classifier
- Default remains keyword-based unless user opts in

**Time Spent**: ~4 hours (planning, implementation, testing, documentation)

**Result**: Players can now benefit from natural language understanding for creative action phrasings while maintaining the speed and reliability of the keyword-based system! The implementation is fully backward compatible, extensively tested, and ready for optional rollout.

---

## ✅ SyntaxError Fix in web/app_gradio.py ✅ COMPLETED (2026-01-14)

### Fixed Global Declaration Import Error
- **Issue**: Python SyntaxError causing all unit tests to fail
  - Error: `SyntaxError: name 'current_character' is used prior to global declaration`
  - Location: `web/app_gradio.py:1340`
  - Impact: Tests couldn't even import the module, blocking all test execution
- **Root Cause**: `global current_character` declaration appeared at line 1340 inside `/load_game` command handler, but `current_character` was already used earlier in the `chat()` function (line 1136, 1210, etc.)
- **Fix Applied** (2 changes):
  1. Added `current_character` to global declaration at top of `chat()` function (line 839)
  2. Removed duplicate `global current_character` declaration at line 1340
- **Python Rule**: In Python, `global` must be declared before any use of the variable within a function
- **Result**: ✅ Import error fixed, all 557 tests can now run successfully
- **Files Modified**:
  - `web/app_gradio.py:839` (added `current_character` to global declaration)
  - `web/app_gradio.py:1340` (removed duplicate global declaration)
- **Testing**: All unit tests now import successfully and can execute

---

## ✅ Save/Load System for World State ✅ FULLY IMPLEMENTED (2026-01-14)

### Complete Game Session Persistence System
- **Goal**: Enable saving complete game state to disk and loading campaigns across app restarts
- **Status**: ✅ FULLY IMPLEMENTED with 17 passing tests (13 unit + 4 integration)

**Problem Solved**: Game sessions previously only persisted in-memory during runtime. Closing the app meant losing all progress, world exploration, character development, and story progression.

**Implementation**:

1. **Location Serialization** (`game_state.py:138-169`):
   - `Location.to_dict()` - Converts location to JSON-serializable dictionary
   - `Location.from_dict()` - Reconstructs location from dictionary
   - Preserves all location state:
     - Basic info (name, type, description, connections)
     - Persistent state (defeated enemies, moved items, completed events)
     - Discovery and visit tracking (visit_count, last_visited_day, is_discovered)
     - Available items list (items that can be picked up)
     - Shop/safety flags (has_shop, is_safe, resident_npcs)

2. **CharacterState Serialization** (already existed, enhanced):
   - Complete character state including HP, level, gold, inventory
   - Spell slots preservation (current and max for levels 1-9)
   - Conditions tracking (poisoned, stunned, unconscious, etc.)
   - Death saves state (successes and failures)
   - Equipment and attunement status

3. **PartyState Serialization** (`game_state.py:1094-1116`):
   - `PartyState.to_dict()` - Converts party to dictionary
   - `PartyState.from_dict()` - Reconstructs party with all members
   - Preserves:
     - Party name and shared gold
     - All party member character states (recursive serialization)
     - Shared inventory items

4. **CombatState Serialization** (`game_state.py:971-999`):
   - `CombatState.to_dict()` - Converts combat state to dictionary
   - `CombatState.from_dict()` - Reconstructs combat mid-battle
   - Preserves:
     - Combat status (in_combat flag, round_number)
     - Initiative order with all participants and rolls
     - Current turn tracking (current_turn_index)
     - Active effects (buffs, debuffs, durations)

5. **GameSession Save/Load** (`game_state.py:1372-1476`):
   - `GameSession.save_to_json(filepath)` - Complete session serialization
   - `GameSession.load_from_json(filepath)` - Complete session restoration
   - Saves everything:
     - **World map**: All locations with connections and state
     - **Character/Party**: Complete character or party state
     - **Combat**: Mid-combat saves work perfectly
     - **Quests**: Active and completed quests
     - **NPCs**: Currently present NPCs
     - **Time**: Day and time_of_day tracking
     - **Encounter tracking**: Turns since last encounter, last location
     - **Notes**: Player notes and session history
   - Versioned format (version 1.0) for future compatibility
   - Creates save directory automatically if missing

6. **UI Commands** (`web/app_gradio.py:1084-1194`):
   - `/save_game <name>` - Save current session with custom name
     - Creates `saves/<name>.json` file
     - Shows save path confirmation
     - Handles errors gracefully
   - `/load_game <name>` - Load previously saved session
     - Lists available saves if file not found
     - Restores complete game state
     - Updates UI character sheet automatically
     - Shows location, character info, combat status
   - Both commands integrated into help system

**Save File Structure**:
```json
{
  "version": "1.0",
  "session_name": "Epic Adventure",
  "current_location": "Ancient Crypt",
  "world_map": {
    "Town Square": {...},
    "Forest Path": {...},
    "Ancient Crypt": {...}
  },
  "character_state": {...},
  "party": {...},
  "combat": {...},
  "active_quests": [...],
  "completed_quests": [...],
  "npcs_present": [...],
  "day": 1,
  "time_of_day": "evening"
}
```

**Testing (17 tests total)**:

**Unit Tests** (`tests/test_save_load_system.py` - 13 tests):
- `TestLocationSerialization`: 2 tests
  - Basic location serialization with all fields
  - Location with state changes (defeated enemies, moved items, events)
- `TestCharacterStateSerialization`: 3 tests
  - Basic character state (HP, gold, inventory)
  - Character with spell slots preservation
  - Character with conditions and death saves
- `TestPartyStateSerialization`: 1 test
  - Party with multiple characters and shared inventory
- `TestCombatStateSerialization`: 2 tests
  - Combat state with initiative order and turn tracking
  - Combat with active effects (buffs/debuffs)
- `TestGameSessionSerialization`: 5 tests
  - Basic session save/load
  - Session with party mode
  - Session during combat (mid-battle saves)
  - Session with quests
  - Session with complex world (multiple locations, connections, enemy tracking)

**Integration Tests** (`tests/test_save_load_integration.py` - 4 tests):
- `test_full_game_session_workflow`: Complete gameplay simulation
  - Create character → travel to dungeon → fight enemies → collect loot
  - Save game mid-combat → load game → verify complete state preservation
  - Tests: character HP, gold, inventory, combat state, world map, defeated enemies, quests
- `test_save_load_with_party_mode`: Multi-character party persistence
  - Create party with multiple members → save → load
  - Verify all party members and shared inventory preserved
- `test_save_load_preserves_location_state`: Location-specific state
  - Defeated enemies, moved items, completed events, visit counts all preserved
- `test_multiple_save_slots`: Multiple save file support
  - Create different saves → load each → verify independence

**Example Usage**:
```
Player: /save_game epic_dragon_quest
GM: ✅ Game saved successfully!
    Saved to: `saves/epic_dragon_quest.json`
    You can load this save with: /load_game epic_dragon_quest

[Player closes app, reopens later]

Player: /load_game epic_dragon_quest
GM: ✅ Game loaded successfully!
    Location: Ancient Crypt
    Character: Adventurer
    HP: 20/30
    Gold: 200 GP
    ⚔️ In Combat - Round 1
```

**Error Handling**:
- Missing save files → Shows list of available saves
- Invalid JSON → Clear error message
- Missing save directory → Creates automatically
- Save during critical states → Works perfectly (even mid-combat)

**Files Created (2 test files)**:
- `tests/test_save_load_system.py` (407 lines, 13 tests)
- `tests/test_save_load_integration.py` (305 lines, 4 tests)

**Files Modified (3 files)**:
- `dnd_rag_system/systems/game_state.py` (added serialization methods)
  - `Location.to_dict()` and `from_dict()` (enhanced with available_items)
  - `PartyState.to_dict()` and `from_dict()` (new)
  - `CombatState.to_dict()` and `from_dict()` (new)
  - `GameSession.save_to_json()` and `load_from_json()` (new)
- `web/app_gradio.py` (added save/load commands)
  - `/save_game <name>` command handler (lines 1084-1120)
  - `/load_game <name>` command handler (lines 1122-1194)
  - Help text updated with save/load commands
- `TODO.md` (marked as completed)

**Result**: Players can now save their campaigns at any point and resume across app restarts! Complete world state, character progression, combat status, and story progress all preserved. The system handles edge cases gracefully (mid-combat saves, party mode, complex world maps) and provides clear user feedback.

---

## ✅ Spell System with Prepared/Known Spells Distinction ✅ FULLY IMPLEMENTED (2026-01-14)

### Complete D&D 5e Spell System
- **Goal**: Implement proper D&D 5e spell mechanics with prepared vs known spells
- **Status**: ✅ FULLY IMPLEMENTED with 28 passing tests

**Problem Solved**: Previously, there was no distinction between prepared and known spells. All spell casting was handled generically without tracking which spells a character knows or has prepared. This didn't follow D&D 5e rules where:
- **Prepared Casters** (Wizard, Cleric, Druid, Paladin) must prepare a limited subset of spells each day
- **Known Casters** (Sorcerer, Bard, Warlock, Ranger) permanently know spells but can't easily change them

**Implementation**:

1. **Spell Tracking Fields** (`game_state.py:321-325`):
   - `spellcasting_class: Optional[str]` - Character's spellcasting class (None for non-casters)
   - `spellcasting_ability: str` - Spellcasting ability (INT, WIS, or CHA)
   - `known_spells: List[str]` - All spells the character knows
   - `prepared_spells: List[str]` - Currently prepared spells (for prepared casters)

2. **Caster Type Detection** (`game_state.py:535-559`):
   - `is_prepared_caster()` - Returns True for Wizard, Cleric, Druid, Paladin
   - `is_known_caster()` - Returns True for Sorcerer, Bard, Warlock, Ranger
   - Determines which spell preparation system to use

3. **Spell Learning** (`game_state.py:584-624`):
   - `learn_spell(spell_name)` - Add spell to known_spells list
   - For prepared casters: Must prepare spell daily before casting
   - For known casters: Automatically prepares upon learning (can cast immediately)
   - Returns success status and descriptive message

4. **Spell Preparation** (`game_state.py:626-674` for prepared casters only):
   - `prepare_spell(spell_name, ability_modifier)` - Prepare spell for daily use
   - Checks if spell is known before allowing preparation
   - Enforces preparation limit: `ability_modifier + level` (minimum 1)
   - Prevents duplicate preparation
   - Wizards/Clerics/Druids/Paladins only

5. **Spell Unpreparing** (`game_state.py:676-704`):
   - `unprepare_spell(spell_name)` - Remove spell from prepared list
   - Frees up a preparation slot
   - Only works for prepared casters

6. **Spell Casting Validation** (`game_state.py:706-735`):
   - `can_cast_spell(spell_name)` - Validates spell can be cast
   - Checks if character is a spellcaster
   - Checks if spell is known
   - For prepared casters: Checks if spell is prepared
   - Returns `(can_cast, reason)` tuple

7. **Integrated Spell Slot Tracking** (already existed, enhanced):
   - `SpellSlots` class tracks levels 1-9 (current and max)
   - `cast_spell()` now validates known/prepared status before consuming slot
   - Optional `skip_validation` parameter for backwards compatibility
   - Concentration tracking integration

8. **Maximum Prepared Spells Calculation** (`game_state.py:561-583`):
   - `get_max_prepared_spells(ability_modifier)` - Calculate preparation limit
   - Prepared casters: `max(1, ability_modifier + level)`
   - Known casters: Returns number of known spells (unlimited prepared)
   - Non-casters: Returns 0

9. **UI Commands** (`web/app_gradio.py:1084-1260`):
   - `/spells` - Show known and prepared spells with spell slot status
     - Displays different format for prepared vs known casters
     - Shows max prepared limit for prepared casters
     - Lists spell slots by level with current/max counts
   - `/learn_spell <name>` - Learn a new spell
   - `/prepare_spell <name>` - Prepare a spell (prepared casters only)
   - `/unprepare_spell <name>` - Unprepare a spell
   - All commands integrated with help text

10. **Serialization** (`game_state.py:1015-1068`):
    - All spell data saved in to_dict() and from_dict()
    - Preserves known_spells, prepared_spells, spellcasting_class, spellcasting_ability
    - Full compatibility with save/load system

**D&D 5e Rules Implementation**:

**Prepared Casters** (Wizard, Cleric, Druid, Paladin):
- Must prepare spells after a long rest
- Number of spells prepared = spellcasting ability modifier + class level (minimum 1)
- Example: Level 5 Wizard with INT 16 (+3 modifier) → 3 + 5 = 8 spells prepared
- Can only cast prepared spells (must have them in prepared list)
- Can change prepared spells after each long rest

**Known Casters** (Sorcerer, Bard, Warlock, Ranger):
- Permanently know a limited set of spells
- All known spells are automatically prepared (can cast any known spell)
- Learn new spells when leveling up
- Cannot easily change known spells (requires special mechanics)

**Testing (28 tests total)**:

**Test File**: `tests/test_spell_preparation.py` (480 lines)

- `TestSpellCasterTypes`: 3 tests
  - Prepared caster identification (Wizard, Cleric, Druid, Paladin)
  - Known caster identification (Sorcerer, Bard, Warlock, Ranger)
  - Non-caster identification

- `TestSpellLearning`: 4 tests
  - Wizard learning spell (must prepare separately)
  - Sorcerer learning spell (auto-prepares)
  - Attempting to learn already-known spell (rejected)
  - Non-caster attempting to learn spell (rejected)

- `TestSpellPreparation`: 6 tests
  - Wizard preparing spell successfully
  - Preparing multiple spells up to limit
  - Exceeding preparation limit (rejected)
  - Preparing unknown spell (rejected)
  - Re-preparing already-prepared spell (rejected)
  - Known caster attempting to use prepare (rejected)

- `TestUnprepareSpell`: 2 tests
  - Unpreparing spell successfully
  - Unpreparing non-prepared spell (rejected)

- `TestSpellCastingValidation`: 5 tests
  - Prepared spell can be cast (wizard)
  - Unprepared spell cannot be cast (wizard)
  - Known spell can be cast (sorcerer)
  - Unknown spell cannot be cast
  - Non-caster cannot cast spells

- `TestCastSpellIntegration`: 3 tests
  - Casting prepared spell consumes slot
  - Casting unprepared spell fails and doesn't consume slot
  - Skip validation parameter works (backwards compatibility)

- `TestSpellSerialization`: 2 tests
  - Spell data serializes correctly
  - Spell data deserializes correctly

- `TestMaxPreparedSpells`: 3 tests
  - Prepared caster max calculation with different modifiers
  - Known caster max calculation (equals known spells)
  - Non-caster returns 0

**All 28 tests passing** ✅

**Example Usage**:

```
# Wizard (Prepared Caster)
Player: /learn_spell Fireball
GM: Learned Fireball! (must prepare to cast)

Player: /learn_spell Magic Missile
GM: Learned Magic Missile! (must prepare to cast)

Player: /spells
GM: **Known Spells (2)**:
    - Fireball
    - Magic Missile
    **Prepared Spells (0)**:
    *None - use /prepare_spell to prepare spells*
    **Max Prepared**: 6 (3 INT mod + 3 level)

Player: /prepare_spell Fireball
GM: Prepared Fireball (1/6 spells prepared)

Player: /prepare_spell Magic Missile
GM: Prepared Magic Missile (2/6 spells prepared)

Player: /cast Fireball
GM: Cast Fireball (level 3 slot used, 1 remaining)

# Sorcerer (Known Caster)
Player: /learn_spell Magic Missile
GM: Learned Magic Missile! (automatically prepared)

Player: /spells
GM: **Known Spells (1)**:
    - Magic Missile
    **Type**: Known Caster (all known spells are prepared)

Player: /cast Magic Missile
GM: Cast Magic Missile (level 1 slot used, 3 remaining)
```

**Files Modified (2 files)**:
- `dnd_rag_system/systems/game_state.py` - Added spell tracking and management methods
  - New fields: spellcasting_class, spellcasting_ability, known_spells, prepared_spells
  - New methods: learn_spell(), prepare_spell(), unprepare_spell(), can_cast_spell()
  - Enhanced cast_spell() with validation
  - Updated serialization to include spell data
- `web/app_gradio.py` - Added spell management commands
  - `/spells` command (lines 1191-1260)
  - `/learn_spell <name>` command (lines 1084-1115)
  - `/prepare_spell <name>` command (lines 1117-1156)
  - `/unprepare_spell <name>` command (lines 1158-1189)
  - Updated help text with spell commands

**Files Created (1 test file)**:
- `tests/test_spell_preparation.py` (480 lines, 28 tests)

**Integration**:
- Works seamlessly with existing spell slot system (SpellSlots class)
- Compatible with save/load system (spell data persists)
- Integrates with concentration mechanics
- Compatible with spell_manager.py spell lookup functions

**Result**: Players can now properly learn and prepare spells following D&D 5e rules! Wizards must prepare spells daily, Sorcerers can cast any known spell. The system enforces preparation limits, validates spell knowledge, and provides clear feedback. Full D&D 5e compliance for spellcasting classes!

---

## ✅ Equipment System with Magic Items & Class Features ✅ FULLY IMPLEMENTED (2026-01-14)

### Complete Magic Item and Class Feature System
- **Goal**: Allow players to equip magic items, see automatic bonuses, and access class features through RAG
- **Status**: ✅ FULLY IMPLEMENTED with 70+ passing tests + integration test + E2E tests

**Implementation**:
1. **Magic Items Database** (`dnd_rag_system/data/magic_items.py`):
   - 30+ magic items including rings, cloaks, weapons, armor, potions
   - Structured data with rarity, attunement requirements, effects, descriptions
   - Items: Ring of Protection, Cloak of Protection, Flametongue, +1/+2/+3 weapons/armor
   - Potions: Healing (all variants), Invisibility, Flying, Greater Healing

2. **Class Features Database** (`dnd_rag_system/data/class_features.py`):
   - 6 classes: Fighter, Wizard, Rogue, Cleric, Barbarian, Paladin
   - 60+ class features covering levels 1-20
   - Each feature: name, level, description, mechanics, usage restrictions
   - Examples: Sneak Attack, Action Surge, Rage, Divine Smite, Spellcasting

3. **Magic Item Manager** (`dnd_rag_system/systems/magic_item_manager.py`):
   - Item lookup by name
   - Attunement limit enforcement (max 3 per D&D 5e rules)
   - Slot conflict detection (can't wear 2 rings on same hand)
   - Bonus calculation and aggregation
   - Potion consumption system
   - **Tests**: 15 unit tests ✅

4. **Class Feature Manager** (`dnd_rag_system/systems/class_feature_manager.py`):
   - Feature lookup by class and level
   - Spell list retrieval for caster classes
   - Feature availability checking
   - Level-scaled effects (e.g., Sneak Attack damage increases with level)
   - **Tests**: 20 unit tests ✅

5. **Character Equipment Integration** (`dnd_rag_system/systems/character_equipment.py`):
   - Equip/unequip system with 11 equipment slots
   - Automatic bonus application (AC, saving throws, attack rolls)
   - Attunement tracking (visual indicators ⭐)
   - Equipment summary with total bonuses
   - Potion usage with effects
   - **Tests**: 35 unit tests ✅

6. **Game Engine Integration** (`web/app_gradio.py`):
   - `/equip <item>` - Equip magic item from inventory
   - `/unequip <slot>` - Unequip item from specific slot
   - `/equipment` - Show all equipped items and total bonuses
   - Commands integrated into help text
   - Full error handling and user feedback

7. **RAG Ingestion** (`ingest_game_content.py`):
   - Loads magic items into ChromaDB collection
   - Loads class features into ChromaDB collection
   - Enables semantic search for "What does Ring of Protection do?"

**Equipment Slots**:
- ring_left, ring_right (max 2 rings)
- neck (amulets, necklaces)
- armor (armor pieces)
- main_hand, off_hand (weapons, shields)
- head (helmets)
- hands (gloves)
- feet (boots)
- back (cloaks)
- waist (belts)
- arms (bracers)

**Attunement System**:
- D&D 5e rule: Maximum 3 attuned items
- Attuned items marked with ⭐ in equipment list
- Attunement counter shows "X/3"
- Cannot equip 4th attuned item (enforced)

**Testing (70+ tests total)**:
- Unit Tests:
  - `tests/test_magic_item_manager.py` - 15 tests ✅
  - `tests/test_class_feature_manager.py` - 20 tests ✅
  - `tests/test_character_equipment.py` - 35 tests ✅
- Integration Test:
  - `tests/test_equipment_integration.py` - Full system integration ✅
- E2E Tests:
  - `e2e_tests/test_equipment_system_e2e.py` - Browser-based test ✅
  - `e2e_tests/test_magic_item_rag_e2e.py` - RAG query test ✅

**Example Usage**:
```
Player: /equip Ring of Protection
GM: ✅ Equipped Ring of Protection (attuned)
    Effects:
      +1 AC
      +1 Saving Throws

Player: /equipment
GM: **Equipped Items:**
    • Ring_Left: Ring of Protection ⭐ (attuned)
    **Attunement:** 1/3
    **Total Bonuses:**
      +1 AC
      +1 Saving Throws

Player: /unequip ring_left
GM: 🔓 Unequipped Ring of Protection
```

**Files Created (12 files)**:
- `dnd_rag_system/data/magic_items.py`
- `dnd_rag_system/data/class_features.py`
- `dnd_rag_system/systems/magic_item_manager.py`
- `dnd_rag_system/systems/class_feature_manager.py`
- `dnd_rag_system/systems/character_equipment.py`
- `tests/test_magic_item_manager.py`
- `tests/test_class_feature_manager.py`
- `tests/test_character_equipment.py`
- `tests/test_equipment_integration.py`
- `e2e_tests/test_equipment_system_e2e.py`
- `e2e_tests/test_magic_item_rag_e2e.py`
- `ingest_game_content.py`

**Files Modified (3 files)**:
- `web/app_gradio.py` (added equipment commands)
- `TODO.md` (marked as completed)
- `docs/DONE.md` (added this entry)

**Documentation**:
- `docs/EQUIPMENT_SYSTEM.md` - Complete system guide with usage examples

**Commit**: e49c161 - "feat: Add complete equipment system with magic items and class features"

**Result**: Players can now equip magic items, see automatic stat bonuses, and query RAG for class features and magic items! Equipment system fully functional and tested at unit, integration, and E2E levels.

---

## ✅ Party Member Interactions - Healing & Targeting ✅ IMPLEMENTED (2026-01-05)

### Party Member Healing System
- **Goal**: Allow party members to cast healing spells and buffs on each other
- **Status**: ✅ IMPLEMENTED - Healing other party members works

**Implementation**:
1. **Heal Other Party Members** (gm_dialogue_unified.py:475-510):
   - `/cast Cure Wounds on Thorin` - heals target party member
   - Parser extracts target name after "on" keyword
   - Looks up target in `session.party` list
   - Applies healing to target's HP
   - Shows feedback: "Elara casts Cure Wounds on Thorin, healing 8 HP"

2. **Target Validation**:
   - Checks if target party member exists in party
   - Falls back to self-targeting if no target specified
   - Works for both cantrips and leveled spells
   - Validates spell level before casting

3. **Spell Slot Consumption**:
   - Properly consumes spell slots when healing allies
   - Prevents casting without available slots
   - Cantrips (level 0) don't consume slots

**Supported Actions**:
- ✅ Single-target healing: `/cast Cure Wounds on Thorin`
- ✅ Self-healing: `/cast Cure Wounds` (defaults to self)
- ✅ Healing multiple party members sequentially
- ✅ Upcasting healing spells: `/cast Cure Wounds` (uses higher slot automatically)
- ❌ Party-wide buffs: "cast Bless on the entire party" (NOT YET IMPLEMENTED)
- ❌ Item sharing: "Thorin hands his rope to Legolas" (NOT YET IMPLEMENTED)
- ❌ Coordinated attacks: "Aragorn and Gimli attack together" (NOT YET IMPLEMENTED)

**Testing**:
- `tests/test_party_member_interactions.py` - 5 passing tests ✅
  - Test casting healing spell on party member
  - Test healing increases target HP
  - Test healing cannot exceed max HP
  - Test self-healing when no target specified
  - Test healing multiple party members sequentially

**Example Usage**:
```
Player: /cast Cure Wounds on Thorin
GM: ⚕️ Elara casts Cure Wounds on Thorin, healing 6 HP

[Thorin's HP: 15 → 21]
[Elara's Spell Slots: Level 1: 3/4 remaining]
```

**Files**:
- Core logic: `dnd_rag_system/systems/spell_manager.py:cast_healing_spell()`
- Integration: `dnd_rag_system/systems/gm_dialogue_unified.py:475-510`
- Tests: `tests/test_party_member_interactions.py`

**Next Steps** (NOT YET IMPLEMENTED):
- Party-wide buff spells (`/cast Bless on party`)
- Item sharing between party members (`/give rope to Legolas`)
- Coordinated multi-character attacks
- Social interactions tracking

---

## ✅ World State & Exploration System ✅ FULLY IMPLEMENTED (2025-12-26)

### Complete Persistent World with Lazy Generation
- **Goal**: Maintain consistent, persistent game world with interconnected locations
- **Status**: ✅ FULLY IMPLEMENTED with 29 passing tests

**Implementation**:
1. **Location System** (`game_state.py`):
   - `Location` dataclass with comprehensive metadata
   - `LocationType` enum (town, tavern, shop, dungeon, cave, forest, etc.)
   - Persistent state tracking:
     - `visit_count` - tracks number of visits
     - `defeated_enemies` - set of dead enemies (stay dead!)
     - `moved_items` - dict tracking taken items
     - `completed_events` - set of finished events
   - `connections` list for graph structure
   - Discovery system (`is_discovered` flag)

2. **World Map Integration** (`GameSession`):
   - `world_map: Dict[str, Location]` - persistent location storage
   - `get_location()`, `get_current_location_obj()` methods
   - `connect_locations()` - creates bidirectional connections
   - `travel_to()` - validates connections before travel
   - `get_available_destinations()` - shows where you can go
   - `mark_enemy_defeated_at_current_location()` - persistent enemy tracking
   - `is_enemy_defeated_here()` - check if enemy already dead

3. **World Builder** (`world_builder.py`):
   - `initialize_world()` - creates starting world with 11 locations
   - `generate_random_location()` - **LAZY GENERATION**
   - Context-aware generation (forests → caves, towns → wilderness)
   - Weighted probabilities for realistic geography
   - Procedural names ("Dark Forest", "Hidden Cavern")
   - Varied descriptions (multiple templates per type)

4. **Navigation Commands** (`gm_dialogue_unified.py`):
   - `/travel <location>` - move between connected locations
   - `/map` - show available destinations from current location
   - `/locations` - list all discovered locations with visit counts
   - `/explore` - **LAZY GENERATION** - discover new areas!

**Starting World** (11 locations):
- Town Square (hub)
- The Prancing Pony Inn
- Market Square
- Temple District
- Adventurer's Guild Hall
- Town Gates
- Forest Path
- Mountain Road
- Dark Cave (undiscovered)
- Old Ruins (undiscovered)
- Dragon's Lair (undiscovered)

**Lazy Generation**:
- `/explore` generates new locations procedurally
- Context-aware (forest generates caves/ruins, town generates wilderness)
- Unique names from prefix+suffix combinations
- Varied descriptions
- Auto-connects to current location
- Connection limit (max 6 per location prevents infinite sprawl)

**Persistence**:
- ✅ Defeated enemies stay dead across visits
- ✅ Locations persist in `session.world_map`
- ✅ Connections maintained bidirectionally
- ✅ Visit counts tracked
- ✅ Discovery status tracked
- ✅ Item tracking structure exists (`moved_items`)

**GM Context Integration**:
- GM knows about return visits (describes naturally without counting)
- GM aware of defeated enemies (can mention remains)
- Location descriptions consistent
- Scene continuity maintained

**Testing**:
- `test_world_system.py` - 11 tests ✅ (static world)
- `test_lazy_generation.py` - 10 tests ✅ (procedural generation)
- `test_location_items.py` - 8 tests ✅ (item persistence infrastructure)
- `e2e_tests/test_world_exploration.py` - Selenium E2E test

**Total**: 29 passing tests ✅

**Documentation**:
- `docs/WORLD_SYSTEM_COMPLETE.md` - Complete system guide
- `docs/ITEM_PERSISTENCE_EXPLAINED.md` - Item tracking details
- `e2e_tests/README_WORLD_EXPLORATION.md` - E2E test guide

**Commits**:
- a0e3812 - World state system with static locations
- 22da0c8 - Lazy location generation
- f9d108a - E2E test for world exploration
- 89d1542 - GM contextual awareness
- aa76412 - Item persistence tests

**Files**:
- `dnd_rag_system/systems/game_state.py` (Location, LocationType, GameSession)
- `dnd_rag_system/systems/world_builder.py` (world creation, lazy generation)
- `dnd_rag_system/systems/gm_dialogue_unified.py` (navigation commands)
- `test_world_system.py`
- `test_lazy_generation.py`
- `test_location_items.py`
- `e2e_tests/test_world_exploration.py`

**Result**: Players can explore infinite procedurally-generated world with full persistence!

---

## ✅ Party-Based Gameplay System

### Party-Based Chat Mode ✅ IMPLEMENTED
- When party is defined and party mode is active, send full party info to GM chat context
- Enabled true party-based D&D gameplay where GM manages adventures for the whole group
- GM receives complete party information including all character stats, equipment, and abilities

### Party/Character Mode Toggle in Play Game Tab ✅ IMPLEMENTED
- Added radio button toggle: "🎭 Single Character" vs "🎲 Party Mode"
- UI dynamically shows/hides appropriate controls based on mode
- **Character Mode**: Load single character, GM sees only that character's info
- **Party Mode**: Load entire party, GM sees all party members' stats and equipment
- Mode switching updates displayed character sheet and load buttons

### GM Context Enhancement for Party Mode ✅ IMPLEMENTED
- Format party context with all character stats, equipment, spells for each party member
- GM prompts include full party roster with individual stats
- /stats command shows party sheet in party mode
- Party sheet displays all members with HP, AC, ability scores, and equipment

---

## ✅ Turn-Based Combat System ✅ FULLY IMPLEMENTED

### Combat System Implementation
- **Initiative System**:
  - Roll initiative for all party members + enemies at combat start
  - Sort by initiative order (highest to lowest)
  - Track current turn in combat round
  - Display initiative order in UI
- **Turn Management**:
  - Active character indicator: "🎯 [Character]'s Turn"
  - Manual turn advance with `/next_turn` command
  - Auto-advancement after combat actions
  - End round detection (all characters acted)
  - New round notification and counter
- **Commands**:
  - `/start_combat [enemy1, enemy2, ...]` - Start combat with initiative rolls
  - `/next_turn` - Manually advance to next turn
  - `/initiative` - Display current initiative tracker
  - `/end_combat` - End combat encounter
- **Technical Implementation**:
  - `CombatManager` class in `dnd_rag_system/systems/combat_manager.py`
  - Integrated with `CombatState` in `game_state.py`
  - Initiative ordering, turn tracking, round counter
  - Support for both party mode and single character mode
- **Testing**:
  - E2E test suite: `e2e_tests/test_combat_system.py` - 9/9 tests passing
  - UI integration test: `e2e_tests/test_ui_combat_integration.py` - 5/5 tests passing
- **Files**:
  - Core logic: `dnd_rag_system/systems/combat_manager.py`
  - Integration: `dnd_rag_system/systems/gm_dialogue_unified.py`
  - Tests: `e2e_tests/test_combat_system.py`, `e2e_tests/test_ui_combat_integration.py`

---

## ✅ Narrative to Mechanics Translation System ✅ FULLY IMPLEMENTED (2025-12-26)

### Automatic Game State Updates from GM Narrative
- **Goal**: Automatically extract and apply game mechanics from GM narrative responses to keep game state in sync
- **Problem Solved**: GM could narrate "The dragon deals 30 damage!" but HP wouldn't update automatically
- **Implementation**: Created comprehensive two-component system:
  
**Component 1: MechanicsExtractor** (`mechanics_extractor.py`)
  - Uses small LLM (qwen2.5:3b) for structured extraction
  - Parses narrative text into JSON with specific mechanics schema
  - Extracts: damage, healing, conditions, spell slots, item consumption, death/unconscious
  - Character-aware: Accepts character names list for better extraction accuracy
  - Debug mode available for testing and troubleshooting
  
**Component 2: MechanicsApplicator** (`mechanics_applicator.py`)
  - Applies extracted mechanics to CharacterState or PartyState objects
  - Calls appropriate game_state.py methods: `take_damage()`, `heal()`, `add_condition()`, etc.
  - Returns feedback messages describing what was applied
  - Supports both single character and party mode
  
**Integration** (in `gm_dialogue_unified.py`):
  - Step 5.3 in response generation pipeline (lines 388-418)
  - Automatically triggered after GM generates narrative
  - Extracts mechanics → Applies to game state → UI auto-updates
  - Error handling ensures graceful degradation if extraction fails
  
**Supported Mechanics**:
  ✅ **Damage**: Amount, type (slashing/fire/etc.), target
  ✅ **Healing**: Amount, source, target
  ✅ **Conditions**: Added/removed, duration, target
  ✅ **Spell Slots**: Level, spell name, caster
  ✅ **Items**: Consumed items, quantity, character
  ✅ **Death/Unconscious**: Character state changes
  
**Example Flow**:
  1. GM: "The dragon's fiery breath scorches Thorin for 30 fire damage!"
  2. Extractor: `{"damage": [{"target": "Thorin", "amount": 30, "type": "fire"}]}`
  3. Applicator: Calls `thorin_state.take_damage(30, "fire")`
  4. Game State: `thorin.current_hp: 28 → -2` (unconscious!)
  5. UI: Character sheet automatically shows "HP: 0/28 💀 UNCONSCIOUS"
  
**Testing**:
  - Unit tests: `test_mechanics_system.py` ✅
  - E2E tests: `e2e_tests/test_dragon_combat_mechanics.py` ✅
  - All core mechanics tested and working
  - Minor edge cases where non-mechanics text triggers extraction (low impact)
  
**Result**: Game state now automatically stays synchronized with narrative! Players don't need to manually track HP, conditions, or resources. The system handles it transparently.

**Commit**: cf43f62 - "feat: Implement narrative to mechanics translation + fix shop/testing bugs"

**Files**:
  - `dnd_rag_system/systems/mechanics_extractor.py`
  - `dnd_rag_system/systems/mechanics_applicator.py`
  - `dnd_rag_system/systems/gm_dialogue_unified.py` (integration)
  - `test_mechanics_system.py` (test suite)

---

## ✅ Party Mode UI Bug Fix ✅ COMPLETED (2025-12-26)

### Fixed Party Mode Chat Textarea Non-Interactive Bug
- **Issue**: When party mode was enabled or "Load Party" was clicked, the chat textarea became non-interactive, preventing users from sending messages
- **Impact**: Made party mode completely unusable - users could load party but couldn't play
- **Root Cause**: `load_party_mode()` was returning empty string `""` for msg_input parameter instead of using `gr.update()`
- **Gradio Behavior**: Gradio interpreted the empty string as a component value update that accidentally disabled interactivity
- **Fix Applied**:
  - Changed return type from `Tuple[str, str, list]` to `Tuple[str, gr.update, list]`
  - Used `gr.update(interactive=True, value="")` to explicitly keep textarea interactive and clear it
  - Applied fix to both error case (no party members) and success case
- **Result**: Party mode is now fully functional - players can send messages and play with their party! ✅
- **Commit**: ed75a27
- **File Modified**: `web/app_gradio.py`

---

## ✅ Action Validator Bug Fixes ✅ COMPLETED (2025-12-26)

### Fixed Action Validator False Positives & Combat State Bugs
- **Issue 1**: "ready for battle" incorrectly parsed as ITEM_USE
  - **Problem**: Phrase matched "ready" keyword but extracted "for battle" as item name
  - **Fix**: Added filtering to skip matches where word after action keyword is a preposition (for, to, if, when, as, because)
  - **Result**: "ready for battle" → EXPLORATION, "ready my shield" → ITEM_USE (still works)
  
- **Issue 2**: "swing at dragon" failed to detect target
  - **Problem**: Articles like "the" prevented fuzzy matching with "Ancient Red Dragon"
  - **Fix**: Enhanced fuzzy matching to strip articles (the, a, an) before comparison
  - **Result**: All variations ("swing at dragon", "attack the dragon") now correctly match entity names
  
- **Issue 3**: Combat state persistence bug causing crashes
  - **Problem**: Code referenced non-existent `game_session.combat_state` attribute (should be `game_session.combat`)
  - **Fix**: Corrected attribute reference in `_validate_combat()` method
  - **Result**: Combat validation no longer crashes during state checks

- **🔥 Issue 4**: **CRITICAL - Spell target hallucination (ROOT CAUSE of "large bug")**
  - **Problem**: Spell validation never checked if TARGET exists, only if spell is known
  - **Symptom**: "I cast Magic Missile at the goblin" → GM hallucinated goblin death, dragon, Thorin, combat cascade
  - **Root Cause**: `_validate_spell()` missing target existence check
  - **Fix Applied**:
    1. Added target validation in `_validate_spell()` - checks npcs_present and combat state
    2. Created `_extract_spell_target()` - properly extracts target after spell name
    3. Added spell-specific invalid target response - deterministic rejection message
  - **Result**: Spell targets now validated like combat targets - prevents ALL hallucinations
  - **Testing**: "cast Magic Missile at goblin" (no goblin) → INVALID ✅
  
- **Testing**: All existing tests pass, comprehensive edge case testing confirms no regressions
- **Files Modified**: 
  - `dnd_rag_system/systems/action_validator.py` (spell target validation added)
  - `dnd_rag_system/systems/gm_dialogue_unified.py` (spell target rejection responses)
- **E2E Test Created**: `e2e_tests/test_hallucination_bug.py` - validates fix prevents hallucination cascade

---

## ✅ Context Grounding / Reality Check System ✅ FULLY IMPLEMENTED

### "Reality Check" for Player Actions
- **Goal**: Prevent the GM LLM from hallucinating entities or actions inconsistent with the current game state.
- **Implementation**: Created hybrid "tagging" system in `dnd_rag_system/systems/action_validator.py`
  - **Intent Analysis**: Parses player input to identify action type (combat, spell, conversation, item use, exploration)
  - **State Validation**: Validates actions against `GameSession` state
    - Combat: Verifies targets exist in `npcs_present` or `combat.initiative_order`
    - Weapon validation: Checks if weapon used in combat is in inventory
    - Spells: Checks if spell is known by character (with fuzzy matching)
    - Items: Validates items exist in character inventory
    - Conversations: Allows NPC introduction for contextually appropriate NPCs
  - **Fuzzy Matching**: Handles partial matches (e.g., "goblin" → "Goblin Scout")
  - **Personality-Driven Deterministic Responses**: Invalid actions get character-appropriate rejections
    - Dwarf Fighter: "Ye reach fer yer Bow to attack, but it's not there! Can't attack with a weapon ye don't have, ye daft fool!"
    - Dwarf Fighter casting spell: "Ye try to cast Fireball? Are ye daft?! Ye're a FIGHTER, not some fancy-robed wizard!"
    - Shows inventory hints and character class information
  - **NPC Conversation Features**:
    - Encourages dynamic NPC introduction in appropriate contexts
    - Auto-adds NPCs to `npcs_present` when GM introduces them
    - Rejects NPC interactions that don't make contextual sense
  - **Integration**: Fully integrated into `gm_dialogue_unified.py.generate_response()`
  - **Testing**:
    - E2E test suite: `e2e_tests/test_reality_check_e2e.py` (6/6 tests passing)
    - Browser test suite: `e2e_tests/test_reality_check_browser.py` (Selenium-based)
- **Files**:
  - Core logic: `dnd_rag_system/systems/action_validator.py`
  - Integration: `dnd_rag_system/systems/gm_dialogue_unified.py`
  - Tests: `e2e_tests/test_reality_check_e2e.py`, `e2e_tests/test_reality_check_browser.py`

---

## ✅ Inventory & Shopping System ✅ FULLY IMPLEMENTED

### GM-Driven Conversational Shop System
- **Philosophy**: Shop interactions happen through natural conversation with GM-controlled NPC shopkeepers
- **Equipment RAG Database**: Parsed 58 equipment items from equipment.txt into ChromaDB
  - Weapons (swords, axes, bows, etc.) with damage and properties
  - Armor (leather, chainmail, plate, etc.) with AC and weight
  - Adventuring gear (rope, torches, rations, etc.) with description and weight
  - Magical items (if applicable)
- **Shop Transaction System**:
  - Purchase validation (checks gold, updates inventory)
  - Sell system (half market price, D&D 5e standard)
  - Natural language parsing ("/buy longsword", "I'll take the rope", etc.)
  - Gold deduction and inventory management
  - Fuzzy item matching for flexible user input
- **NPC Shopkeeper Integration**:
  - GM controls shopkeeper personality (friendly, grumpy, mysterious, greedy, etc.)
  - Players converse naturally: ask about prices, haggle, request recommendations
  - System processes transactions automatically via chat commands
  - GM narrates transaction outcomes naturally
  - Shopkeeper context generator for GM prompts
- **Testing**: Comprehensive test suite (test_shop_system.py) - ALL TESTS PASSING
- **Files**:
  - Equipment loader: `dnd_rag_system/loaders/equipment_loader.py`
  - Shop system: `dnd_rag_system/systems/shop_system.py`
  - Tests: `test_shop_system.py`
  - Equipment data: `dnd_rag_system/data/equipment.txt`

### Real-Time Inventory Display Updates ✅ IMPLEMENTED (2026-01-13)
- **Goal**: Automatically refresh inventory display in UI after `/buy` and `/sell` transactions
- **Status**: ✅ ALREADY WORKING - Inventory updates automatically via Gradio's reactive output system
- **How It Works**:
  1. Shop transactions update `char_state.inventory` (shop_system.py:164-177)
  2. The `chat()` function returns `character_sheet` on every message (app_gradio.py:995)
  3. Gradio's reactive system auto-updates UI components (app_gradio.py:1480,1489)
  4. `format_character_sheet()` reads live data from `char_state.inventory` (app_gradio.py:639)
- **Flow**: `/buy longsword` → shop updates inventory → chat returns updated sheet → UI refreshes automatically
- **Testing**: Comprehensive shop tests verify inventory updates (test_shop_system.py:130-187)
  - Test 3.1: Purchase adds item to inventory (line 152-153)
  - Test 3.2: Multiple item purchases update inventory correctly (line 166)
  - Test 4.1: Sales remove items from inventory (line 212)
  - Test 7: Complete shopping experience validates full flow (line 307-352)
- **Files**:
  - Shop logic: `dnd_rag_system/systems/shop_system.py`
  - UI integration: `web/app_gradio.py:599-648` (format_character_sheet)
  - Chat handler: `web/app_gradio.py:831-995` (returns character_sheet)
  - Gradio wiring: `web/app_gradio.py:1477-1493` (event handlers)
  - Tests: `tests/test_shop_system.py`

---

## ✅ RAG-Based Character Creation (Partial)

### Racial Bonuses from RAG ✅ IMPLEMENTED (with fallback)
- Query ChromaDB for race information during character creation
- **Issue Found**: Current ChromaDB racial data has incorrect ability scores (OCR errors from PDF parsing)
- **Solution**: Implemented with fallback to hardcoded correct D&D 5e racial bonuses
- Auto-apply ability score increases (e.g., Dwarf +2 CON, Elf +2 DEX)
- Add racial traits (Darkvision, Fey Ancestry, Dwarven Resilience, etc.)
- Set speed, size, languages
- Display racial features in character creation form

---

## System Integration Points

### Game State System
- File: `dnd_rag_system/systems/game_state.py`
- `CharacterState` class for individual character tracking
- `PartyState` class for party management
- `CombatState` class for turn-based combat
- `GameSession` class for overall game state
- `SpellSlots` class for spell tracking
- Inventory management system
- HP, AC, ability score tracking

### RAG System
- File: `dnd_rag_system/core/chroma_manager.py`
- ChromaDB integration for D&D 5e content
- Collections: races, classes, spells, monsters, equipment
- Query system for retrieving game data

### Action Validation System
- File: `dnd_rag_system/systems/action_validator.py`
- Intent detection and classification
- Game state validation
- Fuzzy matching for flexible input
- Personality-driven rejection messages

### Combat Management
- File: `dnd_rag_system/systems/combat_manager.py`
- Initiative rolling and tracking
- Turn advancement (manual and automatic)
- Round counter
- Combat state display utilities

### Shop System
- File: `dnd_rag_system/systems/shop_system.py`
- Purchase/sell transaction handling
- Gold management
- Inventory updates
- Equipment database integration

### GM Dialogue System
- File: `dnd_rag_system/systems/gm_dialogue_unified.py`
- Main conversation handler
- Integration point for all subsystems
- Prompt engineering for GM responses
- Command parsing (/start_combat, /stats, /buy, etc.)

### Gradio UI
- File: `web/app_gradio.py`
- Character creation tab
- Play game tab with party mode toggle
- Chat interface
- Character/party sheet display
- Initiative tracker display

---

## 🤖 Narrative to Mechanics Translation System (2025-12-26)

**Status:** ✅ Fully Implemented and Working

### Overview
Automatically extracts game mechanics from GM narrative responses and updates game state using a small LLM (Qwen 2.5 3B).

### Features
- **Automatic Mechanics Extraction**: Uses Qwen 2.5 3B to parse GM narratives for:
  - Damage dealt (amount, type, target)
  - Healing received (amount, source, target)
  - Conditions added/removed (poisoned, stunned, frightened, etc.)
  - Spell slots used (caster, level, spell name)
  - Items consumed (character, item, quantity)
  - Character deaths/unconscious states

- **Automatic State Updates**:
  - Character HP automatically updated when damage/healing mentioned
  - Conditions automatically tracked
  - Spell slots decremented when spells cast
  - Inventory items removed when consumed

- **Smart Extraction**:
  - Handles multiple characters in party mode
  - Works with natural language variations
  - Extracts structured JSON from narrative text
  - Gracefully handles extraction failures

### Implementation Files
- `dnd_rag_system/systems/mechanics_extractor.py`: LLM-based extraction (344 lines)
- `dnd_rag_system/systems/mechanics_applicator.py`: State application (262 lines)
- `test_mechanics_system.py`: Comprehensive test suite
- Integrated into: `gm_dialogue_unified.py:388-418`

### Example
```
GM Narrative: "The goblin's axe strikes Thorin, dealing 8 slashing damage!"
Auto-Extracted: {"damage": [{"target": "Thorin", "amount": 8, "type": "slashing"}]}
Auto-Applied: Thorin's HP: 28 → 20
```

---

## 🧪 Testing & Bug Fixes (2025-12-26)

### Selenium E2E Tests - Fixed
- **Issue**: Gradio 6.x changed chat message selectors, breaking test suite
- **Fix**: Updated `get_chat_messages()` to use `.message` class selector with deduplication
- **Location**: `e2e_tests/test_shop_ui.py:71-86`
- **Status**: ✅ Chat messages now retrieve correctly

### Shop System Integration - Fixed (3 bugs)
1. **UI Command Interception Bug**:
   - **Issue**: `app_gradio.py` intercepted `/buy` and `/sell`, returned "Unknown command" before reaching GM
   - **Fix**: Removed else clause that blocked unknown commands (let them pass through to GM)
   - **Location**: `web/app_gradio.py:629-630`

2. **Missing Gold Field Bug**:
   - **Issue**: `CharacterState` lacked `gold` attribute, shop system couldn't track gold
   - **Fix**: Added `gold: int = 50` field to `CharacterState` dataclass with serialization support
   - **Location**: `dnd_rag_system/systems/game_state.py:172-173`

3. **Wrong Gold Location Bug**:
   - **Issue**: Shop system looked for `inventory['Gold']` instead of `character_state.gold`
   - **Fix**: Updated shop system to use `getattr(character_state, 'gold', 0)`
   - **Location**: `dnd_rag_system/systems/shop_system.py:164, 177, 239-240`

**Result**: All shop commands (`/buy`, `/sell`) now working correctly ✅

### Dragon Combat E2E Test - Improved (2025-12-26)
- **File**: `e2e_tests/test_dragon_combat_mechanics.py`
- **Improvements**:
  1. **Fixed jarring location jump**: Added scene transition message that establishes dragon's lair before combat
     - Previously: Load character → random location (Market Square) → "I enter the dragon's lair" (confusing!)
     - Now: Load character → transition message → dragon's lair established → combat starts smoothly
  2. **Fixed HP extraction**: Improved `get_character_sheet_hp()` to search multiple DOM element types
     - Added XPath search for elements containing "HP:" or "Hit Points"
     - Added fallback checks for textareas, labels
     - Previously returned `None`, now robust extraction
  3. **Fixed "Loading content" bug**: Added wait loop to skip intermediate loading states
     - Prevents getting partial/loading messages instead of final GM responses
  4. **Fixed None HP crashes**: Added proper None checks throughout all HP comparisons
     - Prevents `TypeError: '>' not supported between instances of 'NoneType'`
     - Gracefully handles cases where HP tracking unavailable
  5. **Removed blocking input()**: Replaced with automatic browser close after 2s
     - Allows test to run in CI/CD without manual intervention
     - Optional commented code for manual browser inspection during development
  6. **Updated model references**: Changed from "Gemma 2 2B" to "Qwen 2.5 3B" throughout
- **Status**: ✅ Test now runs smoothly with proper scene transitions and error handling

