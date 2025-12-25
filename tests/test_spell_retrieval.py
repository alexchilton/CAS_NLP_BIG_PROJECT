#!/usr/bin/env python3
"""
Test Spell Retrieval - Validates every spell can be found by name

This test iterates through all parsed spells and verifies:
1. Each spell can be found in the RAG system
2. The spell name is returned as the top result
3. The metadata contains the correct spell name

This ensures the name weighting and parsing is working correctly.
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.parsers.spell_parser import SpellParser
from dnd_rag_system.config import settings


class SpellRetrievalTest:
    """Test that all spells can be retrieved by name."""

    def __init__(self):
        self.db = ChromaDBManager()
        self.parser = SpellParser()
        self.passed = []
        self.failed = []
        self.warnings = []

    def run_test(self):
        """Run the complete spell retrieval test."""
        print("="*70)
        print("🧪 SPELL RETRIEVAL VALIDATION TEST")
        print("="*70)
        print()
        print("This test checks that every spell from both spells.txt and")
        print("all_spells.txt can be found in the RAG system.\n")

        # Step 1: Parse all spells from both sources
        print("📖 Step 1: Parsing spells from spells.txt and all_spells.txt...")
        parsed_spells = self.parser.parse()

        # Get unique spell names from parser (which combines both files)
        spell_names = set()
        for parsed_spell in parsed_spells:
            spell_name = parsed_spell.metadata.get('name', '')
            if spell_name:
                spell_names.add(spell_name)

        spell_names = sorted(spell_names)
        print(f"   Found {len(spell_names)} unique spells to test")
        print(f"   (Combined from spells.txt detailed descriptions + all_spells.txt class lists)\n")

        # Step 2: Get collection stats
        try:
            stats = self.db.get_collection_stats(settings.COLLECTION_NAMES['spells'])
            chunk_count = stats.get('total_documents', 0)
            print(f"📊 Step 2: RAG system has {chunk_count} spell chunks\n")
        except Exception as e:
            print(f"❌ Error accessing spell collection: {e}")
            return

        # Step 3: Test each spell
        print("🔍 Step 3: Testing spell retrieval...")
        print("-"*70)

        for i, spell_name in enumerate(spell_names, 1):
            # Progress indicator
            if i % 20 == 0:
                print(f"   Progress: {i}/{len(spell_names)} spells tested...")

            self._test_spell(spell_name)

        # Step 4: Print results
        self._print_results(len(spell_names))

    def _test_spell(self, spell_name: str):
        """
        Test that a specific spell can be found.

        Args:
            spell_name: Name of the spell to search for
        """
        try:
            # Search for the spell
            results = self.db.search(
                settings.COLLECTION_NAMES['spells'],
                spell_name,
                n_results=3
            )

            # Check if we got results
            if not results or not results['documents'] or len(results['documents'][0]) == 0:
                self.failed.append({
                    'name': spell_name,
                    'reason': 'No results returned',
                    'top_result': None
                })
                return

            # Get top result
            top_metadata = results['metadatas'][0][0]
            top_name = top_metadata.get('name', 'Unknown').upper()
            search_name = spell_name.upper()
            distance = results['distances'][0][0]

            # Check if top result matches
            if top_name == search_name:
                self.passed.append({
                    'name': spell_name,
                    'distance': distance
                })
            else:
                # Check if the correct spell is in top 3
                found_in_top_3 = False
                for j in range(min(3, len(results['metadatas'][0]))):
                    result_name = results['metadatas'][0][j].get('name', '').upper()
                    if result_name == search_name:
                        found_in_top_3 = True
                        self.warnings.append({
                            'name': spell_name,
                            'reason': f'Found at position {j+1}, not #1',
                            'top_result': top_metadata.get('name', 'Unknown'),
                            'distance': distance
                        })
                        break

                if not found_in_top_3:
                    self.failed.append({
                        'name': spell_name,
                        'reason': 'Not in top 3 results',
                        'top_result': top_metadata.get('name', 'Unknown'),
                        'distance': distance
                    })

        except Exception as e:
            self.failed.append({
                'name': spell_name,
                'reason': f'Error: {str(e)}',
                'top_result': None
            })

    def _print_results(self, total_spells: int):
        """Print test results summary."""
        print()
        print("="*70)
        print("📊 TEST RESULTS")
        print("="*70)
        print()

        # Summary stats
        pass_count = len(self.passed)
        warn_count = len(self.warnings)
        fail_count = len(self.failed)
        pass_rate = (pass_count / total_spells * 100) if total_spells > 0 else 0

        print(f"Total Spells Tested: {total_spells}")
        print(f"✅ Passed (Top Result): {pass_count} ({pass_rate:.1f}%)")
        print(f"⚠️  Warnings (Found in Top 3): {warn_count}")
        print(f"❌ Failed (Not Found): {fail_count}")
        print()

        # Show warnings if any
        if self.warnings:
            print("="*70)
            print("⚠️  WARNINGS - Spell Not Top Result")
            print("="*70)
            for warning in self.warnings[:10]:  # Show first 10
                print(f"\n🔸 {warning['name']}")
                print(f"   Reason: {warning['reason']}")
                print(f"   Top result was: {warning['top_result']}")
                print(f"   Distance: {warning['distance']:.4f}")

            if len(self.warnings) > 10:
                print(f"\n... and {len(self.warnings) - 10} more warnings")
            print()

        # Show failures if any
        if self.failed:
            print("="*70)
            print("❌ FAILURES - Spell Not Found or Retrieved Incorrectly")
            print("="*70)
            for failure in self.failed[:20]:  # Show first 20
                print(f"\n❌ {failure['name']}")
                print(f"   Reason: {failure['reason']}")
                if failure['top_result']:
                    print(f"   Top result was: {failure['top_result']}")
                    if 'distance' in failure:
                        print(f"   Distance: {failure['distance']:.4f}")

            if len(self.failed) > 20:
                print(f"\n... and {len(self.failed) - 20} more failures")
            print()

        # Final assessment
        print("="*70)
        if fail_count == 0 and warn_count == 0:
            print("🎉 PERFECT! All spells retrieved correctly!")
            print("   Every spell returns as the top result when searched.")
        elif fail_count == 0:
            print("✅ PASS! All spells found in database.")
            print(f"   {warn_count} spells not ranking #1 (but found in top 3)")
        else:
            print("⚠️  ISSUES FOUND!")
            print(f"   {fail_count} spells are missing or not retrieved correctly")
            print("   Consider:")
            print("   - Re-running: python initialize_rag.py --clear --only spells")
            print("   - Checking spells.txt for parsing issues")
        print("="*70)

        # Detailed statistics
        if self.passed:
            distances = [p['distance'] for p in self.passed]
            avg_distance = sum(distances) / len(distances)
            print()
            print("📈 Distance Statistics (for passed spells):")
            print(f"   Average: {avg_distance:.4f}")
            print(f"   Best: {min(distances):.4f}")
            print(f"   Worst: {max(distances):.4f}")
            print()
            print("   Note: Lower distance = better match")
            print("   Distance < 0.5 is excellent for exact name matches")


def main():
    """Run the spell retrieval test."""
    try:
        test = SpellRetrievalTest()
        test.run_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
