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
from dnd_rag_system.systems.monster_stat_system import MonsterStatSystem, MonsterInstance


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

        # Monster stat system for loading NPC stats
        self.monster_stats = MonsterStatSystem(debug=debug)

        # Track NPC monster instances in combat {npc_name: MonsterInstance}
        self.npc_monsters: Dict[str, MonsterInstance] = {}

    def _load_npc_stats(self, npc_names: List[str]) -> Dict[str, int]:
        """
        Load monster stats for NPCs and return their DEX modifiers.

        Args:
            npc_names: List of NPC/monster names

        Returns:
            Dictionary of {npc_name: dex_modifier}
        """
        dex_modifiers = {}

        for npc_name in npc_names:
            # Try to load monster stats
            monster = self.monster_stats.create_monster_instance(npc_name)

            if monster:
                # Store monster instance for HP tracking
                self.npc_monsters[npc_name] = monster

                # Calculate DEX modifier: (DEX - 10) // 2
                dex_mod = (monster.dex - 10) // 2
                dex_modifiers[npc_name] = dex_mod

                if self.debug:
                    print(f"🐉 Loaded {npc_name} stats:")
                    print(f"   HP: {monster.current_hp}/{monster.max_hp}")
                    print(f"   AC: {monster.ac}")
                    print(f"   DEX mod: +{dex_mod}")
            else:
                # Fallback if monster not in database
                if self.debug:
                    print(f"⚠️  No stats found for {npc_name}, using default DEX +0")
                dex_modifiers[npc_name] = 0

        return dex_modifiers

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
        Auto-loads monster stats for NPCs from database.

        Args:
            party: The party state with all characters
            npcs: List of NPC/enemy names
            party_dex_modifiers: {character_name: dex_mod} for party members (optional)
            npc_dex_modifiers: {npc_name: dex_mod} for NPCs/enemies (optional, auto-calculated from stats)

        Returns:
            String describing initiative order
        """
        if party_dex_modifiers is None:
            party_dex_modifiers = {}

        # Auto-load NPC stats if modifiers not provided
        if npc_dex_modifiers is None:
            npc_dex_modifiers = self._load_npc_stats(npcs)

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
        Auto-loads monster stats for NPCs from database.

        Args:
            character: The character state
            npcs: List of NPC/enemy names
            character_dex_mod: Dexterity modifier for the character
            npc_dex_modifiers: {npc_name: dex_mod} for NPCs/enemies (optional, auto-calculated from stats)

        Returns:
            String describing initiative order
        """
        # Auto-load NPC stats if modifiers not provided
        if npc_dex_modifiers is None:
            npc_dex_modifiers = self._load_npc_stats(npcs)

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

        lines = []

        # Identify NPCs/monsters in combat
        npcs_in_combat = [name for name in self.npc_monsters.keys()]

        if npcs_in_combat:
            if len(npcs_in_combat) == 1:
                lines.append(f"⚔️ **A {npcs_in_combat[0]} appears!**\n")
            else:
                npc_list = ", ".join(npcs_in_combat[:-1]) + f" and {npcs_in_combat[-1]}"
                lines.append(f"⚔️ **{npc_list} appear!**\n")
        else:
            lines.append("⚔️ **COMBAT BEGINS!**\n")

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
        Get a formatted initiative tracker display with HP for both party and NPCs.

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

            # Get HP info
            hp_info = ""

            # Check if party member
            if party and name in party.characters:
                char = party.characters[name]
                hp_info = f" - HP: {char.current_hp}/{char.max_hp}"
                if not char.is_conscious():
                    hp_info += " 💀 UNCONSCIOUS"

            # Check if NPC with loaded stats
            elif name in self.npc_monsters:
                monster = self.npc_monsters[name]
                hp_info = f" - HP: {monster.current_hp}/{monster.max_hp}"
                if not monster.is_alive():
                    hp_info += " ☠️ DEAD"

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

    def get_npc_monster(self, npc_name: str) -> Optional[MonsterInstance]:
        """
        Get the MonsterInstance for an NPC in combat.

        Args:
            npc_name: Name of the NPC

        Returns:
            MonsterInstance or None if not found
        """
        return self.npc_monsters.get(npc_name)

    def apply_damage_to_npc(self, npc_name: str, damage: int) -> tuple[int, bool]:
        """
        Apply damage to an NPC and check if it died.

        Args:
            npc_name: Name of the NPC
            damage: Amount of damage to apply

        Returns:
            (actual_damage, is_dead) tuple
        """
        if npc_name in self.npc_monsters:
            monster = self.npc_monsters[npc_name]
            actual_damage, is_dead = monster.take_damage(damage)

            if self.debug:
                print(f"💥 {npc_name} takes {actual_damage} damage")
                print(f"   HP: {monster.current_hp}/{monster.max_hp}")
                if is_dead:
                    print(f"   ☠️  {npc_name} has died!")

            return (actual_damage, is_dead)

        # Fallback if NPC not tracked
        if self.debug:
            print(f"⚠️  NPC '{npc_name}' not found in tracked monsters")
        return (0, False)

    def get_npc_ac(self, npc_name: str) -> int:
        """
        Get the AC (Armor Class) of an NPC.

        Args:
            npc_name: Name of the NPC

        Returns:
            AC value, or 10 if not found
        """
        if npc_name in self.npc_monsters:
            return self.npc_monsters[npc_name].ac
        return 10  # Default AC

    def get_npc_attack_bonus(self, npc_name: str, attack_name: str) -> int:
        """
        Get the attack bonus for a specific NPC attack.

        Args:
            npc_name: Name of the NPC
            attack_name: Name of the attack

        Returns:
            Attack bonus, or 0 if not found
        """
        if npc_name in self.npc_monsters:
            return self.npc_monsters[npc_name].get_attack_bonus(attack_name)
        return 0

    def roll_npc_attack_damage(self, npc_name: str, attack_name: str) -> tuple[int, str]:
        """
        Roll damage for an NPC attack.

        Args:
            npc_name: Name of the NPC
            attack_name: Name of the attack

        Returns:
            (damage_amount, damage_type) tuple
        """
        if npc_name in self.npc_monsters:
            return self.npc_monsters[npc_name].roll_attack_damage(attack_name)
        return (0, "unknown")

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

    def generate_npc_attack(self, npc_name: str, target_ac: int = 15) -> str:
        """
        Generate an NPC attack using loaded monster stats.

        Args:
            npc_name: Name of the NPC to attack
            target_ac: AC of the target (default 15)

        Returns:
            Description of the attack and result
        """
        if npc_name not in self.npc_monsters:
            return f"⚠️ {npc_name} has no loaded stats for attacking"

        monster = self.npc_monsters[npc_name]

        if not monster.is_alive():
            return f"☠️ {npc_name} is dead and cannot attack!"

        if not monster.attacks:
            return f"{npc_name} has no attacks available"

        # Pick a random attack
        import random
        attack = random.choice(monster.attacks)
        attack_name = attack["name"]

        # Roll attack (d20 + to_hit bonus)
        attack_roll = random.randint(1, 20)
        attack_bonus = attack.get("to_hit", 0)
        total_attack = attack_roll + attack_bonus

        # Check if hit
        if total_attack >= target_ac:
            # Hit! Roll damage
            damage, damage_type = monster.roll_attack_damage(attack_name)

            if attack_roll == 20:
                # Critical hit! Double damage
                damage *= 2
                return (
                    f"🎯 **CRITICAL HIT!** {npc_name} attacks with {attack_name}!\n"
                    f"Attack: {attack_roll} (natural 20) + {attack_bonus} = {total_attack} vs AC {target_ac}\n"
                    f"💥 **{damage} {damage_type} damage** (critical!)"
                )
            else:
                return (
                    f"🎯 **HIT!** {npc_name} attacks with {attack_name}!\n"
                    f"Attack: {attack_roll} + {attack_bonus} = {total_attack} vs AC {target_ac}\n"
                    f"💥 **{damage} {damage_type} damage**"
                )
        else:
            # Miss
            if attack_roll == 1:
                return (
                    f"❌ **CRITICAL MISS!** {npc_name}'s {attack_name} goes wide!\n"
                    f"Attack: {attack_roll} (natural 1) + {attack_bonus} = {total_attack} vs AC {target_ac}\n"
                    f"The {npc_name} stumbles and misses completely!"
                )
            else:
                return (
                    f"❌ **MISS!** {npc_name} attacks with {attack_name}!\n"
                    f"Attack: {attack_roll} + {attack_bonus} = {total_attack} vs AC {target_ac}\n"
                    f"The attack misses!"
                )

    def process_npc_turns(self, target_ac: int = 15) -> List[str]:
        """
        Process all consecutive NPC turns automatically.

        Args:
            target_ac: AC of the target to attack (usually player's AC)

        Returns:
            List of attack descriptions from all NPCs who took turns
        """
        if not self.combat.in_combat:
            return []

        npc_actions = []
        current_turn = self.combat.get_current_turn()

        # Keep processing turns while it's an NPC turn
        while current_turn and current_turn in self.npc_monsters:
            # Generate NPC attack
            attack_result = self.generate_npc_attack(current_turn, target_ac)
            npc_actions.append(attack_result)

            if self.debug:
                print(f"🎲 NPC Turn: {current_turn}")
                print(attack_result)

            # Advance to next turn
            next_char = self.combat.next_turn()
            current_turn = self.combat.get_current_turn()

            # Safety: prevent infinite loop
            if len(npc_actions) > 10:
                npc_actions.append("⚠️ Too many consecutive NPC turns, stopping")
                break

        return npc_actions


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
