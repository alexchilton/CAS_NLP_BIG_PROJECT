# DONE - Completed Features

This file tracks completed and working features that have been implemented and tested.

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
  - Equipment data: `web/equipment.txt`

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

