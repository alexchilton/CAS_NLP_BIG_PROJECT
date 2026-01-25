"""
Character-related commands.

Handles: /use, /pickup, /death_save, /rest, /short_rest, /long_rest, /level_up
"""

import logging
import random
from typing import List

from .base import GameCommand, CommandResult, CommandContext
from dnd_rag_system.constants import Commands

logger = logging.getLogger(__name__)


class UseItemCommand(GameCommand):
    """Handle /use <item> command."""

    def get_patterns(self) -> List[str]:
        return ['/use ']  # Trailing space for prefix match

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Use an item from inventory."""
        if not context.session.character_state:
            return CommandResult.error("No character loaded!")

        # Extract item name
        item_name = user_input.split(' ', 1)[1].strip() if ' ' in user_input else ""
        if not item_name:
            return CommandResult.error("Specify an item to use! Example: /use Healing Potion")

        # Check if character has the item
        if item_name not in context.session.character_state.inventory:
            inventory_preview = ", ".join(context.session.character_state.inventory[:5])
            return CommandResult.error(
                f"You don't have '{item_name}'!\n\nInventory: {inventory_preview}"
            )

        # TODO: Implement actual item effects (healing potions, etc.)
        # For now, just remove from inventory and provide feedback
        context.session.character_state.remove_item(item_name, 1)

        feedback = f"✅ Used **{item_name}**\n\n"
        feedback += f"*Item removed from inventory. Ask GM for effects.*"

        return CommandResult.success(feedback)


class PickupItemCommand(GameCommand):
    """Handle /pickup <item> command."""

    def get_patterns(self) -> List[str]:
        return ['/pickup ']  # Trailing space for prefix match

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Pick up an item from current location."""
        if not context.session.character_state:
            return CommandResult.error("No character loaded!")

        # Extract item name
        item_name = user_input.split(' ', 1)[1].strip() if ' ' in user_input else ""
        if not item_name:
            return CommandResult.error("Specify an item to pick up! Example: /pickup Rope")

        # Get current location
        current_loc = context.session.get_current_location_obj()
        if not current_loc:
            return CommandResult.error("No location information available.")

        # Check if item exists at location
        if not current_loc.has_item(item_name):
            available = ", ".join(current_loc.available_items[:5]) if current_loc.available_items else "nothing"
            return CommandResult.error(
                f"'{item_name}' is not here.\n\nYou see: {available}"
            )

        # Move item from location to inventory
        current_loc.remove_item(item_name, moved_to="inventory")
        context.session.character_state.add_item(item_name, 1)

        return CommandResult.success(f"✅ Picked up **{item_name}**")


