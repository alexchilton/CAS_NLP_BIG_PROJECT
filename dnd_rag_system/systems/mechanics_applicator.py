"""
D&D Mechanics Applicator

Applies extracted game mechanics to CharacterState and PartyState objects.
Automatically updates HP, conditions, inventory, spell slots, etc.
"""

import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from dnd_rag_system.systems.game_state import CharacterState, PartyState, Condition
from dnd_rag_system.systems.mechanics_extractor import ExtractedMechanics

if TYPE_CHECKING:
    from dnd_rag_system.systems.game_state import GameSession

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
        character_state: CharacterState,
        game_session: Optional['GameSession'] = None
    ) -> List[str]:
        """
        Apply mechanics to a single character.

        Args:
            mechanics: Extracted mechanics
            character_state: Character to update
            game_session: Optional game session for location item tracking

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
        
        # Apply item acquisition
        for item in mechanics.items_acquired:
            acquirer = item.get("character", "").lower()
            if char_name.lower() in acquirer or acquirer == "you":
                item_name = item.get("item", "item")
                quantity = item.get("quantity", 1)

                character_state.add_item(item_name, quantity)
                feedback.append(f"📦 {char_name} acquired {quantity}x {item_name}")

                # Remove from location if game session provided
                if game_session:
                    current_loc = game_session.get_current_location_obj()
                    if current_loc and current_loc.has_item(item_name):
                        current_loc.remove_item(item_name, moved_to=f"{char_name}'s inventory")
                        if self.debug:
                            logger.debug(f"📦 Removed {item_name} from {current_loc.name}")

                if self.debug:
                    logger.debug(f"📦 Added {quantity}x {item_name} to {char_name}'s inventory")

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

    def apply_npcs_to_session(
        self,
        mechanics: ExtractedMechanics,
        game_session: "GameSession"
    ) -> List[str]:
        """
        Apply NPC introductions to game session.

        Args:
            mechanics: Extracted mechanics
            game_session: GameSession to update

        Returns:
            List of feedback messages
        """
        feedback = []

        if not mechanics.npcs_introduced:
            return feedback

        # Add each extracted NPC to npcs_present
        for npc_data in mechanics.npcs_introduced:
            npc_name = npc_data.get("name", "").strip().title()
            npc_type = npc_data.get("type", "neutral")

            if npc_name and npc_name not in game_session.npcs_present:
                game_session.npcs_present.append(npc_name)
                feedback.append(f"🎭 {npc_name} has appeared ({npc_type})")

                if self.debug:
                    logger.debug(f"🎭 Added NPC to scene: {npc_name} (type: {npc_type})")

        return feedback

    def apply_damage_to_npcs(
        self,
        mechanics: ExtractedMechanics,
        combat_manager,
        game_session: "GameSession"
    ) -> List[str]:
        """
        Apply damage to NPCs (enemies) from player attacks.

        Args:
            mechanics: Extracted mechanics with damage info
            combat_manager: CombatManager to track NPC HP
            game_session: GameSession for NPC tracking

        Returns:
            List of feedback messages about NPC damage
        """
        feedback = []

        if not mechanics.damage:
            return feedback

        # Get list of NPCs that could be damaged (enemies in combat)
        present_npcs = game_session.npcs_present

        for dmg in mechanics.damage:
            target = dmg.get("target", "").strip()
            amount = dmg.get("amount", 0)
            dmg_type = dmg.get("type", "untyped")

            # Check if target is an NPC (not "you" or player character name)
            if target.lower() not in ["you", "yourself"]:
                # Try to find matching NPC
                matched_npc = None
                for npc in present_npcs:
                    if npc.lower() in target.lower() or target.lower() in npc.lower():
                        matched_npc = npc
                        break

                if matched_npc:
                    # Apply damage to NPC via combat manager
                    actual_damage, is_dead = combat_manager.apply_damage_to_npc(matched_npc, amount)
                    
                    if actual_damage > 0:
                        if is_dead:
                            feedback.append(f"💥 {matched_npc} takes {actual_damage} {dmg_type} damage and dies! ☠️")
                            # Remove from NPCs present
                            if matched_npc in game_session.npcs_present:
                                game_session.npcs_present.remove(matched_npc)
                        else:
                            # Get current HP for display
                            monster = combat_manager.npc_monsters.get(matched_npc)
                            if monster:
                                hp_display = f"HP: {monster.current_hp}/{monster.max_hp}"
                                feedback.append(f"💥 {matched_npc} takes {actual_damage} {dmg_type} damage! ({hp_display})")
                            else:
                                feedback.append(f"💥 {matched_npc} takes {actual_damage} {dmg_type} damage!")

                        if self.debug:
                            logger.debug(f"💥 Applied {actual_damage} damage to {matched_npc} (dead: {is_dead})")

        return feedback

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
