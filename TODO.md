# TODO - D&D RAG System Feature Roadmap

## Party-Based Gameplay

- [x] **Implement party-based chat mode** ✅ IMPLEMENTED
  - When party is defined and party mode is active, send full party info to GM chat context
  - Enabled true party-based D&D gameplay where GM manages adventures for the whole group
  - GM receives complete party information including all character stats, equipment, and abilities

- [x] **Add party/character mode toggle in Play Game tab** ✅ IMPLEMENTED
  - Added radio button toggle: "🎭 Single Character" vs "🎲 Party Mode"
  - UI dynamically shows/hides appropriate controls based on mode
  - **Character Mode**: Load single character, GM sees only that character's info
  - **Party Mode**: Load entire party, GM sees all party members' stats and equipment
  - Mode switching updates displayed character sheet and load buttons

- [x] **Update GM context to handle party-based gameplay** ✅ IMPLEMENTED
  - Format party context with all character stats, equipment, spells for each party member
  - GM prompts include full party roster with individual stats
  - /stats command shows party sheet in party mode
  - Party sheet displays all members with HP, AC, ability scores, and equipment

- [x] **Fix Party Mode UI Bug** ✅ FIXED
  - **Issue**: When party mode checkbox is enabled, chat textarea becomes non-interactable
  - **Impact**: Cannot send messages in party mode, makes feature unusable
  - **Root Cause**: `load_party_mode()` was returning `""` for msg_input, breaking interactivity
  - **Solution**: Changed to return `gr.update(interactive=True, value="")` to explicitly keep textarea interactive
  - **Files**: `web/app_gradio.py` lines 204-242

- [ ] **Implement Turn-Based Combat System for Party Mode** 🏗️ IN PROGRESS
  - **Initiative System**:
    - Roll initiative for all party members + enemies at combat start
    - Sort by initiative order (highest to lowest)
    - Track current turn in combat round
    - Display initiative order in UI
  - **Turn Management**:
    - Active character indicator: "🎯 Thorin's Turn"
    - Turn advance button or automatic progression
    - End round detection (all characters acted)
    - New round notification
  - **Action Resolution**:
    - Player specifies which character is acting: "Thorin attacks" or prefix with character name
    - Reality Check validates action against THAT character's inventory/spells/abilities
    - GM narrates the outcome for that specific character
    - Auto-advance to next character's turn after action resolved
  - **Group Dynamics**:
    - Characters can interact with each other (healing, buffs, coordinated actions)
    - NPC targeting: any party member can be targeted by enemies
    - Shared combat state: all party members see same enemies
  - **Technical Implementation**:
    - Integration with existing `CombatState` in `game_state.py`
    - `CombatState.initiative_order` already exists, needs full utilization
    - Add `current_turn_index` to track whose turn it is
    - Add `rounds_elapsed` counter
    - UI component to display initiative tracker
  - **UI Components Needed**:
    - Initiative tracker panel (shows all combatants in order)
    - Current turn indicator (highlight active character)
    - Turn advance button
    - Round counter display

