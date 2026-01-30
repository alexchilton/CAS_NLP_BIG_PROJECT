import sys
import os
from pathlib import Path
import chromadb

# Setup path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from dnd_rag_system.config import settings

def debug_retrieval():
    print("🔍 Debugging ChromaDB Retrieval...")
    
    chroma_path = project_root / "chromadb"
    if not chroma_path.exists():
        print(f"❌ ChromaDB path not found: {chroma_path}")
        return

    client = chromadb.PersistentClient(path=str(chroma_path))
    
    collections = client.list_collections()
    print(f"📂 Found collections: {[c.name for c in collections]}")
    
    # 1. Check Equipment (Chain Mail)
    equip_col_name = settings.COLLECTION_NAMES.get('equipment', 'dnd_equipment')
    print(f"\n🛡️ Checking collection: {equip_col_name}")
    
    try:
        equip_col = client.get_collection(equip_col_name)
        count = equip_col.count()
        print(f"   Count: {count}")
        
        if count > 0:
            # Query for Chain Mail
            results = equip_col.query(
                query_texts=["Chain Mail"],
                n_results=3
            )
            print("   Query 'Chain Mail' results:")
            for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                print(f"     {i+1}. {doc[:100]}... (Meta: {meta})")
        else:
            print("   ⚠️ Collection is empty!")
            
    except Exception as e:
        print(f"   ❌ Error accessing collection: {e}")

    # 2. Check Monsters (Goblin)
    monster_col_name = settings.COLLECTION_NAMES.get('monsters', 'dnd_monsters')
    print(f"\n👹 Checking collection: {monster_col_name}")
    
    try:
        monster_col = client.get_collection(monster_col_name)
        count = monster_col.count()
        print(f"   Count: {count}")
        
        if count > 0:
            # Query for Goblin
            results = monster_col.query(
                query_texts=["Goblin"],
                n_results=3
            )
            print("   Query 'Goblin' results:")
            for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                print(f"     {i+1}. {doc[:100]}... (Meta: {meta})")
        else:
            print("   ⚠️ Collection is empty!")

    except Exception as e:
        print(f"   ❌ Error accessing collection: {e}")

if __name__ == "__main__":
    debug_retrieval()
