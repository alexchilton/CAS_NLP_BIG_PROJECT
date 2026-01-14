"""
Tests for bug fixes: travel, combat targeting, explore/map display.

Bug fixes tested:
1. /travel command is case-insensitive (e.g., "town square" = "Town Square")
2. Combat damage uses fuzzy-matched name (e.g., "goblin" → "Goblin Scout")
3. /explore generates locations that show up on /map
4. Steal validation properly checks item existence
"""

import pytest
from dnd_rag_system.systems.game_state import GameSession, Location, LocationType
from dnd_rag_system.systems.world_builder import create_starting_world, generate_random_location, generate_llm_enhanced_location
from dnd_rag_system.systems.action_validator import ActionValidator, ActionType, ValidationResult
from dnd_rag_system.systems.combat_manager import CombatManager
from unittest.mock import Mock, MagicMock
import re


class TestTravelCaseSensitivity:
    """Test case-insensitive travel command."""
    
    def test_travel_lowercase(self):
        """BUG: /travel town square failed even though 'Town Square' was connected."""
        world_map = create_starting_world()
        
        session = GameSession()
        session.world_map = world_map
        session.current_location = "Town Square"
        
        # User types lowercase - should still work
        success, message = session.travel_to("the prancing pony inn")
        
        assert success, f"Expected success, got: {message}"
        assert session.current_location == "The Prancing Pony Inn"
    
    def test_travel_uppercase(self):
        """Test travel with ALL CAPS works."""
        world_map = create_starting_world()
        
        session = GameSession()
        session.world_map = world_map
        session.current_location = "Town Square"
        
        success, message = session.travel_to("MARKET SQUARE")
        
        assert success, f"Expected success, got: {message}"
        assert session.current_location == "Market Square"
    
    def test_travel_mixed_case(self):
        """Test travel with MiXeD case works."""
        world_map = create_starting_world()
        
        session = GameSession()
        session.world_map = world_map
        session.current_location = "Town Square"
        
        success, message = session.travel_to("tEmPlE dIsTrIcT")
        
        assert success, f"Expected success, got: {message}"
        assert session.current_location == "Temple District"
    
    def test_travel_invalid_destination_still_fails(self):
        """Test that truly invalid destinations are still rejected."""
        world_map = create_starting_world()
        
        session = GameSession()
        session.world_map = world_map
        session.current_location = "Town Square"
        
        success, message = session.travel_to("narnia")
        
        assert not success
        assert "Cannot travel to" in message


class TestCombatTargetMatching:
    """Test combat damage applies to fuzzy-matched target."""
    
    def test_fuzzy_match_validation(self):
        """BUG: 'attack goblin' should match to 'Goblin'."""
        validator = ActionValidator()

        session = Mock()
        session.combat = Mock()
        session.combat.initiative_order = [("Goblin", 15)]
        session.npcs_present = ["Goblin"]
        session.character_state = None

        intent = validator.analyze_intent("attack the goblin")
        validation = validator.validate_action(intent, session)

        # Should match
        assert validation.result in [ValidationResult.VALID, ValidationResult.FUZZY_MATCH]
        assert validation.matched_entity.lower() == "goblin"
    
    def test_exact_match_validation(self):
        """Test exact match still works."""
        validator = ActionValidator()
        
        session = Mock()
        session.combat = Mock()
        session.combat.initiative_order = [("Goblin", 10)]
        session.npcs_present = ["Goblin"]
        session.character_state = None
        
        intent = validator.analyze_intent("attack the Goblin")
        validation = validator.validate_action(intent, session)
        
        assert validation.result == ValidationResult.VALID
        assert validation.matched_entity.lower() == "goblin"
    
    def test_combat_damage_integration(self):
        """
        BUG: Player attacks always missed because code used incorrect name
        for damage lookup.

        This tests the integration: validation → matched_entity → damage application.
        """
        from dnd_rag_system.systems.monster_stat_system import MonsterInstance
        from dnd_rag_system.systems.game_state import CombatState

        # Setup combat manager with "Goblin"
        combat_state = CombatState()
        combat_mgr = CombatManager(combat_state)
        goblin = MonsterInstance(
            name="Goblin",
            cr=0.25,
            size="Small",
            type="humanoid",
            ac=15,
            max_hp=7,
            current_hp=7,
            speed=30,
            str=8, dex=14, con=10, int=10, wis=8, cha=8,
            attacks=[{"name": "Scimitar", "to_hit": 4, "damage": "1d6+2", "damage_type": "slashing"}],
            traits=[],
            description="A small goblin"
        )
        combat_mgr.npc_monsters["Goblin"] = goblin

        # Setup validator
        validator = ActionValidator()
        session = Mock()
        session.combat = Mock()
        session.combat.initiative_order = [("Goblin", 15)]
        session.npcs_present = ["Goblin"]
        session.character_state = None

        # User types "attack the goblin" (lowercase)
        intent = validator.analyze_intent("attack the goblin")
        validation = validator.validate_action(intent, session)

        # Validation should return matched_entity = "Goblin"
        assert validation.matched_entity == "Goblin"

        # The GM system should use validation.matched_entity for damage
        # (In gm_dialogue_unified.py, line 565 now uses this)
        target_name = validation.matched_entity if validation.matched_entity else intent.target
        assert target_name == "Goblin"

        # Damage should apply to the correct monster
        assert target_name in combat_mgr.npc_monsters
        actual_damage, is_dead = combat_mgr.apply_damage_to_npc(target_name, 5)
        assert goblin.current_hp == 2  # 7 - 5 = 2


