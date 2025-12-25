---
title: D&D RAG GM
emoji: 🎲
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# D&D RAG System

An AI-powered Dungeon Master assistant using Retrieval Augmented Generation (RAG) with D&D 5e content.

## 🎯 Features

- **Semantic Search** across D&D spells, monsters, classes, and races
- **RAG-Enhanced GM Dialogue** with accurate rule retrieval
- **Character Creation** system
- **ChromaDB** vector database for fast retrieval
- **Ollama Integration** for local LLM inference

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- The following data files in the project root:
  - `spells.txt` - Spell descriptions
  - `all_spells.txt` - Spell/class associations
  - `extracted_monsters.txt` - Monster stat blocks
  - `extracted_classes.txt` - Class features
  - `Dungeons Dragons 5e Players Handbook.pdf` - For race extraction (optional)

### Installation Steps

#### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `chromadb` - Vector database
- `sentence-transformers` - Embedding models
- `pdfplumber` - PDF parsing (if needed)
- `ollama` - LLM client (for GM dialogue)
- Additional utilities

**Expected time:** 2-5 minutes (downloads ~500MB of models on first run)

#### 2. Verify Installation

```bash
python -c "import chromadb; import sentence_transformers; print('✓ All dependencies installed')"
```

If this prints `✓ All dependencies installed`, you're ready!

### Running the System

The system has four main components:
1. **Initialize RAG Database** - Load D&D content
2. **Test Searches** - Verify the system works
3. **Create Characters** - Interactive character builder
4. **Play with AI GM** - RAG-enhanced D&D sessions

#### Step 1: Initialize the RAG Database

Load all D&D content into ChromaDB:

```bash
python initialize_rag.py
```

**What this does:**
- Parses spells from `spells.txt` + `all_spells.txt` (~86 spells → 250+ chunks)
- Parses monsters from `extracted_monsters.txt` (~332 monsters)
- Parses classes from `extracted_classes.txt` (~12 classes)
- Extracts races from Player's Handbook PDF pages 18-46 (~9 races → 18 chunks)
- Creates 4 ChromaDB collections with **name-weighted chunks**
- Generates embeddings for semantic search
- Shows statistics

**Expected output:**
```
🎲 D&D RAG SYSTEM INITIALIZATION
...
✅ Total: 600+ chunks loaded into ChromaDB
🎉 Initialization complete!
```

**Key Feature:** Each entity name appears 2-3× in its chunk for better exact-match retrieval!

**Time:** ~30 seconds on first run (downloads embedding model), ~5 seconds on subsequent runs

**Options:**
```bash
python initialize_rag.py --clear           # Clear existing data and reload
python initialize_rag.py --only spells     # Load only spells
python initialize_rag.py --only monsters,classes  # Load specific collections
```

#### Step 2: Verify System is Working

**Option A: Comprehensive Test Suite** (recommended)
```bash
python tests/test_all_collections.py
```

Runs 26+ automated tests validating:
- ✅ Name weighting (exact matches rank first)
- ✅ Semantic search (related concepts found)
- ✅ Metadata extraction (CR, level, abilities, etc.)
- ✅ All 4 collections operational
- ✅ Cross-collection search

**Expected output:**
```
🧪 D&D RAG SYSTEM - COMPREHENSIVE TEST SUITE
...
✅ PASSED: 26/26 (100.0%)
🎉 ALL TESTS PASSED!
```

**Option B: Manual Testing**
```bash
python tests/test_spell_search.py
```

Shows detailed search results for spells, monsters, classes, and races.

**Option C: Interactive Query Tool** (most fun!)
```bash
python query_rag.py
```

Interactive CLI to explore the RAG system:
```
🎲 Query: fireball
🎲 Query: /monster dragon
🎲 Query: /spell healing
🎲 Query: /stats
```

If all tests pass, your RAG system is fully operational! 🎉

#### Step 3: Create Your D&D Character

Run the interactive character creator:

```bash
python create_character.py
```

