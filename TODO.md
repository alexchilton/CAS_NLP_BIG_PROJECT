# TODO - D&D RAG System Feature Roadmap

> **Note**: See DONE.md for completed features that are already implemented and working.

---

## 🚨 HIGH PRIORITY - Core Mechanics

### Party Member Interactions
**STATUS: PARTIALLY IMPLEMENTED** 🚧

**✅ COMPLETED (2026-01-05)**:
- ✅ **Single-target healing**: `/cast Cure Wounds on Thorin` works
- ✅ **Target validation**: Checks if target party member exists
- ✅ **Self-healing fallback**: Defaults to self if no target specified
- ✅ **Spell slot consumption**: Properly tracks and consumes slots
- ✅ **Test suite**: 5 passing tests in `tests/test_party_member_interactions.py`
- **Files**: `spell_manager.py:cast_healing_spell()`, `gm_dialogue_unified.py:475-510`

**❌ NOT YET IMPLEMENTED**:
- **Party-wide buffs**: "Gandalf casts Bless on the entire party"
  - Need to detect "party", "everyone", "all" keywords
  - Apply buff to all party members in `session.party` list
  - Track concentration and duration
- **Item sharing**: "Thorin hands his rope to Legolas"
  - Add `/give <item> to <character>` command
  - Validate item in giver's inventory
  - Transfer item between party members
  - Update both inventories
- **Coordinated attacks**: "Aragorn and Gimli attack together"
  - Parse multi-character actions
  - Grant advantage or bonus damage
  - Require both characters have actions available
- **Social Interactions**:
  - Party member conversations
  - Strategy discussions
  - Roleplaying between characters (not mechanically enforced)

---

## 📚 MEDIUM PRIORITY - UX & Polish

### Contextual Help System (4 hours)
**BETTER NEW PLAYER EXPERIENCE** - Current help overwhelming for beginners
- **File**: `app_gradio.py:870-919`
- **Current**: `/help` shows all 25+ commands at once
- **Improve**:
  1. Context-aware help:
     - In combat → show combat commands first
     - In shop → show buy/sell commands
     - Exploring → show map/travel commands
  2. Add "Getting Started" tutorial popup on first load
  3. Add tooltips on UI elements (HP, AC, spell slots)
  4. Natural language examples: "I attack the goblin" vs "/attack goblin"
- **Impact**: Lower barrier to entry, better onboarding

### Party HP Display in Combat (3 hours)
**CRITICAL FOR PARTY MODE** - Can't see ally health during battles
- **File**: `app_gradio.py` (new UI component)
- **Add**: Dedicated "Party Status" panel visible during combat
- **Show**:
  - All party member HP bars
  - Color-coded: green (>75%), yellow (25-75%), red (<25%)
  - Unconscious/dead status clearly marked
  - Conditions (poisoned, blessed, etc.)
- **Impact**: Tactical party coordination possible

### Quest Tracker UI (1 day)
**GAME STRUCTURE** - Give players clear objectives
- **File**: `app_gradio.py` (new UI panel), `game_state.py:1429-1443`
- **Has**: `session.active_quests` already exists but unused!
- **Add**:
  1. UI panel showing active quests
  2. Quest log with descriptions
  3. Mark completed quests
  4. Command: `/quests` to view
  5. GM can add quests dynamically
- **Impact**: Better story flow, players know what to do next

---

## 📚 MEDIUM PRIORITY - Game Mechanics

### Location-Based Item Spawning & Pickup System
- **Current State**: Infrastructure exists but not integrated
  - `location.moved_items` dict exists ✅
  - `location.available_items` list exists ✅
  - Tracks which items were taken ✅
  - Persists across visits (via save/load) ✅
  - BUT: No automatic item spawning or pickup commands
- **Need to Implement**:
  1. **Item Spawning**: Procedural item generation when creating locations
     - Based on location type (caves have treasure, forests have herbs)
  2. **Pickup Command**: `/pickup <item>` or natural language
     - Remove from `location.available_items`
     - Add to `character.inventory`
     - Track in `location.moved_items`
  3. **GM Integration**: GM should mention items in descriptions
     - "You see a glinting sword" (first visit)
     - Skip items in `moved_items` (return visit)
- **Testing**: `test_location_items.py` already has 8 tests for the infrastructure---

## 📚 LOWER PRIORITY / ENHANCEMENTS

### Weight & Encumbrance System (4 hours)
**MISSING D&D MECHANIC** - Players can carry infinite items
- **Current**: No weight tracking at all
- **Need**:
  1. Add weight to equipment database (data exists in ChromaDB)
  2. Calculate total carried weight
  3. Enforce STR-based carrying capacity (STR × 15 lbs)
  4. Encumbered status (speed penalty at STR × 10 lbs)
  5. Show in inventory: "Carrying: 45/150 lbs"
- **Impact**: Adds D&D realism, prevents inventory hoarding

### Enemy HP Display Options (1 hour)
**TACTICAL CLARITY** - Players can't gauge enemy health
- **File**: `combat_manager.py:get_initiative_tracker()`
- **Add**: Toggleable enemy HP display modes:
  - **DM Mode**: "Goblin (injured)" instead of exact HP
  - **Player Mode**: "Goblin (8/15 HP)" exact numbers
  - **Config**: Setting in UI for display preference
- **Impact**: Better tactical decisions without meta-gaming

---

## 🧹 CODE CLEANLINESS (Refactoring)

> **Note**: See docs/DONE.md for completed refactoring tasks (Constants, GameSession rename, LLM Intent Classification)

### Refactor GameMaster God Object (2-3 days)
**ARCHITECTURE** - 1400+ line class doing everything
- **File**: `gm_dialogue_unified.py`
- **Current**: Single class handles:
  - RAG search, combat, shop, spells, travel, validation, LLM prompting
- **Fix**: Extract subsystems:
  - CommandHandler class (routes commands)
  - NarrativeGenerator class (LLM prompts)
  - Keep GameMaster as thin coordinator
- **Impact**: Easier testing, better maintainability

### Deduplicate Character Sheet Formatting
**CODE DUPLICATION** - 80-90% identical functions
- **Files**: `app_gradio.py`
  - `format_character_sheet()` (lines 600-674) - Single character mode
  - `format_character_sheet_for_char()` (lines 1552-1568) - Party mode
- **Differences**:
  - Data source: `gm.session.character_state` vs `party.get_character()`
  - Features: First includes gold, temp HP, death saves, spell slots; second is simpler
- **Fix**: Extract common logic to `_format_sheet_core(char, char_state, show_extras=True)`
- **Complexity**: Moderate - requires careful handling of different data sources
- **Impact**: Single point for bug fixes and improvements
- **Status**: Identified but deferred (larger than 30 min estimate)

---

## 📚 LOWER PRIORITY - Data Quality

> **Note**: See docs/DONE.md for completed RAG Data Quality improvements (SRD integration completed 2026-01-15)


