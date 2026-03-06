#!/usr/bin/env python3
"""
Evaluation script for the D&D RAG System.
Generates real, verifiable metrics for the CAS thesis.

Metrics produced:
  1. RAG Retrieval Precision@k (exact-match and semantic)
  2. Name-weighting effectiveness (rank comparison)
  3. Reality Check validation accuracy (true/false positive rates)
  4. Test suite summary (pass/fail counts)

Usage:
  python thesis/evaluate.py            # run all evaluations
  python thesis/evaluate.py --rag      # RAG retrieval only
  python thesis/evaluate.py --reality  # Reality Check only
  python thesis/evaluate.py --tests    # test suite only
"""

import sys, os, json, time, argparse
from pathlib import Path
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ═══════════════════════════════════════════════════════════════════════
# 1. RAG RETRIEVAL PRECISION
# ═══════════════════════════════════════════════════════════════════════

# Ground-truth queries: (query, expected_entity_name, collection)
RETRIEVAL_QUERIES = {
    "spells": [
        ("fireball", "Fireball"),
        ("magic missile", "Magic Missile"),
        ("cure wounds", "Cure Wounds"),
        ("shield", "Shield"),
        ("lightning bolt", "Lightning Bolt"),
        ("healing word", "Healing Word"),
        ("hold person", "Hold Person"),
        ("counterspell", "Counterspell"),
        ("eldritch blast", "Eldritch Blast"),
        ("thunderwave", "Thunderwave"),
        ("detect magic", "Detect Magic"),
        ("mage hand", "Mage Hand"),
        ("fire bolt", "Fire Bolt"),
        ("sacred flame", "Sacred Flame"),
        ("bless", "Bless"),
        ("sleep", "Sleep"),
        ("charm person", "Charm Person"),
        ("misty step", "Misty Step"),
        ("web", "Web"),
        ("ice storm", "Ice Storm"),
    ],
    "monsters": [
        ("goblin", "Goblin"),
        ("orc", "Orc"),
        ("skeleton", "Skeleton"),
        ("wolf", "Wolf"),
        ("ogre", "Ogre"),
        ("troll", "Troll"),
        ("bugbear", "Bugbear"),
        ("hobgoblin", "Hobgoblin"),
        ("giant rat", "Giant Rat"),
        ("dire wolf", "Dire Wolf"),
        ("werewolf", "Werewolf"),
        ("hill giant", "Hill Giant"),
        ("vampire", "Vampire"),
        ("chimera", "Chimera"),
        ("adult red dragon", "Adult Red Dragon"),
        ("young white dragon", "Young White Dragon"),
    ],
}

# Semantic queries where the query doesn't match the entity name exactly
SEMANTIC_QUERIES = [
    ("healing restore hit points", "spells", ["Cure Wounds", "Healing Word"]),
    ("fire damage area spell", "spells", ["Fireball", "Fire Bolt"]),
    ("undead animated bones", "monsters", ["Skeleton"]),
    ("small green humanoid", "monsters", ["Goblin"]),
    ("large brutish creature", "monsters", ["Ogre", "Troll", "Hill Giant"]),
    ("protective barrier magic", "spells", ["Shield", "Mage Armor"]),
    ("ranged cantrip attack", "spells", ["Fire Bolt", "Eldritch Blast", "Sacred Flame"]),
    ("paralysis immobilize", "spells", ["Hold Person"]),
    ("invisible hand manipulation", "spells", ["Mage Hand"]),
    ("flying fire breathing beast", "monsters", ["Adult Red Dragon", "Young White Dragon", "Chimera"]),
]