**What this does:**
- Interactive character creation wizard
- Choose name, race, and class
- RAG-powered lookups for race traits and class features
- Generate ability scores (standard array, roll, or point buy)
- Calculate HP, AC, and modifiers
- Select starting equipment
- Choose starting spells (for spellcasters)
- Display complete character sheet
- Option to save character to JSON file

**Example workflow:**
```
🎲 D&D CHARACTER CREATOR
Let's create your D&D character!

What is your character's name? Gandalf

STEP 1: Choose Your Race
  1. Human
  2. Elf
  3. Dwarf
  ...

STEP 2: Choose Your Class
  1. Fighter
  2. Wizard
  3. Cleric
  ...

STEP 3: Ability Scores
  1. Standard Array (15, 14, 13, 12, 10, 8)
  2. Roll 4d6, drop lowest
  3. Point Buy

... [continues through equipment and spells]

🎉 CHARACTER CREATION COMPLETE!
Gandalf
Human Wizard, Level 1
Sage | Neutral Good
...
```

**Features:**
- RAG integration shows race/class information from the knowledge base
- Smart equipment selection based on class
- Automatic spell selection for casters
- Export to JSON for use in other tools

#### Step 4: Play D&D with AI Game Master

**Prerequisites:**
- Install Ollama: https://ollama.ai
- Download RPG model: `ollama pull hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M`

You have **two ways** to play:

---

### Option A: 🌐 Web Interface (Gradio) **⭐ RECOMMENDED**

Launch the web UI for the best experience:

```bash
python web/app_gradio.py
```

Then open http://localhost:7860 in your browser.

**Features:**
- 🎭 **Pre-made Characters**: Play as Thorin Stormshield (Dwarf Fighter) or Elara Moonwhisper (Elf Wizard)
- ✨ **Create Characters**: Full interactive character creation in the web UI
- 💬 **Chat Interface**: Clean conversation view with the AI GM
- 📊 **Character Sheet**: Live character stats displayed in sidebar
- 🖼️ **Character Portraits**: Placeholder for future GAN-generated images
- ⚡ **Quick Commands**: Built-in buttons for common actions
- 🎲 **RAG Search**: Test spell/monster lookups directly in the UI

**Quick Start:**
1. **Play Game Tab**: Select Thorin or Elara from the dropdown
2. Or **Create Character Tab**: Build your own custom character
3. Click "Load Character" to begin
4. Type your action in the chat box
5. The GM responds with RAG-enhanced D&D rules!

**Example Actions:**
```
# As Thorin (Fighter):
I draw my longsword and look for enemies
I attack with my weapon
/stats

# As Elara (Wizard):
I cast Magic Missile at the goblin
I look through my spellbook
/rag Magic Missile
```

---

### Option B: 💻 Command Line Interface

For terminal lovers, use the CLI version:

```bash
python play_with_character.py
```

**Character Selection:**
```
1. Create new character (full interactive creation)
2. Load existing character (from JSON file)
3. Use test character (quick start with Thorin)
```

**Available Characters:**

**Thorin Stormshield** - Level 3 Dwarf Fighter
- HP: 28 | AC: 18 | Proficiency: +2
- STR 16 (+3) | DEX 12 (+1) | CON 16 (+3)
- Equipment: Longsword, Shield, Plate Armor
- Perfect for: Melee combat, tanking, straightforward gameplay

**Elara Moonwhisper** - Level 2 Elf Wizard
- HP: 14 | AC: 12 | Proficiency: +2
- INT 17 (+3) | DEX 14 (+2) | CON 12 (+1)
- Spells: Fire Bolt, Mage Hand, Magic Missile, Shield
- Equipment: Quarterstaff, Spellbook, Component Pouch
- Perfect for: Spellcasting, strategic gameplay, testing RAG

