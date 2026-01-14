# TODO - D&D RAG System Feature Roadmap

> **Note**: See DONE.md for completed features that are already implemented and working.

---

## 🔥 HIGH PRIORITY

### ✅ Improve RAG Data for Equipment, Abilities & Class Features - COMPLETED (2026-01-14)

**See `docs/DONE.md` for full implementation details.**

**Summary**: Fully implemented equipment system with:
- ✅ 30+ magic items (rings, cloaks, weapons, armor, potions)
- ✅ 6 classes with 60+ class features
- ✅ `/equip`, `/unequip`, `/equipment` commands in game
- ✅ 70+ unit tests + integration test + E2E tests
- ✅ Full documentation in `docs/EQUIPMENT_SYSTEM.md`

**Future Enhancements** (optional):
- Add remaining 6 classes (Monk, Ranger, Bard, Sorcerer, Warlock, Druid)
- Add feats system (~40 PHB feats)
- Add conditions mechanics (Grappled, Restrained, Paralyzed, Stunned)

---

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


