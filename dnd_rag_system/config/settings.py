"""
D&D RAG System Configuration

Central configuration file for all system settings, paths, and parameters.
"""

import os
from pathlib import Path
from typing import Dict, List

# ============================================================================
# PROJECT PATHS
# ============================================================================

# Root project directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
CHROMADB_DIR = PROJECT_ROOT / "chromadb"

# Source data files
SPELLS_TXT = PROJECT_ROOT / "spells.txt"
ALL_SPELLS_TXT = PROJECT_ROOT / "all_spells.txt"
MONSTER_MANUAL_PDF = PROJECT_ROOT / "Dungeons and Dragons - Monster Manual (Skip Williams, Jonathan Tweet, Monte Cook) (Z-Library).pdf"
PLAYERS_HANDBOOK_PDF = PROJECT_ROOT / "Dungeons  Dragons 5e Players Handbook (Wizards RPG Team Wyatt James, Schwalb Robert J etc.) (Z-Library).pdf"

# Extracted text files (optional backups)
EXTRACTED_MONSTERS_TXT = PROJECT_ROOT / "extracted_monsters.txt"
EXTRACTED_CLASSES_TXT = PROJECT_ROOT / "extracted_classes.txt"

# ============================================================================
# CHROMADB CONFIGURATION
# ============================================================================

# ChromaDB settings
CHROMA_PERSIST_DIR = str(CHROMADB_DIR)
CHROMA_ALLOW_RESET = False  # Set to True only for development

# Collection names (standardized naming convention)
COLLECTION_NAMES = {
    "spells": "dnd_spells",
    "monsters": "dnd_monsters",
    "classes": "dnd_classes",
    "races": "dnd_races"
}

# Collection metadata
COLLECTION_METADATA = {
    "dnd_spells": {
        "description": "D&D 5e spell descriptions, mechanics, and class associations",
        "source": "Player's Handbook - Spells"
    },
    "dnd_monsters": {
        "description": "D&D 5e monster stat blocks, abilities, and combat info",
        "source": "Monster Manual"
    },
    "dnd_classes": {
        "description": "D&D 5e class features, progressions, and subclasses",
        "source": "Player's Handbook - Classes"
    },
    "dnd_races": {
        "description": "D&D 5e race traits, subraces, and lore",
        "source": "Player's Handbook - Races"
    }
}

# ============================================================================
# EMBEDDING MODEL CONFIGURATION
# ============================================================================

# Sentence transformers model for embeddings
# all-MiniLM-L6-v2: Fast, good quality, 384 dimensions
# alternatives: all-mpnet-base-v2 (slower, better), paraphrase-MiniLM-L6-v2
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2

# Embedding batch size
EMBEDDING_BATCH_SIZE = 50

# ============================================================================
# CHUNKING PARAMETERS
# ============================================================================

# Maximum tokens per chunk (rough estimate: 1 token ≈ 4 characters)
MAX_CHUNK_TOKENS = 400
MAX_CHUNK_CHARS = MAX_CHUNK_TOKENS * 4

# Overlap for text splitting (in tokens)
CHUNK_OVERLAP_TOKENS = 50

# Minimum chunk size (too small chunks are not useful)
MIN_CHUNK_TOKENS = 50

# ============================================================================
# PARSER CONFIGURATION
# ============================================================================

# PDF extraction settings
PDF_EXTRACT_PAGES = {
    "races": (18, 46),      # Player's Handbook pages for races
    "classes": (46, 121),   # Player's Handbook pages for classes
}

# Monster parsing
MONSTER_START_NAME = "ABOLETH"  # First monster to parse in Monster Manual

# Spell parsing
SPELL_LEVELS = list(range(0, 10))  # Cantrips (0) through 9th level

# ============================================================================
# OLLAMA CONFIGURATION
# ============================================================================

# Ollama model for GM dialogue
OLLAMA_MODEL_NAME = "hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M"
OLLAMA_BASE_URL = "http://localhost:11434"  # Default Ollama API endpoint
OLLAMA_TIMEOUT = 30  # Timeout in seconds for model responses

