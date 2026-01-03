"""
Monster Stat System

Provides accurate D&D 5e monster stats for combat encounters.
Integrates with CombatManager to create CombatNPC objects with real stats.
"""

import random
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

# Import the monster stats database
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dnd_rag_system.data.monster_stats import (
    get_monster_stat,
    get_monsters_by_cr,
    get_all_monster_names,
    MONSTER_STATS
)


@dataclass
class MonsterInstance:
    """A specific instance of a monster in combat."""
    name: str
    cr: float
    size: str
    type: str
    ac: int
    max_hp: int
    current_hp: int
    speed: int
    str: int
    dex: int
    con: int
    int: int
    wis: int
    cha: int
    attacks: List[Dict[str, Any]]
    traits: List[str]
    description: str

    def is_alive(self) -> bool:
        """Check if monster is still alive."""
        return self.current_hp > 0

    def take_damage(self, amount: int) -> tuple[int, bool]:
        """
        Apply damage to monster.

        Returns:
            (actual_damage, is_dead) tuple
        """
        actual_damage = min(amount, self.current_hp)
        self.current_hp -= actual_damage
        return (actual_damage, self.current_hp <= 0)

    def heal(self, amount: int) -> int:
        """
        Heal monster.

        Returns:
            Actual amount healed
        """
        actual_heal = min(amount, self.max_hp - self.current_hp)
        self.current_hp += actual_heal
        return actual_heal

    def get_attack_bonus(self, attack_name: str) -> int:
        """Get to-hit bonus for a specific attack."""
        for attack in self.attacks:
            if attack["name"].lower() == attack_name.lower():
                return attack.get("to_hit", 0)
        return 0

    def roll_attack_damage(self, attack_name: str) -> tuple[int, str]:
        """
        Roll damage for a specific attack.

        Returns:
            (damage_amount, damage_type) tuple
        """
        for attack in self.attacks:
            if attack["name"].lower() == attack_name.lower():
                damage_dice = attack.get("damage", "1d6")
                damage_type = attack.get("damage_type", "bludgeoning")

                # Parse dice notation (e.g., "2d6+3")
                damage = self._roll_dice(damage_dice)
                return (damage, damage_type)

        return (0, "unknown")

    def _roll_dice(self, dice_notation: str) -> int:
        """
        Roll dice from notation like "2d6+3" or "1d8".

        Args:
            dice_notation: Dice string (e.g., "2d6+3", "1d10")

        Returns:
            Total rolled value
        """
        import re

        # Parse notation: XdY+Z or XdY
        match = re.match(r'(\d+)d(\d+)([+-]\d+)?', dice_notation)
        if not match:
            return 0

        num_dice = int(match.group(1))
        die_size = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        # Roll the dice
        total = sum(random.randint(1, die_size) for _ in range(num_dice))
        return total + modifier

    def get_stat_summary(self) -> str:
        """Get a summary of monster stats for display."""
        return (
            f"{self.name} (CR {self.cr})\n"
            f"HP: {self.current_hp}/{self.max_hp} | AC: {self.ac}\n"
            f"Attacks: {', '.join([a['name'] for a in self.attacks])}"
        )


