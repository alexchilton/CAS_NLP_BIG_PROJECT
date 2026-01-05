# TODO - D&D RAG System Feature Roadmap

> **Note**: See DONE.md for completed features that are already implemented and working.

---

## 🔥 HIGH PRIORITY

### Character-Specific Action Parsing for Party Mode
- **Problem**: When player says "Elara casts Fire Bolt", system needs to know Elara is acting
- **Solution**: Parse character names from player input
  - Extract character name from prefix: "Thorin attacks the goblin"
  - Use character name to set `gm.session.character_state` to correct party member
  - Validate action against THAT character's stats/inventory/spells
- **Examples**:
  - "Thorin attacks the dragon with his longsword" → Set active character to Thorin, validate longsword
  - "Elara casts Fire Bolt at the dragon" → Set active character to Elara, validate Fire Bolt spell
  - "Gimli drinks a healing potion" → Set active character to Gimli, validate potion in inventory
- **Fallback**: If no character name detected, use current turn's character from initiative order
- **Implementation**: Add character name parser to `action_validator.py`

### Party Member Interactions
- **Character-to-Character Actions**:
  - Healing: "Elara casts Cure Wounds on Thorin"
  - Buffs: "Gandalf casts Bless on the entire party"
  - Item sharing: "Thorin hands his rope to Legolas"
  - Coordinated attacks: "Aragorn and Gimli attack together"
- **Validation**:
  - Check if target party member exists
  - Check if healer has the spell/ability
  - Update target's HP/status
- **Social Interactions**:
  - Party member conversations
  - Strategy discussions
  - Roleplaying between characters
- **Technical**: Extend `action_validator.py` to handle party-member-as-target

### Integrate Shop Reality Check
- **Problem**: Currently players can use `/buy` and `/sell` anywhere, even in a dragon's lair!
- **Solution**: Validate shop location before allowing transactions
- **Implementation**:
  - Check if current location is a shop (`location.has_shop = True`)
  - OR check if a merchant/shopkeeper NPC is present in `npcs_present`
  - Reject transactions with message: "There's no shop here! You're in a dragon's lair, not a marketplace!"
- **Examples**:
  - ✅ Valid: Player in "Market Square" (has_shop=True) → `/buy` works
  - ✅ Valid: "Greta the Merchant" in `npcs_present` → `/buy` works
  - ❌ Invalid: Player in "Dragon's Lair" → `/buy` rejected
  - ❌ Invalid: No merchant NPC present → `/buy` rejected
- **Integration Point**: Add shop location validation in `ShopSystem.attempt_purchase()` and `attempt_sale()`

### Update Inventory Display After Shop Transactions
- **Problem**: After `/buy` or `/sell` commands, inventory shown in GUI is not updated
- **Solution**: Refresh the inventory display component after successful purchase/sale
- **Implementation**:
  - Update Gradio inventory component after `ShopSystem.attempt_purchase()` succeeds
  - Update Gradio inventory component after `ShopSystem.attempt_sale()` succeeds
  - Ensure gold and item quantities reflect current state immediately
- **User Experience**: Players should see inventory change in real-time without manual refresh

---

## 📚 MEDIUM PRIORITY

### Location-Based Item Spawning & Pickup System
- **Current State**: Infrastructure exists but not integrated
  - `location.moved_items` dict exists ✅
  - Tracks which items were taken ✅
  - Persists across visits ✅
  - BUT: No automatic item spawning or pickup
- **Need to Implement**:
  1. **Item Spawning**: Add `items_present: Dict[str, int]` to Location
     - Generate items when location is created
     - Based on location type (caves have treasure, forests have herbs)
  2. **Pickup Command**: `/pickup <item>` or natural language
     - Remove from `location.items_present`
     - Add to `character.inventory`
     - Track in `location.moved_items`
  3. **GM Integration**: GM should mention items in descriptions
     - "You see a glinting sword" (first visit)
     - Skip items in `moved_items` (return visit)
- **Testing**: `test_location_items.py` already has 8 tests for the infrastructure

### World State & Exploration System
**STATUS: PARTIALLY IMPLEMENTED** 🚧

#### Infrastructure Completed ✅
- World state manager with location tracking
- Lazy location generation system
- Location visit tracking and state persistence
- Item placement and removal system
- NPC and creature persistence per location
- Random encounter system with Monster RAG integration
- Comprehensive selenium tests created
- Documentation in `docs/world_state_guide.md`

#### Broken/Not Working ❌
- **`/map` command**: GM intercepts and hallucinates instead of showing locations
  - Symptom: Returns goblin narrative instead of location list
  - **FIX NEEDED**: Make `/map` bypass GM and query world state directly
- **`/travel` command**: Not tested yet, may have similar issues
- **`/explore` command**: Not tested with lazy generation
- **GM narrative integration**: GM doesn't mention visited locations correctly

#### Not Yet Implemented
- Save/load world state to disk
- Automatic item spawning in new locations
- Integration with combat system (dead enemies persistence)

### Save/Load System for World State
- **Current State**: World persists in-memory during session only
- **Need**: Save world state to disk, load on startup
- **Implementation**:
  - Add `Location.to_dict()` / `from_dict()` (partially exists)
  - Add `GameSession.save_to_json()` / `load_from_json()`
  - Save: `session.world_map`, all locations, character state
  - Load on startup or via `/load_game` command
- **Benefit**: Persistent campaigns across app restarts

### Spell System Improvements
- Add spell slots tracking by level (1st-9th level slots)
- Implement prepared spells vs known spells distinction
- Add spell casting mechanics with slot consumption
- Proper D&D 5e spell levels and rules
- Integration with existing `SpellSlots` class in `game_state.py`