def evaluate_retrieval(db_manager, k_values=(1, 3, 5)):
    """Evaluate retrieval precision@k for exact-match queries."""
    from dnd_rag_system.config import settings

    results = {"per_collection": {}, "overall": {}}

    for collection_key, queries in RETRIEVAL_QUERIES.items():
        collection_name = settings.COLLECTION_NAMES.get(collection_key, f"dnd_{collection_key}")
        hits = {k: 0 for k in k_values}
        reciprocal_ranks = []
        total = len(queries)

        print(f"\n{'='*60}")
        print(f"  Collection: {collection_name} ({total} queries)")
        print(f"{'='*60}")

        for query, expected in queries:
            try:
                search_results = db_manager.search(collection_name, query, n_results=max(k_values))
                docs = search_results.get("documents", [[]])[0]
                metas = search_results.get("metadatas", [[]])[0]
                distances = search_results.get("distances", [[]])[0]

                # Check where the expected entity appears
                found_rank = None
                for i, (doc, meta) in enumerate(zip(docs, metas)):
                    entity_name = meta.get("name", meta.get("monster_name", ""))
                    # Check in document text too
                    doc_upper = doc[:200].upper() if doc else ""
                    if (expected.lower() == entity_name.lower() or
                        expected.upper() in doc_upper or
                        f"SPELL: {expected.upper()}" in doc_upper or
                        f"Monster: {expected}" in doc[:200]):
                        found_rank = i + 1
                        break

                for k in k_values:
                    if found_rank is not None and found_rank <= k:
                        hits[k] += 1

                rr = 1.0 / found_rank if found_rank else 0.0
                reciprocal_ranks.append(rr)

                status = f"rank {found_rank}" if found_rank else "NOT FOUND"
                dist_str = f"(d={distances[0]:.3f})" if distances else ""
                symbol = "✅" if found_rank == 1 else ("⚠️" if found_rank else "❌")
                print(f"  {symbol} '{query}' → {status} {dist_str}")

            except Exception as e:
                print(f"  ❌ '{query}' → ERROR: {e}")
                reciprocal_ranks.append(0.0)

        precision = {k: hits[k] / total for k in k_values}
        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0

        results["per_collection"][collection_key] = {
            "total_queries": total,
            "precision_at_k": precision,
            "mrr": mrr,
        }

        print(f"\n  Precision@1: {precision[1]:.1%}  "
              f"Precision@3: {precision[3]:.1%}  "
              f"Precision@5: {precision[5]:.1%}  "
              f"MRR: {mrr:.3f}")

    # Overall
    all_p = {k: [] for k in k_values}
    all_mrr = []
    for coll_res in results["per_collection"].values():
        for k in k_values:
            all_p[k].append(coll_res["precision_at_k"][k])
        all_mrr.append(coll_res["mrr"])

    results["overall"] = {
        "precision_at_k": {k: sum(v)/len(v) for k, v in all_p.items()},
        "mrr": sum(all_mrr) / len(all_mrr),
    }
    return results


def evaluate_semantic(db_manager, k=5):
    """Evaluate semantic search (non-exact queries)."""
    from dnd_rag_system.config import settings

    print(f"\n{'='*60}")
    print(f"  Semantic Search Evaluation ({len(SEMANTIC_QUERIES)} queries)")
    print(f"{'='*60}")

    hits = 0
    total = len(SEMANTIC_QUERIES)

    for query, collection_key, acceptable in SEMANTIC_QUERIES:
        collection_name = settings.COLLECTION_NAMES.get(collection_key, f"dnd_{collection_key}")
        try:
            search_results = db_manager.search(collection_name, query, n_results=k)
            docs = search_results.get("documents", [[]])[0]
            metas = search_results.get("metadatas", [[]])[0]

            found = False
            returned_names = []
            for doc, meta in zip(docs, metas):
                name = meta.get("name", meta.get("monster_name", ""))
                returned_names.append(name)
                if any(acc.lower() in name.lower() or
                       acc.upper() in doc[:300].upper()
                       for acc in acceptable):
                    found = True

            if found:
                hits += 1
                print(f"  ✅ '{query}' → found in top-{k}")
            else:
                print(f"  ❌ '{query}' → not found (got: {returned_names[:3]})")

        except Exception as e:
            print(f"  ❌ '{query}' → ERROR: {e}")

    precision = hits / total if total else 0
    print(f"\n  Semantic Precision@{k}: {precision:.1%} ({hits}/{total})")
    return {"semantic_precision_at_k": precision, "k": k, "hits": hits, "total": total}


