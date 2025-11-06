#!/usr/bin/env python3
"""
Comprehensive Test Suite for D&D RAG System

Tests all four collections: spells, monsters, classes, and races
Validates name weighting, semantic search, and metadata filtering
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings


class RAGTestSuite:
    """Comprehensive test suite for D&D RAG system"""

    def __init__(self):
        self.db = ChromaDBManager()
        self.passed = 0
        self.failed = 0
        self.results = []

    def assert_test(self, test_name: str, condition: bool, message: str = ""):
        """Record test result"""
        if condition:
            self.passed += 1
            self.results.append(f"✅ PASS: {test_name}")
            if message:
                self.results.append(f"   {message}")
        else:
            self.failed += 1
            self.results.append(f"❌ FAIL: {test_name}")
            if message:
                self.results.append(f"   {message}")

    def run_all_tests(self):
        """Run all test suites"""
        print("="*70)
        print("🧪 D&D RAG SYSTEM - COMPREHENSIVE TEST SUITE")
        print("="*70)

        # Check collections exist
        print("\n📊 CHECKING COLLECTIONS...")
        self.test_collections_exist()

        # Test each collection
        print("\n📚 TESTING SPELLS...")
        self.test_spell_collection()

        print("\n👹 TESTING MONSTERS...")
        self.test_monster_collection()

        print("\n⚔️  TESTING CLASSES...")
        self.test_class_collection()

        print("\n🧝 TESTING RACES...")
        self.test_race_collection()

        # Cross-collection tests
        print("\n🔀 TESTING CROSS-COLLECTION SEARCH...")
        self.test_cross_collection()

        # Print results
        self.print_results()

    def test_collections_exist(self):
        """Test that all collections are initialized with data"""
        for name, collection_name in settings.COLLECTION_NAMES.items():
            try:
                stats = self.db.get_collection_stats(collection_name)
                count = stats.get('total_documents', 0)

                self.assert_test(
                    f"Collection '{name}' exists",
                    count > 0,
                    f"Found {count} documents"
                )
            except Exception as e:
                self.assert_test(
                    f"Collection '{name}' exists",
                    False,
                    f"Error: {e}"
                )

    def test_spell_collection(self):
        """Test spell search functionality"""

        # Test 1: Exact name match should rank first
        print("  Test 1: Exact name match (fireball)")
        results = self.db.search(settings.COLLECTION_NAMES['spells'], "fireball", n_results=5)

        if results and results['documents'] and len(results['documents'][0]) > 0:
            top_result = results['metadatas'][0][0]
            top_name = top_result.get('name', '').lower()

            self.assert_test(
                "Spell: 'fireball' search returns Fireball first",
                'fireball' in top_name,
                f"Top result: {top_result.get('name', 'Unknown')}"
            )
        else:
            self.assert_test(
                "Spell: 'fireball' search returns results",
                False,
                "No results found"
            )

        # Test 2: Semantic search
        print("  Test 2: Semantic search (healing magic)")
        results = self.db.search(settings.COLLECTION_NAMES['spells'], "healing restore hit points", n_results=3)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            found_healing = any('cure' in meta.get('name', '').lower() or
                              'heal' in meta.get('name', '').lower()
                              for meta in results['metadatas'][0])

            self.assert_test(
                "Spell: Semantic search finds healing spells",
                found_healing,
                f"Found: {[m.get('name') for m in results['metadatas'][0][:3]]}"
            )
        else:
            self.assert_test(
                "Spell: Semantic search returns results",
                False,
                "No results found"
            )

        # Test 3: Level filtering via metadata
        print("  Test 3: Spell metadata (level, school)")
        results = self.db.search(settings.COLLECTION_NAMES['spells'], "magic missile", n_results=1)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            meta = results['metadatas'][0][0]
            has_level = 'level' in meta
            has_school = 'school' in meta

            self.assert_test(
                "Spell: Metadata includes level and school",
                has_level and has_school,
                f"Level: {meta.get('level', 'N/A')}, School: {meta.get('school', 'N/A')}"
            )
        else:
            self.assert_test(
                "Spell: Has metadata",
                False,
                "No results found"
            )

        # Test 4: Multiple chunk types
        print("  Test 4: Multiple chunk types per spell")
        results = self.db.search(settings.COLLECTION_NAMES['spells'], "fireball", n_results=10)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            chunk_types = set(meta.get('chunk_type', '') for meta in results['metadatas'][0])

            self.assert_test(
                "Spell: Multiple chunk types exist",
                len(chunk_types) > 1,
                f"Chunk types: {chunk_types}"
            )
        else:
            self.assert_test(
                "Spell: Has multiple chunks",
                False,
                "Not enough results"
            )

    def test_monster_collection(self):
        """Test monster search functionality"""

        # Test 1: Exact name match
        print("  Test 1: Exact name match (goblin)")
        results = self.db.search(settings.COLLECTION_NAMES['monsters'], "goblin", n_results=5)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            top_name = results['metadatas'][0][0].get('name', '').lower()

            self.assert_test(
                "Monster: 'goblin' search returns Goblin first",
                'goblin' in top_name,
                f"Top result: {results['metadatas'][0][0].get('name', 'Unknown')}"
            )
        else:
            self.assert_test(
                "Monster: Search returns results",
                False,
                "No results found"
            )

        # Test 2: Type search
        print("  Test 2: Search by type (dragon)")
        results = self.db.search(settings.COLLECTION_NAMES['monsters'], "dragon flying fire", n_results=5)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            found_dragon = any('dragon' in meta.get('name', '').lower()
                              for meta in results['metadatas'][0])

            self.assert_test(
                "Monster: Type search finds dragons",
                found_dragon,
                f"Found: {[m.get('name') for m in results['metadatas'][0][:3]]}"
            )
        else:
            self.assert_test(
                "Monster: Type search returns results",
                False,
                "No results found"
            )

        # Test 3: CR metadata
        print("  Test 3: Challenge rating metadata")
        results = self.db.search(settings.COLLECTION_NAMES['monsters'], "goblin", n_results=1)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            meta = results['metadatas'][0][0]
            has_cr = 'challenge_rating' in meta

            self.assert_test(
                "Monster: Metadata includes challenge rating",
                has_cr,
                f"CR: {meta.get('challenge_rating', 'N/A')}"
            )
        else:
            self.assert_test(
                "Monster: Has metadata",
                False,
                "No results found"
            )

        # Test 4: Monster type metadata
        print("  Test 4: Monster type extraction")
        results = self.db.search(settings.COLLECTION_NAMES['monsters'], "dragon", n_results=3)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            has_type_info = any(meta.get('monster_type', '') != ''
                               for meta in results['metadatas'][0])

            self.assert_test(
                "Monster: Type information extracted",
                has_type_info,
                f"Sample types: {[m.get('monster_type', 'N/A') for m in results['metadatas'][0][:2]]}"
            )
        else:
            self.assert_test(
                "Monster: Has type metadata",
                False,
                "No results found"
            )

    def test_class_collection(self):
        """Test class search functionality"""

        # Test 1: Exact name match
        print("  Test 1: Exact name match (wizard)")
        results = self.db.search(settings.COLLECTION_NAMES['classes'], "wizard", n_results=5)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            top_name = results['metadatas'][0][0].get('name', '').lower()

            self.assert_test(
                "Class: 'wizard' search returns Wizard first",
                'wizard' in top_name,
                f"Top result: {results['metadatas'][0][0].get('name', 'Unknown')}"
            )
        else:
            self.assert_test(
                "Class: Search returns results",
                False,
                "No results found"
            )

        # Test 2: Role-based search
        print("  Test 2: Role-based search (warrior combat)")
        results = self.db.search(settings.COLLECTION_NAMES['classes'], "warrior combat fighting", n_results=3)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            found_fighter = any('fighter' in meta.get('name', '').lower() or
                               'barbarian' in meta.get('name', '').lower()
                               for meta in results['metadatas'][0])

            self.assert_test(
                "Class: Role search finds martial classes",
                found_fighter,
                f"Found: {[m.get('name') for m in results['metadatas'][0][:3]]}"
            )
        else:
            self.assert_test(
                "Class: Role search returns results",
                False,
                "No results found"
            )

        # Test 3: Class name weighting
        print("  Test 3: Name weighting check")
        results = self.db.search(settings.COLLECTION_NAMES['classes'], "rogue", n_results=3)

        if results and results['documents'] and len(results['documents'][0]) > 0:
            top_doc = results['documents'][0][0]
            # Check if CLASS: prefix exists (indicates weighting)
            has_weighting = 'CLASS:' in top_doc

            self.assert_test(
                "Class: Name weighting implemented",
                has_weighting,
                "Found CLASS: prefix in document"
            )
        else:
            self.assert_test(
                "Class: Can check weighting",
                False,
                "No results found"
            )

    def test_race_collection(self):
        """Test race search functionality"""

        # Test 1: Exact name match
        print("  Test 1: Exact name match (elf)")
        results = self.db.search(settings.COLLECTION_NAMES['races'], "elf", n_results=5)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            top_name = results['metadatas'][0][0].get('name', '').lower()

            self.assert_test(
                "Race: 'elf' search returns Elf first",
                'elf' in top_name,
                f"Top result: {results['metadatas'][0][0].get('name', 'Unknown')}"
            )
        else:
            self.assert_test(
                "Race: Search returns results",
                False,
                "No results found"
            )

        # Test 2: Trait-based search
        print("  Test 2: Trait search (darkvision)")
        results = self.db.search(settings.COLLECTION_NAMES['races'], "darkvision dark sight", n_results=5)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            found_darkvision = any(meta.get('darkvision', 0) > 0
                                  for meta in results['metadatas'][0])

            self.assert_test(
                "Race: Trait search finds races with darkvision",
                found_darkvision,
                f"Races: {[f\"{m.get('name')} ({m.get('darkvision')}ft)\" for m in results['metadatas'][0][:3] if m.get('darkvision', 0) > 0]}"
            )
        else:
            self.assert_test(
                "Race: Trait search returns results",
                False,
                "No results found"
            )

        # Test 3: Metadata extraction
        print("  Test 3: Metadata (ability bonuses, size, speed)")
        results = self.db.search(settings.COLLECTION_NAMES['races'], "dwarf", n_results=1)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            meta = results['metadatas'][0][0]
            has_metadata = any([
                meta.get('ability_increases'),
                meta.get('size'),
                meta.get('speed')
            ])

            self.assert_test(
                "Race: Has detailed metadata",
                has_metadata,
                f"Size: {meta.get('size', 'N/A')}, Speed: {meta.get('speed', 'N/A')[:30]}"
            )
        else:
            self.assert_test(
                "Race: Has metadata",
                False,
                "No results found"
            )

        # Test 4: Multiple chunk types
        print("  Test 4: Multiple chunk types (description + traits)")
        results = self.db.search(settings.COLLECTION_NAMES['races'], "elf", n_results=10)

        if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
            chunk_types = set(meta.get('chunk_type', '') for meta in results['metadatas'][0])

            self.assert_test(
                "Race: Multiple chunk types exist",
                len(chunk_types) > 1,
                f"Chunk types: {chunk_types}"
            )
        else:
            self.assert_test(
                "Race: Has multiple chunks",
                False,
                "Not enough results"
            )

    def test_cross_collection(self):
        """Test cross-collection search functionality"""

        print("  Test 1: Search all collections for 'dragon'")

        # Search each collection
        results = {}
        for name, collection_name in settings.COLLECTION_NAMES.items():
            try:
                search_results = self.db.search(collection_name, "dragon", n_results=2)
                if search_results and search_results['documents'] and len(search_results['documents'][0]) > 0:
                    results[name] = len(search_results['documents'][0])
                else:
                    results[name] = 0
            except Exception as e:
                results[name] = 0

        # Should find dragon in multiple collections
        collections_with_results = sum(1 for count in results.values() if count > 0)

        self.assert_test(
            "Cross-collection: 'dragon' found in multiple collections",
            collections_with_results >= 2,
            f"Found in {collections_with_results} collections: {results}"
        )

        print("  Test 2: Distinct results per collection")

        # Each collection should return different content types
        content_types = set()
        for name, collection_name in settings.COLLECTION_NAMES.items():
            try:
                search_results = self.db.search(collection_name, "fire", n_results=1)
                if search_results and search_results['metadatas'] and len(search_results['metadatas'][0]) > 0:
                    content_type = search_results['metadatas'][0][0].get('content_type', '')
                    if content_type:
                        content_types.add(content_type)
            except Exception:
                pass

        self.assert_test(
            "Cross-collection: Different content types returned",
            len(content_types) >= 3,
            f"Content types found: {content_types}"
        )

    def print_results(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 TEST RESULTS SUMMARY")
        print("="*70)

        # Print all test results
        for result in self.results:
            print(result)

        # Summary stats
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print("\n" + "="*70)
        print(f"✅ PASSED: {self.passed}/{total} ({pass_rate:.1f}%)")
        print(f"❌ FAILED: {self.failed}/{total}")
        print("="*70)

        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("Your D&D RAG system is fully operational.")
        else:
            print(f"\n⚠️  {self.failed} tests failed.")
            print("Please review the failed tests above.")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if self.failed > 0:
            print("  - Reload collections: python initialize_rag.py --clear")
            print("  - Check data files exist in project root")
        else:
            print("  - System is ready for production use")
            print("  - Try: python run_gm_dialogue.py")


def main():
    """Run the test suite"""
    try:
        suite = RAGTestSuite()
        suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error running tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
