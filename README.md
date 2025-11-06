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
  - `spells.txt`
  - `all_spells.txt` (optional)
  - `extracted_monsters.txt`
  - `extracted_classes.txt`

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

#### Step 1: Initialize the RAG Database

Load all D&D content into ChromaDB:

```bash
python initialize_rag.py
```

**What this does:**
- Parses spells from `spells.txt` (~86 spells)
- Parses monsters from `extracted_monsters.txt` (~332 monsters)
- Parses classes from `extracted_classes.txt` (~5 classes)
- Creates 4 ChromaDB collections
- Generates embeddings for semantic search
- Shows statistics

**Expected output:**
```
🎲 D&D RAG SYSTEM INITIALIZATION
...
✅ Total: 423 chunks loaded into ChromaDB
🎉 Initialization complete!
```

**Time:** ~30 seconds on first run (downloads embedding model), ~5 seconds on subsequent runs

**Options:**
```bash
python initialize_rag.py --clear           # Clear existing data and reload
python initialize_rag.py --only spells     # Load only spells
python initialize_rag.py --only monsters,classes  # Load specific collections
```

#### Step 2: Verify System is Working

Run the test suite to verify searches work:

```bash
python test_rag_search.py
```

**What this tests:**
- ✅ Spell searches ("fireball spell", "cure wounds", etc.)
- ✅ Monster searches ("goblin", "dragon fire breath", etc.)
- ✅ Class searches ("wizard spellcasting", "fighter extra attack", etc.)
- ✅ Cross-collection searches ("fire damage" across all content)

**Expected output:**
```
🧪 D&D RAG SEARCH TEST SUITE
...
✅ TEST SUITE COMPLETE
```

If all tests pass, your RAG system is fully operational! 🎉

#### Step 3: Run Interactive Searches (Optional)

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

### What's Working Now

✅ **Semantic Search**: Find D&D content by meaning
✅ **86 Spells**: Fireball, Cure Wounds, Magic Missile, etc.
✅ **332 Monsters**: Goblins, Dragons, Orcs, etc.
✅ **5 Classes**: Wizard, Fighter, Cleric, etc.
✅ **Cross-Collection**: Search all content at once
✅ **ChromaDB**: Persistent vector database

### What's Coming Soon

⏳ **GM Dialogue System**: RAG-enhanced Ollama integration
⏳ **Character Creator**: Interactive character building
⏳ **Query Interface**: Smart entity recognition

### Next: Run GM Dialogue (Coming Soon)

```bash
python run_gm_dialogue.py
```

Will allow interactive D&D sessions with AI GM that knows all the rules!

## 📁 Project Structure

```
├── dnd_rag_system/          # Main package
│   ├── config/              # Configuration
│   │   └── settings.py
│   ├── core/                # Core infrastructure
│   │   ├── base_parser.py   # Parser framework
│   │   ├── base_chunker.py  # Chunking utilities
│   │   └── chroma_manager.py # Database interface
│   ├── parsers/             # Content parsers (TBD)
│   └── systems/             # GM dialogue, character creator (TBD)
│
├── chromadb/                # Vector database (created on init)
├── initialize_rag.py        # Main initialization script ⭐
├── test_rag_search.py       # Test search functionality ⭐
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

The system creates 4 ChromaDB collections:

1. **dnd_spells** - D&D 5e spells with mechanics
2. **dnd_monsters** - Monster stats and abilities
3. **dnd_classes** - Class features by level
4. **dnd_races** - Race traits and subraces (TBD)

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

### ⏳ Phase 3: Systems Layer (In Progress)
- Query interface with entity recognition
- RAG-enhanced GM dialogue system
- Character creation system

### ⏳ Phase 4: Polish & Testing
- Comprehensive unit tests
- Integration tests
- Performance benchmarks
- Documentation

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