class DeathSaveCommand(GameCommand):
    """Handle /death_save command."""

    def get_patterns(self) -> List[str]:
        return [Commands.DEATH_SAVE]  # '/death_save'

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Make a death saving throw."""
        if not context.session.character_state:
            return CommandResult.error("No character state loaded!")

        if context.session.character_state.is_conscious():
            return CommandResult.error(
                "You are not unconscious! Death saving throws are only for unconscious characters (0 HP)."
            )

        # Roll d20 for death saving throw
        roll = random.randint(1, 20)

        feedback = f"🎲 **Death Saving Throw**: Rolled **{roll}**\n\n"

        # Handle critical rolls first
        if roll == 20:
            # Natural 20: Regain 1 HP and stabilize
            context.session.character_state.current_hp = 1
            context.session.character_state.death_saves.reset()
            feedback += "🌟 **Natural 20!** You regain 1 HP and regain consciousness!\n\n"
            feedback += f"✅ You are now at **1/{context.session.character_state.max_hp} HP**"

        elif roll == 1:
            # Natural 1: Count as 2 failures
            dead, msg1 = context.session.character_state.death_saves.add_failure()
            if not dead:
                dead, msg2 = context.session.character_state.death_saves.add_failure()
                feedback += f"💀 **Natural 1!** That counts as **2 failures**!\n\n"
                feedback += f"❌ {msg2}"
                if dead:
                    feedback += "\n\n☠️ **YOU HAVE DIED** ☠️"
            else:
                feedback += f"💀 **Natural 1!** {msg1}\n\n☠️ **YOU HAVE DIED** ☠️"

        elif roll >= 10:
            # Success
            stabilized, msg = context.session.character_state.death_saves.add_success()
            feedback += f"✅ **Success!** {msg}"
            if stabilized:
                feedback += "\n\n🛡️ You are **stabilized** at 0 HP (no longer dying, but still unconscious)."

        else:
            # Failure
            dead, msg = context.session.character_state.death_saves.add_failure()
            feedback += f"❌ **Failure!** {msg}"
            if dead:
                feedback += "\n\n☠️ **YOU HAVE DIED** ☠️"

        # Show current death save status (unless dead or stabilized)
        if (context.session.character_state.current_hp == 0 and
            not context.session.character_state.death_saves.is_dead()):
            if not context.session.character_state.death_saves.is_stable():
                feedback += f"\n\n**Death Saves**: "
                feedback += f"✅ {context.session.character_state.death_saves.successes}/3 | "
                feedback += f"❌ {context.session.character_state.death_saves.failures}/3"

        return CommandResult.success(feedback)


class ShortRestCommand(GameCommand):
    """Handle /rest and /short_rest commands."""

    def get_patterns(self) -> List[str]:
        return ['/rest', '/short_rest']

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Take a short rest to spend hit dice and heal."""
        if not context.session.character_state:
            return CommandResult.error("No character state loaded!")

        char_state = context.session.character_state

        # Check if character has hit dice to spend
        if char_state.hit_dice_current <= 0:
            feedback = f"⚠️ You have no hit dice remaining!\n\n"
            feedback += f"Hit Dice: {char_state.hit_dice_current}/{char_state.hit_dice_max}\n\n"
            feedback += f"You need a long rest to recover hit dice."
            return CommandResult.error(feedback)

        if char_state.current_hp >= char_state.max_hp:
            feedback = f"⚠️ You're already at full HP ({char_state.current_hp}/{char_state.max_hp})!\n\n"
            feedback += f"Short rests are primarily for healing. You don't need one right now."
            return CommandResult.error(feedback)

        # Spend 1 hit die to heal
        rest_result = char_state.short_rest(hit_dice_spent=1)

        feedback = f"🛏️ **Short Rest (1 hour)**\n\n"
        feedback += f"{rest_result['message']}\n\n"
        feedback += f"**Current Status:**\n"
        feedback += f"- HP: {char_state.current_hp}/{char_state.max_hp}\n"
        feedback += f"- Hit Dice: {char_state.hit_dice_current}/{char_state.hit_dice_max}\n\n"
        feedback += f"💡 *You can take another short rest if needed, or `/long_rest` to fully recover.*"

        return CommandResult.success(feedback)


class LongRestCommand(GameCommand):
    """Handle /long_rest command."""

    def get_patterns(self) -> List[str]:
        return ['/long_rest', '/longrest']

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Take a long rest to fully restore HP, hit dice, and spell slots."""
        if not context.session.character_state:
            return CommandResult.error("No character state loaded!")

        char_state = context.session.character_state

        # Take long rest
        rest_result = char_state.long_rest()

        feedback = f"🌙 **Long Rest (8 hours)**\n\n"
        feedback += f"{rest_result['message']}\n\n"
        feedback += f"**Fully Restored:**\n"
        feedback += f"- HP: {char_state.current_hp}/{char_state.max_hp}\n"
        feedback += f"- Hit Dice: {char_state.hit_dice_current}/{char_state.hit_dice_max}\n"
        feedback += f"- Spell Slots: All spell slots restored\n\n"
        feedback += f"✨ *You wake refreshed and ready for adventure!*"

        return CommandResult.success(feedback)


class LevelUpCommand(GameCommand):
    """Handle /level_up command."""

    def get_patterns(self) -> List[str]:
        return ['/level_up', '/levelup']

    def execute(self, user_input: str, context: CommandContext) -> CommandResult:
        """Level up the character."""
        if not context.session.character_state:
            return CommandResult.error("No character state loaded!")

        char_state = context.session.character_state

        # Check if character has enough XP to level up
        required_xp = char_state.xp_for_next_level()
        if char_state.experience_points < required_xp:
            feedback = f"⚠️ Not enough XP to level up!\n\n"
            feedback += f"Current XP: {char_state.experience_points}\n"
            feedback += f"Required for Level {char_state.level + 1}: {required_xp}\n"
            feedback += f"XP Needed: {required_xp - char_state.experience_points}"
            return CommandResult.error(feedback)

        # Level up
        level_up_result = char_state.level_up()

        feedback = f"🎉 **LEVEL UP!** 🎉\n\n"
        feedback += f"{level_up_result['message']}\n\n"
        feedback += f"**New Stats:**\n"
        feedback += f"- Level: {char_state.level}\n"
        feedback += f"- Max HP: {char_state.max_hp}\n"
        feedback += f"- Proficiency Bonus: +{char_state.proficiency_bonus}\n"

        if level_up_result.get('new_spell_slots'):
            feedback += f"\n**New Spell Slots:** {level_up_result['new_spell_slots']}"

        return CommandResult.success(feedback)
