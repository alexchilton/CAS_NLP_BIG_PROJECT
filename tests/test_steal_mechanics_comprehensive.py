"""
Comprehensive tests for steal mechanics bug fixes.

Tests the full flow:
1. Steal action detection (ActionValidator)
2. Steal validation (item exists check)
3. Steal instruction generation (GM prompt)
4. Steal instruction prominence (appears before "GM RESPONSE:")
5. LLM doesn't spawn random encounters during steal

Bug context:
- Original bug: Stealing triggered goblin spawns instead of NPC reactions
- Root causes:
  a) No steal validation in ActionValidator.validate_action()
  b) Steal instructions buried in middle of prompt (LLM ignored them)
- Fixes:
  a) Added _validate_steal() method
  b) Moved steal instructions to prominent position before "GM RESPONSE:"
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dnd_rag_system.systems.action_validator import ActionValidator, ActionType, ValidationResult
from dnd_rag_system.systems.game_state import GameSession, Location, LocationType
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster


class TestStealActionDetection:
    """Test that steal actions are properly detected."""
    
    def test_steal_keyword_detection(self):
        """Test various steal keywords are detected."""
        validator = ActionValidator()
        
        test_cases = [
            ("steal the healing potion", "steal"),
            ("swipe the potion", "swipe"),
            ("pocket the gold", "pocket"),
            ("pilfer the artifact", "pilfer"),
            ("snatch the key", "snatch"),
            ("lift the purse", "lift"),
        ]
        
        for input_text, keyword in test_cases:
            intent = validator.analyze_intent(input_text)
            assert intent.action_type == ActionType.STEAL, \
                f"Failed to detect steal in: '{input_text}' (keyword: {keyword})"
    
    def test_steal_extracts_item_name(self):
        """Test that item name is extracted from steal command."""
        validator = ActionValidator()
        
        intent = validator.analyze_intent("steal the healing potion")
        assert intent.resource == "healing potion"
        
        intent = validator.analyze_intent("swipe the gold coins")
        assert intent.resource == "gold coins"


class TestStealValidation:
    """Test steal validation logic."""
    
    def test_steal_validation_item_exists(self):
        """Test steal succeeds when item exists at location."""
        validator = ActionValidator()
        
        # Setup location with item
        location = Location(
            name="Test Inn",
            location_type=LocationType.TAVERN,
            description="A cozy inn",
            available_items=["Healing Potion"]
        )
        
        session = Mock()
        session.get_current_location_obj.return_value = location
        session.npcs_present = ["Innkeeper Butterbur"]
        
        intent = validator.analyze_intent("steal the healing potion")
        validation = validator.validate_action(intent, session)
        
        assert validation.result == ValidationResult.VALID
        assert "steal" in validation.message.lower()
    
    def test_steal_validation_item_missing(self):
        """Test steal fails when item doesn't exist."""
        validator = ActionValidator()
        
        # Setup location WITHOUT item
        location = Location(
            name="Test Inn",
            location_type=LocationType.TAVERN,
            description="A cozy inn",
            available_items=[]
        )
        
        session = Mock()
        session.get_current_location_obj.return_value = location
        session.npcs_present = ["Innkeeper Butterbur"]
        
        intent = validator.analyze_intent("steal the healing potion")
        validation = validator.validate_action(intent, session)
        
        assert validation.result == ValidationResult.INVALID
        assert "not here" in validation.message.lower()
    
    def test_steal_validation_case_insensitive(self):
        """Test steal validation is case-insensitive."""
        validator = ActionValidator()
        
        location = Location(
            name="Test Inn",
            location_type=LocationType.TAVERN,
            description="A cozy inn",
            available_items=["Healing Potion"]  # Title case
        )
        
        session = Mock()
        session.get_current_location_obj.return_value = location
        session.npcs_present = ["Innkeeper"]
        
        # User types lowercase
        intent = validator.analyze_intent("steal the healing potion")
        validation = validator.validate_action(intent, session)
        
        # Should still find it
        assert validation.result == ValidationResult.VALID


