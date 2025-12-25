#!/usr/bin/env python3
"""
Test script to check spell search functionality and spell name weighting.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings

def test_spell_search():
    """Test spell search to see if spell names are properly weighted."""

    print("="*70)
    print("🔍 TESTING SPELL SEARCH")
    print("="*70)

    # Initialize ChromaDB
    db = ChromaDBManager()

    # Get collection stats
    try:
        stats = db.get_collection_stats(settings.COLLECTION_NAMES['spells'])
        print(f"\n📊 Spell Collection Stats:")
        print(f"   Total documents: {stats.get('total_documents', 0)}")
    except Exception as e:
        print(f"\n⚠️  Error getting stats: {e}")
        print("   Collection may not exist yet. Run: python initialize_rag.py")
        return

    # Test searches
    test_queries = [
        "fireball",
        "fire damage spell",
        "healing",
        "cure wounds",
        "magic missile",
    ]

    print("\n" + "="*70)
    print("🧪 TESTING SPELL SEARCHES")
    print("="*70)

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 70)

        try:
            results = db.search(settings.COLLECTION_NAMES['spells'], query, n_results=5)

            if results and results['documents'] and len(results['documents'][0]) > 0:
                for i, (doc, meta, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                ), 1):
                    spell_name = meta.get('name', 'Unknown')
                    level = meta.get('level', '?')
                    school = meta.get('school', '?')

                    print(f"{i}. {spell_name} (Level {level} {school})")
                    print(f"   Distance: {distance:.4f}")
                    print(f"   Preview: {doc[:100]}...")
                    print()
            else:
                print("   No results found")
        except Exception as e:
            print(f"   Error: {e}")

    # Test race search
    print("\n" + "="*70)
    print("🧝 TESTING RACE SEARCH")
    print("="*70)

    try:
        race_stats = db.get_collection_stats(settings.COLLECTION_NAMES['races'])
        print(f"\n📊 Race Collection Stats:")
        print(f"   Total documents: {race_stats.get('total_documents', 0)}")

        if race_stats.get('total_documents', 0) > 0:
            # Test 1: Basic race search
            print(f"\n🔍 Test 1: Search for 'elf traits'")
            race_results = db.search(settings.COLLECTION_NAMES['races'], "elf traits darkvision", n_results=3)

            if race_results and race_results['documents'] and len(race_results['documents'][0]) > 0:
                for i, (doc, meta, distance) in enumerate(zip(
                    race_results['documents'][0],
                    race_results['metadatas'][0],
                    race_results['distances'][0]
                ), 1):
                    race_name = meta.get('name', 'Unknown')
                    chunk_type = meta.get('chunk_type', 'unknown')
                    darkvision = meta.get('darkvision', 0)

                    print(f"{i}. {race_name} ({chunk_type})")
                    print(f"   Distance: {distance:.4f}")
                    if darkvision:
                        print(f"   Darkvision: {darkvision} feet")
                    print(f"   Preview: {doc[:150]}...")
                    print()

            # Test 2: Character creation search
            print(f"🔍 Test 2: Search for 'dwarf warrior strong'")
            dwarf_results = db.search(settings.COLLECTION_NAMES['races'], "dwarf warrior strong constitution", n_results=2)

            if dwarf_results and dwarf_results['documents'] and len(dwarf_results['documents'][0]) > 0:
                for i, (doc, meta) in enumerate(zip(
                    dwarf_results['documents'][0],
                    dwarf_results['metadatas'][0]
                ), 1):
                    race_name = meta.get('name', 'Unknown')
                    abilities = meta.get('ability_increases', {})

                    print(f"{i}. {race_name}")
                    if abilities:
                        print(f"   Ability Bonuses: {abilities}")
                    print(f"   Preview: {doc[:120]}...")
                    print()

            # Test 3: Specific trait search
            print(f"🔍 Test 3: Search for races with darkvision")
            dark_results = db.search(settings.COLLECTION_NAMES['races'], "darkvision dark sight", n_results=5)

            if dark_results and dark_results['metadatas'] and len(dark_results['metadatas'][0]) > 0:
                darkvision_races = set()
                for meta in dark_results['metadatas'][0]:
                    if meta.get('darkvision', 0) > 0:
                        darkvision_races.add(f"{meta.get('name')} ({meta.get('darkvision')}ft)")

                if darkvision_races:
                    print(f"   Races with darkvision: {', '.join(sorted(darkvision_races))}")
                else:
                    print(f"   No darkvision info found in results")
        else:
            print("   ⚠️  No race data loaded yet")
            print("   Run: python initialize_rag.py --only races")
    except Exception as e:
        print(f"   ⚠️  Error testing races: {e}")

    # Test monster search
    print("\n" + "="*70)
    print("👹 TESTING MONSTER SEARCH")
    print("="*70)

    try:
        monster_stats = db.get_collection_stats(settings.COLLECTION_NAMES['monsters'])
        print(f"\n📊 Monster Collection Stats:")
        print(f"   Total documents: {monster_stats.get('total_documents', 0)}")

        if monster_stats.get('total_documents', 0) > 0:
            # Test 1: Search by monster name
            print(f"\n🔍 Test 1: Search for 'goblin'")
            goblin_results = db.search(settings.COLLECTION_NAMES['monsters'], "goblin", n_results=3)

            if goblin_results and goblin_results['documents'] and len(goblin_results['documents'][0]) > 0:
                for i, (doc, meta, distance) in enumerate(zip(
                    goblin_results['documents'][0],
                    goblin_results['metadatas'][0],
                    goblin_results['distances'][0]
                ), 1):
                    monster_name = meta.get('name', 'Unknown')
                    cr = meta.get('challenge_rating', '?')
                    monster_type = meta.get('monster_type', '')

                    print(f"{i}. {monster_name} (CR {cr})")
                    print(f"   Distance: {distance:.4f}")
                    if monster_type:
                        print(f"   Type: {monster_type}")
                    print(f"   Preview: {doc[:120]}...")
                    print()

            # Test 2: Search by monster type
            print(f"🔍 Test 2: Search for 'dragon fire breath'")
            dragon_results = db.search(settings.COLLECTION_NAMES['monsters'], "dragon fire breath", n_results=3)

            if dragon_results and dragon_results['documents'] and len(dragon_results['documents'][0]) > 0:
                for i, (doc, meta) in enumerate(zip(
                    dragon_results['documents'][0],
                    dragon_results['metadatas'][0]
                ), 1):
                    monster_name = meta.get('name', 'Unknown')
                    cr = meta.get('challenge_rating', '?')

                    print(f"{i}. {monster_name} (CR {cr})")
                    print(f"   Preview: {doc[:120]}...")
                    print()

            # Test 3: Search for low-level monsters
            print(f"🔍 Test 3: Search for 'undead skeleton zombie'")
            undead_results = db.search(settings.COLLECTION_NAMES['monsters'], "undead skeleton zombie", n_results=3)

            if undead_results and undead_results['documents'] and len(undead_results['documents'][0]) > 0:
                for i, (doc, meta) in enumerate(zip(
                    undead_results['documents'][0],
                    undead_results['metadatas'][0]
                ), 1):
                    monster_name = meta.get('name', 'Unknown')
                    cr = meta.get('challenge_rating', '?')

                    print(f"{i}. {monster_name} (CR {cr})")
                    print()
        else:
            print("   ⚠️  No monster data loaded yet")
            print("   Run: python initialize_rag.py --only monsters")
    except Exception as e:
        print(f"   ⚠️  Error testing monsters: {e}")

    # Test class search
    print("\n" + "="*70)
    print("⚔️  TESTING CLASS SEARCH")
    print("="*70)

    try:
        class_stats = db.get_collection_stats(settings.COLLECTION_NAMES['classes'])
        print(f"\n📊 Class Collection Stats:")
        print(f"   Total documents: {class_stats.get('total_documents', 0)}")

        if class_stats.get('total_documents', 0) > 0:
            # Test class search
            print(f"\n🔍 Test 1: Search for 'wizard'")
            wizard_results = db.search(settings.COLLECTION_NAMES['classes'], "wizard magic spellcasting", n_results=2)

            if wizard_results and wizard_results['documents'] and len(wizard_results['documents'][0]) > 0:
                for i, (doc, meta, distance) in enumerate(zip(
                    wizard_results['documents'][0],
                    wizard_results['metadatas'][0],
                    wizard_results['distances'][0]
                ), 1):
                    class_name = meta.get('name', 'Unknown')

                    print(f"{i}. {class_name}")
                    print(f"   Distance: {distance:.4f}")
                    print(f"   Preview: {doc[:120]}...")
                    print()

            print(f"🔍 Test 2: Search for 'fighter combat'")
            fighter_results = db.search(settings.COLLECTION_NAMES['classes'], "fighter combat warrior", n_results=2)

            if fighter_results and fighter_results['documents'] and len(fighter_results['documents'][0]) > 0:
                for i, (doc, meta) in enumerate(zip(
                    fighter_results['documents'][0],
                    fighter_results['metadatas'][0]
                ), 1):
                    class_name = meta.get('name', 'Unknown')
                    print(f"{i}. {class_name}")
                    print()
        else:
            print("   ⚠️  No class data loaded yet")
            print("   Run: python initialize_rag.py --only classes")
    except Exception as e:
        print(f"   ⚠️  Error testing classes: {e}")

    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)

if __name__ == '__main__':
    test_spell_search()
