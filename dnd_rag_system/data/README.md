# D&D RAG System - Data Directory

This directory contains all source data for the RAG (Retrieval-Augmented Generation) system.

## Directory Structure

```
data/
├── reference/              # Original D&D 5e reference PDFs
│   ├── players_handbook.pdf    (80 MB)
│   ├── monster_manual.pdf      (12 MB)
│   └── dm_guide.pdf            (12 MB)
│
├── extracted/              # Processed text extracted from PDFs
│   ├── spells.txt              (342 KB - detailed spell descriptions)
│   ├── all_spells.txt          (13 KB - spell lists by class)
│   ├── extracted_classes.txt   (279 KB - class descriptions)
│   └── extracted_monsters.txt  (1.6 MB - monster stat blocks)
│
├── class_features.py       # Structured class feature data
├── magic_items.py          # Structured magic item data
├── monster_stats.py        # Structured monster statistics
└── equipment.txt           # D&D 5e equipment tables (from PHB)
```

## File Descriptions

### Reference PDFs (`reference/`)
These are the original D&D 5e books used as source material. They are loaded into ChromaDB using specialized ingestion scripts.

- **players_handbook.pdf**: Core player rules, spells, equipment
- **monster_manual.pdf**: Monster stats and lore
- **dm_guide.pdf**: DM guidance, magic items, world-building

### Extracted Text (`extracted/`)
Text files extracted from PDFs for easier processing and ingestion.

- **spells.txt**: Detailed spell descriptions
- **all_spells.txt**: Spell lists organized by class and level
- **extracted_classes.txt**: Class features and abilities
- **extracted_monsters.txt**: Monster stat blocks and descriptions

### Structured Data (Python modules)
Python files containing structured data for direct import.

- **class_features.py**: Class features organized by class/level
- **magic_items.py**: Magic items with properties and effects
- **monster_stats.py**: Monster statistics in structured format
- **equipment.txt**: Equipment tables (armor, weapons, gear, tools)

## Loading Data into RAG System

### Loading Spells
```python
from dnd_rag_system.loaders.spell_loader import load_spells_to_chromadb
from dnd_rag_system.core.chroma_manager import ChromaDBManager

db = ChromaDBManager()
load_spells_to_chromadb(db)
```

### Loading Equipment
```python
from dnd_rag_system.loaders.equipment_loader import load_equipment_to_chromadb
from pathlib import Path

equipment_file = Path("dnd_rag_system/data/equipment.txt")
load_equipment_to_chromadb(db, equipment_file)
```

### Loading DM Guide
```bash
python ingest_dm_guide.py [--clear]
```

### Splitting Monster Data
```bash
python 1_split_monsters.py
```

## Data Sources

All D&D 5e content is © Wizards of the Coast. This is for personal/educational use only.

- Player's Handbook (2014)
- Monster Manual (2014)
- Dungeon Master's Guide (2014)

## Notes

- PDF files are large (~104 MB total) and are in `.gitignore`
- Text files are committed for easier access
- Structured Python files are committed and imported directly
- ChromaDB collections are created on-demand and stored in `chromadb/`