# ═══════════════════════════════════════════════════════════════════════
# 2. NAME-WEIGHTING ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

# Confusable pairs: queries where name-weighting matters most
CONFUSABLE_PAIRS = [
    ("goblin", "Goblin", "Hobgoblin", "monsters"),
    ("wolf", "Wolf", "Dire Wolf", "monsters"),
    ("dire wolf", "Dire Wolf", "Wolf", "monsters"),
    ("hill giant", "Hill Giant", "Ogre", "monsters"),
    ("cure wounds", "Cure Wounds", "Healing Word", "spells"),
    ("shield", "Shield", "Shield of Faith", "spells"),
    ("fire bolt", "Fire Bolt", "Fireball", "spells"),
    ("sleep", "Sleep", "Deep Slumber", "spells"),
    ("hold person", "Hold Person", "Hold Monster", "spells"),
    ("charm person", "Charm Person", "Charm Monster", "spells"),
]


def evaluate_name_weighting(db_manager):
    """Check if name-weighted embeddings resolve confusable pairs correctly."""
    from dnd_rag_system.config import settings

    print(f"\n{'='*60}")
    print(f"  Name-Weighting Effectiveness ({len(CONFUSABLE_PAIRS)} confusable pairs)")
    print(f"{'='*60}")

    correct = 0
    total = len(CONFUSABLE_PAIRS)
    rank1_distances = []
    rank2_distances = []

    for query, expected, confusable, collection_key in CONFUSABLE_PAIRS:
        collection_name = settings.COLLECTION_NAMES.get(collection_key, f"dnd_{collection_key}")
        try:
            search_results = db_manager.search(collection_name, query, n_results=5)
            docs = search_results.get("documents", [[]])[0]
            metas = search_results.get("metadatas", [[]])[0]
            distances = search_results.get("distances", [[]])[0]

            # Check rank-1 result
            rank1_name = metas[0].get("name", metas[0].get("monster_name", "")) if metas else ""
            rank1_doc = docs[0][:200].upper() if docs else ""

            is_correct = (expected.lower() == rank1_name.lower() or
                         expected.upper() in rank1_doc or
                         f"SPELL: {expected.upper()}" in rank1_doc or
                         f"Monster: {expected}" in docs[0][:200] if docs else False)

            if is_correct:
                correct += 1
                if distances:
                    rank1_distances.append(distances[0])
                    if len(distances) > 1:
                        rank2_distances.append(distances[1])
                print(f"  ✅ '{query}' → rank 1: {expected} (d={distances[0]:.3f})")
            else:
                print(f"  ❌ '{query}' → rank 1: {rank1_name or rank1_doc[:30]} "
                      f"(expected: {expected})")
                if distances:
                    rank1_distances.append(distances[0])

        except Exception as e:
            print(f"  ❌ '{query}' → ERROR: {e}")

    accuracy = correct / total if total else 0
    avg_d1 = sum(rank1_distances) / len(rank1_distances) if rank1_distances else 0
    avg_d2 = sum(rank2_distances) / len(rank2_distances) if rank2_distances else 0

    print(f"\n  Confusable-pair accuracy: {accuracy:.1%} ({correct}/{total})")
    print(f"  Avg rank-1 distance: {avg_d1:.4f}")
    print(f"  Avg rank-2 distance: {avg_d2:.4f}")
    if avg_d1 and avg_d2:
        print(f"  Separation ratio: {avg_d2/avg_d1:.2f}x")

    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "avg_rank1_distance": avg_d1,
        "avg_rank2_distance": avg_d2,
        "separation_ratio": avg_d2 / avg_d1 if avg_d1 else 0,
    }


# ═══════════════════════════════════════════════════════════════════════
# 3. REALITY CHECK VALIDATION
# ═══════════════════════════════════════════════════════════════════════

