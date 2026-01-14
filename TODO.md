# TODO - D&D RAG System Feature Roadmap

> **Note**: See DONE.md for completed features that are already implemented and working.

---

## 🔥 HIGH PRIORITY

### Improve RAG Data for Equipment, Abilities & Class Features
**STATUS: ✅ COMPLETED (2026-01-14)**

#### Implementation Summary
- ✅ **Magic Items**: 30+ items added to `dnd_rag_system/data/magic_items.py`
- ✅ **Class Features**: 6 classes, 60+ features in `dnd_rag_system/data/class_features.py`
- ✅ **Equipment System**: Full integration with `/equip`, `/unequip`, `/equipment` commands
- ✅ **Tests**: 70+ unit tests + integration tests (all passing)
- ✅ **E2E Tests**: Created browser-based tests for live game verification
- **See**: `docs/EQUIPMENT_SYSTEM.md` for full documentation

#### Previous State Analysis
- **Equipment Collection**: 58 docs ⚠️ - Only basic weapons/armor, NO magic items
- **Classes Collection**: 11 docs ⚠️ - Only class overviews, NO structured class features
- **Spells Collection**: 586 docs ✅ - Good coverage
- **Monsters Collection**: 332 docs ✅ - Good coverage + structured monster_stats.py

#### What Was Missing (NOW FIXED)
1. **Magic Items & Equipment**:
   - Rings (Ring of Protection, Ring of Invisibility, etc.)
   - Cloaks (Cloak of Elvenkind, Cloak of Protection)
   - Boots (Boots of Speed, Boots of Elvenkind)
   - Wondrous items (Bag of Holding, Rope of Climbing, etc.)
   - Magic weapons (+1, +2, Flametongue, Vorpal Sword)
   - Magic armor (+1, Armor of Resistance, Plate of the Ethereal)
   - Advanced potions (Potion of Invisibility, Potion of Flying, etc.)

2. **Class Features & Abilities**:
   - Rogue: Sneak Attack, Cunning Action, Uncanny Dodge, Evasion, Reliable Talent
   - Fighter: Action Surge, Second Wind, Extra Attack (1-4), Indomitable
   - Barbarian: Rage, Reckless Attack, Danger Sense, Fast Movement
   - Monk: Ki points, Flurry of Blows, Stunning Strike, Deflect Missiles, Slow Fall
   - Paladin: Divine Smite, Lay on Hands, Divine Sense, Channel Divinity
   - Ranger: Hunter's Mark, Favored Enemy, Natural Explorer, Primeval Awareness
   - All classes: Class features by level (1-20)

3. **Feats & General Abilities**:
   - Feats (Great Weapon Master, Sharpshooter, Lucky, Alert, etc.)
   - Conditions (Grappled, Restrained, Paralyzed, Stunned mechanics)
   - Status effects with mechanical impact

#### Implementation Plan (Follow monster_stats.py Pattern)

**Phase 1: Create Structured Data Files** (3-4 hours)
1. Create `dnd_rag_system/data/magic_items.py`:
   - Rings (15+ common magic rings)
   - Wondrous items (20+ items: Bag of Holding, Immovable Rod, etc.)
   - Magic weapons (10+ weapons: +1/+2/+3, Flametongue, Vorpal, etc.)
   - Magic armor (8+ armors: +1/+2/+3, Armor of Resistance, etc.)
   - Potions (12+ potions beyond healing)
   - Structure: name, rarity, attunement, effects, description

2. Create `dnd_rag_system/data/class_features.py`:
   - All 12 classes with features by level
   - Each feature: name, level, class, description, mechanics, usage
   - Example structure:
     ```python
     "Sneak Attack": {
         "class": "Rogue",
         "level": 1,
         "damage_by_level": {1: "1d6", 3: "2d6", 5: "3d6", ...},
         "trigger": "advantage or ally within 5 feet",
         "description": "...",
         "mechanics": "Once per turn, deal extra damage..."
     }
     ```

3. Create `dnd_rag_system/data/feats.py`:
   - All PHB feats (~40 feats)
   - Structure: name, prerequisites, benefits, description

**Phase 2: Create Management Systems** (2-3 hours)
1. Create `dnd_rag_system/systems/magic_item_manager.py`:
   - `lookup_magic_item(name)` - Get item details
   - `get_items_by_rarity(rarity)` - Filter by rarity
   - `check_attunement(item)` - Check if attunement required
   - Integration with inventory system

