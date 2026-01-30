"""
Combat-related commands.

Handles: /start_combat, /next_turn, /flee, /end_combat, /initiative
"""

import logging
from typing import List

from .base import GameCommand, CommandResult, CommandContext
from dnd_rag_system.constants import Commands

logger = logging.getLogger(__name__)


class StartCombatCommand(GameCommand):
    """Handle /start_combat [NPCs] command."""

    def get_patterns(self) -> List[str]:
        return [Commands.START_COMBAT, '/start_combat ']  # Exact + with arguments

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Start combat with specified or existing NPCs."""
        # Parse NPCs from command: /start_combat Goblin, Orc, Dragon
        npc_list = []
        if ' ' in user_input:
            npc_text = user_input.split(' ', 1)[1]
            npc_list = [npc.strip() for npc in npc_text.split(',')]

        # Use existing NPCs if no list provided
        if not npc_list:
            npc_list = context.session.npcs_present

        if not npc_list:
            return CommandResult.failure("No NPCs specified and none present in scene!")

        # Start combat with party or single character
        if context.session.party and len(context.session.party.characters) > 0:
            feedback = context.combat_manager.start_combat_with_party(
                context.session.party,
                npc_list,
                session=context.session
            )
        elif context.session.character_state:
            feedback = context.combat_manager.start_combat_with_character(
                context.session.character_state,
                npc_list,
                session=context.session
            )
        else:
            return CommandResult.failure("No character or party loaded!")

        # Add NPCs to session for targeting
        for npc in npc_list:
            if npc not in context.session.npcs_present:
                context.session.npcs_present.append(npc)
                if self.debug:
                    logger.debug(f"🎭 Added {npc} to npcs_present for combat targeting")

        # If combat starts with NPC's turn, process NPC turns immediately
        current_turn = context.combat_manager.get_current_turn_name()
        if current_turn and current_turn in context.combat_manager.npc_monsters:
            # Get player AC for NPC targeting
            target_ac = 15  # Default
            if context.session.party:
                # Use first character's AC (TODO: Improve targeting logic)
                if context.session.party.characters:
                    target_ac = context.session.party.characters[0].armor_class
            elif context.session.character_state:
                target_ac = context.session.character_state.armor_class

            npc_feedback = context.combat_manager.process_npc_turn(target_ac=target_ac)
            feedback += f"\n\n{npc_feedback}"

        return CommandResult.success(feedback)


class NextTurnCommand(GameCommand):
    """Handle /next_turn command."""

    def get_patterns(self) -> List[str]:
        return ['/next_turn', '/next']

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Advance to next turn in combat."""
        if not context.session.combat or not context.session.combat.in_combat:
            return CommandResult.failure("No active combat!")

        feedback = context.combat_manager.next_turn()

        # If it's an NPC's turn, process it automatically
        current_turn = context.combat_manager.get_current_turn_name()
        if current_turn and current_turn in context.combat_manager.npc_monsters:
            # Get player AC for NPC targeting
            target_ac = 15  # Default
            if context.session.party and context.session.party.characters:
                target_ac = context.session.party.characters[0].armor_class
            elif context.session.character_state:
                target_ac = context.session.character_state.armor_class

            npc_feedback = context.combat_manager.process_npc_turn(target_ac=target_ac)
            feedback += f"\n\n{npc_feedback}"

        return CommandResult.success(feedback)


class FleeCommand(GameCommand):
    """Handle /flee command."""

    def get_patterns(self) -> List[str]:
        return ['/flee', '/run', '/escape']

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Attempt to flee from combat."""
        if not context.session.combat or not context.session.combat.in_combat:
            return CommandResult.failure("No active combat to flee from!")

        feedback = context.combat_manager.flee_combat()
        return CommandResult.success(feedback)


class EndCombatCommand(GameCommand):
    """Handle /end_combat command."""

    def get_patterns(self) -> List[str]:
        return [Commands.END_COMBAT]  # '/end_combat'

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """End combat and award XP."""
        if not context.session.combat or not context.session.combat.in_combat:
            return CommandResult.failure("No active combat!")

        feedback = context.combat_manager.end_combat()
        return CommandResult.success(feedback)


class InitiativeCommand(GameCommand):
    """Handle /initiative command."""

    def get_patterns(self) -> List[str]:
        return [Commands.INITIATIVE]  # '/initiative'

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Show current initiative order."""
        if not context.session.combat or not context.session.combat.in_combat:
            return CommandResult.failure("No active combat!")

        feedback = context.combat_manager.show_initiative()
        return CommandResult.success(feedback)