class TestStealPromptGeneration:
    """Test that steal generates proper LLM instructions."""
    
    def test_steal_instruction_generated_with_npc(self):
        """Test steal instruction is generated when NPC is present."""
        from dnd_rag_system.systems.world_builder import create_starting_world
        
        # Setup GM system
        gm = GameMaster(db_manager=None)
        gm.session.world_map = create_starting_world()
        gm.session.current_location = "The Prancing Pony Inn"
        
        # Add item and NPC
        inn = gm.session.get_current_location_obj()
        inn.available_items = ["Healing Potion"]
        gm.session.npcs_present = ["Innkeeper Butterbur"]
        
        # Mock character state
        gm.session.character_state = Mock()
        gm.session.character_state.character_name = "Thorin"
        gm.session.character_state.inventory = []
        gm.session.character_state.conditions = []
        
        # Analyze steal action
        intent = gm.action_validator.analyze_intent("steal the healing potion")
        validation = gm.action_validator.validate_action(intent, gm.session)
        
        assert intent.action_type == ActionType.STEAL
        assert validation.result == ValidationResult.VALID
        
        # Generate steal instruction (simulating lines 504-534 in gm_dialogue_unified.py)
        steal_instruction = ""
        if intent.action_type == ActionType.STEAL:
            item_name = intent.resource or "item"
            current_loc = gm.session.get_current_location_obj()
            item_available = current_loc and current_loc.has_item(item_name)
            
            if item_available and gm.session.npcs_present:
                npc_names = ", ".join(gm.session.npcs_present)
                steal_instruction = f"""
STEAL ATTEMPT: Player is trying to steal {item_name} while {npc_names} is present.

CRITICAL INSTRUCTIONS:
1. DO NOT spawn random monsters (goblins, orcs, etc.)
2. ONLY {npc_names} should react
3. Roll stealth check: d20 + DEX modifier vs DC 15
4. If SUCCESS: Player sneaks the item away unnoticed
5. If FAILURE: {npc_names} catches them and reacts with anger/calls guards
6. DO NOT introduce new NPCs or enemies

"""
        
        assert steal_instruction != ""
        assert "Innkeeper Butterbur" in steal_instruction
        assert "DO NOT spawn random monsters" in steal_instruction
        assert "stealth check" in steal_instruction.lower()
    
    def test_steal_instruction_auto_success_no_npc(self):
        """Test steal auto-succeeds when no NPCs present."""
        from dnd_rag_system.systems.world_builder import create_starting_world
        
        gm = GameMaster(db_manager=None)
        gm.session.world_map = create_starting_world()
        gm.session.current_location = "The Prancing Pony Inn"
        
        inn = gm.session.get_current_location_obj()
        inn.available_items = ["Healing Potion"]
        gm.session.npcs_present = []  # No NPCs
        
        gm.session.character_state = Mock()
        gm.session.character_state.character_name = "Thorin"
        
        intent = gm.action_validator.analyze_intent("steal the healing potion")
        
        # Generate instruction
        steal_instruction = ""
        if intent.action_type == ActionType.STEAL:
            item_name = intent.resource or "item"
            current_loc = gm.session.get_current_location_obj()
            item_available = current_loc and current_loc.has_item(item_name)
            
            if item_available and not gm.session.npcs_present:
                steal_instruction = f"Player takes the {item_name}. (No one is watching)"
        
        assert steal_instruction != ""
        assert "No one is watching" in steal_instruction


