import sys
import os
from pathlib import Path

# Mock environment setup
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings

# Import the new logic from initialize_rag directly for testing
# (We need to import it as a module to access its private helpers)
import initialize_rag as init_script

def test_equipment_extraction():
    print("Testing Equipment PDF Extraction (Chain Mail)...")
    
    # 1. Use the new extraction logic
    phb_path = project_root / "dnd_rag_system/data/reference/players_handbook.pdf"
    if not phb_path.exists():
        print("PHB not found.")
        return

    # Extract pages 143-163 (Equipment chapter)
    raw_text = init_script._extract_pdf_range(phb_path, 143, 163)
    
    # Run the new chunker
    chunks = init_script._create_equipment_pdf_chunks(raw_text)
    
    # Find Chain Mail
    found = False
    for chunk in chunks:
        if "ITEM: Chain Mail" in chunk.content:
            print(f"\n✅ Found Chain Mail Chunk!")
            print("-" * 40)
            print(chunk.content[:200] + "...")
            print("-" * 40)
            found = True
            break
            
    if not found:
        print("\n❌ Chain Mail NOT found as a specific item chunk.")
        # Debug: search raw text
        if "Chain Mail" in raw_text:
            print("  (But 'Chain Mail' IS present in the raw extracted text)")
        else:
            print("  ('Chain Mail' is MISSING from extracted text entirely)")

def test_goblin_extraction():
    print("\nTesting Goblin Monster Extraction (Structured)...")
    
    # Import structured monster data (ensure this is available in init_script or directly imported)
    try:
        from dnd_rag_system.data.monster_stats import MONSTER_STATS
    except ImportError:
        print("❌ Cannot import MONSTER_STATS for testing.")
        return

    if "Goblin" in MONSTER_STATS:
        goblin_data = MONSTER_STATS["Goblin"]
        
        # Use the _create_monster_chunk helper from initialize_rag to create the chunk
        
        chunk_content = init_script._create_monster_chunk("Goblin", goblin_data)
        
        # Verify basic content directly on the string, including markdown
        if "MONSTER: Goblin" in chunk_content and "**Armor Class:** 15" in chunk_content and "**Hit Points:** 7 (2d6)" in chunk_content:
            print(f"\n✅ Found Goblin Chunk Content!")
            print("-" * 40)
            print(chunk_content[:200] + "...")
            print("-" * 40)
        else:
            print(f"\n❌ Goblin Chunk content verification failed. Expected parts not found.")
            print(f"Content: {chunk_content[:200]}...")
            
    else:
        print("\n❌ Goblin NOT found in MONSTER_STATS.")

if __name__ == "__main__":
    test_equipment_extraction()
    test_goblin_extraction()
