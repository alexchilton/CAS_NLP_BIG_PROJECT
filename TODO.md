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

### ✅ Rename GameSession to ConversationSession - COMPLETED (2026-01-15)
**NAMING CLARITY** - Resolved naming conflict between two different session classes
- **Files**:
  - Simple dialogue system: `gm_dialogue.py:30-47` (ConversationSession - tracks LLM conversation)
  - Full game system: `game_state.py:1386-1713` (GameSession - tracks complete D&D game state)
- **Analysis**: These are NOT duplicates - they serve different purposes
  - `ConversationSession`: Conversation history for simple RAG dialogue system (used by 2 scripts)
  - `GameSession`: Comprehensive D&D game state (used by web app and unified system)
- **Fix Applied**: Renamed `gm_dialogue.py`'s `GameSession` to `ConversationSession`
  - Added clarifying docstring explaining distinction from game_state.GameSession
  - Verified backward compatibility (scripts don't import it directly)
- **Impact**: Eliminates naming confusion, clarifies architecture

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

## ✅ COMPLETED TASKS

### Extract Magic Strings to Constants ✅ DONE (2026-01-15)
**MAINTAINABILITY** - Commands and keywords hardcoded everywhere
- **✅ Created**: `dnd_rag_system/constants.py` with comprehensive constant classes:
  - `Commands`: All slash commands (`/help`, `/attack`, `/cast`, etc.)
  - `ActionKeywords`: Intent detection keywords (attack, spell, steal, etc.)
  - `ItemEffects`: Magic item effect types
  - `EquipmentSlots`: Character equipment locations
  - `LocationTypes`: World location categories
  - `DamageTypes`, `Conditions`, `CharacterClasses`, `CharacterRaces`
- **✅ Refactored**: 
  - `gm_dialogue_unified.py`: Using `Commands` constants
  - `action_validator.py`: Using `ActionKeywords` constants
- **✅ Tests**: `tests/test_constants.py` - 30 passing tests
- **Impact**: Typos now caught at import time, easier refactoring, IDE autocomplete
  ```
- **Fix**: Create constants file:
  ```python
  class Commands:
      HELP = '/help'
      ATTACK = '/attack'
      CAST = '/cast'
  ```
- **Impact**: Refactoring safer, typos caught at import time

---

## 📚 LOWER PRIORITY - Data Quality

### ✅ RAG Data Quality Improvements - COMPLETED (2026-01-15)

#### ✅ Parse SRD-OGL_V5.1.pdf and Ingest to ChromaDB
**OFFICIAL D&D 5E RULES** - Use authoritative SRD data instead of hardcoded approximations
- **✅ Created**: `scripts/parse_srd_pdf.py` (332 lines)
  - Extracts 12 classes with hit dice, proficiencies, saving throws
  - Extracts 24+ spells with level, school, descriptions
  - Extracts 9 races with traits
  - Outputs to `dnd_rag_system/data/extracted/srd/` as JSON
- **✅ Created**: `scripts/ingest_srd_to_chromadb.py` (137 lines)
  - Ingests parsed data into ChromaDB collection `dnd5e_srd`
  - 45+ documents with structured metadata
  - Queryable for character creation and gameplay
- **✅ Created**: `dnd_rag_system/systems/rag_character_enhancer.py` (322 lines)
  - Auto-applies class features during character creation
  - Sets correct hit dice (Barbarian: d12, Wizard: d6, etc.)
  - Applies proficiencies (armor, weapons, tools, saving throws)
  - Adds class abilities by level
  - Sets spell slots for caster classes (full/half/pact magic)
  - Looks up and suggests appropriate spells from RAG database
- **✅ Tests**: `tests/test_rag_character_enhancer.py` - 16 passing tests
- **✅ Documentation**: `docs/SRD_RAG_INTEGRATION.md` - Complete implementation guide
- **✅ Dependencies**: Added `PyPDF2>=3.0.0` to `requirements.txt`
- **Impact**: 
  - Accurate character creation using official D&D 5e SRD rules
  - Reduces manual errors and LLM hallucinations
  - Single source of truth for class features
  - Easy to update if new SRD versions released

#### Fix Racial Data in ChromaDB
- Current problem: All races showing same ability scores (CHA +1, DEX +1) due to OCR errors
- Need to re-parse or manually add correct racial bonuses:
  - Dwarf: CON +2
  - Elf: DEX +2
  - Halfling: DEX +2
  - Human: All abilities +1
  - Dragonborn: STR +2, CHA +1
  - Gnome: INT +2
  - Half-Elf: CHA +2, two others +1
  - Half-Orc: STR +2, CON +1
  - Tiefling: CHA +2, INT +1
- Note: Currently using fallback hardcoded data, so not critical

#### Improve Class Features Data in RAG
- Current state: Class descriptions exist but lack structured metadata
- Need to add structured metadata for each class:
  - Hit dice (d6, d8, d10, d12)
  - Proficiencies (armor types, weapon types, saving throws, skills)
  - Starting equipment lists
  - Class features by level (e.g., Fighter gets Second Wind at level 1)
  - Spell slots for caster classes
- Options:
  1. Parse existing PDF text more thoroughly
  2. Add structured JSON data manually for 12 classes
  3. Use additional source files with structured class data

#### Auto-apply Class Features During Character Creation
- Query ChromaDB for class information during character creation
- Set correct hit dice (d6/d8/d10/d12)
- Apply proficiencies (armor, weapons, tools, saving throws)
- Add class abilities by level
- Set spell slots for caster classes

### ✅ Upgrade Reality Check with LLM-based NLP Intent Classification - COMPLETED (2026-01-14)
- **Problem**: Current keyword-based approach is brittle
  - Works: "fire my bow", "shoot my bow", "attack with sword"
  - Fails: "loose an arrow", "nock and release my bowstring", "let fly with my longbow"
  - Keyword lists require constant expansion for synonyms and variations
- **Implemented Solution**: Optional LLM-based intent classifier using Qwen2.5-3B
  - **Parallel Implementation**: Both keyword and LLM classifiers available
  - **Runtime Toggle**: Switch via `classifier_type="llm"` parameter
  - **Comparison Mode**: Run both and log differences for validation
  - **Graceful Fallback**: LLM errors automatically fall back to keyword-based
  - **No Breaking Changes**: Default remains keyword-based (fast, reliable)
  - **Model Reuse**: Shares Qwen2.5-3B with mechanics extractor
- **Benefits**:
  - ✅ Handles creative phrasings: "loose an arrow", "nock and release my bowstring"
  - ✅ No keyword maintenance required for LLM mode
  - ✅ Preserves existing functionality (keyword mode still works)
  - ✅ 100% backward compatible (default behavior unchanged)
- **Files Changed**:
  - `dnd_rag_system/config.py` (NEW): Configuration for intent classifiers
  - `dnd_rag_system/systems/action_validator.py`: Added LLM classifier alongside keyword classifier
  - `tests/test_llm_intent_classifier.py` (NEW): Comprehensive test suite
- **Test Results**: All tests passing (keyword, LLM, comparison mode)
- **Time Spent**: ~4 hours (planning, implementation, testing)


