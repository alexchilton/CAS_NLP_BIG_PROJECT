# TODO - D&D RAG System Feature Roadmap

> **Note**: See DONE.md for completed features that are already implemented and working.

---

## 🔴 CRITICAL PRIORITY

### Fix Party Mode UI Bug 🔴 CRITICAL
- **Issue**: When party mode checkbox is enabled, chat textarea becomes non-interactable
- **Impact**: Cannot send messages in party mode, makes feature unusable
- **Root Cause**: Gradio UI state management issue when switching modes
- **Investigation Needed**: Check `web/app_gradio.py` party mode toggle implementation
- **Test Case**: `e2e_tests/test_party_mode_logging.py` documents the issue
- **Priority**: MUST FIX FIRST - blocks all party mode development

---

## 🔥 HIGH PRIORITY

### Narrative to Mechanics Translation (GM Output Processing)
**Critical for dynamic gameplay!** The GM LLM can narrate events, but game state doesn't update automatically.

- **Problem**: GM's narrative ("The dragon breathes fire, dealing 30 damage!") doesn't update `game_state.py`
- **Goal**: Automatically apply mechanical effects from GM narration to game state
- **Recommended Approach**: **Structured Output (JSON + Narrative)**
  - GM LLM outputs both narrative text AND structured mechanics data
  - Use Claude's function calling / structured output capabilities
  - Python parses mechanics JSON and updates game state
  - Display narrative to player
- **Example Output**:
  ```json
  {
    "narrative": "The dragon's fiery breath scorches the party! Thorin takes 30 damage, Elara 15.",
    "mechanics": {
      "action_type": "dragon_breath_attack",
      "targets": [
        {"name": "Thorin", "damage": 30, "damage_type": "fire"},
        {"name": "Elara", "damage": 15, "damage_type": "fire"}
      ],
      "status_effects": []
    }
  }
  ```
- **Implementation Points**:
  - Modify GM prompt in `gm_dialogue_unified.py` to request structured output
  - Add JSON parser for mechanics extraction
  - Call appropriate `game_state.py` methods (e.g., `character.take_damage()`)
  - Update UI to reflect state changes
- **Priority**: HIGH - Essential for immersive, mechanically-accurate gameplay

---

## 🎯 MEDIUM PRIORITY

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
  - Check if current location is a shop (`location_type = "shop"` in GameSession)
  - OR check if a merchant/shopkeeper NPC is present in `npcs_present`
  - Reject transactions with message: "There's no shop here! You're in a dragon's lair, not a marketplace!"
- **Examples**:
  - ✅ Valid: Player in "The Rusty Blade" shop location → `/buy` works
  - ✅ Valid: "Grum the Shopkeeper" in `npcs_present` → `/buy` works
  - ❌ Invalid: Player in "Dragon's Lair" → `/buy` rejected
  - ❌ Invalid: No merchant NPC present → `/buy` rejected
- **Integration Point**: Add shop location validation in `ShopSystem.attempt_purchase()` and `attempt_sale()`

---

## 📚 LOWER PRIORITY / ENHANCEMENTS

### Spell System Improvements
- Add spell slots tracking by level (1st-9th level slots)
- Implement prepared spells vs known spells distinction
- Add spell casting mechanics with slot consumption
- Proper D&D 5e spell levels and rules
- Integration with existing `SpellSlots` class in `game_state.py`

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

### World State & Exploration System
- **Goal**: Maintain a consistent, persistent game world with interconnected locations
- **Approach: Lazy Graph Implementation**:
  - Pre-defined core locations (towns, quest hubs) with direct connections
  - "Lazy" generation: dynamically generate unexplored areas when players enter them
  - Persistent scene state: store location state (dead monsters, moved items) for consistency
- **Integration with `game_state.py`**:
  - `GameSession.current_location`: Become a `Location` object (new dataclass)
  - `GameSession.world_map` (new field): Dictionary/graph of visited locations
- **Priority**: Lower (nice-to-have, but not blocking core gameplay)


A large Bug...

So i start and try and cast magic missile at the goblin- there is no goblin but...then it goes into combat with a dragon who appears from nowhere and together with thorin...
Example 

Welcome, Elara Moonwhisper!

You find yourself in The Adventurer's Guild Hall.

A gathering place for heroes seeking quests and glory. Notice boards line the walls with job postings. A small shop in the corner sells equipment.

You have 125 gold pieces in your purse.

What would you like to do?

Type /help to see available commands, or describe your action!


"I cast Magic Missile at the goblin"


Your magic missile streaks through the air, guided by your arcane power. As it strikes its target, a shower of tiny, glowing darts erupts from its tip, each one dealing a small but concentrated damage.

The goblin, startled by the sudden barrage, yelps in pain as the missiles explode around it. It stumbles back, clutching its chest, before falling to the ground, lifeless. The room falls silent for a moment, the sound of your spell echoing off the walls. You stand there, panting, your spellbook open in your hands, feeling a rush of power and satisfaction.

The ancient red dragon raises its massive head, its scales shimmering in the light. It opens its jaws, revealing rows of razor-sharp teeth.

"Well played, human mage," it says, its voice booming. "But even a wizard cannot save you from the wrath of the Red Dragon."

🎯 Thorin Stormshield's turn!


Your Action
⚔️ Initiative Tracker
▼
⚔️ Combat Round 2

📜 Initiative Order: Ancient Red Dragon (20) 🎯 Thorin Stormshield (2)