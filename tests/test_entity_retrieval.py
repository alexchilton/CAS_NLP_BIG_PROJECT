#!/usr/bin/env python3
"""
Test Entity Retrieval - Validates all entities can be found by name

This test validates that every entity (spell, monster, class, race) can be
retrieved from the RAG system:

1. Spells - from spells.txt + all_spells.txt
2. Monsters - from extracted_monsters.txt
3. Classes - from extracted_classes.txt
4. Races - from Player's Handbook PDF

For each entity, verifies:
- Entity can be found in the RAG system
- Entity name is returned as the top result
- Metadata contains the correct entity name

This ensures name weighting and parsing work correctly across all collections.
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Set

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.parsers.spell_parser import SpellParser
from dnd_rag_system.config import settings


class EntityRetrievalTest:
    """Test that all entities can be retrieved by name."""

    def __init__(self):
        self.db = ChromaDBManager()
        self.results_by_collection = {}

    def run_all_tests(self):
        """Run retrieval tests for all collections."""
        print("="*70)
        print("🧪 COMPREHENSIVE ENTITY RETRIEVAL VALIDATION")
        print("="*70)
        print()
        print("Testing all 4 collections: Spells, Monsters, Classes, Races")
        print("Validates that every entity can be found by name.\n")

        # Test each collection
        self.test_spells()
        self.test_monsters()
        self.test_classes()
        self.test_races()

        # Print overall summary
        self._print_overall_summary()

    def test_spells(self):
        """Test spell retrieval."""
        print("="*70)
        print("📚 TESTING SPELLS")
        print("="*70)
        print()

        # Parse spells from both sources
        parser = SpellParser()
        parsed_spells = parser.parse()

        # Get unique spell names
        spell_names = set()
        for parsed_spell in parsed_spells:
            spell_name = parsed_spell.metadata.get('name', '')
            if spell_name:
                spell_names.add(spell_name)

        spell_names = sorted(spell_names)
        print(f"Found {len(spell_names)} unique spells to test")
        print(f"(from spells.txt + all_spells.txt)\n")

        # Test each spell
        results = self._test_collection(
            spell_names,
            settings.COLLECTION_NAMES['spells'],
            'Spell'
        )

        self.results_by_collection['spells'] = results
        self._print_collection_results(results, 'SPELLS')

    def test_monsters(self):
        """Test monster retrieval."""
        print("\n" + "="*70)
        print("👹 TESTING MONSTERS")
        print("="*70)
        print()

        # Parse monsters from file
        monster_names = self._extract_monster_names()
        print(f"Found {len(monster_names)} monsters to test")
        print(f"(from extracted_monsters.txt)\n")

        # Test each monster
        results = self._test_collection(
            monster_names,
            settings.COLLECTION_NAMES['monsters'],
            'Monster'
        )

        self.results_by_collection['monsters'] = results
        self._print_collection_results(results, 'MONSTERS')

    def test_classes(self):
        """Test class retrieval."""
        print("\n" + "="*70)
        print("⚔️  TESTING CLASSES")
        print("="*70)
        print()

        # Parse classes from file
        class_names = self._extract_class_names()
        print(f"Found {len(class_names)} classes to test")
        print(f"(from extracted_classes.txt)\n")

        # Test each class
        results = self._test_collection(
            class_names,
            settings.COLLECTION_NAMES['classes'],
            'Class'
        )

        self.results_by_collection['classes'] = results
        self._print_collection_results(results, 'CLASSES')

    def test_races(self):
        """Test race retrieval."""
        print("\n" + "="*70)
        print("🧝 TESTING RACES")
        print("="*70)
        print()

        # Use standard D&D races
        race_names = [
            'Dragonborn', 'Dwarf', 'Elf', 'Gnome',
            'Half-Elf', 'Halfling', 'Half-Orc', 'Human', 'Tiefling'
        ]
        print(f"Found {len(race_names)} races to test")
        print(f"(from Player's Handbook PDF)\n")

        # Test each race
        results = self._test_collection(
            race_names,
            settings.COLLECTION_NAMES['races'],
            'Race'
        )

        self.results_by_collection['races'] = results
        self._print_collection_results(results, 'RACES')

    def _test_collection(self, entity_names: List[str], collection_name: str, entity_type: str) -> Dict:
        """
        Test retrieval for a collection of entities.

        Args:
            entity_names: List of entity names to test
            collection_name: ChromaDB collection name
            entity_type: Type of entity (for logging)

        Returns:
            Dictionary with test results
        """
        passed = []
        warnings = []
        failed = []

        for i, entity_name in enumerate(entity_names, 1):
            # Progress indicator
            if i % 20 == 0:
                print(f"   Progress: {i}/{len(entity_names)} {entity_type.lower()}s tested...")

            try:
                # Search for the entity
                results = self.db.search(collection_name, entity_name, n_results=3)

                # Check if we got results
                if not results or not results['documents'] or len(results['documents'][0]) == 0:
                    failed.append({
                        'name': entity_name,
                        'reason': 'No results returned',
                        'top_result': None
                    })
                    continue

                # Get top result
                top_metadata = results['metadatas'][0][0]
                top_name = top_metadata.get('name', 'Unknown').upper()
                search_name = entity_name.upper()
                distance = results['distances'][0][0]

                # Check if top result matches
                if top_name == search_name:
                    passed.append({
                        'name': entity_name,
                        'distance': distance
                    })
                else:
                    # Check if correct entity is in top 3
                    found_in_top_3 = False
                    for j in range(min(3, len(results['metadatas'][0]))):
                        result_name = results['metadatas'][0][j].get('name', '').upper()
                        if result_name == search_name:
                            found_in_top_3 = True
                            warnings.append({
                                'name': entity_name,
                                'reason': f'Found at position {j+1}, not #1',
                                'top_result': top_metadata.get('name', 'Unknown'),
                                'distance': distance
                            })
                            break

                    if not found_in_top_3:
                        failed.append({
                            'name': entity_name,
                            'reason': 'Not in top 3 results',
                            'top_result': top_metadata.get('name', 'Unknown'),
                            'distance': distance
                        })

            except Exception as e:
                failed.append({
                    'name': entity_name,
                    'reason': f'Error: {str(e)}',
                    'top_result': None
                })

        return {
            'total': len(entity_names),
            'passed': passed,
            'warnings': warnings,
            'failed': failed
        }

    def _extract_monster_names(self) -> List[str]:
        """Extract monster names from extracted_monsters.txt."""
        monster_file = Path(settings.EXTRACTED_MONSTERS_TXT)
        if not monster_file.exists():
            print(f"Warning: {monster_file} not found")
            return []

        with open(monster_file, 'r', encoding='utf-8') as f:
            text = f.read()

        # Split by double newlines to get monster blocks
        blocks = text.split('\n\n')
        monster_names = []

        for block in blocks:
            lines = block.strip().split('\n')
            if lines:
                # First line is typically the monster name
                name = lines[0].strip()
                # Filter out empty lines and non-monster entries
                if name and not name.startswith('#') and len(name) > 1:
                    monster_names.append(name)

        return sorted(set(monster_names))

    def _extract_class_names(self) -> List[str]:
        """Extract class names from extracted_classes.txt."""
        class_file = Path(settings.EXTRACTED_CLASSES_TXT)
        if not class_file.exists():
            print(f"Warning: {class_file} not found")
            return []

        with open(class_file, 'r', encoding='utf-8') as f:
            text = f.read()

        # Use the standard D&D class list
        standard_classes = settings.DND_CLASSES
        found_classes = []

        # Check which classes are present in the file
        for class_name in standard_classes:
            if class_name in text or class_name.upper() in text:
                found_classes.append(class_name)

        return sorted(found_classes)

    def _print_collection_results(self, results: Dict, collection_name: str):
        """Print results for a single collection."""
        total = results['total']
        passed = len(results['passed'])
        warnings = len(results['warnings'])
        failed = len(results['failed'])
        pass_rate = (passed / total * 100) if total > 0 else 0

        print()
        print(f"📊 {collection_name} Results:")
        print(f"   Total: {total}")
        print(f"   ✅ Passed: {passed} ({pass_rate:.1f}%)")
        print(f"   ⚠️  Warnings: {warnings}")
        print(f"   ❌ Failed: {failed}")

        # Show first few failures
        if results['failed']:
            print(f"\n   Failed entities (showing first 5):")
            for fail in results['failed'][:5]:
                print(f"      ❌ {fail['name']}: {fail['reason']}")
                if fail['top_result']:
                    print(f"         (Top result: {fail['top_result']})")

    def _print_overall_summary(self):
        """Print overall summary across all collections."""
        print("\n" + "="*70)
        print("📊 OVERALL SUMMARY")
        print("="*70)
        print()

        total_entities = 0
        total_passed = 0
        total_warnings = 0
        total_failed = 0

        for collection, results in self.results_by_collection.items():
            total_entities += results['total']
            total_passed += len(results['passed'])
            total_warnings += len(results['warnings'])
            total_failed += len(results['failed'])

        overall_pass_rate = (total_passed / total_entities * 100) if total_entities > 0 else 0

        print(f"Total Entities Tested: {total_entities}")
        print(f"✅ Passed: {total_passed} ({overall_pass_rate:.1f}%)")
        print(f"⚠️  Warnings: {total_warnings}")
        print(f"❌ Failed: {total_failed}")
        print()

        # Breakdown by collection
        print("Breakdown by Collection:")
        for collection, results in self.results_by_collection.items():
            passed = len(results['passed'])
            total = results['total']
            rate = (passed / total * 100) if total > 0 else 0
            print(f"   {collection.capitalize()}: {passed}/{total} ({rate:.1f}%)")

        print()
        print("="*70)

        if total_failed == 0 and total_warnings == 0:
            print("🎉 PERFECT! All entities retrieved correctly!")
        elif total_failed == 0:
            print("✅ GOOD! All entities found (some not ranking #1)")
        else:
            print("⚠️  ISSUES FOUND - Some entities missing or incorrect")
            print(f"   Run: python initialize_rag.py --clear")

        print("="*70)


def main():
    """Run the entity retrieval test."""
    try:
        test = EntityRetrievalTest()
        test.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
