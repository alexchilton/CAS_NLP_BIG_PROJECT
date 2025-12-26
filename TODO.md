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

- [ ] **Implement initiative-based party actions** 🔴 TODO
  - Roll initiative for all party members at start of combat
  - Each party member automatically takes action based on initiative order
  - GM describes what each character does in turn
  - Integration with existing `CombatState` in `game_state.py` for initiative tracking
  - Display initiative order in UI during combat encounters
  - **Note**: CombatState already supports initiative tracking, needs UI integration

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
    - Adventuring gear (rope, torches, rations, potions, etc.)
    - Tools, mounts, and other equipment
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
  - Add starting equipment based on class
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
      - Spells: Checks if spell is known by character (with fuzzy matching)
      - Items: Validates items exist in character inventory
      - Conversations: Allows NPC introduction for contextually appropriate NPCs
    - **Context-Aware Prompting**: Enhances GM prompts with validation guidance
      - Valid actions: Proceed normally
      - Invalid actions: Instructs GM to narrate failure without introducing non-existent entities
      - NPC introductions: Allows GM to introduce NPCs that make contextual sense
    - **Fuzzy Matching**: Handles partial matches (e.g., "goblin" → "Goblin Scout")
  - **NPC Conversation Features**:
    - Encourages dynamic NPC introduction in appropriate contexts
    - Auto-adds NPCs to `npcs_present` when GM introduces them
    - Rejects NPC interactions that don't make contextual sense
  - **Integration**: Fully integrated into `gm_dialogue_unified.py.generate_response()`
  - **Testing**: Comprehensive test suite in `test_reality_check.py` (all tests passing)
  - **Files**:
    - Core logic: `dnd_rag_system/systems/action_validator.py`
    - Integration: `dnd_rag_system/systems/gm_dialogue_unified.py`
    - Tests: `test_reality_check.py`


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