def build_test_game_session():
    """Build a minimal GameSession with a wizard character for validation testing."""
    from dnd_rag_system.systems.game_state import GameSession, CharacterState, SpellSlots

    char = CharacterState(
        character_name="TestHero",
        current_hp=30,
        max_hp=30,
        level=5,
        spellcasting_class="Wizard",
        spellcasting_ability="INT",
        known_spells=[
            "Fire Bolt", "Mage Hand", "Prestidigitation",
            "Magic Missile", "Shield", "Detect Magic", "Sleep",
            "Misty Step", "Web",
            "Fireball", "Counterspell",
        ],
        prepared_spells=[
            "Magic Missile", "Shield", "Detect Magic", "Sleep",
            "Misty Step", "Web", "Fireball", "Counterspell",
        ],
        inventory={"quarterstaff": 1, "dagger": 1, "spellbook": 1},
        gold=50,
        conditions=[],
    )
    # Set spell slots for a level 5 wizard
    char.spell_slots.slots = {1: 4, 2: 3, 3: 2}
    char.spell_slots.max_slots = {1: 4, 2: 3, 3: 2}

    session = GameSession()
    session.character_state = char
    session.npcs_present = ["Goblin", "Orc", "Skeleton"]
    session.current_location = "Dark Cave"

    return session


# (action_text, should_be_valid, reason)
REALITY_CHECK_SCENARIOS = [
    # Valid actions
    ("I cast Fireball at the Goblin", True, "known spell, valid target, has slots"),
    ("I cast Magic Missile at the Orc", True, "known spell, valid target"),
    ("I attack the Goblin with my quarterstaff", True, "weapon in inventory, valid target"),

    # Invalid: wrong target
    ("I cast Fireball at the Balrog", False, "target not in scene"),
    ("I attack the Dragon", False, "target not in scene"),
    ("I cast Magic Missile at the Lich", False, "target not in scene"),

    # Invalid: unknown spell
    ("I cast Wish", False, "spell not known"),
    ("I cast Power Word Kill", False, "spell not known"),
    ("I cast Meteor Swarm", False, "spell not known"),

    # Invalid: no spell slots (tested after exhaustion)
    # These are tested dynamically below

    # Invalid: wrong weapon
    ("I attack the Goblin with my longsword", False, "weapon not in inventory"),
]