**Example Session:**
```
🎲 D&D GAME SESSION - Playing as Elara Moonwhisper
======================================================================
Character: Elara Moonwhisper (Elf Wizard)
Model: hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M

Type /help for commands or start playing!
======================================================================

🎲 Elara Moonwhisper: I look around the tavern

🎭 GM: The tavern is dimly lit by flickering torches. You notice a group
of rough-looking adventurers in the corner, and a hooded figure sitting
alone by the fireplace...

🎲 Elara Moonwhisper: /stats

📊 Elara Moonwhisper | HP: 14 | AC: 12 | Prof: +2
   STR -1 | DEX +2 | CON +1 | INT +3 | WIS +1 | CHA +0
```

---

### 🎮 Commands Reference

**Character Commands:**
```
/character      - Show full character sheet
/stats          - Quick stats view (HP, AC, modifiers)
/context        - View current scene and character context
```

**RAG Commands:**
```
/rag <query>    - Search D&D knowledge base
                  Examples:
                  /rag Magic Missile    - Look up spell details
                  /rag Goblin          - Look up monster stats
                  /rag Fighter         - Look up class features
                  /rag Elf             - Look up race traits
```

**Session Commands:**
```
/help           - Show all available commands
/history        - Show conversation history
/save <file>    - Save session to JSON
/quit           - Exit the game
```

---

### 💡 How It Works

**Character-Aware Gameplay:**
1. Select or create a character (Thorin, Elara, or custom)
2. Character stats, spells, and equipment are passed to the GM
3. GM knows YOUR character and references it in responses

**RAG Integration:**
1. You type an action (e.g., "I cast Magic Missile")
2. System searches ChromaDB for relevant spells/monsters/rules
3. RAG results are injected into the AI GM's context
4. GM generates response using accurate D&D 5e rules
5. Response references your character's abilities

**Example RAG Flow:**
```
Input: "I cast Magic Missile at the goblin"
  ↓
RAG Search: Finds "Magic Missile" spell
  ↓
Context: "Elara (Wizard) has Magic Missile in spell list"
  ↓
Context: "Magic Missile: 1st-level, 3 darts, 1d4+1 force damage each"
  ↓
AI GM Response: Uses accurate spell mechanics + your character's stats
```

---

### 🎯 Gameplay Tips

**For Best Results:**
- **Be Specific**: "I cast Fire Bolt at the closest goblin" vs "I attack"
- **Use RAG**: Test `/rag <spell>` before casting to see what the GM knows
- **Check Context**: Use `/context` to see what the GM knows about your character
- **View Stats**: Use `/stats` during combat to remember your modifiers
- **Roleplay**: The GM responds to narrative actions ("I cautiously enter the room")

**Testing Spells with Elara:**
```
/rag Magic Missile     # See full spell description
I cast Magic Missile   # GM should apply 1st-level spell rules
/rag Fireball         # Search for a spell Elara doesn't know
I cast Fireball       # GM behavior (should it allow this?)
```

**Combat with Thorin:**
```
/stats                      # Check your attack bonus
I attack with my longsword # GM will ask for d20 roll
I use my shield             # GM applies AC bonus
I use Second Wind          # GM applies fighter class feature
```

#### Step 5: Run Interactive Searches (Optional)

Test your own queries:

```bash
python -c "
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings

db = ChromaDBManager()
results = db.search(settings.COLLECTION_NAMES['spells'], 'healing spell', n_results=3)

print('Top 3 Healing Spells:')
for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
    print(f\"  - {meta['name']}\")
"
```

### Troubleshooting

#### "ModuleNotFoundError: No module named 'chromadb'"

```bash
pip install chromadb sentence-transformers
```

#### "File not found: spells.txt"

Make sure these files exist in the project root:
```bash
ls spells.txt extracted_monsters.txt extracted_classes.txt
```

If missing, you need to extract them from your PDF files first.

#### "No results found" in searches

Re-initialize the database:
```bash
python initialize_rag.py --clear
```

#### Embedding model download is slow

The first run downloads ~80MB of models. This is normal. Subsequent runs are much faster.

#### "Ollama not found" when running GM dialogue

