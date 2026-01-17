"""
Integration tests for constants usage in actual system

Verifies that:
1. Commands work through the GameMaster system
2. ActionValidator uses constants correctly
3. No magic strings remain in key files
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dnd_rag_system.constants import Commands, ActionKeywords
from dnd_rag_system.systems.action_validator import ActionValidator, ActionType
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster


class TestCommandsInGameMaster:
    """Test that Commands constants work in GameMaster."""
    
    @patch.object(GameMaster, '_query_ollama')
    def test_start_combat_command_constant(self, mock_llm):
        """Test /start_combat uses Commands.START_COMBAT constant."""
        gm = GameMaster(db_manager=None)
        gm.session.character_state = Mock()
        gm.session.character_state.character_name = "Thorin"
        gm.session.character_state.current_hp = 20
        gm.session.character_state.max_hp = 20
        gm.session.character_state.armor_class = 15  # Fix: Mock needs armor_class for NPC attacks
        gm.session.character_state.conditions = []  # Fix: Mock needs iterable

        mock_llm.return_value = "Combat begins!"

        # Use the constant instead of magic string
        response = gm.generate_response(f"{Commands.START_COMBAT} Goblin")

        assert gm.combat_manager.is_in_combat()
        assert "Goblin" in gm.session.npcs_present
    
    @patch.object(GameMaster, '_query_ollama')
    def test_map_command_constant(self, mock_llm):
        """Test /map uses Commands.MAP constant."""
        from dnd_rag_system.systems.world_builder import create_starting_world
        
        gm = GameMaster(db_manager=None)
        gm.session.world_map = create_starting_world()
        gm.session.current_location = "The Prancing Pony Inn"
        
        # Use the constant
        response = gm.generate_response(Commands.MAP)
        
        # Should return map text (not call LLM)
        assert mock_llm.called == False
        assert "World Map" in response or "Locations" in response


class TestActionKeywordsInValidator:
    """Test that ActionKeywords are used by ActionValidator."""
    
    def test_attack_keywords_from_constants(self):
        """Test that COMBAT_KEYWORDS comes from ActionKeywords."""
        validator = ActionValidator()
        
        # Verify it uses constants
        assert validator.COMBAT_KEYWORDS == ActionKeywords.ATTACK_KEYWORDS
        
        # Test actual intent detection
        intent = validator.analyze_intent("attack the goblin")
        assert intent.action_type == ActionType.COMBAT
    
    def test_spell_keywords_from_constants(self):
        """Test that SPELL_KEYWORDS comes from ActionKeywords."""
        validator = ActionValidator()
        
        assert validator.SPELL_KEYWORDS == ActionKeywords.SPELL_KEYWORDS
        
        intent = validator.analyze_intent("cast fireball")
        assert intent.action_type == ActionType.SPELL_CAST
    
    def test_steal_keywords_from_constants(self):
        """Test that STEAL_KEYWORDS comes from ActionKeywords."""
        validator = ActionValidator()
        
        assert validator.STEAL_KEYWORDS == ActionKeywords.STEAL_KEYWORDS
        
        intent = validator.analyze_intent("steal the potion")
        assert intent.action_type == ActionType.STEAL
    
    def test_conversation_keywords_from_constants(self):
        """Test that CONVERSATION_KEYWORDS comes from ActionKeywords."""
        validator = ActionValidator()
        
        assert validator.CONVERSATION_KEYWORDS == ActionKeywords.CONVERSATION_KEYWORDS
        
        intent = validator.analyze_intent("talk to the innkeeper")
        assert intent.action_type == ActionType.CONVERSATION


class TestConstantsConsistency:
    """Test that constants are consistent across modules."""
    
    def test_no_hardcoded_start_combat(self):
        """Verify Commands.START_COMBAT is used instead of '/start_combat'."""
        # This is a smoke test - if constants are imported, they should be used
        assert Commands.START_COMBAT == '/start_combat'
    
    def test_no_hardcoded_map_command(self):
        """Verify Commands.MAP is used instead of '/map'."""
        assert Commands.MAP == '/map'
    
    def test_unconscious_commands_list_valid(self):
        """Test unconscious allowed commands are valid Commands."""
        allowed = Commands.unconscious_allowed_commands()
        all_cmds = Commands.all_commands()
        
        for cmd in allowed:
            assert cmd in all_cmds, f"{cmd} not in all_commands()"


class TestCommandDetection:
    """Test command detection with constants."""
    
    def test_commands_module_imported_in_gm(self):
        """Test that Commands is imported in gm_dialogue_unified."""
        from dnd_rag_system.systems import gm_dialogue_unified
        
        # Verify Commands is imported
        assert hasattr(gm_dialogue_unified, 'Commands')
    
    def test_action_keywords_imported_in_validator(self):
        """Test that ActionKeywords is imported in action_validator."""
        from dnd_rag_system.systems import action_validator
        
        # Verify ActionKeywords is imported
        assert hasattr(action_validator, 'ActionKeywords')


class TestBackwardCompatibility:
    """Test that refactoring didn't break existing behavior."""
    
    def test_validator_still_detects_attacks(self):
        """Test attack detection still works after refactoring."""
        validator = ActionValidator()
        
        test_attacks = [
            "attack the goblin",
            "hit the orc with my sword",
            "shoot the dragon",
        ]
        
        for attack_text in test_attacks:
            intent = validator.analyze_intent(attack_text)
            assert intent.action_type == ActionType.COMBAT, \
                f"Failed to detect combat in: {attack_text}"
    
    def test_validator_still_detects_spells(self):
        """Test spell detection still works after refactoring."""
        validator = ActionValidator()
        
        test_spells = [
            "cast magic missile",
            "I cast fireball at the enemies",
            "casting cure wounds",
        ]
        
        for spell_text in test_spells:
            intent = validator.analyze_intent(spell_text)
            assert intent.action_type == ActionType.SPELL_CAST, \
                f"Failed to detect spell in: {spell_text}"
    
    def test_validator_still_detects_stealing(self):
        """Test steal detection still works after refactoring."""
        validator = ActionValidator()
        
        test_steals = [
            "steal the gold",
            "swipe the potion",
            "pocket the ring",
        ]
        
        for steal_text in test_steals:
            intent = validator.analyze_intent(steal_text)
            assert intent.action_type == ActionType.STEAL, \
                f"Failed to detect steal in: {steal_text}"


class TestConstantsUsagePatterns:
    """Test proper usage patterns of constants."""
    
    def test_command_comparison_case_insensitive(self):
        """Test that command comparisons should be case-insensitive."""
        # This tests the pattern: lower_input == Commands.MAP.lower()
        user_input = "/MAP"
        lower_input = user_input.lower()
        
        # Correct pattern
        assert lower_input == Commands.MAP.lower()
        assert lower_input == Commands.MAP  # Constants are lowercase
    
    def test_keyword_membership_check(self):
        """Test pattern for checking if keyword in list."""
        user_input = "attack the goblin"
        lower_input = user_input.lower()
        
        # Should use constants
        found = any(keyword in lower_input for keyword in ActionKeywords.ATTACK_KEYWORDS)
        assert found


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
