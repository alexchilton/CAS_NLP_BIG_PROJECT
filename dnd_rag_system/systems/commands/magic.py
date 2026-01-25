"""
Magic and spell-related commands.

Handles: /cast
"""

import logging
from typing import List

from .base import GameCommand, CommandResult, CommandContext

logger = logging.getLogger(__name__)


class CastSpellCommand(GameCommand):
    """Handle /cast <spell> [at target] command."""

    def get_patterns(self) -> List[str]:
        return ['/cast ']  # Trailing space for prefix match

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Cast a spell."""
        if not context.session.character_state:
            return CommandResult.error("No character loaded!")

        # Extract spell name and target from command
        # Examples: "/cast Fireball at goblin", "/cast Cure Wounds", "/cast Magic Missile"
        command_text = user_input.split(' ', 1)[1].strip() if ' ' in user_input else ""
        if not command_text:
            return CommandResult.error("Specify a spell to cast! Example: /cast Fireball")

        # Parse spell name and target
        spell_name = command_text
        target = None

        # Look for " at " or " on " to extract target
        for separator in [' at ', ' on ', ' towards ']:
            if separator in command_text.lower():
                parts = command_text.split(separator, 1)
                spell_name = parts[0].strip()
                target = parts[1].strip() if len(parts) > 1 else None
                break

        # Use spell manager to cast spell
        result = context.spell_manager.cast_spell(
            character=context.session.character_state,
            spell_name=spell_name,
            target=target
        )

        if result['success']:
            feedback = f"✨ **{spell_name}** cast successfully!\n\n"
            feedback += result.get('message', '')

            # Show remaining spell slots
            if result.get('slot_used'):
                slots_info = context.spell_manager.get_spell_slots_display(context.session.character_state)
                feedback += f"\n\n{slots_info}"

            return CommandResult.success(feedback)
        else:
            return CommandResult.error(result.get('message', 'Failed to cast spell'))