**Install Ollama:**
```bash
# Visit https://ollama.ai and download for your platform
# Or use package manager:
# macOS: brew install ollama
# Linux: curl https://ollama.ai/install.sh | sh
```

**Download the RPG model:**
```bash
ollama pull hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M
```

**Verify installation:**
```bash
ollama list
```

You should see the Qwen3-4B-RPG model in the list.

### What's Working Now

✅ **Semantic Search**: Find D&D content by meaning
✅ **250+ Spell Chunks**: 86 spells with multiple chunk types (full, quick_ref, by_class)
✅ **332 Monsters**: With CR, type extraction, and name weighting
✅ **12 Classes**: Wizard, Fighter, Cleric, Rogue, Barbarian, Bard, Druid, Monk, Paladin, Ranger, Sorcerer, Warlock
✅ **18 Race Chunks**: 9 core races (Dragonborn, Dwarf, Elf, Gnome, Half-Elf, Halfling, Half-Orc, Human, Tiefling)
✅ **Name-Weighted Retrieval**: Entity names appear 2-3× per chunk for accurate exact-match search
✅ **Cross-Collection Search**: Search all content types at once
✅ **ChromaDB**: Persistent vector database
✅ **Interactive Query Tool**: Command-line interface for exploring the RAG system
✅ **Comprehensive Tests**: 26+ automated tests validating all functionality
✅ **Character Creator**: Interactive character builder with RAG integration
✅ **AI Game Master**: RAG-enhanced dialogue system with Ollama

### What's Coming Soon

⏳ **Subrace Support**: High Elf, Mountain Dwarf, etc. with specific abilities
⏳ **Multi-Character Party**: Create and manage groups of characters
⏳ **Advanced Filtering**: Search by CR range, spell level, class, etc.

## 📁 Project Structure

```
├── characters/              # Character JSON files ⭐ NEW!
│   ├── thorin_stormshield.json
│   ├── elara_moonwhisper.json
│   └── [custom characters...]
│
├── dnd_rag_system/          # Main package
│   ├── config/              # Configuration
│   │   └── settings.py
│   ├── core/                # Core infrastructure
│   │   ├── base_parser.py   # Parser framework
│   │   ├── base_chunker.py  # Chunking utilities
│   │   └── chroma_manager.py # Database interface
│   ├── parsers/             # Content parsers
│   │   └── spell_parser.py  # Spell parser with name weighting
│   └── systems/             # High-level systems
│       ├── character_creator.py # Interactive character builder
│       └── gm_dialogue.py   # RAG-enhanced AI Game Master
│
├── docs/                    # Documentation ⭐ NEW!
│   ├── plan_progress.md     # Development progress tracking
│   └── HUGGINGFACE_DEPLOYMENT.md
│
├── tests/                   # Test suite ⭐ NEW!
│   ├── test_all_collections.py  # Comprehensive tests
│   ├── test_spell_search.py
│   └── [other test files...]
│
├── web/                     # Web applications ⭐ NEW!
│   ├── app_gradio.py        # Main Gradio UI with tabs
│   └── app.py               # Alternative Gradio UI
│
├── chromadb/                # Vector database (created on init)
├── initialize_rag.py        # Main initialization script
├── query_rag.py             # Interactive query CLI
├── create_character.py      # Character creator launcher (CLI)
├── play_with_character.py  # Character-aware gameplay CLI
├── run_gm_dialogue.py       # AI GM dialogue launcher
└── requirements.txt         # Python dependencies
```

## 🗂️ Required Data Files

These should be in the project root:

