"""
Pytest configuration and shared fixtures.

Provides session-scoped ChromaDB instance to avoid reloading
the embedding model (500MB) for every test.
"""

import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager


@pytest.fixture(scope="session")
def shared_chromadb():
    """
    Shared ChromaDB instance for all tests.
    
    Session-scoped to avoid:
    - Reloading 500MB embedding model for each test
    - Reinitializing ChromaDB client multiple times
    - Slow test execution
    
    The database is read-only for tests - initialization should
    be done via initialize_rag.py before running tests.
    """
    print("\n📦 Loading shared ChromaDB instance (once for all tests)...")
    db = ChromaDBManager()
    print(f"✅ ChromaDB loaded: {db.persist_dir}")
    return db


@pytest.fixture(scope="function")
def chromadb(shared_chromadb):
    """
    Function-scoped ChromaDB fixture.
    
    Returns the shared session ChromaDB instance.
    Use this in tests that need database access.
    
    Example:
        def test_something(chromadb):
            results = chromadb.search("dnd_spells", "fireball")
    """
    return shared_chromadb
