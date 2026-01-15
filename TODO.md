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
  - All SRD code: Using `CharacterClasses` and `CharacterRaces` constants
- **✅ Tests**: `tests/test_constants.py` - 30 passing tests
- **Impact**: Typos now caught at import time, easier refactoring, IDE autocomplete

---

## 📚 LOWER PRIORITY - Data Quality

### ✅ RAG Data Quality Improvements - COMPLETED (2026-01-15)

**OFFICIAL D&D 5E RULES** - Full SRD integration with auto-applied character features

#### ✅ SRD PDF Parsing & Ingestion
- **✅ Created**: `scripts/parse_srd_pdf.py` (332 lines)
  - Extracts 12 classes with hit dice, proficiencies, saving throws
  - Extracts 24+ spells with level, school, descriptions
  - Extracts 9 races with ability score bonuses and traits
  - Outputs to `dnd_rag_system/data/extracted/srd/` as JSON
- **✅ Created**: `scripts/ingest_srd_to_chromadb.py` (137 lines)
  - Ingests parsed data into ChromaDB collection `dnd5e_srd`
  - 45+ documents with structured metadata
  - Auto-runs on first use via `chroma_manager.py._ensure_srd_data()`

#### ✅ RAG-Powered Character Creation
- **✅ Created**: `dnd_rag_system/systems/rag_character_enhancer.py` (322 lines)
  - Auto-applies class features during character creation
  - Sets correct hit dice (Barbarian: d12, Wizard: d6, etc.)
  - Applies proficiencies (armor, weapons, tools, saving throws)
  - Adds class abilities by level
  - Sets spell slots for caster classes (full/half/pact magic) levels 1-20
  - Looks up and suggests appropriate spells from RAG database
- **✅ Modified**: `character_creator.py`
  - Fixed HP calculation to scale with level (not just level 1)
  - `_apply_race_traits()` queries ChromaDB for racial bonuses
  - `_apply_class_features()` calls RAG enhancement
  - Uses constants instead of magic strings

#### ✅ Constants & Code Quality
- **✅ Created**: `dnd_rag_system/constants.py`
  - `CharacterClasses` - All 12 D&D classes
  - `CharacterRaces` - All 9 PHB races  
  - Eliminates magic strings throughout codebase
- **✅ Refactored**: All SRD code uses constants
  - `CharacterClasses.WIZARD` instead of `'Wizard'`
  - `CharacterRaces.ELF` instead of `'Elf'`

#### ✅ GUI Enhancements
- **✅ Modified**: `web/app_gradio.py` character creation display
  - Shows racial bonuses breakdown: "STR: 10 + 2 = 12 (+1)"
  - Shows hit die and HP calculation
  - Shows class features and proficiencies
  - Shows spell slots for all 9 spell levels (when applicable)
  - "✨ Enhanced with D&D 5e SRD data" badge

#### ✅ Comprehensive Testing
- **✅ Created**: `tests/test_rag_character_enhancer.py` - 16 unit tests
- **✅ Created**: `tests/test_srd_character_creation_integration.py` - 16 integration tests
- **✅ Created**: `tests/test_complete_character_creation_e2e.py` - 2 E2E tests
- **✅ Created**: `tests/test_all_classes_races_creation.py` - 60 comprehensive tests
  - All 12 classes at levels 1, 5, 10
  - All 9 races with Wizard and Fighter
  - Classic combinations (Elf Wizard, Half-Orc Barbarian, Human Cleric)
  - Edge cases (level 20, low CON, non-casters)
  - Validates: HP scaling, spell slots 1-20, proficiencies, racial bonuses
- **Total**: 94 tests passing

#### ✅ Bug Fixes
- **✅ HP Calculation**: Fixed to account for all levels, not just level 1
  - Formula: Level 1 (hit_die + CON) + (level-1) × (avg_roll + CON)
  - Level 10 Wizard now gets 22 HP instead of 4
- **✅ Spell Slots**: Added complete tables for levels 1-20 (was only 1-5)
- **✅ Proficiency Parsing**: Fixed regex to stop at next field (was capturing paragraphs)
- **✅ Page Indexing**: Corrected PDF page numbers (physical page - 1 for 0-indexed array)
- **✅ Spellcasting Detection**: Fixed `/spells` button showing "not a spellcaster" for Wizards
  - Now sets `CharacterState.spellcasting_class` when loading characters
  - Works in both solo and party mode

#### ✅ Documentation & Dependencies
- **✅ Updated**: `docs/README.md` with RAG Character Creation section
- **✅ Updated**: `requirements.txt` - Added `PyPDF2>=3.0.0`
- **✅ Updated**: `pytest.ini` - Tests run to completion instead of stopping on first failure

#### Impact Summary
- ✅ Accurate character creation using official D&D 5e SRD rules
- ✅ Reduces manual errors and LLM hallucinations  
- ✅ Single source of truth for class features
- ✅ No magic strings - all constants-based
- ✅ GUI shows all racial/class bonuses
- ✅ Easy to update if new SRD versions released
- ✅ Fully automated like other ChromaDB systems
- ✅ Comprehensive test coverage (94 tests)

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


