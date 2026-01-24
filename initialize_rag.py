#!/usr/bin/env python3
"""
Initialize RAG System for HuggingFace Deployment

This script initializes the ChromaDB vector database by running the
newer ingestion scripts that work with the current data structure.
"""

import sys
from pathlib import Path

# Set up project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("🎲 INITIALIZING D&D RAG SYSTEM")
print("=" * 70)
print()

# Track success/failure
all_successful = True
results = {}

# =============================================================================
# 1. INGEST SRD DATA (Classes, Spells, Races from JSON)
# =============================================================================
print("📚 Step 1: Ingesting SRD data (classes, spells, races from JSON)...")
print("-" * 70)

try:
    from scripts.ingest_srd_to_chromadb import ingest_srd_data

    ingest_srd_data()
    print("✅ SRD data ingestion completed\n")
    results['srd_data'] = 'success'

except Exception as e:
    print(f"❌ Error during SRD ingestion: {e}")
    import traceback
    traceback.print_exc()
    results['srd_data'] = 'failed'
    all_successful = False

# =============================================================================
# 2. INGEST GAME CONTENT (Magic Items, Class Features from Python modules)
# =============================================================================
print("✨ Step 2: Ingesting game content (magic items, class features)...")
print("-" * 70)

try:
    from dnd_rag_system.core.chroma_manager import ChromaDBManager
    sys.path.insert(0, str(project_root / "scripts" / "rag"))
    from ingest_game_content import load_magic_items, load_class_features

    db_manager = ChromaDBManager()

    load_magic_items(db_manager, clear=False)
    load_class_features(db_manager, clear=False)

    print("✅ Game content ingestion completed\n")
    results['game_content'] = 'success'

except Exception as e:
    print(f"❌ Error during game content ingestion: {e}")
    import traceback
    traceback.print_exc()
    results['game_content'] = 'failed'
    all_successful = False

# =============================================================================
# 3. SUMMARY
# =============================================================================
print("=" * 70)
print("📊 INITIALIZATION SUMMARY")
print("=" * 70)

for component, status in results.items():
    status_icon = '✅' if status == 'success' else '❌'
    print(f"  {status_icon} {component.replace('_', ' ').title()}: {status}")

print()

if all_successful:
    print("🎉 RAG system initialization completed successfully!")
    print("   ChromaDB is ready for use.")
    sys.exit(0)
else:
    print("⚠️  Initialization completed with some failures.")
    print("   The application may start with limited functionality.")
    # Exit with 0 to allow the app to start even if RAG init fails
    sys.exit(0)
