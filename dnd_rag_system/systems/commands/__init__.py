"""
Game Command System for D&D RAG.

Implements the Command Pattern to handle slash commands (/start_combat, /cast, /use, etc.)
in a modular, testable way.
"""

from .base import GameCommand, CommandResult, CommandContext
from .dispatcher import CommandDispatcher

__all__ = [
    'GameCommand',
    'CommandResult',
    'CommandContext',
    'CommandDispatcher',
]
