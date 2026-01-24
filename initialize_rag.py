#!/usr/bin/env python3
"""
Initialize RAG System for HuggingFace Deployment

This script initializes the ChromaDB vector database by running the
newer ingestion scripts that work with the current data structure.
"""

import sys
import os
from pathlib import Path

# Set up project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70, flush=True)
print("🎲 INITIALIZING D&D RAG SYSTEM", flush=True)
print("=" * 70, flush=True)
print(flush=True)

# Debug info
print(f"Python version: {sys.version}", flush=True)
print(f"Working directory: {os.getcwd()}", flush=True)
print(f"Project root: {project_root}", flush=True)
print(flush=True)

# Track success/failure
all_successful = True
results = {}

# =============================================================================
# 1. INGEST SRD DATA (Classes, Spells, Races from JSON)
# =============================================================================
print("📚 Step 1: Ingesting SRD data (classes, spells, races from JSON)...", flush=True)
print("-" * 70, flush=True)

try:
    # Check if data files exist
    srd_data_dir = project_root / "dnd_rag_system" / "data" / "extracted" / "srd"
    print(f"Checking for SRD data in: {srd_data_dir}", flush=True)

    if not srd_data_dir.exists():
        print(f"⚠️  SRD data directory not found: {srd_data_dir}", flush=True)
        print(f"   Skipping SRD data ingestion", flush=True)
        results['srd_data'] = 'skipped'
    else:
        json_files = list(srd_data_dir.glob("*.json"))
        print(f"   Found {len(json_files)} JSON files", flush=True)

        from scripts.ingest_srd_to_chromadb import ingest_srd_data

        ingest_srd_data()
        print("✅ SRD data ingestion completed\n", flush=True)
        results['srd_data'] = 'success'

except Exception as e:
    print(f"❌ Error during SRD ingestion: {e}", flush=True)
    import traceback
    traceback.print_exc()
    results['srd_data'] = 'failed'
    all_successful = False

# =============================================================================
# 2. INGEST GAME CONTENT (Magic Items, Class Features from Python modules)
# =============================================================================
print("✨ Step 2: Ingesting game content (magic items, class features)...", flush=True)
print("-" * 70, flush=True)

try:
    from dnd_rag_system.core.chroma_manager import ChromaDBManager
    sys.path.insert(0, str(project_root / "scripts" / "rag"))
    from ingest_game_content import load_magic_items, load_class_features

    db_manager = ChromaDBManager()

    load_magic_items(db_manager, clear=False)
    load_class_features(db_manager, clear=False)

    print("✅ Game content ingestion completed\n", flush=True)
    results['game_content'] = 'success'

except Exception as e:
    print(f"❌ Error during game content ingestion: {e}", flush=True)
    import traceback
    traceback.print_exc()
    results['game_content'] = 'failed'
    all_successful = False

# =============================================================================
# 3. SUMMARY
# =============================================================================
print("=" * 70, flush=True)
print("📊 INITIALIZATION SUMMARY", flush=True)
print("=" * 70, flush=True)

for component, status in results.items():
    status_icon = '✅' if status == 'success' else '❌' if status == 'failed' else '⚠️'
    print(f"  {status_icon} {component.replace('_', ' ').title()}: {status}", flush=True)

print(flush=True)

if all_successful:
    print("🎉 RAG system initialization completed successfully!", flush=True)
    print("   ChromaDB is ready for use.", flush=True)
    sys.exit(0)
else:
    print("⚠️  Initialization completed with some failures.", flush=True)
    print("   The application may start with limited functionality.", flush=True)
    # Exit with 0 to allow the app to start even if RAG init fails
    sys.exit(0)