- [x] **Implement Character-Specific Action Parsing for Party Mode** ✅ IMPLEMENTED
  - **Problem**: When player says "Elara casts Fire Bolt", system needs to know Elara is acting
  - **Solution**: Parse character names from player input and validate against correct character
    - Extract character name from prefix: "Thorin attacks the goblin" → "Thorin"
    - Temporarily set `gm.session.character_state` to that party member for validation
    - Validate action against THAT character's stats/inventory/spells
    - Strip character name from input before action analysis
  - **Implementation**:
    - Added `extract_acting_character()` and `set_party_characters()` to `action_validator.py`
    - Integrated into GM's `generate_response()` flow in `gm_dialogue_unified.py`
    - Fixed word boundary issues in target/spell/item/weapon extraction methods
    - Reordered intent detection to check items before conversation
  - **Testing**: Comprehensive E2E test suite (`e2e_tests/test_party_character_parsing.py`) - ALL 8 TESTS PASSING
    - ✅ Thorin attacks with longsword (valid)
    - ✅ Elara casts Fire Bolt (valid)
    - ✅ Gimli drinks healing potion (valid)
    - ✅ Thorin tries to cast Fireball (rejected - Fighter can't cast)
    - ✅ Elara shoots bow (rejected - no bow in inventory)
    - ✅ Thorin uses staff (rejected - staff belongs to Elara)
    - ✅ Elara casts Shield (valid)
    - ✅ Gimli casts Cure Wounds (valid)

- [ ] **Implement Party Member Interactions** 🎯 ENHANCEMENT
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

## Spell System Improvements

- [ ] **Improve spell system**
  - Add spell slots tracking by level (1st-9th level slots)
  - Implement prepared spells vs known spells distinction
  - Add spell casting mechanics with slot consumption
  - Proper D&D 5e spell levels and rules
  - Integration with existing `SpellSlots` class in `game_state.py`

## Inventory & Shopping System

- [x] **Implement GM-driven conversational shop system** ✅ IMPLEMENTED
  - **Philosophy**: Shop interactions happen through natural conversation with GM-controlled NPC shopkeepers
  - **Equipment RAG Database**: Parsed 58 equipment items from equipment.txt into ChromaDB
    - Weapons (swords, axes, bows, etc.) with damage and properties
    - Armor (leather, chainmail, plate, etc.) with AC and weight
    - Adventuring gear (rope, torches, rations, etc.)
    - Magical items (if applicable)
  - **Shop Transaction System**:
    - ✅ Purchase validation (checks gold, updates inventory)
    - ✅ Sell system (half market price, D&D 5e standard)
    - ✅ Natural language parsing ("/buy longsword", "I'll take the rope", etc.)
    - ✅ Gold deduction and inventory management
    - ✅ Fuzzy item matching for flexible user input
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

- [ ] **Integrate Shop Reality Check** 🔴 TODO
  - **Problem**: Currently players can use `/buy` and `/sell` anywhere, even in a dragon's lair!
  - **Solution**: Validate shop location before allowing transactions
  - **Implementation**:
    - Check if current location is a shop (`location_type = "shop"` in GameSession)
    - OR check if a merchant/shopkeeper NPC is present in `npcs_present`
    - Reject transactions with message: "There's no shop here! You're in a dragon's lair, not a marketplace!"
  - **Examples**:
    - ✅ Valid: Player in "The Rusty Blade" shop location → `/buy` works
    - ✅ Valid: "Grum the Shopkeeper" in `npcs_present` → `/buy` works
    - ❌ Invalid: Player in "Dragon's Lair" → `/buy` rejected
    - ❌ Invalid: No merchant NPC present → `/buy` rejected
  - **Integration Point**: Add shop location validation in `ShopSystem.attempt_purchase()` and `attempt_sale()`
  - **Priority**: Medium (prevents immersion-breaking shop abuse)

- [ ] **Optional: Create dedicated shop UI tab** (Low Priority)
  - Current system works entirely through GM chat (preferred!)
  - Could add visual inventory browser as enhancement
  - Not required - chat interaction is more immersive

## RAG-Based Character Creation

- [x] **Load racial bonuses from RAG** ✅ IMPLEMENTED (with fallback data)
  - Query ChromaDB for race information during character creation
  - **Issue Found**: Current ChromaDB racial data has incorrect ability scores (OCR errors from PDF parsing)
  - **Solution**: Implemented with fallback to hardcoded correct D&D 5e racial bonuses
  - Auto-apply ability score increases (e.g., Dwarf +2 CON, Elf +2 DEX)
  - Add racial traits (Darkvision, Fey Ancestry, Dwarven Resilience, etc.)
  - Set speed, size, languages
  - Display racial features in character creation form

- [ ] **Fix racial data in ChromaDB** 🔴 DATA QUALITY ISSUE
  - Current problem: All races showing same ability scores (CHA +1, DEX +1)
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

- [ ] **Improve class features data in RAG** 🔴 REQUIRED BEFORE IMPLEMENTATION
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
  - **Blocking**: Cannot implement auto-apply class features until this data is available

- [ ] **Load class features from RAG** (blocked by above)
  - Query ChromaDB for class information during character creation
  - Set correct hit dice (d6/d8/d10/d12)
  - Apply proficiencies (armor, weapons, tools, saving throws)
  - Add class abilities by level
  - Set spell slots for caster classes

- [ ] **Auto-apply racial and class bonuses during character creation**
  - Integrate RAG lookups into character creation workflow
  - Preview bonuses before finalizing character
  - Update ability scores automatically with racial bonuses
  - Show calculated stats (HP, AC, modifiers) with all bonuses applied
  - Save complete character with proper D&D 5e features

## Context Grounding / Reality Check

- [x] **Implement "Reality Check" for player actions before GM LLM generation** ✅ IMPLEMENTED
  - **Goal**: Prevent the GM LLM from hallucinating entities or actions inconsistent with the current game state.
  - **Implementation**: Created hybrid "tagging" system in `dnd_rag_system/systems/action_validator.py`
    - **Intent Analysis**: Parses player input to identify action type (combat, spell, conversation, item use, exploration)
    - **State Validation**: Validates actions against `GameSession` state
      - Combat: Verifies targets exist in `npcs_present` or `combat.initiative_order`
      - Weapon validation: Checks if weapon used in combat is in inventory
      - Spells: Checks if spell is known by character (with fuzzy matching)
      - Items: Validates items exist in character inventory
      - Conversations: Allows NPC introduction for contextually appropriate NPCs
    - **Context-Aware Prompting**: Enhances GM prompts with validation guidance
      - Valid actions: Proceed normally
      - Invalid actions: Returns deterministic personality-driven responses (bypasses LLM)
      - NPC introductions: Allows GM to introduce NPCs that make contextual sense
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

- [ ] **Upgrade Reality Check to use LLM-based NLP Intent Classification** 🎯 ENHANCEMENT
  - **Problem**: Current keyword-based approach is brittle
    - Works: "fire my bow", "shoot my bow", "attack with sword"
    - Fails: "loose an arrow", "nock and release my bowstring", "let fly with my longbow", "discharge my crossbow"
    - Keyword lists require constant expansion for synonyms and variations
  - **Proposed Solution**: Use lightweight local LLM for natural language understanding
    - **Step 1**: Small LLM (3-4B params) classifies intent and extracts entities
      - Models: **Gemma-3-4B** (recommended!), Qwen2.5-3B-Instruct, Llama-3.2-3B, or Phi-3-mini (3.8B)
      - Fast inference (50-200ms on CPU with quantization)
      - Binary classification: COMBAT/SPELL/ITEM/CONVERSATION/EXPLORATION
      - Extract: action_type, target, weapon/item/spell being used
    - **Step 2**: Python logic validates LLM's extracted entities against game state
      - Check if weapon/item exists in inventory
      - Check if target exists in npcs_present/combat
      - Check if spell is known
      - Still deterministic and reliable!
    - **Step 3**: If valid, big LLM (4B RPG model) generates narrative response
    - **Step 4**: If invalid, deterministic personality-driven rejection (current system)
  - **Benefits**:
    - Natural language understanding - handles all synonyms/variations
    - No keyword list maintenance required
    - Still 100% reliable (Python validates LLM's classifications)
    - Fast (small model for intent, deterministic for rejections)
  - **Architecture**:
    ```python
    # Current: Keyword matching
    if "fire" in input or "shoot" in input:  # Brittle!
        return ActionIntent(COMBAT, weapon="bow")

    # Proposed: LLM intent classification
    intent = small_llm.classify(
        action="loose an arrow from my bow at the orc",
        inventory=["Longsword", "Shield"],
        creatures=["Goblin Scout"]
    )
    # Returns: {type: COMBAT, weapon: "bow", target: "orc"}

    # Python validates (still deterministic!)
    if intent.weapon not in inventory:
        return deterministic_rejection()
    ```
  - **Implementation Priority**: Medium (current system works, but this would make it production-ready)
  - **Estimated Effort**: 2-3 hours (model integration, prompt engineering, testing)

## Narrative to Mechanics Translation (GM Output Processing) 🔴 CRITICAL NEW FEATURE

- [ ] **Convert GM's narrative responses into structured game mechanics updates.**
  - **Goal**: Automatically update `game_state.py` based on the GM's storytelling, ensuring mechanical consistency.
  - **Problem**: GM LLM's free-form text output ("The dragon breathes fire, scorching everyone for 30 damage!") needs to be parsed into actionable game mechanics (damage, status effects, etc.).
  - **Proposed Approaches**:

    ### Approach 1: Structured Output (JSON/Tool Use) - Recommended
    - **Method**: Force the GM LLM to generate a structured data block (e.g., JSON) alongside its narrative text. This data block would contain all mechanical details of the GM's described action.
    - **Workflow**:
      1.  Define a schema for GM output (e.g., `action_type`, `source`, `targets`, `damage_type`, `damage_amount`, `status_effects`, etc.).
      2.  Prompt the GM LLM to output both `narrative` and `game_mechanics` JSON blocks.
      3.  Your Python code parses the `game_mechanics` JSON.
      4.  Execute corresponding `game_state.py` functions (e.g., `character.take_damage(amount, type)`).
      5.  Display the `narrative` to the user.
    - **Pros**: High accuracy and reliability for mechanical updates. AI decides the mechanical intent.
    - **Cons**: Requires an LLM capable of generating structured JSON (most modern large models, and some smaller ones, can do this with function calling/tool use). May require careful prompt engineering to ensure correct schema adherence.
    - **Integration Point**: Modify `gm.generate_response` in `dnd_rag_system/systems/gm_dialogue_unified.py` to include structured output in the GM's prompt.

    ### Approach 2: The "Engine-First" Flow (Inversion of Control) - Robust Alternative
    - **Method**: The Python game engine decides the mechanical actions of NPCs/monsters, performs the calculations, and *then* prompts the GM LLM to narrate the outcome.
    - **Workflow**:
      1.  Python code (or a simple tactical AI) determines NPC/monster action (e.g., "Dragon uses Fire Breath").
      2.  Python code performs all mechanical calculations (rolls, damage, saves, status effects) and updates `game_state.py`.
      3.  Construct a detailed prompt for the GM LLM describing the *mechanically resolved* action (e.g., "The Dragon's Fire Breath hit Thorin for 56 damage and Elara for 28 damage. Describe this.").
      4.  GM LLM generates only the narrative description.
    - **Pros**: 100% rules adherence; game state always accurate. GM is purely a narrator.
    - **Cons**: Requires implementing significant NPC/monster AI logic and decision-making in Python. LLM loses creative freedom over mechanical outcomes.
    - **Integration Point**: Modify `gm.generate_response` or introduce a new "GM Orchestrator" that decides when to let the engine act and when to ask the LLM to narrate.

    ### Approach 3: The "Interpreter" Agent (Post-Processing) - Least Recommended
    - **Method**: The GM LLM generates free-form text, and a *secondary* LLM (or a specialized parsing model) then attempts to extract mechanical updates from that text.
    - **Workflow**:
      1.  GM LLM generates narrative response (e.g., "The dragon lashes out, claws raking Thorin for 15 damage!").
      2.  Pass this narrative to a smaller, specialized "Interpreter" LLM.
      3.  The Interpreter LLM extracts `{"action": "claw_attack", "target": "Thorin", "damage": 15}`.
      4.  Your Python code applies the extracted mechanics to `game_state.py`.
    - **Pros**: GM LLM has maximum narrative freedom.
    - **Cons**: Slow (two LLM calls per turn). Prone to "sync errors" (Interpreter might misinterpret, or GM might narrate something mechanically impossible, leading to a desync between narrative and game state).
    - **Integration Point**: Introduce a post-processing step after the main GM response.

  - **Priority**: CRITICAL (Essential for dynamic gameplay where NPC/monster actions have real mechanical impact).
  - **Dependencies**: Relies heavily on robust `game_state.py` definitions for characters, combat, and NPCs.

## Implementation Notes

### Current System Integration Points

- **Game State System**: `dnd_rag_system/systems/game_state.py`
  - `SpellSlots` class for spell tracking
  - `CharacterState.inventory` for item management
  - `PartyState.gold` and `PartyState.shared_inventory` for party resources

- **RAG System**: `dnd_rag_system/core/chroma_manager.py`
  - ChromaDB already contains races, classes, spells, monsters
  - Can query for race/class features during character creation

- **Character Creator**: `dnd_rag_system/systems/character_creator.py`
  - `Character` dataclass needs enhancement for racial traits
  - Integration point for RAG-based feature loading

- **Gradio UI**: `web/app_gradio.py`
  - Add new tabs for shop/marketplace
  - Update character creation form to show RAG-loaded bonuses
  - Add party mode toggle in Play Game tab

### Priority Suggestions

1. **High Priority**: RAG-based racial/class bonuses (foundational for accurate characters)
2. **Medium Priority**: Spell system improvements (critical for casters)
3. **Medium Priority**: Party-based chat mode (enhances existing party system)
4. **Low Priority**: Shop system (nice-to-have, can be simulated by GM)

### Testing Requirements

- Unit tests for RAG queries (race/class lookup)
- E2E tests for character creation with RAG bonuses
- E2E tests for shop transactions
- E2E tests for party mode chat
- Spell casting simulation tests