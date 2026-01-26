"""
Unit tests for PromptBuilder.

Tests the extracted prompt building logic.
"""

import pytest
from unittest.mock import Mock
from dnd_rag_system.dialogue.prompt_builder import PromptBuilder
from dnd_rag_system.systems.action_validator import ValidationResult, ActionIntent, ActionType


@pytest.fixture
def prompt_builder():
    """Create a PromptBuilder instance."""
    return PromptBuilder()


@pytest.fixture
def mock_session():
    """Create a mock GameSession."""
    session = Mock()
    session.current_location = "Tavern"
    session.scene_description = "A cozy tavern"
    session.day = 1
    session.time_of_day = "evening"
    session.npcs_present = []
    session.active_quests = []

    # Mock combat
    session.combat = Mock()
    session.combat.in_combat = False

    # Mock location object
    session.get_current_location_obj.return_value = None

    return session


class TestBasicPromptBuilding:
    """Test suite for basic prompt construction."""

    def test_builds_basic_prompt(self, prompt_builder, mock_session):
        """Test that a basic prompt is constructed correctly."""
        prompt = prompt_builder.build_prompt(
            player_input="I look around",
            game_session=mock_session,
            history_text="Player: Hello\nGM: Welcome"
        )

        assert "You are an experienced Dungeon Master" in prompt
        assert "CURRENT LOCATION: Tavern" in prompt
        assert "SCENE: A cozy tavern" in prompt
        assert "Day 1, evening" in prompt
        assert "PLAYER ACTION: I look around" in prompt
        assert "GM RESPONSE:" in prompt

    def test_includes_conversation_history(self, prompt_builder, mock_session):
        """Test that conversation history is included."""
        history_text = "Player: Hello\nGM: Welcome to the tavern!"

        prompt = prompt_builder.build_prompt(
            player_input="I order a drink",
            game_session=mock_session,
            history_text=history_text
        )

        assert "RECENT CONVERSATION:" in prompt
        assert history_text in prompt

    def test_includes_conversation_summary(self, prompt_builder, mock_session):
        """Test that conversation summary is included when provided."""
        summary = "The party defeated a goblin and entered the tavern."

        prompt = prompt_builder.build_prompt(
            player_input="I look around",
            game_session=mock_session,
            history_text="",
            conversation_summary=summary
        )

        assert "PREVIOUS SESSION SUMMARY:" in prompt
        assert summary in prompt

    def test_excludes_empty_conversation_summary(self, prompt_builder, mock_session):
        """Test that empty summary is not included."""
        prompt = prompt_builder.build_prompt(
            player_input="I look around",
            game_session=mock_session,
            history_text="",
            conversation_summary=""
        )

        assert "PREVIOUS SESSION SUMMARY:" not in prompt


class TestRAGContext:
    """Test suite for RAG context handling."""

    def test_includes_relevant_rag_context(self, prompt_builder, mock_session):
        """Test that relevant RAG context is included."""
        rag_context = "[SPELLS] Fireball: A powerful fire spell..."

        prompt = prompt_builder.build_prompt(
            player_input="I cast fireball",
            game_session=mock_session,
            history_text="",
            rag_context=rag_context
        )

        assert "RETRIEVED D&D RULES" in prompt
        assert rag_context in prompt

    def test_excludes_no_rules_retrieved_message(self, prompt_builder, mock_session):
        """Test that 'No rules retrieved' message is excluded."""
        prompt = prompt_builder.build_prompt(
            player_input="I look around",
            game_session=mock_session,
            history_text="",
            rag_context="No specific rules retrieved."
        )

        assert "RETRIEVED D&D RULES" not in prompt

    def test_excludes_no_relevant_rules_message(self, prompt_builder, mock_session):
        """Test that 'No relevant rules' message is excluded."""
        prompt = prompt_builder.build_prompt(
            player_input="I look around",
            game_session=mock_session,
            history_text="",
            rag_context="No highly relevant rules found."
        )

        assert "RETRIEVED D&D RULES" not in prompt


