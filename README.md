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
python test_all_collections.py
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
python test_spell_search.py
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

Run an interactive D&D session with RAG-enhanced AI GM:

```bash
python run_gm_dialogue.py
```

**Prerequisites:**
- Install Ollama: https://ollama.ai
- Download RPG model: `ollama pull hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M`

**What this does:**
- Interactive D&D game session with AI Dungeon Master
- RAG-powered rule lookups in real-time
- GM searches ChromaDB for spells, monsters, classes when relevant
- Conversation history and context management
- Commands for scene setting, history review, and more

**Example session:**
```
🎲 D&D GAME MASTER - RAG-Enhanced AI Dungeon Master
Model: hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M

Type /help for commands or just start playing!
======================================================================

🎲 You: I cast fireball at the goblins

🎭 GM: Roll for your attack! The spell requires a DC 15 Dexterity saving
throw from each goblin. Roll 8d6 for fire damage. Each goblin in the
20-foot radius must make their save - on a success, they take half damage.

🎲 You: I investigate the room

🎭 GM: Make an Investigation check (roll d20 + INT modifier). I'll set
the DC based on what you're looking for...
```

**Available Commands:**
```
/help           - Show available commands
/context <text> - Set the current scene/context
/history        - Show conversation history
/rag <query>    - Test RAG search (see what the GM knows)
/save <file>    - Save session to JSON
/quit           - Exit the game
```

**How It Works:**
1. Player enters action or question
2. GM searches ChromaDB for relevant spells/monsters/rules
3. RAG results are injected into the LLM prompt
4. AI GM generates response using accurate D&D 5e rules
5. Response is shown to player with proper mechanics

**Tips:**
- Be specific: "I cast fireball" vs "I attack"
- The GM will ask for dice rolls when needed
- Use `/context` to set the scene for better immersion
- Use `/rag` to check if the GM has specific rule information
- The system works best with clear, action-oriented inputs

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
├── dnd_rag_system/          # Main package
│   ├── config/              # Configuration
│   │   └── settings.py
│   ├── core/                # Core infrastructure
│   │   ├── base_parser.py   # Parser framework
│   │   ├── base_chunker.py  # Chunking utilities
│   │   └── chroma_manager.py # Database interface
│   ├── parsers/             # Content parsers
│   │   └── spell_parser.py  # Spell parser with name weighting ⭐
│   └── systems/             # High-level systems
│       ├── character_creator.py # Interactive character builder
│       └── gm_dialogue.py   # RAG-enhanced AI Game Master
│
├── chromadb/                # Vector database (created on init)
├── initialize_rag.py        # Main initialization script ⭐
├── query_rag.py             # Interactive query CLI ⭐ NEW!
├── test_all_collections.py  # Comprehensive test suite ⭐ NEW!
├── test_spell_search.py     # Manual search testing
├── create_character.py      # Character creator launcher
├── run_gm_dialogue.py       # AI GM dialogue launcher
├── plan_progress.md         # Development progress tracking
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
