"""
Command Dispatcher for routing user input to appropriate command handlers.

Implements the Command Pattern to replace the massive if/elif block in GameMaster.
"""

import logging
from typing import List, Optional

from .base import GameCommand, CommandResult, CommandContext
from .combat import (
    StartCombatCommand,
    NextTurnCommand,
    FleeCommand,
    EndCombatCommand,
    InitiativeCommand
)
from .character import (
    UseItemCommand,
    PickupItemCommand,
    DeathSaveCommand,
    ShortRestCommand,
    LongRestCommand,
    LevelUpCommand
)
from .magic import CastSpellCommand
from .travel import TravelCommand, MapCommand, LocationsCommand

logger = logging.getLogger(__name__)


class CommandDispatcher:
    """
    Dispatches user commands to appropriate handlers.

    Replaces the massive if/elif chain in GameMaster with a clean,
    extensible command registry using the Command Pattern.
    """

    def __init__(self, debug: bool = False):
        """
        Initialize command dispatcher.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug
        self.commands: List[GameCommand] = []

        # Register all command handlers
        self._register_commands()

    def _register_commands(self):
        """Register all available command handlers."""
        # Combat commands
        self.commands.append(StartCombatCommand(debug=self.debug))
        self.commands.append(NextTurnCommand(debug=self.debug))
        self.commands.append(FleeCommand(debug=self.debug))
        self.commands.append(EndCombatCommand(debug=self.debug))
        self.commands.append(InitiativeCommand(debug=self.debug))

        # Character commands
        self.commands.append(UseItemCommand(debug=self.debug))
        self.commands.append(PickupItemCommand(debug=self.debug))
        self.commands.append(DeathSaveCommand(debug=self.debug))
        self.commands.append(ShortRestCommand(debug=self.debug))
        self.commands.append(LongRestCommand(debug=self.debug))
        self.commands.append(LevelUpCommand(debug=self.debug))

        # Magic commands
        self.commands.append(CastSpellCommand(debug=self.debug))

        # Travel commands
        self.commands.append(TravelCommand(debug=self.debug))
        self.commands.append(MapCommand(debug=self.debug))
        self.commands.append(LocationsCommand(debug=self.debug))

    def dispatch(self, user_input: str, context: CommandContext) -> CommandResult:
        """
        Dispatch user input to appropriate command handler.

        Args:
            user_input: Raw user input (e.g., "/cast Fireball at goblin")
            context: Command context with game state and managers

        Returns:
            CommandResult indicating if command was handled and any feedback
        """
        if not user_input or not user_input.strip():
            return CommandResult.not_handled()

        # Try each command handler in order
        for command in self.commands:
            if command.matches(user_input):
                if self.debug:
                    logger.debug(f"🎯 Dispatching to {command.__class__.__name__}: {user_input}")

                try:
                    result = command.execute(user_input, context)
                    if self.debug and result.handled:
                        logger.debug(f"✅ Command handled by {command.__class__.__name__}")
                    return result

                except Exception as e:
                    logger.error(f"❌ Command {command.__class__.__name__} failed: {e}")
                    import traceback
                    traceback.print_exc()
                    return CommandResult.failure(f"Command failed: {e}")

        # No handler matched
        if self.debug:
            logger.debug(f"⚠️ No command handler matched: {user_input}")

        return CommandResult.not_handled()

    def add_command(self, command: GameCommand):
        """
        Add a custom command handler.

        Allows plugins or extensions to register new commands.

        Args:
            command: Command handler to register
        """
        self.commands.append(command)
        if self.debug:
            logger.debug(f"➕ Registered command: {command.__class__.__name__}")

    def get_command_list(self) -> List[str]:
        """
        Get list of all registered command patterns.

        Useful for help text generation.

        Returns:
            List of command patterns
        """
        patterns = []
        for command in self.commands:
            patterns.extend(command.get_patterns())
        return sorted(set(patterns))  # Deduplicate and sort
