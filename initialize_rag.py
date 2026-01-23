#!/usr/bin/env python3
"""
Initialize RAG System for HuggingFace Deployment

This script initializes the ChromaDB vector database by running
all necessary ingestion scripts. It's designed to work in a Docker
container where the chromadb/ directory is excluded via .dockerignore.
"""

import sys
import subprocess
from pathlib import Path

print("=" * 70)
print("🎲 INITIALIZING D&D RAG SYSTEM")
print("=" * 70)
print()

# Set up project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Track success/failure
all_successful = True
results = {}

# =============================================================================
# 1. INGEST SRD DATA (Classes, Spells, Races)
# =============================================================================
print("📚 Step 1: Ingesting SRD data (classes, spells, races)...")
print("-" * 70)

try:
    srd_script = project_root / "scripts" / "ingest_srd_to_chromadb.py"

    if srd_script.exists():
        result = subprocess.run(
            [sys.executable, str(srd_script)],
            cwd=str(project_root),
            check=True,
            capture_output=False
        )
        print("✅ SRD data ingestion completed")
        results['srd_data'] = 'success'
    else:
        print(f"⚠️  Script not found: {srd_script}")
        results['srd_data'] = 'skipped'

except subprocess.CalledProcessError as e:
    print(f"❌ SRD data ingestion failed with exit code {e.returncode}")
    results['srd_data'] = 'failed'
    all_successful = False
except Exception as e:
    print(f"❌ Error during SRD ingestion: {e}")
    results['srd_data'] = 'failed'
    all_successful = False

print()

# =============================================================================
# 2. INGEST GAME CONTENT (Magic Items, Class Features)
# =============================================================================
print("✨ Step 2: Ingesting game content (magic items, class features)...")
print("-" * 70)

try:
    game_content_script = project_root / "scripts" / "rag" / "ingest_game_content.py"

    if game_content_script.exists():
        result = subprocess.run(
            [sys.executable, str(game_content_script)],
            cwd=str(project_root),
            check=True,
            capture_output=False
        )
        print("✅ Game content ingestion completed")
        results['game_content'] = 'success'
    else:
        print(f"⚠️  Script not found: {game_content_script}")
        results['game_content'] = 'skipped'

except subprocess.CalledProcessError as e:
    print(f"❌ Game content ingestion failed with exit code {e.returncode}")
    results['game_content'] = 'failed'
    all_successful = False
except Exception as e:
    print(f"❌ Error during game content ingestion: {e}")
    results['game_content'] = 'failed'
    all_successful = False

print()

# =============================================================================
# 3. SUMMARY
# =============================================================================
print("=" * 70)
print("📊 INITIALIZATION SUMMARY")
print("=" * 70)

for component, status in results.items():
    status_icon = {
        'success': '✅',
        'failed': '❌',
        'skipped': '⚠️ '
    }.get(status, '❓')

    print(f"  {status_icon} {component.replace('_', ' ').title()}: {status}")

print()

if all_successful:
    print("🎉 RAG system initialization completed successfully!")
    print("   ChromaDB is ready for use.")
    sys.exit(0)
else:
    print("⚠️  RAG system initialization completed with some failures.")
    print("   The application may have limited functionality.")
    # Don't exit with error code - let the app start anyway
    sys.exit(0)