class TestExploreAndMapDisplay:
    """Test /explore creates locations that show on /map."""
    
    def test_explored_location_is_discovered(self):
        """BUG: /explore created locations but /map showed '??? (undiscovered area)'."""
        world_map = create_starting_world()
        
        session = GameSession()
        session.world_map = world_map
        session.current_location = "Town Square"
        
        town_square = session.get_current_location_obj()
        
        # Generate new location via /explore
        new_loc = generate_random_location(town_square)
        
        # NEW FIX: Should be discovered=True
        assert new_loc.is_discovered == True, "Explored locations should be marked as discovered"
    
    def test_llm_enhanced_location_is_discovered(self):
        """Test LLM-enhanced locations are also discovered."""
        world_map = create_starting_world()
        town_square = world_map["Town Square"]
        
        # Mock LLM function
        def mock_llm(prompt):
            return "NAME: Test Cave\nDESCRIPTION: A dark cave for testing."
        
        new_loc = generate_llm_enhanced_location(
            town_square,
            mock_llm,
            {'npcs_present': [], 'time_of_day': 'morning', 'day': 1}
        )
        
        assert new_loc.is_discovered == True
    
    def test_map_shows_discovered_connections(self):
        """Test that /map displays discovered connected locations."""
        world_map = create_starting_world()
        
        session = GameSession()
        session.world_map = world_map
        session.current_location = "Forest Path"
        
        # Add a new discovered location
        new_cave = Location(
            name="Test Cave",
            location_type=LocationType.CAVE,
            description="A test cave",
            is_safe=False,
            is_discovered=True,
            connections=["Forest Path"]
        )
        session.add_location(new_cave)
        session.connect_locations("Forest Path", "Test Cave")
        
        # Get available destinations
        destinations = session.get_available_destinations()
        
        # Test Cave should be in connections
        assert "Test Cave" in destinations
        
        # Simulate /map display logic
        current_loc = session.get_current_location_obj()
        for dest in destinations:
            dest_loc = session.get_location(dest)
            
            if dest == "Test Cave":
                # Should NOT show "???" because is_discovered=True
                assert dest_loc.is_discovered == True


class TestStealValidation:
    """Test steal mechanics validation."""
    
    def test_steal_validates_item_exists(self):
        """Test steal validation checks if item exists at location."""
        validator = ActionValidator()
        
        # Setup location with healing potion
        location = Location(
            name="Test Inn",
            location_type=LocationType.TAVERN,
            description="A cozy inn",
            available_items=["Healing Potion"]
        )
        
        session = Mock()
        session.get_current_location_obj.return_value = location
        session.npcs_present = ["Innkeeper"]
        
        # Try to steal existing item
        intent = validator.analyze_intent("steal the healing potion")
        assert intent.action_type == ActionType.STEAL
        
        validation = validator.validate_action(intent, session)
        assert validation.result == ValidationResult.VALID
    
    def test_steal_fails_for_missing_item(self):
        """Test steal fails if item doesn't exist."""
        validator = ActionValidator()
        
        # Setup location WITHOUT healing potion
        location = Location(
            name="Test Inn",
            location_type=LocationType.TAVERN,
            description="A cozy inn",
            available_items=[]
        )
        
        session = Mock()
        session.get_current_location_obj.return_value = location
        session.npcs_present = ["Innkeeper"]
        
        # Try to steal non-existent item
        intent = validator.analyze_intent("steal the healing potion")
        validation = validator.validate_action(intent, session)
        
        assert validation.result == ValidationResult.INVALID
        assert "not here" in validation.message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