- `spells.txt` - Spell descriptions (extracted from Player's Handbook)
- `all_spells.txt` - Spell class associations
- `extracted_monsters.txt` - Monster stats (from Monster Manual)
- `extracted_classes.txt` - Class features (from Player's Handbook)

## 🔧 Configuration

Edit `dnd_rag_system/config/settings.py` to customize:

- **Database Path**: `CHROMA_PERSIST_DIR`
- **Embedding Model**: `EMBEDDING_MODEL_NAME` (default: all-MiniLM-L6-v2)
- **Ollama Model**: `OLLAMA_MODEL_NAME`
- **Chunk Size**: `MAX_CHUNK_TOKENS`
- **Collection Names**: `COLLECTION_NAMES`

## 📊 Collections

The system creates 4 ChromaDB collections with **name-weighted retrieval**:

1. **dnd_spells** (~250 chunks)
   - Multiple chunk types per spell: full_spell, quick_reference, by_class
   - Metadata: level, school, casting_time, range, components, duration, classes
   - Name appears 2-3× for better exact-match retrieval

2. **dnd_monsters** (~332 chunks)
   - Full stat blocks with weighted names
   - Metadata: challenge_rating, monster_type (e.g., "Large dragon")
   - Tagged by type: dragon, undead, beast, etc.

3. **dnd_classes** (~12 chunks)
   - Class features and descriptions
   - Name-weighted for accurate class searches
   - Metadata: class name, content_type

4. **dnd_races** (~18 chunks)
   - 2 chunks per race: description + traits
   - Metadata: ability_increases, size, speed, darkvision, languages
   - Extracted from Player's Handbook PDF

## 🧪 Development Status

### ✅ Phase 1: Core Infrastructure (Complete)
- Configuration system
- Base parser and chunker classes
- ChromaDB manager
- Directory structure

### ✅ Phase 2: Quick Integration (Complete)
- Initialize RAG script using notebook code
- Test search functionality
- Basic loaders for spells, monsters, classes

### ✅ Phase 3: Systems Layer (Complete)
- ✅ Character creation system with RAG integration
- ✅ RAG-enhanced GM dialogue system with Ollama
- ✅ Interactive query interface (`query_rag.py`)

### ✅ Phase 4: Polish & Testing (Complete)
- ✅ Comprehensive test suite with 26+ automated tests
- ✅ Name-weighted retrieval for all entity types
- ✅ Multiple chunk types per entity
- ✅ Race data extraction from PDF
- ✅ Interactive query tool
- ✅ Full documentation

## 🎮 Usage Examples

### Search for a Spell

```python
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings

db = ChromaDBManager()
results = db.search(settings.COLLECTION_NAMES['spells'], "fireball", n_results=3)

for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
    print(f"{meta['name']}: {doc[:200]}...")
```

### Cross-Collection Search

```python
results = db.search_all("fire damage", n_results_per_collection=2)

for collection, col_results in results.items():
    print(f"\n{collection}:")
    for doc, meta in zip(col_results['documents'][0], col_results['metadatas'][0]):
        print(f"  - {meta.get('name', 'Unknown')}")
```

## 🤝 Contributing

This is a learning project! Key areas for improvement:

1. **Better Parsing**: Improve OCR error handling in text extraction
2. **More Chunks**: Create better chunk strategies (quick reference, by level, etc.)
3. **Entity Recognition**: Detect spell/monster names in player input
4. **GM System**: Build the RAG-enhanced dialogue system
5. **Character Creator**: Interactive character building with RAG lookup

## 📝 Notes

- **Embedding Model**: Uses `all-MiniLM-L6-v2` (fast, 384 dimensions)
- **Token Limit**: Chunks limited to ~400 tokens (~1600 characters)
- **Ollama Required**: For GM dialogue (download from ollama.ai)
- **Data Sources**: Requires extracted text files (not included in repo)

## 🐛 Troubleshooting

### "ChromaDB not found"
```bash
pip install chromadb
```

### "No results found in search"
```bash
# Re-initialize the database
python initialize_rag.py --clear
```

### "File not found" errors
Make sure these files exist in the project root:
- `spells.txt`
- `extracted_monsters.txt`
- `extracted_classes.txt`

## 📚 References

- [D&D 5e SRD](https://dnd.wizards.com/resources/systems-reference-document)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [Ollama](https://ollama.ai/)

---

**Status**: 🚧 In Active Development

See `plan_progress.md` for detailed development progress.