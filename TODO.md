# TODO - D&D RAG System Feature Roadmap

> **Note**: See DONE.md for completed features that are already implemented and working.

---

## 🔥 HIGH PRIORITY - QUICK WINS (Immediate Impact)

### Fix NPC Cleanup Bug ⚡ (5 min)
**CRITICAL BUG** - Dead enemies remain targetable after combat
- **File**: `combat_manager.py:551-574`
- **Problem**: `end_combat()` clears `npc_monsters` but not `npcs_present` list
- **Impact**: Players can target/interact with corpses, breaks immersion
- **Fix**: Remove dead NPCs from `session.npcs_present` when combat ends

### Add Spell Slot Visualization 🎨 (30 min)
**HIGH VISUAL IMPACT** - Show spell resources at a glance
- **File**: `app_gradio.py:600-649` (format_character_sheet)
- **Add**: Visual spell slot tracker to character sheet sidebar
  ```
  Level 1: ⬛⬛⬜⬜ (2/4)
  Level 2: ⬛⬜⬜ (1/3)
  Level 3: ⬜⬜ (0/2)
  ```
- **Update**: Real-time as spells are cast
- **Impact**: Better resource management for spellcasters, looks professional

### Show Temp HP in Character Sheet ⚡ (10 min)
**MISSING INFO** - Temp HP tracked but invisible
- **File**: `app_gradio.py:620-621`
- **Change**: `HP: 28/30` → `HP: 28/30 (+5 temp HP)`
- **Impact**: Players see their damage shield

### Add Death Save Display ⚡ (15 min)
**CORE MECHANIC VISIBILITY** - Death saves exist but hidden
- **File**: `app_gradio.py:640` (after inventory)
- **Add**: Show when unconscious:
  ```
  ### Death Saves
  - Successes: ✅✅⬜
  - Failures: ❌⬜⬜
  *Make a death saving throw each turn with `/death_save`*
  ```
- **Impact**: Players know their survival status

### Create High-Level Wizard Character 🧙 (20 min)
**SHOWCASE FEATURE** - Demo the spell system with a powerful caster
- **Character**: Level 10+ Wizard with extensive spell list
- **Features**:
  - High HP pool (doesn't die easily)
  - Full spell progression (1st-5th level spells)
  - Signature spells: Fireball, Lightning Bolt, Shield, Counterspell
  - Good stats (INT 18+, CON 14+)
- **Purpose**: Show off RAG spell lookup and slot management
- **Save**: As `characters/archmage.json` for quick loading

---

## 🚨 HIGH PRIORITY - Core Mechanics

### Implement Death Saving Throws (2 hours)
**MISSING CORE D&D MECHANIC** - Infrastructure exists but no command
- **Current**: Warning shows `/death_save` but command doesn't exist
- **Has**: `DeathSaves` class in `game_state.py` already implemented
- **Need**:
  1. Add `/death_save` command handler in `gm_dialogue_unified.py`
  2. Roll d20: 10+ = success, <10 = failure
  3. Track 0-3 successes/failures
  4. Auto-death at 3 failures
  5. Auto-stabilize at 3 successes
  6. Critical hit (nat 20) = regain 1 HP
  7. Critical fail (nat 1) = 2 failures
- **Impact**: Core D&D rules enforcement

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

### Quick Action Buttons (20 min)
**FASTER ACTIONS** - New players discover commands easier
- **File**: `app_gradio.py:1673` (after msg_input)
- **Add**: Button row below chat input:
  - `⚔️ Attack` → fills "I attack "
  - `✨ Cast Spell` → runs "/spells"
  - `🎒 Use Item` → fills "I use "
  - `❓ Help` → runs "/help"
- **Impact**: UI feels more polished, better UX

### Implement `/pickup` Command (30 min)
**COMPLETE LOOT SYSTEM** - Infrastructure exists, just needs command
- **File**: `gm_dialogue_unified.py` (add command handler)
- **Has**: `location.available_items` and `location.moved_items` already tracked
- **Add**:
  ```python
  elif lower_input.startswith('/pickup '):
      item_name = player_input[8:].strip()
      current_loc = self.session.get_current_location_obj()
      if current_loc and current_loc.has_item(item_name):
          current_loc.remove_item(item_name, moved_to="inventory")
          self.session.character_state.add_item(item_name, 1)
          return f"✅ Picked up {item_name}"
  ```
- **Impact**: Makes exploration rewarding, completes item persistence

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

### Delete Duplicate GameSession Class (30 min)
**CRITICAL CLEANUP** - Two conflicting classes exist
- **Files**:
  - Old: `gm_dialogue.py:30-44` (4 fields, simple)
  - New: `game_state.py:1386-1713` (20+ fields, comprehensive)
- **Problem**: Wrong import causes subtle bugs
- **Fix**: Delete old class, update all imports to use `game_state.GameSession`

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

### Deduplicate Character Sheet Formatting (30 min)
**CODE DUPLICATION** - 90% identical functions
- **Files**: `app_gradio.py`
  - `format_character_sheet()` (lines 600-649)
  - `format_character_sheet_for_char()` (lines 1527-1569)
- **Fix**: Extract common logic to `_format_sheet_core()`
- **Impact**: Single point for bug fixes and improvements

### Extract Magic Strings to Constants (2 hours)
**MAINTAINABILITY** - Commands and keywords hardcoded everywhere
- **Current**:
  ```python
  if cmd == '/help':  # Magic string
  if 'goblin' in lower_input:  # Magic string
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