2. Create `dnd_rag_system/systems/class_feature_manager.py`:
   - `get_class_features(class_name, level)` - Get features for class/level
   - `lookup_feature_mechanics(feature_name)` - Get detailed mechanics
   - `calculate_feature_effect(feature, level)` - Scale by level (e.g., Sneak Attack damage)

3. Create `dnd_rag_system/systems/feat_manager.py`:
   - `lookup_feat(name)` - Get feat details
   - `check_prerequisites(feat, character)` - Validate prerequisites

**Phase 3: Integrate with Game Systems** (2-3 hours)
1. **Equipment System Integration**:
   - Add magic item effects to `CharacterState`
   - Auto-apply item bonuses (Ring of Protection → +1 AC)
   - Handle attunement slots (max 3 attuned items)
   - Add `/equip` and `/unequip` commands for magic items

2. **Class Feature Integration**:
   - Auto-apply class features on level-up
   - Add commands: `/sneak_attack`, `/action_surge`, `/rage`
   - Integrate with action validator (validate feature usage)
   - Track usage (Action Surge: 1/rest, Ki points, Rage: X/day)

3. **Reality Check Enhancement**:
   - Validate class feature usage in action parser
   - Example: "I use Sneak Attack" → Check if Rogue, check advantage/ally
   - Example: "I use Action Surge" → Check if Fighter, check uses remaining

**Phase 4: Comprehensive Testing** (2-3 hours)
1. Create `tests/test_magic_item_manager.py`:
   - Test magic item lookup
   - Test rarity filtering
   - Test attunement system
   - Test item effect application (25+ tests)

2. Create `tests/test_class_feature_manager.py`:
   - Test class feature lookup by level
   - Test feature scaling (Sneak Attack damage)
   - Test feature prerequisites
   - Test all 12 classes (30+ tests)

3. Create `tests/test_feat_manager.py`:
   - Test feat lookup
   - Test prerequisite checking
   - Test feat effects (10+ tests)

4. Integration tests:
   - Test equipping magic items and stat changes
   - Test using class features in combat
   - Test level-up feature grants

#### Benefits
- **Rogue players** can use Sneak Attack, Cunning Action, Uncanny Dodge
- **Fighters** can use Action Surge and Second Wind
- **All classes** get their signature abilities with proper mechanics
- **Magic items** work with proper effects (Ring of Protection → +1 AC/saves)
- **Equipment system** becomes fully functional with RAG support
- **Reality check** can validate class-specific actions
- **40-60% more RAG coverage** for character abilities and items

#### Estimated Total Effort
- **Phase 1**: 3-4 hours (data entry)
- **Phase 2**: 2-3 hours (management systems)
- **Phase 3**: 2-3 hours (integration)
- **Phase 4**: 2-3 hours (testing)
- **Total**: 10-13 hours

#### What Was Actually Implemented (Quick Win Approach)
✅ Completed in ~4 hours:
1. **Magic Items**: 30+ items (rings, cloaks, weapons, armor, potions)
2. **Class Features**: 6 classes (Fighter, Wizard, Rogue, Cleric, Barbarian, Paladin)
3. **Equipment Integration**: Full system with `/equip`, `/unequip`, `/equipment` commands
4. **Tests**: 70+ unit tests + integration test + 2 E2E tests
5. **Documentation**: `docs/EQUIPMENT_SYSTEM.md`

**Files Created**:
- `dnd_rag_system/data/magic_items.py` (30+ items)
- `dnd_rag_system/data/class_features.py` (6 classes, 60+ features)
- `dnd_rag_system/systems/magic_item_manager.py`
- `dnd_rag_system/systems/class_feature_manager.py`
- `dnd_rag_system/systems/character_equipment.py`
- `tests/test_magic_item_manager.py` (15 tests)
- `tests/test_class_feature_manager.py` (20 tests)
- `tests/test_character_equipment.py` (35 tests)
- `ingest_game_content.py` (RAG ingestion)
- `e2e_tests/test_equipment_system_e2e.py`
- `e2e_tests/test_magic_item_rag_e2e.py`

**Files Modified**:
- `web/app_gradio.py` (added equipment commands)

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