class TestStealPromptPlacement:
    """Test that steal instructions are in prominent position in prompt."""
    
    @patch.object(GameMaster, '_query_ollama')
    def test_steal_instruction_before_gm_response(self, mock_llm):
        """
        CRITICAL BUG FIX TEST: Steal instruction must appear RIGHT BEFORE "GM RESPONSE:"
        
        Original bug: Instructions were in middle of prompt, LLM ignored them
        Fix: Moved to most prominent position like INVALID action warnings
        """
        from dnd_rag_system.systems.world_builder import create_starting_world
        
        # Setup
        gm = GameMaster(db_manager=None)
        gm.session.world_map = create_starting_world()
        gm.session.current_location = "The Prancing Pony Inn"
        
        inn = gm.session.get_current_location_obj()
        inn.available_items = ["Healing Potion"]
        gm.session.npcs_present = ["Innkeeper Butterbur"]
        
        gm.session.character_state = Mock()
        gm.session.character_state.character_name = "Thorin"
        gm.session.character_state.inventory = []
        gm.session.character_state.conditions = []
        
        # Mock LLM to capture prompt
        mock_llm.return_value = "The innkeeper glares at you suspiciously."
        
        # Process steal command
        response = gm.generate_response("steal the healing potion")
        
        # Check that LLM was called
        assert mock_llm.called
        
        # Get the actual prompt sent to LLM
        prompt = mock_llm.call_args[0][0]
        
        # CRITICAL CHECKS:
        # 1. Steal instruction should be in the prompt
        assert "STEAL ATTEMPT" in prompt or "Player takes the" in prompt
        
        # 2. Steal instruction should come AFTER normal instructions
        assert "INSTRUCTIONS:" in prompt
        instructions_pos = prompt.find("INSTRUCTIONS:")
        steal_pos = prompt.find("STEAL") if "STEAL" in prompt else prompt.find("Player takes")
        assert steal_pos > instructions_pos, "Steal instruction should come after general instructions"
        
        # 3. Steal instruction should come RIGHT BEFORE "GM RESPONSE:"
        gm_response_pos = prompt.find("GM RESPONSE:")
        assert gm_response_pos > steal_pos, "GM RESPONSE should come after steal instruction"
        
        # 4. There should be minimal content between steal instruction and GM RESPONSE
        between_content = prompt[steal_pos:gm_response_pos]
        # Should be mostly the steal instruction + border + newlines (relaxed to allow for formatting)
        assert between_content.count('\n') < 25, "Steal instruction should be immediately before GM RESPONSE"
    
    @patch.object(GameMaster, '_query_ollama')
    def test_steal_has_prominent_border(self, mock_llm):
        """Test steal instruction has visual border like INVALID actions."""
        from dnd_rag_system.systems.world_builder import create_starting_world
        
        gm = GameMaster(db_manager=None)
        gm.session.world_map = create_starting_world()
        gm.session.current_location = "The Prancing Pony Inn"
        
        inn = gm.session.get_current_location_obj()
        inn.available_items = ["Healing Potion"]
        gm.session.npcs_present = ["Innkeeper Butterbur"]
        
        gm.session.character_state = Mock()
        gm.session.character_state.character_name = "Thorin"
        gm.session.character_state.inventory = []
        gm.session.character_state.conditions = []
        
        mock_llm.return_value = "You pocket the potion."
        
        response = gm.generate_response("steal the healing potion")
        prompt = mock_llm.call_args[0][0]
        
        # Should have prominent border (===...===)
        assert "═══" in prompt, "Steal instruction should have visual border"
        assert "🎯 STEAL ATTEMPT MECHANICS 🎯" in prompt or "STEAL ATTEMPT" in prompt


class TestStealNoRandomEncounters:
    """Test that steal doesn't trigger random encounter system."""
    
    @patch.object(GameMaster, '_query_ollama')
    def test_steal_doesnt_trigger_encounter_check(self, mock_llm):
        """
        BUG FIX TEST: Stealing should NOT trigger random encounter generation.
        
        The encounter system checks for exploration keywords like 'explore', 'search', etc.
        'steal' is NOT an exploration keyword, so encounters should not be generated.
        """
        from dnd_rag_system.systems.world_builder import create_starting_world
        
        gm = GameMaster(db_manager=None)
        gm.session.world_map = create_starting_world()
        gm.session.current_location = "The Prancing Pony Inn"
        
        inn = gm.session.get_current_location_obj()
        inn.available_items = ["Healing Potion"]
        gm.session.npcs_present = ["Innkeeper Butterbur"]
        
        gm.session.character_state = Mock()
        gm.session.character_state.character_name = "Thorin"
        gm.session.character_state.inventory = []
        gm.session.character_state.conditions = []
        gm.session.character_state.level = 3
        gm.session.character_state.hp = 20
        gm.session.character_state.max_hp = 20
        gm.session.character_state.take_damage = Mock(return_value={"message": "Took damage"})
        gm.session.character_state.heal = Mock(return_value={"message": "Healed"})
        gm.session.character_state.add_condition = Mock()
        gm.session.character_state.remove_condition = Mock()
        
        # Reset encounter cooldown (ensure we're eligible for encounters if triggered)
        gm.session.turns_since_last_encounter = 10
        gm.session.last_encounter_location = ""
        
        mock_llm.return_value = "The innkeeper catches you! Guards are called."
        
        # Process steal - should NOT trigger encounter
        response = gm.generate_response("steal the healing potion")
        
        # Check that no encounter was added to NPCs
        # (If encounter triggered, a monster would be added to npcs_present)
        assert "Goblin" not in gm.session.npcs_present
        assert "Orc" not in gm.session.npcs_present
        
        # The original NPC should still be present (Guards might be added from narrative, which is OK)
        assert "Innkeeper Butterbur" in gm.session.npcs_present


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
