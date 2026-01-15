#!/usr/bin/env python3
"""
Ingest parsed SRD data into ChromaDB for RAG queries.

This script loads the extracted class/spell/race data and adds it
to the ChromaDB collection for use in character creation and gameplay.
"""

import json
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer


def ingest_srd_data():
    """Ingest SRD data into ChromaDB."""
    
    # Paths
    data_dir = Path('dnd_rag_system/data/extracted/srd')
    chroma_path = Path('chromadb')
    
    print("🔮 SRD ChromaDB Ingestion")
    print("=" * 60)
    
    # Load data
    print("📖 Loading JSON data...")
    with open(data_dir / 'classes.json') as f:
        classes = json.load(f)
    with open(data_dir / 'spells.json') as f:
        spells = json.load(f)
    with open(data_dir / 'races.json') as f:
        races = json.load(f)
    
    print(f"  - {len(classes)} classes")
    print(f"  - {len(spells)} spells")
    print(f"  - {len(races)} races")
    
    # Initialize ChromaDB
    print("\n🗄️  Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=str(chroma_path))
    
    # Get or create collection
    try:
        collection = client.get_collection("dnd5e_srd")
        print(f"  - Found existing collection (deleting for fresh import)")
        client.delete_collection("dnd5e_srd")
    except:
        pass
    
    collection = client.create_collection(
        name="dnd5e_srd",
        metadata={"description": "D&D 5e SRD content for RAG"}
    )
    print(f"  - Created collection 'dnd5e_srd'")
    
    # Prepare documents
    documents = []
    metadatas = []
    ids = []
    
    # Add classes
    for idx, cls in enumerate(classes):
        doc_text = f"""
Class: {cls['name']}
Hit Die: {cls['hit_die']}
Primary Ability: {cls['primary_ability']}
Saving Throws: {', '.join(cls['saving_throws'][:2]) if cls['saving_throws'] else 'N/A'}
Armor Proficiency: {cls['armor_proficiency']}
Weapon Proficiency: {cls['weapon_proficiency']}
"""
        documents.append(doc_text.strip())
        metadatas.append({
            'type': 'class',
            'name': cls['name'],
            'hit_die': cls['hit_die'],
            'source': 'SRD 5.1'
        })
        ids.append(f"class_{idx}")
    
    # Add spells
    for idx, spell in enumerate(spells):
        doc_text = f"""
Spell: {spell['name']}
Level: {spell['level']}
School: {spell['school']}
{spell.get('description', '')[:300]}
"""
        documents.append(doc_text.strip())
        metadatas.append({
            'type': 'spell',
            'name': spell['name'],
            'level': spell['level'],
            'school': spell['school'],
            'source': 'SRD 5.1'
        })
        ids.append(f"spell_{idx}")
    
    # Add races
    for idx, race in enumerate(races):
        # Build document text including ability bonuses
        bonuses = race.get('ability_bonuses', {})
        bonus_text = ', '.join(f"+{val} {key.capitalize()}" for key, val in bonuses.items())
        
        doc_text = f"""
Race: {race['name']}
Ability Score Bonuses: {bonus_text if bonus_text else 'None'}
{race.get('traits', 'See SRD for full traits')}
"""
        documents.append(doc_text.strip())
        
        # Store bonuses as JSON string in metadata (ChromaDB doesn't support nested dicts)
        metadata = {
            'type': 'race',
            'name': race['name'],
            'source': 'SRD 5.1'
        }
        
        # Add each ability bonus as a separate metadata field
        for ability, bonus in bonuses.items():
            metadata[f'bonus_{ability}'] = bonus
        
        metadatas.append(metadata)
        ids.append(f"race_{idx}")
    
    # Add to ChromaDB
    print(f"\n✨ Ingesting {len(documents)} documents...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"✅ Successfully ingested all documents!")
    
    # Test query
    print("\n🔍 Testing query: 'Wizard class features'")
    results = collection.query(
        query_texts=["Wizard class features hit dice spells"],
        n_results=3
    )
    
    for i, doc in enumerate(results['documents'][0]):
        print(f"\n  Result {i+1}:")
        print(f"    {doc[:150]}...")
        print(f"    Metadata: {results['metadatas'][0][i]}")
    
    print("\n" + "=" * 60)
    print("🎉 Ingestion complete!")
    print(f"📊 Collection 'dnd5e_srd' now contains {len(documents)} documents")
    print("💡 Use this for character creation, spell lookups, and gameplay queries")


if __name__ == '__main__':
    ingest_srd_data()