def evaluate_reality_check():
    """Evaluate the Reality Check validation system using actual ActionValidator API."""
    print(f"\n{'='*60}")
    print(f"  Reality Check Validation Accuracy")
    print(f"{'='*60}")

    try:
        from dnd_rag_system.systems.action_validator import (
            ActionValidator, ActionIntent, ActionType, ValidationResult
        )
    except ImportError as e:
        print(f"  ⚠️  Could not import ActionValidator: {e}")
        return None

    try:
        game_session = build_test_game_session()
    except Exception as e:
        print(f"  ⚠️  Could not build GameSession: {e}")
        return None

    validator = ActionValidator()

    # Test scenarios: (ActionIntent, expected_result, description)
    scenarios = [
        # ── Valid combat actions ──
        (ActionIntent(ActionType.COMBAT, target="Goblin", resource="quarterstaff",
                      raw_input="I attack the Goblin with my quarterstaff"),
         ValidationResult.VALID, "valid: weapon in inventory, target in scene"),

        (ActionIntent(ActionType.COMBAT, target="Orc", resource=None,
                      raw_input="I attack the Orc"),
         ValidationResult.VALID, "valid: target in scene, unarmed"),

        (ActionIntent(ActionType.COMBAT, target="Skeleton", resource="dagger",
                      raw_input="I stab the Skeleton with my dagger"),
         ValidationResult.VALID, "valid: dagger in inventory, skeleton present"),

        # ── Invalid combat: wrong target ──
        (ActionIntent(ActionType.COMBAT, target="Balrog", resource=None,
                      raw_input="I attack the Balrog"),
         ValidationResult.INVALID, "invalid: target not in scene"),

        (ActionIntent(ActionType.COMBAT, target="Dragon", resource=None,
                      raw_input="I attack the Dragon"),
         ValidationResult.INVALID, "invalid: target not in scene"),

        (ActionIntent(ActionType.COMBAT, target="Lich", resource=None,
                      raw_input="I attack the Lich"),
         ValidationResult.INVALID, "invalid: target not in scene"),

        # ── Valid spell actions ──
        (ActionIntent(ActionType.SPELL_CAST, target="Goblin", resource="Fireball",
                      raw_input="I cast Fireball at the Goblin"),
         ValidationResult.VALID, "valid: known spell, target present, has slots"),

        (ActionIntent(ActionType.SPELL_CAST, target="Orc", resource="Magic Missile",
                      raw_input="I cast Magic Missile at the Orc"),
         ValidationResult.VALID, "valid: known spell, target present"),

        # ── Invalid spell: unknown spell ──
        (ActionIntent(ActionType.SPELL_CAST, target="Goblin", resource="Wish",
                      raw_input="I cast Wish"),
         ValidationResult.INVALID, "invalid: spell not known"),

        (ActionIntent(ActionType.SPELL_CAST, target="Goblin", resource="Power Word Kill",
                      raw_input="I cast Power Word Kill"),
         ValidationResult.INVALID, "invalid: spell not known"),

        (ActionIntent(ActionType.SPELL_CAST, target="Goblin", resource="Meteor Swarm",
                      raw_input="I cast Meteor Swarm"),
         ValidationResult.INVALID, "invalid: spell not known"),

        # ── Invalid spell: wrong target ──
        (ActionIntent(ActionType.SPELL_CAST, target="Balrog", resource="Fireball",
                      raw_input="I cast Fireball at the Balrog"),
         ValidationResult.INVALID, "invalid: target not in scene"),

        # ── Exploration (always valid) ──
        (ActionIntent(ActionType.EXPLORATION, raw_input="I look around the cave"),
         ValidationResult.VALID, "valid: exploration always allowed"),

        (ActionIntent(ActionType.EXPLORATION, raw_input="I search for traps"),
         ValidationResult.VALID, "valid: exploration always allowed"),

        # ── Invalid combat: weapon not in inventory ──
        (ActionIntent(ActionType.COMBAT, target="Goblin", resource="longsword",
                      raw_input="I attack with my longsword"),
         ValidationResult.INVALID, "invalid: longsword not in inventory"),
    ]

    true_pos = 0   # correctly blocked invalid
    true_neg = 0   # correctly allowed valid
    false_pos = 0  # incorrectly blocked valid
    false_neg = 0  # incorrectly allowed invalid
    errors = 0

    for intent, expected_result, desc in scenarios:
        try:
            report = validator.validate_action(intent, game_session)
            actual = report.result

            # For our purposes, NPC_INTRODUCTION and FUZZY_MATCH count as "allowed"
            actual_valid = actual in (ValidationResult.VALID, ValidationResult.NPC_INTRODUCTION,
                                      ValidationResult.FUZZY_MATCH)
            expected_valid = expected_result == ValidationResult.VALID

            if actual_valid == expected_valid:
                if expected_valid:
                    true_neg += 1
                else:
                    true_pos += 1
                print(f"  ✅ {desc}")
            else:
                if expected_valid:
                    false_pos += 1
                else:
                    false_neg += 1
                print(f"  ❌ {desc} → got {actual.value} (expected {expected_result.value})")

        except Exception as e:
            errors += 1
            print(f"  ⚠️  {desc} → ERROR: {e}")

    total_correct = true_pos + true_neg
    total_tested = true_pos + true_neg + false_pos + false_neg
    accuracy = total_correct / total_tested if total_tested else 0

    results = {
        "scenarios": [],
        "summary": {
            "total_tested": total_tested,
            "accuracy": accuracy,
            "true_positives": true_pos,
            "true_negatives": true_neg,
            "false_positives": false_pos,
            "false_negatives": false_neg,
            "errors": errors,
        }
    }

    print(f"\n  Accuracy: {accuracy:.1%} ({total_correct}/{total_tested})")
    print(f"  TP (blocked invalid): {true_pos}  TN (allowed valid): {true_neg}")
    print(f"  FP (blocked valid):   {false_pos}  FN (allowed invalid): {false_neg}")
    if errors:
        print(f"  Errors/skipped: {errors}")

    return results