---

## 📚 LOWER PRIORITY / ENHANCEMENTS

### RAG Data Quality Improvements

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

### Upgrade Reality Check with LLM-based NLP Intent Classification
- **Problem**: Current keyword-based approach is brittle
  - Works: "fire my bow", "shoot my bow", "attack with sword"
  - Fails: "loose an arrow", "nock and release my bowstring", "let fly with my longbow"
  - Keyword lists require constant expansion for synonyms and variations
- **Proposed Solution**: Use lightweight local LLM for natural language understanding
  - Small LLM (3-4B params) classifies intent and extracts entities
  - Models: Gemma-3-4B, Qwen2.5-3B-Instruct, Llama-3.2-3B, or Phi-3-mini
  - Fast inference (50-200ms on CPU with quantization)
  - Python validates LLM's extracted entities against game state (still deterministic!)
- **Benefits**: Natural language understanding, no keyword maintenance, still 100% reliable
- **Estimated Effort**: 2-3 hours (model integration, prompt engineering, testing)

---

## ✅ COMPLETED (See DONE.md for details)

- ✅ **Level Up System with Auto-Leveling (2026-01-05)**
  - Implemented automatic level-up on XP threshold
  - Added `/level_up` command for manual leveling
  - HP increase with hit die rolls + CON modifier (minimum 1)
  - Proficiency bonus progression at levels 5, 9, 13, 17
  - Spell slot upgrades via RAG lookup
  - Healing on level-up (current HP increases by HP gain)
  - Comprehensive test suite (10 tests in `test_game_state.py`)
  - Auto-leveling integration in combat XP awards
  - Files: `game_state.py:661-750`, `gm_dialogue_unified.py:326-565`, `tests/test_game_state.py:396-492`

- ✅ **Spell Casting, Rest Mechanics & XP System (2026-01-05)**
  - `/cast <spell>` command with spell slot consumption
  - Cantrip detection (level 0 = unlimited use)
  - Spell upcasting to higher-level slots
  - Healing spell mechanics with dice rolling
  - Target type detection (self/ally/enemy/area)
  - `/rest` (short rest) with hit dice spending
  - `/long_rest` for full HP/slot/hit dice restoration
  - Automatic XP awards when defeating enemies
  - Monster CR lookup via RAG
  - XP-to-CR conversion using DMG p.274 table
  - Victory rewards display with enemy list
  - Test suites: `test_rest_mechanics.py` (11 tests), `test_spell_manager.py` (31 tests)
  - Files: `spell_manager.py`, `gm_dialogue_unified.py`, `combat_manager.py`

- ✅ **NPC Combat AI & Auto-Population System (2026-01-03)**
  - Implemented NPC combat AI with automatic monster attacks during their turns
  - NPCs now automatically attack when their initiative comes up
  - Auto-populate NPCs when loading combat locations (e.g., Goblin Cave → 2 Goblins appear)
  - Fixed bidirectional location matching for proper NPC spawning
  - Updated welcome message to show NPCs present: "⚠️ **You see:** Goblin, Goblin!"
  - Fixed `/context` command error (GameSession.scene_description)
  - Created comprehensive E2E test suite:
    - `test_goblin_cave_combat.py` - Fighter combat with goblins
    - `test_wizard_spell_combat.py` - Wizard spell combat with Skeleton
    - `test_combat_scenarios.py` - Full test suite with 4 scenarios:
      - Wizard vs Skeleton (Ancient Ruins) - RAG integration
      - Fighter vs Ogre (Rocky Mountain Pass) - Melee combat
      - Wizard vs Wolf Pack (Dark Forest) - Multi-enemy
      - Fighter vs Young Dragon (Dragon's Lair) - Boss fight
  - All tests fight until death or victory
  - **Impact**: Combat encounters feel alive with NPCs taking actions
  - Files: `combat_manager.py`, `gm_dialogue_unified.py`, `app_gradio.py`, E2E tests
- ✅ **Monster Stats Integration with Combat System (2026-01-03)**
  - Created monster stats database with 16 D&D 5e creatures (CR 0-17)
  - Built MonsterStatSystem for creating monster instances with real stats
  - Integrated with CombatManager to auto-load stats when combat starts
  - NPC HP tracking in initiative tracker
  - Real AC, attack bonuses, and damage rolls from stat blocks
  - Comprehensive test suite with Goblin, Wolf, Skeleton, and Dragon combat
  - **Impact**: Moves RAG usage from ~10% to ~40% for combat encounters
  - Files: `dnd_rag_system/data/monster_stats.py`, `dnd_rag_system/systems/monster_stat_system.py`
- ✅ NPC Auto-Extraction from GM Responses (2025-12-27)
  - When GM mentions NPCs in narrative, they're automatically added to `npcs_present`
  - Uses existing Qwen 2.5 3B mechanics extractor to parse `npcs_introduced`
  - Fixes bug where GM introduces NPC but it's not tracked in game state
  - Verified with unit tests and E2E selenium tests with debug logging
- ✅ Spell Target Hallucination Fix (2025-12-26)
- ✅ Action Validator False Positives Fix (2025-12-26)
- ✅ Party Mode UI Bug Fix (2025-12-26)
- ✅ Narrative to Mechanics Translation System (2025-12-26)
- ✅ Combat System (Turn-based)
- ✅ Reality Check / Action Validation
- ✅ Shop System
- ✅ Party Mode
- ✅ Random Encounter System with Monster RAG Integration (2025-12-26)
- ✅ Selenium Test Character Loading Fixed (2025-12-26)

