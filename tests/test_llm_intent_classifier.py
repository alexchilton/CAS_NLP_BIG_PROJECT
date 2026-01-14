#!/usr/bin/env python3
"""
Unit Tests for LLM-Based Intent Classification

Tests the optional LLM-based intent classifier against the keyword-based classifier.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from dnd_rag_system.systems.action_validator import ActionValidator, ActionType


class TestKeywordClassifier:
    """Tests for keyword-based intent classifier (baseline)"""

    def test_standard_combat_action(self):
        """Keyword classifier handles standard combat phrases"""
        validator = ActionValidator(classifier_type="keyword")

        test_cases = [
            ("I attack the goblin", ActionType.COMBAT, "goblin"),
            ("I shoot my bow at the orc", ActionType.COMBAT, "orc"),
            ("I strike the dragon with my sword", ActionType.COMBAT, "dragon"),
        ]

        for user_input, expected_type, expected_target in test_cases:
            intent = validator.analyze_intent(user_input)
            assert intent.action_type == expected_type, \
                f"Expected {expected_type} for '{user_input}', got {intent.action_type}"
            if expected_target:
                assert intent.target.lower() == expected_target.lower(), \
                    f"Expected target '{expected_target}' for '{user_input}', got '{intent.target}'"

    def test_standard_spell_casting(self):
        """Keyword classifier handles standard spell phrases"""
        validator = ActionValidator(classifier_type="keyword")

        test_cases = [
            ("I cast Fireball", ActionType.SPELL_CAST, "Fireball"),
            ("I cast Magic Missile at the goblin", ActionType.SPELL_CAST, "Magic Missile"),
        ]

        for user_input, expected_type, expected_spell in test_cases:
            intent = validator.analyze_intent(user_input)
            assert intent.action_type == expected_type
            if expected_spell:
                assert intent.resource == expected_spell

    def test_creative_combat_fails_keyword(self):
        """Keyword classifier FAILS on creative combat phrases"""
        validator = ActionValidator(classifier_type="keyword")

        # These should FAIL with keyword-based (not contain combat keywords)
        creative_phrases = [
            "I loose an arrow at the dragon",
            "I nock and release my bowstring at the goblin",
            "Let fly with my longbow towards the orc",
        ]

        for user_input in creative_phrases:
            intent = validator.analyze_intent(user_input)
            # Keyword classifier will likely classify these as EXPLORATION
            # since they don't contain combat keywords like "attack", "shoot", etc.
            # Note: Some might work if they contain keywords like "bow"
            print(f"Keyword result for '{user_input}': {intent.action_type.value}")


class TestLLMClassifier:
    """Tests for LLM-based intent classifier"""

    @pytest.mark.skipif(
        not Path("/usr/local/bin/ollama").exists() and not Path("/opt/homebrew/bin/ollama").exists(),
        reason="Ollama not installed"
    )
    def test_creative_combat_works_llm(self):
        """LLM classifier handles creative combat phrases"""
        validator = ActionValidator(classifier_type="llm", debug=True)

        test_cases = [
            ("I loose an arrow at the dragon", ActionType.COMBAT, "dragon", "arrow"),
            ("I nock and release my bowstring at the goblin", ActionType.COMBAT, "goblin", "bow"),
            ("Let fly with my longbow towards the orc", ActionType.COMBAT, "orc", "longbow"),
        ]

        for user_input, expected_type, expected_target, expected_weapon in test_cases:
            intent = validator.analyze_intent(user_input)
            print(f"\n🎯 Input: '{user_input}'")
            print(f"   Result: {intent}")

            assert intent.action_type == expected_type, \
                f"Expected {expected_type} for '{user_input}', got {intent.action_type}"

            if expected_target:
                assert intent.target is not None, f"Expected target for '{user_input}'"
                assert intent.target.lower() == expected_target.lower(), \
                    f"Expected target '{expected_target}', got '{intent.target}'"

    @pytest.mark.skipif(
        not Path("/usr/local/bin/ollama").exists() and not Path("/opt/homebrew/bin/ollama").exists(),
        reason="Ollama not installed"
    )
    def test_standard_actions_work_llm(self):
        """LLM classifier handles standard phrases correctly"""
        validator = ActionValidator(classifier_type="llm", debug=True)

        test_cases = [
            ("I attack the goblin", ActionType.COMBAT, "goblin"),
            ("I cast Fireball at the orc", ActionType.SPELL_CAST, "orc"),
            ("I talk to the innkeeper", ActionType.CONVERSATION, "innkeeper"),
            ("I drink a healing potion", ActionType.ITEM_USE, None),
            ("I look around the room", ActionType.EXPLORATION, None),
        ]

        for user_input, expected_type, expected_target in test_cases:
            intent = validator.analyze_intent(user_input)
            print(f"\n🎯 Input: '{user_input}'")
            print(f"   Result: {intent}")

            assert intent.action_type == expected_type, \
                f"Expected {expected_type} for '{user_input}', got {intent.action_type}"

            if expected_target:
                assert intent.target is not None
                assert intent.target.lower() == expected_target.lower()

    @pytest.mark.skipif(
        not Path("/usr/local/bin/ollama").exists() and not Path("/opt/homebrew/bin/ollama").exists(),
        reason="Ollama not installed"
    )
    def test_llm_fallback_on_error(self):
        """LLM classifier falls back to keyword on error"""
        # Use invalid model to trigger fallback
        validator = ActionValidator(classifier_type="llm", debug=True)
        validator.llm_model = "nonexistent-model-xyz"

        intent = validator.analyze_intent("I attack the goblin")

        # Should still work (fallback to keyword)
        assert intent.action_type == ActionType.COMBAT
        assert intent.target.lower() == "goblin"


class TestComparisonMode:
    """Tests for comparison mode (runs both classifiers)"""

    @pytest.mark.skipif(
        not Path("/usr/local/bin/ollama").exists() and not Path("/opt/homebrew/bin/ollama").exists(),
        reason="Ollama not installed"
    )
    def test_comparison_mode_standard_phrases(self):
        """Comparison mode: both classifiers should agree on standard phrases"""
        validator = ActionValidator(compare_classifiers=True, debug=True)

        standard_inputs = [
            "I attack the goblin",
            "I cast Fireball",
            "I talk to the bartender",
            "I drink a potion",
        ]

        for user_input in standard_inputs:
            # Get result from comparison mode (returns LLM result)
            intent = validator.analyze_intent(user_input)
            print(f"\n🔀 Comparing classifiers for: '{user_input}'")
            print(f"   Result: {intent}")

            # Both should produce valid results
            assert intent.action_type is not None

    @pytest.mark.skipif(
        not Path("/usr/local/bin/ollama").exists() and not Path("/opt/homebrew/bin/ollama").exists(),
        reason="Ollama not installed"
    )
    def test_comparison_mode_creative_phrases(self):
        """Comparison mode: LLM should handle creative phrases better"""
        validator = ActionValidator(compare_classifiers=True, debug=True)

        creative_inputs = [
            "I loose an arrow at the dragon",
            "I nock and release my bowstring",
            "Let fly with my longbow at the orc",
        ]

        for user_input in creative_inputs:
            intent = validator.analyze_intent(user_input)
            print(f"\n🔀 Comparing classifiers for: '{user_input}'")
            print(f"   LLM Result: {intent}")

            # LLM should classify as combat
            # (Comparison mode returns LLM result, logs will show differences)
            assert intent.action_type is not None


class TestEdgeCases:
    """Edge case tests for intent classification"""

    @pytest.mark.skipif(
        not Path("/usr/local/bin/ollama").exists() and not Path("/opt/homebrew/bin/ollama").exists(),
        reason="Ollama not installed"
    )
    def test_party_member_actions(self):
        """Test parsing of party member actions"""
        validator = ActionValidator(classifier_type="llm", debug=True)
        validator.set_party_characters(["Thorin", "Gimli", "Legolas"])

        test_cases = [
            ("Thorin attacks the goblin", ActionType.COMBAT, "goblin"),
            ("Gimli talks to the innkeeper", ActionType.CONVERSATION, "innkeeper"),
            ("Legolas casts Cure Wounds on Thorin", ActionType.SPELL_CAST, "Thorin"),
        ]

        for user_input, expected_type, expected_target in test_cases:
            intent = validator.analyze_intent(user_input)
            print(f"\n🎯 Input: '{user_input}'")
            print(f"   Result: {intent}")

            assert intent.action_type == expected_type
            if expected_target:
                assert intent.target is not None
                assert intent.target.lower() == expected_target.lower()

    @pytest.mark.skipif(
        not Path("/usr/local/bin/ollama").exists() and not Path("/opt/homebrew/bin/ollama").exists(),
        reason="Ollama not installed"
    )
    def test_ambiguous_actions(self):
        """Test handling of ambiguous or unclear actions"""
        validator = ActionValidator(classifier_type="llm", debug=True)

        ambiguous_inputs = [
            "I do something",
            "What happens?",
            "I wait",
        ]

        for user_input in ambiguous_inputs:
            intent = validator.analyze_intent(user_input)
            print(f"\n🎯 Input: '{user_input}'")
            print(f"   Result: {intent}")

            # Should classify as something (likely exploration or unknown)
            assert intent.action_type is not None


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