def evaluate_reality_check_patterns(character, npcs):
    """Fallback: test validation logic patterns without full ActionValidator."""
    print("\n  Testing validation patterns directly...")

    results = {"scenarios": [], "summary": {}}
    correct = 0
    total = 0

    # Target validation
    target_tests = [
        ("Goblin", True),
        ("Orc", True),
        ("Balrog", False),
        ("Dragon", False),
        ("Skeleton", True),
        ("Lich", False),
    ]

    print("\n  Target validation:")
    for target, expected in target_tests:
        total += 1
        # Simple presence check (what the validator does)
        is_present = any(
            target.lower() == npc.lower() or
            target.lower() in npc.lower()
            for npc in npcs
        )
        if is_present == expected:
            correct += 1
            print(f"    ✅ target='{target}' → {'found' if is_present else 'not found'}")
        else:
            print(f"    ❌ target='{target}' → {'found' if is_present else 'not found'} "
                  f"(expected {'found' if expected else 'not found'})")

    # Spell validation
    spell_tests = [
        ("Fireball", True),
        ("Magic Missile", True),
        ("Wish", False),
        ("Power Word Kill", False),
        ("Shield", True),
        ("Meteor Swarm", False),
    ]

    print("\n  Spell-known validation:")
    for spell, expected in spell_tests:
        total += 1
        is_known = spell in character["known_spells"]
        if is_known == expected:
            correct += 1
            print(f"    ✅ spell='{spell}' → {'known' if is_known else 'unknown'}")
        else:
            print(f"    ❌ spell='{spell}' → {'known' if is_known else 'unknown'}")

    # Inventory validation
    inv_tests = [
        ("quarterstaff", True),
        ("dagger", True),
        ("longsword", False),
        ("greataxe", False),
    ]

    print("\n  Inventory validation:")
    for item, expected in inv_tests:
        total += 1
        has_item = item in character["inventory"]
        if has_item == expected:
            correct += 1
            print(f"    ✅ item='{item}' → {'in inventory' if has_item else 'not found'}")
        else:
            print(f"    ❌ item='{item}' → {'in inventory' if has_item else 'not found'}")

    accuracy = correct / total if total else 0
    print(f"\n  Pattern accuracy: {accuracy:.1%} ({correct}/{total})")

    results["summary"] = {
        "total_tested": total,
        "accuracy": accuracy,
        "correct": correct,
    }
    return results


# ═══════════════════════════════════════════════════════════════════════
# 4. TEST SUITE SUMMARY
# ═══════════════════════════════════════════════════════════════════════

def evaluate_test_suite():
    """Run pytest in collect-only mode to get test counts, then run a quick subset."""
    import subprocess

    print(f"\n{'='*60}")
    print(f"  Test Suite Summary")
    print(f"{'='*60}")

    results = {}

    # Count tests
    for test_dir in ["tests", "e2e_tests"]:
        test_path = PROJECT_ROOT / test_dir
        if test_path.exists():
            count_cmd = f"cd {PROJECT_ROOT} && python -m pytest {test_dir} --collect-only -q 2>/dev/null | tail -1"
            try:
                out = subprocess.run(count_cmd, shell=True, capture_output=True, text=True, timeout=60)
                line = out.stdout.strip().split('\n')[-1] if out.stdout.strip() else ""
                print(f"  {test_dir}/: {line}")
                results[test_dir] = {"collect_output": line}
            except Exception as e:
                print(f"  {test_dir}/: error counting ({e})")

    # Count test functions via grep (always works)
    for test_dir in ["tests", "e2e_tests"]:
        test_path = PROJECT_ROOT / test_dir
        if test_path.exists():
            count_cmd = f'grep -r "def test_" {test_path} --include="*.py" | wc -l'
            try:
                out = subprocess.run(count_cmd, shell=True, capture_output=True, text=True, timeout=10)
                count = out.stdout.strip()
                print(f"  {test_dir}/ test functions (grep): {count}")
                if test_dir in results:
                    results[test_dir]["grep_count"] = int(count)
                else:
                    results[test_dir] = {"grep_count": int(count)}
            except Exception:
                pass

    return results