# ============================================================================
# QUERY INTERFACE SETTINGS
# ============================================================================

# Default number of results to retrieve from RAG
DEFAULT_RAG_RESULTS = 5

# Maximum context tokens for LLM (approximate)
MAX_CONTEXT_TOKENS = 2000

# Entity recognition patterns
ENTITY_PATTERNS = {
    "spell_indicators": ["cast", "spell", "fireball", "magic missile", "cure wounds"],
    "monster_indicators": ["attack", "fight", "goblin", "dragon", "zombie"],
    "class_indicators": ["fighter", "wizard", "cleric", "rogue", "barbarian"],
    "race_indicators": ["elf", "dwarf", "human", "halfling", "dragonborn"]
}

# ============================================================================
# CHARACTER CREATION SETTINGS
# ============================================================================

# Available D&D classes
DND_CLASSES = [
    "Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk",
    "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"
]

# Available D&D races
DND_RACES = [
    "Dragonborn", "Dwarf", "Elf", "Gnome", "Half-Elf",
    "Halfling", "Half-Orc", "Human", "Tiefling"
]

# Ability score generation methods
ABILITY_SCORE_METHODS = {
    "standard_array": [15, 14, 13, 12, 10, 8],
    "point_buy": 27,  # Total points for point buy
    "roll_4d6_drop_lowest": True
}

# ============================================================================
# LOGGING & DEBUG
# ============================================================================

# Logging configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = PROJECT_ROOT / "dnd_rag_system.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Debug mode (verbose output, validation checks)
DEBUG_MODE = False

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

# Batch processing sizes
CHROMA_BATCH_SIZE = 100  # Documents to add in one ChromaDB batch
PARSER_BATCH_SIZE = 50   # Items to process before progress update

# Query caching
ENABLE_QUERY_CACHE = True
CACHE_SIZE = 100  # Number of queries to cache

# ============================================================================
# VALIDATION SETTINGS
# ============================================================================

# Enable validation checks during initialization
ENABLE_VALIDATION = True

# Minimum number of chunks expected per collection
MIN_CHUNKS = {
    "dnd_spells": 400,
    "dnd_monsters": 800,
    "dnd_classes": 1500,
    "dnd_races": 80
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_collection_name(content_type: str) -> str:
    """Get standardized collection name for content type."""
    return COLLECTION_NAMES.get(content_type.lower(), f"dnd_{content_type.lower()}")

def get_data_file(file_type: str) -> Path:
    """Get path to data file."""
    file_map = {
        "spells": SPELLS_TXT,
        "all_spells": ALL_SPELLS_TXT,
        "monster_manual": MONSTER_MANUAL_PDF,
        "players_handbook": PLAYERS_HANDBOOK_PDF,
        "extracted_monsters": EXTRACTED_MONSTERS_TXT,
        "extracted_classes": EXTRACTED_CLASSES_TXT,
    }
    return file_map.get(file_type.lower(), DATA_DIR / file_type)

def validate_paths() -> List[str]:
    """Validate that all required paths and files exist."""
    missing = []

    # Check if data files exist
    if not SPELLS_TXT.exists():
        missing.append(f"Spells file: {SPELLS_TXT}")
    if not ALL_SPELLS_TXT.exists():
        missing.append(f"All spells file: {ALL_SPELLS_TXT}")
    if not MONSTER_MANUAL_PDF.exists():
        missing.append(f"Monster Manual PDF: {MONSTER_MANUAL_PDF}")

    # ChromaDB directory will be created if it doesn't exist

    return missing

def get_config_summary() -> Dict:
    """Get a summary of current configuration."""
    return {
        "project_root": str(PROJECT_ROOT),
        "chroma_dir": CHROMA_PERSIST_DIR,
        "embedding_model": EMBEDDING_MODEL_NAME,
        "ollama_model": OLLAMA_MODEL_NAME,
        "collections": list(COLLECTION_NAMES.values()),
        "max_chunk_tokens": MAX_CHUNK_TOKENS,
        "debug_mode": DEBUG_MODE
    }
