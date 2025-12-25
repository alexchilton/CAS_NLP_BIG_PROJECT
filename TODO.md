# TODO - D&D RAG System Feature Roadmap

## Party-Based Gameplay

- [ ] **Implement party-based chat mode**
  - When party is defined and no single character is loaded, send full party info to GM chat context instead of individual character
  - Enable true party-based D&D gameplay where GM manages adventures for the whole group

- [ ] **Add party/character mode toggle in Play Game tab**
  - Allow switching between single character mode and party mode
  - Update UI to show which mode is active

- [ ] **Update GM context to handle party-based gameplay**
  - Format party context with all character stats, equipment, spells
  - Handle multi-character scenarios in GM responses

## Spell System Improvements

- [ ] **Improve spell system**
  - Add spell slots tracking by level (1st-9th level slots)
  - Implement prepared spells vs known spells distinction
  - Add spell casting mechanics with slot consumption
  - Proper D&D 5e spell levels and rules
  - Integration with existing `SpellSlots` class in `game_state.py`

## Inventory & Shopping System

- [ ] **Create inventory shop/marketplace tab**
  - New Gradio tab for browsing and purchasing items
  - UI for viewing available items with descriptions and prices

- [ ] **Add shop inventory with D&D items**
  - Weapons (Longsword, Shortsword, Greataxe, etc.)
  - Armor (Leather, Chainmail, Plate, etc.)
  - Potions (Healing, Greater Healing, etc.)
  - Adventuring gear (Rope, Torches, Rations, etc.)
  - Magical items (if applicable)

- [ ] **Implement buy/sell transactions**
  - Update character/party gold on purchases
  - Add items to character/party inventory
  - Sell items back to shop
  - Transaction validation (enough gold, inventory space)

## RAG-Based Character Creation

- [ ] **Load racial bonuses from RAG**
  - Query ChromaDB for race information during character creation
  - Auto-apply ability score increases (e.g., Dwarf +2 CON, Elf +2 DEX)
  - Add racial traits (Darkvision, Fey Ancestry, Dwarven Resilience, etc.)
  - Set speed, size, languages
  - Display racial features in character creation form

- [ ] **Load class features from RAG**
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
