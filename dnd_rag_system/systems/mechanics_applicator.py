"""
D&D Mechanics Applicator

Applies extracted game mechanics to CharacterState and PartyState objects.
Automatically updates HP, conditions, inventory, spell slots, etc.
"""

import logging
from typing import Dict, List, Any, Optional
from dnd_rag_system.systems.game_state import CharacterState, PartyState, Condition
from dnd_rag_system.systems.mechanics_extractor import ExtractedMechanics

logger = logging.getLogger(__name__)


class MechanicsApplicator:
    """
    Applies extracted mechanics to game state.

    Takes ExtractedMechanics and updates CharacterState/PartyState accordingly.
    """

    def __init__(self, debug: bool = False):
        """
        Initialize mechanics applicator.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug
        if self.debug:
            logger.setLevel(logging.DEBUG)

    def apply_to_character(
        self,
        mechanics: ExtractedMechanics,
        character_state: CharacterState
    ) -> List[str]:
        """
        Apply mechanics to a single character.

        Args:
            mechanics: Extracted mechanics
            character_state: Character to update

        Returns:
            List of feedback messages describing what was applied
        """
        feedback = []

        if not mechanics.has_mechanics():
            return feedback

        char_name = character_state.character_name

        # Apply damage
        for dmg in mechanics.damage:
            target = dmg.get("target", "").lower()
            if char_name.lower() in target or target == "you":
                amount = dmg.get("amount", 0)
                dmg_type = dmg.get("type", "untyped")

                result = character_state.take_damage(amount, dmg_type)
                feedback.append(result["message"])

                if self.debug:
                    logger.debug(f"💥 Applied {amount} {dmg_type} damage to {char_name}")

        # Apply healing
        for heal in mechanics.healing:
            target = heal.get("target", "").lower()
            if char_name.lower() in target or target == "you":
                amount = heal.get("amount", 0)
                source = heal.get("source", "healing")

                result = character_state.heal(amount)
                feedback.append(f"{result['message']} (from {source})")

                if self.debug:
                    logger.debug(f"❤️  Applied {amount} healing to {char_name} from {source}")

        # Apply conditions added
        for cond in mechanics.conditions_added:
            target = cond.get("target", "").lower()
            if char_name.lower() in target or target == "you":
                condition_name = cond.get("condition", "").lower()

                # Map to D&D 5e conditions
                try:
                    condition = Condition(condition_name)
                    character_state.add_condition(condition)
                    feedback.append(f"⚠️ {char_name} is now {condition_name}")

                    if self.debug:
                        logger.debug(f"🔴 Added condition '{condition_name}' to {char_name}")

                except ValueError:
                    # Not a standard D&D condition, add as custom
                    if condition_name not in character_state.conditions:
                        character_state.conditions.append(condition_name)
                        feedback.append(f"⚠️ {char_name} is now {condition_name}")

                        if self.debug:
                            logger.debug(f"🔴 Added custom condition '{condition_name}' to {char_name}")

        # Remove conditions
        for cond in mechanics.conditions_removed:
            target = cond.get("target", "").lower()
            if char_name.lower() in target or target == "you":
                condition_name = cond.get("condition", "").lower()

                try:
                    condition = Condition(condition_name)
                    removed = character_state.remove_condition(condition)
                    if removed:
                        feedback.append(f"✅ {char_name} is no longer {condition_name}")

                        if self.debug:
                            logger.debug(f"🟢 Removed condition '{condition_name}' from {char_name}")

                except ValueError:
                    # Custom condition
                    if condition_name in character_state.conditions:
                        character_state.conditions.remove(condition_name)
                        feedback.append(f"✅ {char_name} is no longer {condition_name}")

                        if self.debug:
                            logger.debug(f"🟢 Removed custom condition '{condition_name}' from {char_name}")

        # Apply spell slot usage
        for spell in mechanics.spell_slots_used:
            caster = spell.get("caster", "").lower()
            if char_name.lower() in caster or caster == "you":
                level = spell.get("level", 1)
                spell_name = spell.get("spell", "spell")

                used = character_state.spell_slots.use_slot(level)
                if used:
                    remaining = getattr(character_state.spell_slots, f"current_{level}")
                    feedback.append(f"✨ {char_name} used level {level} spell slot for {spell_name} ({remaining} remaining)")

                    if self.debug:
                        logger.debug(f"✨ Used level {level} spell slot for {spell_name} ({remaining} remaining)")
                else:
                    feedback.append(f"⚠️ {char_name} has no level {level} spell slots remaining!")

        # Apply item consumption
        for item in mechanics.items_consumed:
            user = item.get("character", "").lower()
            if char_name.lower() in user or user == "you":
                item_name = item.get("item", "item")
                quantity = item.get("quantity", 1)

                removed = character_state.remove_item(item_name, quantity)
                if removed:
                    feedback.append(f"🎒 {char_name} used {quantity}x {item_name}")

                    if self.debug:
                        logger.debug(f"🎒 Removed {quantity}x {item_name} from {char_name}'s inventory")
                else:
                    feedback.append(f"⚠️ {char_name} doesn't have {quantity}x {item_name}")

        # Handle death
        for death in mechanics.deaths:
            target = death.get("character", "").lower()
            if char_name.lower() in target or target == "you":
                character_state.current_hp = 0
                character_state.death_saves.failures = 3
                feedback.append(f"☠️ {char_name} has died!")

                if self.debug:
                    logger.debug(f"☠️ {char_name} died")

        # Handle unconscious
        for unconscious in mechanics.unconscious:
            target = unconscious.get("character", "").lower()
            if char_name.lower() in target or target == "you":
                if character_state.current_hp > 0:
                    character_state.current_hp = 0
                character_state.add_condition(Condition.UNCONSCIOUS)
                feedback.append(f"😵 {char_name} fell unconscious!")

                if self.debug:
                    logger.debug(f"😵 {char_name} is unconscious")

        return feedback

    def apply_to_party(
        self,
        mechanics: ExtractedMechanics,
        party: PartyState
    ) -> List[str]:
        """
        Apply mechanics to a party (applies to each member).

        Args:
            mechanics: Extracted mechanics
            party: Party to update

        Returns:
            List of feedback messages
        """
        all_feedback = []

        if not mechanics.has_mechanics():
            return all_feedback

        # Apply to each party member
        for char_name, char_state in party.characters.items():
            feedback = self.apply_to_character(mechanics, char_state)
            all_feedback.extend(feedback)

        return all_feedback

    def apply_with_logging(
        self,
        mechanics: ExtractedMechanics,
        character_state: Optional[CharacterState] = None,
        party: Optional[PartyState] = None
    ) -> List[str]:
        """
        Apply mechanics and log results (convenience method).

        Args:
            mechanics: Extracted mechanics
            character_state: Single character (optional)
            party: Party (optional)

        Returns:
            List of feedback messages
        """
        feedback = []

        if character_state:
            feedback = self.apply_to_character(mechanics, character_state)
        elif party:
            feedback = self.apply_to_party(mechanics, party)

        if feedback:
            print("\n" + "=" * 80)
            print("MECHANICS APPLIED TO GAME STATE:")
            print("-" * 80)
            for msg in feedback:
                print(f"  {msg}")
            print("=" * 80 + "\n")

        return feedback
