# TODO - D&D RAG System Feature Roadmap

> **Note**: See DONE.md for completed features that are already implemented and working.

---

## 🔥 HIGH PRIORITY

### Improve RAG Data for Equipment, Abilities & Class Features
**STATUS: PLANNED - NOT STARTED** 📋

#### Current State Analysis
- **Equipment Collection**: 58 docs ⚠️ - Only basic weapons/armor, NO magic items
- **Classes Collection**: 11 docs ⚠️ - Only class overviews, NO structured class features
- **Spells Collection**: 586 docs ✅ - Good coverage
- **Monsters Collection**: 332 docs ✅ - Good coverage + structured monster_stats.py

#### Critical Missing Data
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

#### Alternative: Quick Win Approach (3-4 hours)
If time is limited, start with essentials:
1. Magic items data file (top 20 most common items)
2. Class features for top 4 classes (Rogue, Fighter, Wizard, Cleric)
3. Basic integration with existing systems
4. Core tests (15-20 tests)

---

### ✅ Character-Specific Action Parsing - ALREADY WORKING (Verified 2026-01-13)
- **First-Person Pronouns** ("I cast Fire Bolt"):
  - When you say "**I cast Fire Bolt**" → No character name extracted → Uses current `character_state` ✅
  - Works automatically in both single-character and party mode
  - System defaults to current turn's character from initiative order

- **Third-Person** ("Elara casts Fire Bolt"):
  - When you say "**Elara casts Fire Bolt**" → Extracts "Elara" → Switches to Elara's state ✅
  - Character name parser already implemented in `action_validator.py:extract_acting_character()`
  - Integrated in `gm_dialogue_unified.py:900-918`

- **Status**: ✅ FULLY WORKING - No action needed

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

### ✅ World State & Exploration System - FULLY WORKING (Verified 2026-01-13)

**Infrastructure Completed**:
- World state manager with location tracking
- Lazy location generation system
- Location visit tracking and state persistence
- Item placement and removal system
- NPC and creature persistence per location
- Random encounter system with Monster RAG integration
- Comprehensive selenium tests created
- Documentation in `docs/world_state_guide.md`

**Commands Working**:
- ✅ **`/map` command**: Shows world map with discovered locations (gm_dialogue_unified.py:742-779)
- ✅ **`/travel` command**: Case-insensitive travel between locations (tested in test_case_sensitivity_fixes.py)
- ✅ **`/explore` command**: Lazy generation creates new locations (tested in test_lazy_generation.py)
- ✅ **`/locations` command**: Lists all discovered locations

**Status**: ✅ FULLY IMPLEMENTED - See DONE.md for complete documentation

**Still TODO**:
- Save/load world state to disk
- Automatic item spawning in new locations (infrastructure exists, not auto-spawning yet)

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

- ✅ **Party Member Healing & Targeting (2026-01-05)** [PARTIAL]
  - Single-target healing spells work (`/cast Cure Wounds on Thorin`)
  - Target validation checks if party member exists
  - Self-healing fallback when no target specified
  - Spell slot consumption properly tracked
  - 5 passing tests in `tests/test_party_member_interactions.py`
  - **Still needed**: Party-wide buffs, item sharing, coordinated attacks
  - Files: `spell_manager.py`, `gm_dialogue_unified.py:475-510`, `tests/test_party_member_interactions.py`

- ✅ **DM Guide RAG Ingestion with Quality Tests (2026-01-05)**
  - Added complete DM Guide (286 pages) to RAG system
  - 95 chunks with intelligent page grouping (3 pages per chunk)
  - Auto-detection of magic item content (53/95 chunks tagged)
  - Comprehensive test suite: 26 tests validating retrieval quality
  - Total RAG coverage: 1,098 documents (was 1,003)
  - Magic items, treasure tables, and rules now searchable
  - Query response times < 2s
  - Files: `ingest_dm_guide.py`, `dm_guide.pdf`, `tests/test_dm_guide_rag_quality.py`

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

