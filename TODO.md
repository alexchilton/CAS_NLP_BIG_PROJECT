# TODO - D&D RAG System Feature Roadmap

> **Note**: See DONE.md for completed features that are already implemented and working.

---

## 🔥 HIGH PRIORITY

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

## 📚 MEDIUM PRIORITY

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


