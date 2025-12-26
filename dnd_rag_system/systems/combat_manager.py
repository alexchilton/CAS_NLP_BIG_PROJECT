"""
Combat Manager System for Turn-Based Party Combat

Extends CombatState with:
- Initiative rolling for party members and NPCs
- Turn tracking and advancement
- Integration with party mode
- Combat state display utilities
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from dnd_rag_system.systems.game_state import CombatState, PartyState, CharacterState


@dataclass
class CombatantInfo:
    """Information about a combatant for display purposes."""
    name: str
    initiative: int
    is_party_member: bool
    hp: Optional[int] = None
    max_hp: Optional[int] = None
    is_current_turn: bool = False
    is_conscious: bool = True


class CombatManager:
    """Manages turn-based combat for party mode."""

    def __init__(self, combat_state: CombatState, debug: bool = False):
        """
        Initialize combat manager.

        Args:
            combat_state: The CombatState instance to manage
            debug: Enable debug output
        """
        self.combat = combat_state
        self.debug = debug

    def roll_initiative(self, character_name: str, dex_modifier: int = 0) -> int:
        """
        Roll initiative for a character (d20 + DEX modifier).

        Args:
            character_name: Name of the character
            dex_modifier: Dexterity modifier to add to roll

        Returns:
            Initiative value (d20 + modifier)
        """
        roll = random.randint(1, 20)
        initiative = roll + dex_modifier

        if self.debug:
            print(f"🎲 {character_name} rolls initiative: {roll} + {dex_modifier} = {initiative}")

        return initiative

    def start_combat_with_party(
        self,
        party: PartyState,
        npcs: List[str],
        party_dex_modifiers: Optional[Dict[str, int]] = None,
        npc_dex_modifiers: Optional[Dict[str, int]] = None
    ) -> str:
        """
        Start combat with initiative rolls for all party members and NPCs.

        Args:
            party: The party state with all characters
            npcs: List of NPC/enemy names
            party_dex_modifiers: {character_name: dex_mod} for party members
            npc_dex_modifiers: {npc_name: dex_mod} for NPCs/enemies

        Returns:
            String describing initiative order
        """
        if party_dex_modifiers is None:
            party_dex_modifiers = {}
        if npc_dex_modifiers is None:
            npc_dex_modifiers = {}

        initiatives = {}

        # Roll initiative for all party members
        for char_name, char_state in party.characters.items():
            dex_mod = party_dex_modifiers.get(char_name, 0)
            initiative = self.roll_initiative(char_name, dex_mod)
            initiatives[char_name] = initiative

        # Roll initiative for all NPCs/enemies
        for npc_name in npcs:
            dex_mod = npc_dex_modifiers.get(npc_name, 0)
            initiative = self.roll_initiative(npc_name, dex_mod)
            initiatives[npc_name] = initiative

        # Start combat with rolled initiatives
        self.combat.start_combat(initiatives)

        # Generate summary
        return self.get_combat_start_message()

    def start_combat_with_character(
        self,
        character: CharacterState,
        npcs: List[str],
        character_dex_mod: int = 0,
        npc_dex_modifiers: Optional[Dict[str, int]] = None
    ) -> str:
        """
        Start combat with a single character (non-party mode).

        Args:
            character: The character state
            npcs: List of NPC/enemy names
            character_dex_mod: Dexterity modifier for the character
            npc_dex_modifiers: {npc_name: dex_mod} for NPCs/enemies

        Returns:
            String describing initiative order
        """
        if npc_dex_modifiers is None:
            npc_dex_modifiers = {}

        initiatives = {}

        # Roll initiative for character
        char_initiative = self.roll_initiative(character.character_name, character_dex_mod)
        initiatives[character.character_name] = char_initiative

        # Roll initiative for NPCs
        for npc_name in npcs:
            dex_mod = npc_dex_modifiers.get(npc_name, 0)
            initiative = self.roll_initiative(npc_name, dex_mod)
            initiatives[npc_name] = initiative

        # Start combat
        self.combat.start_combat(initiatives)

        return self.get_combat_start_message()

    def get_combat_start_message(self) -> str:
        """Generate a message announcing combat start and initiative order."""
        if not self.combat.in_combat:
            return "⚠️ Not in combat"

        lines = ["⚔️ **COMBAT BEGINS!**\n"]
        lines.append("📜 **Initiative Order:**")

        for idx, (name, init) in enumerate(self.combat.initiative_order, 1):
            lines.append(f"{idx}. {name} ({init})")

        current = self.combat.get_current_turn()
        if current:
            lines.append(f"\n🎯 **{current}'s turn!**")

        return "\n".join(lines)

    def advance_turn(self) -> str:
        """
        Advance to the next turn and return a message.

        Returns:
            String announcing whose turn it is
        """
        if not self.combat.in_combat:
            return "⚠️ Not in combat"

        old_round = self.combat.round_number
        next_character = self.combat.next_turn()
        new_round = self.combat.round_number

        message_parts = []

        # Check if new round started
        if new_round > old_round:
            message_parts.append(f"\n🔄 **Round {new_round} begins!**\n")

        if next_character:
            message_parts.append(f"🎯 **{next_character}'s turn!**")

        return "\n".join(message_parts)

    def get_initiative_tracker(self, party: Optional[PartyState] = None) -> str:
        """
        Get a formatted initiative tracker display.

        Args:
            party: Optional party state to include HP information

        Returns:
            Formatted initiative tracker string
        """
        if not self.combat.in_combat:
            return "⚠️ Not in combat"

        lines = [f"⚔️ **Combat Round {self.combat.round_number}**\n"]
        lines.append("📜 **Initiative Order:**")

        current_name = self.combat.get_current_turn()

        for name, initiative in self.combat.initiative_order:
            # Marker for current turn
            marker = "🎯 " if name == current_name else "   "

            # Get HP info if party member
            hp_info = ""
            if party and name in party.characters:
                char = party.characters[name]
                hp_info = f" - HP: {char.current_hp}/{char.max_hp}"
                if not char.is_conscious():
                    hp_info += " 💀 UNCONSCIOUS"

            lines.append(f"{marker}{name} ({initiative}){hp_info}")

        return "\n".join(lines)

    def get_combatants_info(self, party: Optional[PartyState] = None) -> List[CombatantInfo]:
        """
        Get detailed information about all combatants.

        Args:
            party: Optional party state to include HP information

        Returns:
            List of CombatantInfo objects
        """
        if not self.combat.in_combat:
            return []

        current_name = self.combat.get_current_turn()
        combatants = []

        for name, initiative in self.combat.initiative_order:
            is_party_member = party is not None and name in party.characters

            hp = None
            max_hp = None
            is_conscious = True

            if is_party_member:
                char = party.characters[name]
                hp = char.current_hp
                max_hp = char.max_hp
                is_conscious = char.is_conscious()

            combatants.append(CombatantInfo(
                name=name,
                initiative=initiative,
                is_party_member=is_party_member,
                hp=hp,
                max_hp=max_hp,
                is_current_turn=(name == current_name),
                is_conscious=is_conscious
            ))

        return combatants

    def end_combat(self) -> str:
        """
        End combat and return a message.

        Returns:
            String announcing combat end
        """
        if not self.combat.in_combat:
            return "⚠️ Not in combat"

        rounds = self.combat.round_number
        self.combat.end_combat()

        return f"⚔️ **Combat has ended!** (lasted {rounds} rounds)"

    def is_in_combat(self) -> bool:
        """Check if currently in combat."""
        return self.combat.in_combat

    def get_current_turn_name(self) -> Optional[str]:
        """Get the name of the character whose turn it is."""
        return self.combat.get_current_turn()

    def get_round_number(self) -> int:
        """Get the current round number."""
        return self.combat.round_number

    def remove_combatant(self, name: str) -> str:
        """
        Remove a combatant from initiative order (when defeated/fled).

        Args:
            name: Name of combatant to remove

        Returns:
            String describing the removal
        """
        if not self.combat.in_combat:
            return "⚠️ Not in combat"

        # Find and remove combatant
        original_length = len(self.combat.initiative_order)
        self.combat.initiative_order = [
            (n, i) for n, i in self.combat.initiative_order if n != name
        ]

        if len(self.combat.initiative_order) < original_length:
            # Adjust current turn index if needed
            if self.combat.current_turn_index >= len(self.combat.initiative_order):
                self.combat.current_turn_index = 0
                if self.combat.initiative_order:
                    self.combat.round_number += 1

            # Check if combat should end
            if len(self.combat.initiative_order) <= 1:
                return self.end_combat()

            return f"💀 **{name} has been removed from combat!**"

        return f"⚠️ {name} not found in initiative order"


def format_combat_status(
    combat_manager: CombatManager,
    party: Optional[PartyState] = None
) -> str:
    """
    Utility function to format complete combat status for display.

    Args:
        combat_manager: The combat manager instance
        party: Optional party state for HP information

    Returns:
        Formatted combat status string
    """
    if not combat_manager.is_in_combat():
        return "Not in combat"

    return combat_manager.get_initiative_tracker(party)