class MonsterStatSystem:
    """System for managing monster stats and creating combat instances."""

    def __init__(self, debug: bool = False):
        """
        Initialize monster stat system.

        Args:
            debug: Enable debug logging
        """
        self.debug = debug

    def create_monster_instance(self, monster_name: str) -> Optional[MonsterInstance]:
        """
        Create a monster instance from the stats database.

        Args:
            monster_name: Name of the monster (case-insensitive)

        Returns:
            MonsterInstance with rolled HP, or None if monster not found
        """
        # Get base stats
        stats = get_monster_stat(monster_name)
        if not stats:
            if self.debug:
                print(f"⚠️  Monster '{monster_name}' not found in database")
            return None

        # Roll HP from hit dice
        hp_dice = stats.get("hp_dice", "1d8")
        rolled_hp = self._roll_hp(hp_dice)

        # Use average HP as fallback
        max_hp = max(rolled_hp, stats.get("hp", 10))

        # Create instance
        instance = MonsterInstance(
            name=stats["name"],
            cr=stats["cr"],
            size=stats["size"],
            type=stats["type"],
            ac=stats["ac"],
            max_hp=max_hp,
            current_hp=max_hp,
            speed=stats["speed"],
            str=stats["str"],
            dex=stats["dex"],
            con=stats["con"],
            int=stats["int"],
            wis=stats["wis"],
            cha=stats["cha"],
            attacks=stats["attacks"].copy(),
            traits=stats["traits"].copy(),
            description=stats["description"]
        )

        if self.debug:
            print(f"🐉 Created monster instance: {instance.name}")
            print(f"   HP: {instance.max_hp} ({hp_dice})")
            print(f"   AC: {instance.ac}")
            print(f"   Attacks: {[a['name'] for a in instance.attacks]}")

        return instance

    def create_random_monster_by_cr(self, min_cr: float = 0, max_cr: float = 5) -> Optional[MonsterInstance]:
        """
        Create a random monster instance within a CR range.

        Args:
            min_cr: Minimum challenge rating
            max_cr: Maximum challenge rating

        Returns:
            MonsterInstance, or None if no monsters found
        """
        # Get monsters in CR range
        monsters = get_monsters_by_cr(min_cr, max_cr)
        if not monsters:
            if self.debug:
                print(f"⚠️  No monsters found in CR range {min_cr}-{max_cr}")
            return None

        # Pick random monster
        monster_stats = random.choice(monsters)
        return self.create_monster_instance(monster_stats["name"])

    def get_monster_description(self, monster_name: str) -> str:
        """
        Get the flavor text description of a monster.

        Args:
            monster_name: Name of the monster

        Returns:
            Description string, or empty string if not found
        """
        stats = get_monster_stat(monster_name)
        if stats:
            return stats.get("description", "")
        return ""

    def list_available_monsters(self, cr_filter: Optional[float] = None) -> List[str]:
        """
        List all available monsters, optionally filtered by CR.

        Args:
            cr_filter: If provided, only show monsters of this CR

        Returns:
            List of monster names
        """
        if cr_filter is not None:
            monsters = get_monsters_by_cr(cr_filter, cr_filter)
            return [m["name"] for m in monsters]
        else:
            return get_all_monster_names()

    def _roll_hp(self, hp_dice: str) -> int:
        """
        Roll HP from hit dice notation.

        Args:
            hp_dice: Dice notation (e.g., "2d6", "5d10+10")

        Returns:
            Rolled HP value
        """
        import re

        # Parse notation: XdY+Z or XdY
        match = re.match(r'(\d+)d(\d+)([+-]\d+)?', hp_dice)
        if not match:
            return 10  # Default

        num_dice = int(match.group(1))
        die_size = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

        # Roll HP
        total = sum(random.randint(1, die_size) for _ in range(num_dice))
        return max(1, total + modifier)  # Minimum 1 HP


# Quick test
if __name__ == "__main__":
    print("🎲 Monster Stat System Test\n")

    system = MonsterStatSystem(debug=True)

    # Test creating specific monsters
    print("=" * 60)
    print("TEST 1: Create Goblin")
    print("=" * 60)
    goblin = system.create_monster_instance("Goblin")
    if goblin:
        print(f"\n{goblin.get_stat_summary()}\n")

        # Test attack
        print("🗡️  Goblin attacks with scimitar:")
        damage, dtype = goblin.roll_attack_damage("Scimitar")
        print(f"   Damage: {damage} {dtype}")
        print(f"   To hit: +{goblin.get_attack_bonus('Scimitar')}")

    # Test random monster
    print("\n" + "=" * 60)
    print("TEST 2: Random CR 1-2 Monster")
    print("=" * 60)
    monster = system.create_random_monster_by_cr(1, 2)
    if monster:
        print(f"\n{monster.get_stat_summary()}\n")

    # Test combat simulation
    print("\n" + "=" * 60)
    print("TEST 3: Combat Simulation - Goblin vs Player")
    print("=" * 60)
    goblin = system.create_monster_instance("Goblin")
    if goblin:
        print(f"⚔️  {goblin.name} HP: {goblin.current_hp}/{goblin.max_hp}")

        # Simulate 3 attacks
        for round_num in range(1, 4):
            damage, dtype = goblin.roll_attack_damage("Scimitar")
            print(f"\n  Round {round_num}: Deals {damage} {dtype} damage")

            # Goblin takes damage back
            counter_damage = random.randint(4, 10)
            actual, died = goblin.take_damage(counter_damage)
            print(f"  Goblin takes {actual} damage")
            print(f"  💚 HP: {goblin.current_hp}/{goblin.max_hp}")

            if died:
                print(f"\n  ☠️  {goblin.name} has been slain!")
                break

    # List monsters
    print("\n" + "=" * 60)
    print("TEST 4: Available Monsters by CR")
    print("=" * 60)
    for cr in [0, 0.25, 1, 2, 5]:
        monsters = system.list_available_monsters(cr_filter=cr)
        if monsters:
            print(f"CR {cr}: {', '.join(monsters)}")