class TestGameStateContext:
    """Test suite for game state context."""

    def test_includes_npcs_present(self, prompt_builder, mock_session):
        """Test that NPCs are included when present."""
        mock_session.npcs_present = ["Goblin", "Orc"]

        prompt = prompt_builder.build_prompt(
            player_input="I attack",
            game_session=mock_session,
            history_text=""
        )

        assert "NPCs/CREATURES PRESENT: Goblin, Orc" in prompt

    def test_excludes_npcs_when_none_present(self, prompt_builder, mock_session):
        """Test that NPC section is excluded when no NPCs."""
        mock_session.npcs_present = []

        prompt = prompt_builder.build_prompt(
            player_input="I look around",
            game_session=mock_session,
            history_text=""
        )

        assert "NPCS/CREATURES PRESENT:" not in prompt

    def test_includes_combat_state(self, prompt_builder, mock_session):
        """Test that combat state is included when in combat."""
        mock_session.combat.in_combat = True
        mock_session.combat.round_number = 3
        mock_session.combat.get_current_turn.return_value = "Player"
        mock_session.combat.initiative_order = [("Player", 18), ("Goblin", 12)]

        prompt = prompt_builder.build_prompt(
            player_input="I attack the goblin",
            game_session=mock_session,
            history_text=""
        )

        assert "COMBAT STATUS: Round 3, Player's turn" in prompt
        assert "Initiative Order: Player (18), Goblin (12)" in prompt

    def test_includes_active_quests(self, prompt_builder, mock_session):
        """Test that active quests are included."""
        mock_session.active_quests = [
            {"name": "Find the sword", "status": "active"},
            {"name": "Defeat the dragon", "status": "active"},
            {"name": "Old quest", "status": "completed"}
        ]

        prompt = prompt_builder.build_prompt(
            player_input="I continue my quest",
            game_session=mock_session,
            history_text=""
        )

        assert "ACTIVE QUESTS: Find the sword, Defeat the dragon" in prompt
        assert "Old quest" not in prompt

    def test_limits_active_quests_to_two(self, prompt_builder, mock_session):
        """Test that only 2 active quests are shown."""
        mock_session.active_quests = [
            {"name": "Quest 1", "status": "active"},
            {"name": "Quest 2", "status": "active"},
            {"name": "Quest 3", "status": "active"}
        ]

        prompt = prompt_builder.build_prompt(
            player_input="I continue",
            game_session=mock_session,
            history_text=""
        )

        assert "Quest 1" in prompt
        assert "Quest 2" in prompt
        assert "Quest 3" not in prompt


class TestLocationContext:
    """Test suite for location context."""

    def test_includes_return_visit_note(self, prompt_builder, mock_session):
        """Test that return visits are noted."""
        mock_loc = Mock()
        mock_loc.visit_count = 3
        mock_loc.defeated_enemies = set()
        mock_session.get_current_location_obj.return_value = mock_loc

        prompt = prompt_builder.build_prompt(
            player_input="I look around",
            game_session=mock_session,
            history_text=""
        )

        assert "The party has been here before" in prompt

    def test_includes_defeated_enemies_aftermath(self, prompt_builder, mock_session):
        """Test that defeated enemies are mentioned."""
        mock_loc = Mock()
        mock_loc.visit_count = 1
        mock_loc.defeated_enemies = {"Goblin", "Orc", "Troll"}
        mock_session.get_current_location_obj.return_value = mock_loc

        prompt = prompt_builder.build_prompt(
            player_input="I look around",
            game_session=mock_session,
            history_text=""
        )

        assert "AFTERMATH:" in prompt
        assert "defeated here previously" in prompt


