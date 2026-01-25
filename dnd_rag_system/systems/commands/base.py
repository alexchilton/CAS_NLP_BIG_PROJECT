"""
Base classes for the Command Pattern implementation.

Defines the abstract GameCommand class and supporting types.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from dnd_rag_system.systems.game_state import GameSession
    from dnd_rag_system.systems.combat_manager import CombatManager
    from dnd_rag_system.systems.spell_manager import SpellManager
    from dnd_rag_system.systems.shop_system import ShopSystem


@dataclass
class CommandContext:
    """
    Context object passed to command handlers.

    Contains all the dependencies and state a command might need.
    """
    session: 'GameSession'
    combat_manager: 'CombatManager'
    spell_manager: 'SpellManager'
    shop_system: 'ShopSystem'
    debug: bool = False


@dataclass
class CommandResult:
    """
    Result of executing a command.

    Attributes:
        handled: Whether the command was recognized and handled
        feedback: User-facing feedback message (markdown supported)
        error: Optional error message if command failed
    """
    handled: bool
    feedback: str = ""
    error: Optional[str] = None

    @classmethod
    def not_handled(cls) -> 'CommandResult':
        """Factory method for unhandled command."""
        return cls(handled=False)

    @classmethod
    def success(cls, feedback: str) -> 'CommandResult':
        """Factory method for successful command."""
        return cls(handled=True, feedback=feedback)

    @classmethod
    def failure(cls, error_message: str) -> 'CommandResult':
        """Factory method for failed command."""
        return cls(handled=True, error=error_message, feedback=f"⚠️ {error_message}")


class GameCommand(ABC):
    """
    Abstract base class for all game commands.

    Subclasses implement specific command logic (combat, spells, items, etc.)
    following the Command Pattern.
    """

    def __init__(self, debug: bool = False):
        """
        Initialize command.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug

    @abstractmethod
    def get_patterns(self) -> List[str]:
        """
        Get command patterns this handler recognizes.

        Returns:
            List of command patterns (can include prefixes like '/cast')

        Examples:
            - ['/start_combat', '/combat'] - exact matches
            - ['/use '] - prefix match (trailing space matters)
        """
        pass

    @abstractmethod
    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """
        Execute the command.

        Args:
            user_input: Original user input (e.g., "/cast Fireball at goblin")
            context: Command context with game state and managers

        Returns:
            CommandResult with feedback or error
        """
        pass

    def matches(self, user_input: str) -> bool:
        """
        Check if this command matches the user input.

        Args:
            user_input: User input to check

        Returns:
            True if this command should handle the input
        """
        lower_input = user_input.lower().strip()

        for pattern in self.get_patterns():
            # Exact match
            if lower_input == pattern.lower():
                return True

            # Prefix match (for commands with arguments like "/cast Fireball")
            if pattern.endswith(' ') and lower_input.startswith(pattern.lower()):
                return True

        return False