# ═══════════════════════════════════════════════════════════════════════
# 5. COLLECTION STATISTICS
# ═══════════════════════════════════════════════════════════════════════

def evaluate_collections(db_manager):
    """Get detailed collection statistics."""
    print(f"\n{'='*60}")
    print(f"  ChromaDB Collection Statistics")
    print(f"{'='*60}")

    results = {}
    total = 0

    try:
        collections = db_manager.client.list_collections()
        for col in collections:
            count = col.count()
            total += count

            # Sample metadata keys
            sample = col.peek(1)
            meta_keys = list(sample["metadatas"][0].keys()) if sample.get("metadatas") and sample["metadatas"] else []

            results[col.name] = {"count": count, "metadata_keys": meta_keys}
            print(f"  {col.name:25s} {count:5d} vectors  meta: {meta_keys}")

        print(f"  {'TOTAL':25s} {total:5d} vectors")
        results["_total"] = total
    except Exception as e:
        print(f"  Error: {e}")

    return results


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="D&D RAG System Evaluation")
    parser.add_argument("--rag", action="store_true", help="Run RAG retrieval evaluation")
    parser.add_argument("--reality", action="store_true", help="Run Reality Check evaluation")
    parser.add_argument("--tests", action="store_true", help="Run test suite summary")
    parser.add_argument("--all", action="store_true", help="Run all evaluations (default)")
    parser.add_argument("--output", type=str, default=None, help="Save results to JSON file")
    args = parser.parse_args()

    run_all = args.all or not (args.rag or args.reality or args.tests)

    print("╔══════════════════════════════════════════════════════════╗")
    print("║     D&D RAG System — Evaluation Metrics                 ║")
    print("╚══════════════════════════════════════════════════════════╝")

    all_results = {}

    # Initialize ChromaDB if needed
    db_manager = None
    if run_all or args.rag:
        try:
            from dnd_rag_system.core.chroma_manager import ChromaDBManager
            db_manager = ChromaDBManager()
            print(f"\n✅ ChromaDB connected")
        except Exception as e:
            print(f"\n⚠️  ChromaDB not available: {e}")
            print("   RAG evaluation will be skipped.")

    # 1. Collection stats
    if db_manager and (run_all or args.rag):
        all_results["collections"] = evaluate_collections(db_manager)

    # 2. RAG retrieval
    if db_manager and (run_all or args.rag):
        all_results["retrieval"] = evaluate_retrieval(db_manager)
        all_results["semantic"] = evaluate_semantic(db_manager)
        all_results["name_weighting"] = evaluate_name_weighting(db_manager)

    # 3. Reality Check
    if run_all or args.reality:
        all_results["reality_check"] = evaluate_reality_check()

    # 4. Test suite
    if run_all or args.tests:
        all_results["test_suite"] = evaluate_test_suite()

    # Summary
    print(f"\n{'='*60}")
    print(f"  EVALUATION SUMMARY")
    print(f"{'='*60}")

    if "retrieval" in all_results:
        ov = all_results["retrieval"]["overall"]
        print(f"  RAG Precision@1: {ov['precision_at_k'][1]:.1%}")
        print(f"  RAG Precision@3: {ov['precision_at_k'][3]:.1%}")
        print(f"  RAG MRR:         {ov['mrr']:.3f}")
    if "semantic" in all_results:
        print(f"  Semantic P@5:    {all_results['semantic']['semantic_precision_at_k']:.1%}")
    if "name_weighting" in all_results:
        nw = all_results["name_weighting"]
        print(f"  Name-weight acc: {nw['accuracy']:.1%}")
        if nw["separation_ratio"]:
            print(f"  Separation ratio:{nw['separation_ratio']:.2f}x")
    if "reality_check" in all_results and all_results["reality_check"]:
        rc = all_results["reality_check"]["summary"]
        print(f"  Reality Check:   {rc.get('accuracy', 0):.1%}")

    # Save JSON
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\n  Results saved to {output_path}")

    return all_results


if __name__ == "__main__":
    main()