class TestSpecialInstructions:
    """Test suite for special instructions."""

    def test_includes_encounter_instruction(self, prompt_builder, mock_session):
        """Test that encounter instructions are included."""
        encounter_instr = "A wild goblin appears!"

        prompt = prompt_builder.build_prompt(
            player_input="I explore",
            game_session=mock_session,
            history_text="",
            encounter_instruction=encounter_instr
        )

        assert encounter_instr in prompt

    def test_includes_player_attack_instruction(self, prompt_builder, mock_session):
        """Test that player attack instructions are included."""
        attack_instr = "COMBAT INSTRUCTION: You hit for 8 damage!"

        prompt = prompt_builder.build_prompt(
            player_input="I attack",
            game_session=mock_session,
            history_text="",
            player_attack_instruction=attack_instr
        )

        assert attack_instr in prompt

    def test_steal_instruction_takes_precedence(self, prompt_builder, mock_session):
        """Test that steal instruction is prominent and ends prompt."""
        steal_instr = "Player is stealing an item."

        prompt = prompt_builder.build_prompt(
            player_input="I steal the gem",
            game_session=mock_session,
            history_text="",
            steal_instruction=steal_instr
        )

        assert "🎯 STEAL ATTEMPT MECHANICS 🎯" in prompt
        assert steal_instr in prompt
        assert prompt.endswith("GM RESPONSE:")

class TestValidationGuidance:
    """Test suite for validation guidance."""

    def test_invalid_action_validation(self, prompt_builder, mock_session):
        """Test INVALID action validation guidance."""
        validation = Mock()
        validation.result = ValidationResult.INVALID
        validation.message = "You don't have that weapon."

        prompt = prompt_builder.build_prompt(
            player_input="I attack with my bow",
            game_session=mock_session,
            history_text="",
            validation=validation
        )

        assert "🚫 CRITICAL RULE - THIS ACTION IS IMPOSSIBLE 🚫" in prompt
        assert "YOU MUST NARRATE FAILURE" in prompt
        assert validation.message in prompt

    def test_npc_introduction_validation(self, prompt_builder, mock_session):
        """Test NPC introduction validation guidance."""
        validation = Mock()
        validation.result = ValidationResult.NPC_INTRODUCTION
        validation.message = "Player wants to talk to someone."
        validation.action = Mock()
        validation.action.target = "Bartender"

        prompt = prompt_builder.build_prompt(
            player_input="I talk to the bartender",
            game_session=mock_session,
            history_text="",
            validation=validation
        )

        assert "💬 NPC INTRODUCTION OPPORTUNITY 💬" in prompt
        assert "Bartender" in prompt

    def test_target_clarification_validation(self, prompt_builder, mock_session):
        """Test target clarification validation."""
        validation = Mock()
        validation.result = ValidationResult.VALID
        validation.matched_entity = "Goblin"
        validation.message = "Target clarified."
        validation.action = Mock()
        validation.action.target = "gobbo"

        prompt = prompt_builder.build_prompt(
            player_input="I attack the gobbo",
            game_session=mock_session,
            history_text="",
            validation=validation
        )

        assert "ℹ️ TARGET CLARIFICATION ℹ️" in prompt
        assert "gobbo" in prompt
        assert "Goblin" in prompt

    def test_valid_action_simple_message(self, prompt_builder, mock_session):
        """Test valid action with simple message."""
        validation = Mock()
        validation.result = ValidationResult.VALID
        validation.matched_entity = None
        validation.message = "Action is valid."

        prompt = prompt_builder.build_prompt(
            player_input="I look around",
            game_session=mock_session,
            history_text="",
            validation=validation
        )

        assert "Action is valid." in prompt
        assert "GM RESPONSE:" in prompt


class TestPromptEnding:
    """Test suite for prompt ending."""

    def test_ends_with_gm_response_marker(self, prompt_builder, mock_session):
        """Test that prompts end with GM RESPONSE marker."""
        prompt = prompt_builder.build_prompt(
            player_input="I look around",
            game_session=mock_session,
            history_text=""
        )

        assert prompt.strip().endswith("GM RESPONSE:")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
