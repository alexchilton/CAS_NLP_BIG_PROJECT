#!/usr/bin/env python3
"""
Unit tests for the Command Pattern implementation.

Tests all command handlers to ensure they:
1. Match the correct patterns
2. Execute successfully
3. Return appropriate feedback
4. Update game state correctly
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import Mock, MagicMock

from dnd_rag_system.systems.commands.base import GameCommand, CommandContext, CommandResult
from dnd_rag_system.systems.commands.combat import (
    StartCombatCommand, NextTurnCommand, FleeCommand, EndCombatCommand, InitiativeCommand
)
from dnd_rag_system.systems.commands.character import (
    UseItemCommand, PickupItemCommand, DeathSaveCommand,
    ShortRestCommand, LongRestCommand, LevelUpCommand
)
from dnd_rag_system.systems.commands.magic import CastSpellCommand
from dnd_rag_system.systems.commands.travel import TravelCommand, MapCommand, LocationsCommand
from dnd_rag_system.systems.commands.dispatcher import CommandDispatcher
from dnd_rag_system.systems.game_state import GameSession, CharacterState


class TestCommandBase:
    """Test base command functionality."""

    def test_command_result_factories(self):
        """Test CommandResult factory methods."""
        # Not handled
        result = CommandResult.not_handled()
        assert result.handled == False
        assert result.feedback == ""
        assert result.error is None

        # Success
        result = CommandResult.success("Great!")
        assert result.handled == True
        assert result.feedback == "Great!"
        assert result.error is None

        # Failure
        result = CommandResult.failure("Failed!")
        assert result.handled == True
        assert result.error == "Failed!"
        assert "⚠️" in result.feedback


class TestCombatCommands:
    """Test combat command handlers."""

    @pytest.fixture
    def context(self):
        """Create mock command context."""
        session = GameSession()
        combat_manager = Mock()
        spell_manager = Mock()
        shop_system = Mock()

        return CommandContext(
            session=session,
            combat_manager=combat_manager,
            spell_manager=spell_manager,
            shop_system=shop_system,
            debug=False
        )

    def test_start_combat_pattern_matching(self):
        """Test StartCombatCommand pattern matching."""
        cmd = StartCombatCommand()

        assert cmd.matches("/start_combat")
        assert cmd.matches("/start_combat Goblin")
        assert cmd.matches("/start_combat Goblin, Orc, Dragon")
        assert not cmd.matches("/combat")
        assert not cmd.matches("start combat")

    def test_start_combat_with_npcs(self, context):
        """Test starting combat with specified NPCs."""
        cmd = StartCombatCommand()
        context.session.character_state = Mock(character_name="Hero", armor_class=15)
        context.combat_manager.start_combat_with_character.return_value = "Combat started!"
        context.combat_manager.get_current_turn_name.return_value = "Hero"
        context.combat_manager.npc_monsters = {}  # Empty dict (Hero's turn, not NPC)

        result = cmd.execute("/start_combat Goblin, Orc", context)

        assert result.handled == True
        assert "Combat started!" in result.feedback
        context.combat_manager.start_combat_with_character.assert_called_once()
        assert "Goblin" in context.session.npcs_present
        assert "Orc" in context.session.npcs_present

    def test_start_combat_no_character(self, context):
        """Test starting combat with no character loaded."""
        cmd = StartCombatCommand()
        context.session.character_state = None

        result = cmd.execute("/start_combat Goblin", context)

        assert result.handled == True
        assert result.error is not None

    def test_next_turn_pattern_matching(self):
        """Test NextTurnCommand pattern matching."""
        cmd = NextTurnCommand()

        assert cmd.matches("/next_turn")
        assert cmd.matches("/next")
        assert not cmd.matches("/next_round")

    def test_next_turn_no_combat(self, context):
        """Test advancing turn with no active combat."""
        cmd = NextTurnCommand()
        context.session.combat.in_combat = False

        result = cmd.execute("/next", context)

        assert result.handled == True
        assert result.error is not None

    def test_flee_command(self, context):
        """Test flee command."""
        cmd = FleeCommand()
        context.session.combat.in_combat = True
        context.combat_manager.flee_combat.return_value = "You flee!"

        result = cmd.execute("/flee", context)

        assert result.handled == True
        assert "You flee!" in result.feedback

    def test_end_combat_command(self, context):
        """Test end combat command."""
        cmd = EndCombatCommand()
        context.session.combat.in_combat = True
        context.combat_manager.end_combat.return_value = "Combat ended! +50 XP"

        result = cmd.execute("/end_combat", context)

        assert result.handled == True
        assert "Combat ended" in result.feedback

    def test_initiative_command(self, context):
        """Test initiative command."""
        cmd = InitiativeCommand()
        context.session.combat.in_combat = True
        context.combat_manager.show_initiative.return_value = "Initiative: Hero (15), Goblin (10)"

        result = cmd.execute("/initiative", context)

        assert result.handled == True
        assert "Initiative" in result.feedback


class TestCharacterCommands:
    """Test character command handlers."""

    @pytest.fixture
    def context(self):
        """Create mock command context with character."""
        session = GameSession()
        session.character_state = Mock()
        session.character_state.inventory = {"Healing Potion": 1, "Rope": 1}
        session.character_state.character_name = "Hero"

        combat_manager = Mock()
        spell_manager = Mock()
        shop_system = Mock()

        return CommandContext(
            session=session,
            combat_manager=combat_manager,
            spell_manager=spell_manager,
            shop_system=shop_system,
            debug=False
        )

    def test_use_item_success(self, context):
        """Test using an item from inventory."""
        cmd = UseItemCommand()
        context.session.character_state.remove_item = Mock()

        result = cmd.execute("/use Healing Potion", context)

        assert result.handled == True
        assert "Healing Potion" in result.feedback
        context.session.character_state.remove_item.assert_called_once()

    def test_use_item_not_in_inventory(self, context):
        """Test using an item not in inventory."""
        cmd = UseItemCommand()

        result = cmd.execute("/use Dragon Scale", context)

        assert result.handled == True
        assert result.error is not None
        assert "don't have" in result.feedback.lower()

    def test_use_item_no_item_specified(self, context):
        """Test /use with no item name."""
        cmd = UseItemCommand()

        result = cmd.execute("/use", context)

        assert result.handled == True
        assert result.error is not None

    def test_pickup_item_success(self, context):
        """Test picking up an item from location."""
        cmd = PickupItemCommand()

        # Mock location with item
        mock_location = Mock()
        mock_location.has_item.return_value = True
        mock_location.remove_item = Mock()
        context.session.get_current_location_obj = Mock(return_value=mock_location)
        context.session.character_state.add_item = Mock()

        result = cmd.execute("/pickup Rope", context)

        assert result.handled == True
        assert "Picked up" in result.feedback
        mock_location.remove_item.assert_called_once()
        context.session.character_state.add_item.assert_called_once()

    def test_death_save_success(self, context):
        """Test death saving throw."""
        cmd = DeathSaveCommand()
        context.session.character_state.is_conscious.return_value = False
        context.session.character_state.current_hp = 0

        # Configure death_saves mock properly
        mock_death_saves = Mock()
        mock_death_saves.add_success.return_value = (False, "Success!")
        mock_death_saves.add_failure.return_value = (False, "Failure!")
        mock_death_saves.is_dead.return_value = False
        mock_death_saves.is_stable.return_value = False
        mock_death_saves.successes = 1
        mock_death_saves.failures = 0
        context.session.character_state.death_saves = mock_death_saves

        result = cmd.execute("/death_save", context)

        assert result.handled == True
        # Should have some feedback about the roll
        assert len(result.feedback) > 0

    def test_death_save_while_conscious(self, context):
        """Test death save while conscious (should fail)."""
        cmd = DeathSaveCommand()
        context.session.character_state.is_conscious.return_value = True

        result = cmd.execute("/death_save", context)

        assert result.handled == True
        assert result.error is not None

    def test_short_rest_success(self, context):
        """Test short rest."""
        cmd = ShortRestCommand()
        context.session.character_state.hit_dice_current = 3
        context.session.character_state.hit_dice_max = 5
        context.session.character_state.current_hp = 10
        context.session.character_state.max_hp = 20
        context.session.character_state.short_rest.return_value = {
            'message': 'Healed 5 HP'
        }

        result = cmd.execute("/rest", context)

        assert result.handled == True
        assert "Short Rest" in result.feedback

    def test_long_rest_success(self, context):
        """Test long rest."""
        cmd = LongRestCommand()
        context.session.character_state.current_hp = 20
        context.session.character_state.max_hp = 20
        context.session.character_state.hit_dice_current = 5
        context.session.character_state.hit_dice_max = 5
        context.session.character_state.long_rest.return_value = {
            'message': 'Fully restored'
        }

        result = cmd.execute("/long_rest", context)

        assert result.handled == True
        assert "Long Rest" in result.feedback


class TestMagicCommands:
    """Test magic command handlers."""

    @pytest.fixture
    def context(self):
        """Create mock command context."""
        session = GameSession()
        session.character_state = Mock(character_name="Wizard")

        combat_manager = Mock()
        spell_manager = Mock()
        shop_system = Mock()

        return CommandContext(
            session=session,
            combat_manager=combat_manager,
            spell_manager=spell_manager,
            shop_system=shop_system,
            debug=False
        )

    def test_cast_spell_success(self, context):
        """Test casting a spell successfully."""
        cmd = CastSpellCommand()
        context.spell_manager.cast_spell.return_value = {
            'success': True,
            'message': 'Fireball explodes!',
            'slot_used': True
        }
        context.spell_manager.get_spell_slots_display.return_value = "Slots: 3/4"

        result = cmd.execute("/cast Fireball at goblin", context)

        assert result.handled == True
        assert "Fireball" in result.feedback
        context.spell_manager.cast_spell.assert_called_once_with(
            character=context.session.character_state,
            spell_name="Fireball",
            target="goblin"
        )

    def test_cast_spell_failure(self, context):
        """Test casting a spell that fails."""
        cmd = CastSpellCommand()
        context.spell_manager.cast_spell.return_value = {
            'success': False,
            'message': 'No spell slots remaining'
        }

        result = cmd.execute("/cast Magic Missile", context)

        assert result.handled == True
        assert result.error is not None


class TestTravelCommands:
    """Test travel command handlers."""

    @pytest.fixture
    def context(self):
        """Create mock command context."""
        session = Mock(spec=GameSession)
        session.current_location = "Town"
        session.world_map = {}
        combat_manager = Mock()
        spell_manager = Mock()
        shop_system = Mock()

        return CommandContext(
            session=session,
            combat_manager=combat_manager,
            spell_manager=spell_manager,
            shop_system=shop_system,
            debug=False
        )

    def test_travel_success(self, context):
        """Test traveling to a location."""
        cmd = TravelCommand()

        # Mock location
        mock_location = Mock()
        mock_location.name = "Tavern"
        mock_location.description = "A cozy tavern"
        mock_location.available_items = ["Ale", "Bread"]
        mock_location.resident_npcs = ["Bartender"]

        context.session.travel_to.return_value = (True, "You travel to Tavern")
        context.session.get_current_location_obj.return_value = mock_location

        result = cmd.execute("/travel Tavern", context)

        assert result.handled == True
        assert "Tavern" in result.feedback
        assert "cozy tavern" in result.feedback

    def test_travel_location_not_found(self, context):
        """Test traveling to unknown location."""
        cmd = TravelCommand()
        context.session.travel_to.return_value = (False, "Location not found")
        context.session.world_map = {"Town": Mock(), "Forest": Mock()}

        result = cmd.execute("/travel Unknown Place", context)

        assert result.handled == True
        assert result.error is not None

    def test_map_command(self, context):
        """Test map command."""
        cmd = MapCommand()
        context.session.current_location = "Town"
        context.session.get_discovered_locations.return_value = ["Town", "Forest", "Cave"]

        # Mock location objects
        mock_loc = Mock()
        mock_loc.description = "A small town"
        mock_loc.resident_npcs = ["Mayor"]
        context.session.get_location.return_value = mock_loc

        result = cmd.execute("/map", context)

        assert result.handled == True
        assert "World Map" in result.feedback
        assert "Town" in result.feedback


class TestCommandDispatcher:
    """Test command dispatcher integration."""

    def test_dispatcher_initialization(self):
        """Test dispatcher initializes with all commands."""
        dispatcher = CommandDispatcher(debug=False)

        # Should have all 15 command handlers
        assert len(dispatcher.commands) == 15

    def test_dispatcher_routes_combat_command(self):
        """Test dispatcher routes combat commands correctly."""
        dispatcher = CommandDispatcher(debug=False)

        session = GameSession()
        session.character_state = Mock(character_name="Hero")
        context = CommandContext(
            session=session,
            combat_manager=Mock(),
            spell_manager=Mock(),
            shop_system=Mock(),
            debug=False
        )
        context.combat_manager.start_combat_with_character.return_value = "Combat!"
        context.combat_manager.get_current_turn_name.return_value = "Hero"

        result = dispatcher.dispatch("/start_combat Goblin", context)

        assert result.handled == True

    def test_dispatcher_unhandled_command(self):
        """Test dispatcher returns not_handled for unknown commands."""
        dispatcher = CommandDispatcher(debug=False)

        session = GameSession()
        context = CommandContext(
            session=session,
            combat_manager=Mock(),
            spell_manager=Mock(),
            shop_system=Mock(),
            debug=False
        )

        result = dispatcher.dispatch("/unknown_command", context)

        assert result.handled == False

    def test_dispatcher_get_command_list(self):
        """Test getting list of all command patterns."""
        dispatcher = CommandDispatcher(debug=False)

        commands = dispatcher.get_command_list()

        # Should have all command patterns
        assert "/start_combat" in commands
        assert "/cast " in commands
        assert "/travel " in commands
        assert len(commands) > 15  # Some commands have multiple patterns


def run_tests():
    """Run all tests."""
    print("=" * 70)
    print("COMMAND SYSTEM UNIT TESTS")
    print("=" * 70)
    print()

    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == '__main__':
    run_tests()
