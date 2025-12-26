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

---

## ✅ COMPLETED (See DONE.md for details)

- ✅ World State & Exploration System (2025-12-26)
- ✅ Lazy Location Generation (2025-12-26)
- ✅ Spell Target Hallucination Fix (2025-12-26)
- ✅ Action Validator False Positives Fix (2025-12-26)
- ✅ Party Mode UI Bug Fix (2025-12-26)
- ✅ Narrative to Mechanics Translation System (2025-12-26)
- ✅ Combat System (Turn-based)
- ✅ Reality Check / Action Validation
- ✅ Shop System
- ✅ Party Mode

---