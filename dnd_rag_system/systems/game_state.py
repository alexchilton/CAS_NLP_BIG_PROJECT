"""
D&D 5e Game State Management System

Comprehensive state tracking for D&D gameplay including:
- Character state (HP, spell slots, inventory, conditions, XP)
- Combat state (initiative, turns, rounds)
- Party management (multiple characters)
- Game session (quests, NPCs, location, time)
- World state (locations, world map, exploration)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
import json
from pathlib import Path


# Location Types
class LocationType(Enum):
    """Types of locations in the game world."""
    TOWN = "town"
    TAVERN = "tavern"
    SHOP = "shop"
    TEMPLE = "temple"
    DUNGEON = "dungeon"
    WILDERNESS = "wilderness"
    CAVE = "cave"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    RUINS = "ruins"
    CASTLE = "castle"
    GUILD_HALL = "guild_hall"


@dataclass
class Location:
    """
    Represents a location in the game world.
    
    Tracks both static metadata and dynamic state changes.
    """
    name: str
    location_type: LocationType
    description: str
    
    # Features
    has_shop: bool = False
    has_inn: bool = False
    is_safe: bool = True  # Can rest here?
    is_discovered: bool = True  # Has player found this location?
    
    # Connections (location names this connects to)
    connections: List[str] = field(default_factory=list)
    
    # Persistent state - tracks what happened here
    defeated_enemies: Set[str] = field(default_factory=set)  # Dead monsters stay dead
    moved_items: Dict[str, str] = field(default_factory=dict)  # {item: new_location}
    available_items: List[str] = field(default_factory=list)  # Items currently at this location
    completed_events: Set[str] = field(default_factory=set)  # Events that happened here
    
    # NPCs that permanently reside here (not combat enemies)
    resident_npcs: List[str] = field(default_factory=list)
    
    # Visit tracking
    visit_count: int = 0
    last_visited_day: Optional[int] = None
    
    def add_connection(self, location_name: str):
        """Add a bidirectional connection to another location."""
        if location_name not in self.connections:
            self.connections.append(location_name)
    
    def remove_connection(self, location_name: str):
        """Remove a connection to another location."""
        if location_name in self.connections:
            self.connections.remove(location_name)
    
    def mark_enemy_defeated(self, enemy_name: str):
        """Mark an enemy as permanently defeated at this location."""
        self.defeated_enemies.add(enemy_name.lower())
    
    def is_enemy_defeated(self, enemy_name: str) -> bool:
        """Check if an enemy was already defeated here."""
        return enemy_name.lower() in self.defeated_enemies
    
    def mark_event_completed(self, event_id: str):
        """Mark an event as completed (e.g., quest objective, triggered trap)."""
        self.completed_events.add(event_id)
    
    def is_event_completed(self, event_id: str) -> bool:
        """Check if an event was already completed."""
        return event_id in self.completed_events
    
    def add_item(self, item_name: str):
        """Add an item to this location."""
        if item_name not in self.available_items:
            self.available_items.append(item_name)
    
    def remove_item(self, item_name: str, moved_to: str = "inventory") -> bool:
        """
        Remove an item from this location (picked up by player).
        
        Args:
            item_name: Name of item to remove
            moved_to: Where the item went (default: "inventory")
        
        Returns:
            True if item was removed, False if not found
        """
        if item_name in self.available_items:
            self.available_items.remove(item_name)
            self.moved_items[item_name] = moved_to
            return True
        return False
    
    def has_item(self, item_name: str) -> bool:
        """Check if item is currently at this location."""
        return item_name in self.available_items
    
    def record_visit(self, current_day: int):
        """Record a visit to this location."""
        self.visit_count += 1
        self.last_visited_day = current_day
        if not self.is_discovered:
            self.is_discovered = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "location_type": self.location_type.value,
            "description": self.description,
            "has_shop": self.has_shop,
            "has_inn": self.has_inn,
            "is_safe": self.is_safe,
            "is_discovered": self.is_discovered,
            "connections": self.connections,
            "defeated_enemies": list(self.defeated_enemies),
            "moved_items": self.moved_items,
            "completed_events": list(self.completed_events),
            "resident_npcs": self.resident_npcs,
            "visit_count": self.visit_count,
            "last_visited_day": self.last_visited_day
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        """Create Location from dictionary."""
        return cls(
            name=data["name"],
            location_type=LocationType(data["location_type"]),
            description=data["description"],
            has_shop=data.get("has_shop", False),
            has_inn=data.get("has_inn", False),
            is_safe=data.get("is_safe", True),
            is_discovered=data.get("is_discovered", True),
            connections=data.get("connections", []),
            defeated_enemies=set(data.get("defeated_enemies", [])),
            moved_items=data.get("moved_items", {}),
            completed_events=set(data.get("completed_events", [])),
            resident_npcs=data.get("resident_npcs", []),
            visit_count=data.get("visit_count", 0),
            last_visited_day=data.get("last_visited_day")
        )


# D&D 5e Official Conditions
class Condition(Enum):
    """Official D&D 5e conditions."""
    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"


@dataclass
class SpellSlots:
    """Manages spell slots for a character (D&D 5e style)."""
    level_1: int = 0
    level_2: int = 0
    level_3: int = 0
    level_4: int = 0
    level_5: int = 0
    level_6: int = 0
    level_7: int = 0
    level_8: int = 0
    level_9: int = 0

    # Current available slots
    current_1: int = 0
    current_2: int = 0
    current_3: int = 0
    current_4: int = 0
    current_5: int = 0
    current_6: int = 0
    current_7: int = 0
    current_8: int = 0
    current_9: int = 0

    def __post_init__(self):
        """Initialize current slots to max slots."""
        self.current_1 = self.level_1
        self.current_2 = self.level_2
        self.current_3 = self.level_3
        self.current_4 = self.level_4
        self.current_5 = self.level_5
        self.current_6 = self.level_6
        self.current_7 = self.level_7
        self.current_8 = self.level_8
        self.current_9 = self.level_9

    def has_slot(self, level: int) -> bool:
        """Check if a spell slot of given level is available."""
        if level < 1 or level > 9:
            return False
        return getattr(self, f"current_{level}") > 0

    def use_slot(self, level: int) -> bool:
        """Use a spell slot. Returns True if successful."""
        if not self.has_slot(level):
            return False
        current = getattr(self, f"current_{level}")
        setattr(self, f"current_{level}", current - 1)
        return True

    def restore_slot(self, level: int, amount: int = 1):
        """Restore spell slot(s). Cannot exceed maximum."""
        if level < 1 or level > 9:
            return
        current = getattr(self, f"current_{level}")
        max_slots = getattr(self, f"level_{level}")
        setattr(self, f"current_{level}", min(current + amount, max_slots))

    def long_rest(self):
        """Restore all spell slots (long rest)."""
        for i in range(1, 10):
            setattr(self, f"current_{i}", getattr(self, f"level_{i}"))

    def get_available(self) -> Dict[int, Tuple[int, int]]:
        """Get available slots as {level: (current, max)}."""
        return {
            i: (getattr(self, f"current_{i}"), getattr(self, f"level_{i}"))
            for i in range(1, 10)
            if getattr(self, f"level_{i}") > 0
        }


@dataclass
class DeathSaves:
    """Track death saving throws."""
    successes: int = 0
    failures: int = 0

    def add_success(self) -> Tuple[bool, str]:
        """Add a success. Returns (stabilized, message)."""
        self.successes += 1
        if self.successes >= 3:
            return True, "Character is stabilized!"
        return False, f"Death save success ({self.successes}/3)"

    def add_failure(self) -> Tuple[bool, str]:
        """Add a failure. Returns (dead, message)."""
        self.failures += 1
        if self.failures >= 3:
            return True, "Character has died!"
        return False, f"Death save failure ({self.failures}/3)"

    def reset(self):
        """Reset death saves (after stabilization or revival)."""
        self.successes = 0
        self.failures = 0

    def is_stable(self) -> bool:
        """Check if character is stable."""
        return self.successes >= 3

    def is_dead(self) -> bool:
        """Check if character is dead."""
        return self.failures >= 3


@dataclass
class CharacterState:
    """
    Comprehensive character state for D&D 5e.

    Tracks all dynamic game state for a character:
    - Health (current, max, temporary)
    - Spell slots (by level)
    - Inventory (items with quantities)
    - Conditions and effects
    - Experience and leveling
    - Death saves
    - Concentration
    """
    character_name: str

    # Health
    current_hp: int = 0
    max_hp: int = 0
    temp_hp: int = 0  # Temporary hit points

    # Resources
    spell_slots: SpellSlots = field(default_factory=SpellSlots)
    hit_dice_current: int = 0  # For short rest healing
    hit_dice_max: int = 0

    # Inventory (item_name: quantity)
    inventory: Dict[str, int] = field(default_factory=dict)

    # Gold
    gold: int = 50  # Starting gold

    # Character progression
    experience_points: int = 0
    level: int = 1

    # Combat state
    conditions: List[str] = field(default_factory=list)  # Active conditions
    death_saves: DeathSaves = field(default_factory=DeathSaves)
    is_concentrating: bool = False
    concentration_spell: Optional[str] = None

    # Equipment slots (what's currently equipped)
    equipped: Dict[str, str] = field(default_factory=dict)  # slot: item_name

    def __post_init__(self):
        """Initialize current HP to max if not set."""
        if self.current_hp == 0 and self.max_hp > 0:
            self.current_hp = self.max_hp
        if self.hit_dice_current == 0 and self.hit_dice_max > 0:
            self.hit_dice_current = self.hit_dice_max

    # Health Management
    def take_damage(self, amount: int, damage_type: str = "untyped") -> Dict[str, Any]:
        """
        Apply damage to character.

        Returns dict with:
        - damage_taken: actual damage applied
        - temp_hp_lost: temp HP lost
        - hp_lost: real HP lost
        - current_hp: HP after damage
        - unconscious: whether character fell unconscious
        - message: description of what happened
        """
        if amount <= 0:
            return {
                "damage_taken": 0,
                "temp_hp_lost": 0,
                "hp_lost": 0,
                "current_hp": self.current_hp,
                "unconscious": False,
                "message": "No damage taken"
            }

        temp_hp_lost = 0
        hp_lost = 0

        # Temp HP absorbs damage first
        if self.temp_hp > 0:
            if amount <= self.temp_hp:
                temp_hp_lost = amount
                self.temp_hp -= amount
                amount = 0
            else:
                temp_hp_lost = self.temp_hp
                amount -= self.temp_hp
                self.temp_hp = 0

        # Apply remaining damage to HP
        if amount > 0:
            hp_lost = min(amount, self.current_hp)
            self.current_hp -= hp_lost

        unconscious = False
        if self.current_hp <= 0:
            self.current_hp = 0
            unconscious = True
            if Condition.UNCONSCIOUS.value not in self.conditions:
                self.conditions.append(Condition.UNCONSCIOUS.value)
            # Break concentration if concentrating
            if self.is_concentrating:
                self.break_concentration()

        message = f"Took {amount} {damage_type} damage"
        if temp_hp_lost > 0:
            message += f" ({temp_hp_lost} absorbed by temp HP)"
        if unconscious:
            message += " - UNCONSCIOUS!"

        return {
            "damage_taken": temp_hp_lost + hp_lost,
            "temp_hp_lost": temp_hp_lost,
            "hp_lost": hp_lost,
            "current_hp": self.current_hp,
            "unconscious": unconscious,
            "message": message
        }

    def heal(self, amount: int) -> Dict[str, Any]:
        """
        Heal character.

        Returns dict with healing info.
        """
        if amount <= 0:
            return {"healed": 0, "current_hp": self.current_hp, "message": "No healing"}

        old_hp = self.current_hp
        self.current_hp = min(self.current_hp + amount, self.max_hp)
        healed = self.current_hp - old_hp

        # Remove unconscious if HP > 0
        if self.current_hp > 0 and Condition.UNCONSCIOUS.value in self.conditions:
            self.conditions.remove(Condition.UNCONSCIOUS.value)
            self.death_saves.reset()

        return {
            "healed": healed,
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "message": f"Healed {healed} HP (now at {self.current_hp}/{self.max_hp})"
        }

    def add_temp_hp(self, amount: int):
        """Add temporary hit points (doesn't stack, takes highest)."""
        if amount > self.temp_hp:
            self.temp_hp = amount

    # Spell Management
    def cast_spell(self, spell_level: int, spell_name: str,
                   requires_concentration: bool = False) -> Dict[str, Any]:
        """
        Cast a spell, consuming a spell slot.

        Returns success status and message.
        """
        # Cantrips don't use slots
        if spell_level == 0:
            if requires_concentration:
                self.start_concentration(spell_name)
            return {
                "success": True,
                "message": f"Cast {spell_name} (cantrip)"
            }

        # Check if slot available
        if not self.spell_slots.has_slot(spell_level):
            return {
                "success": False,
                "message": f"No level {spell_level} spell slots remaining"
            }

        # Use slot
        self.spell_slots.use_slot(spell_level)

        # Handle concentration
        if requires_concentration:
            self.start_concentration(spell_name)

        slots = self.spell_slots.get_available()
        remaining = slots.get(spell_level, (0, 0))[0]

        return {
            "success": True,
            "spell_level": spell_level,
            "remaining_slots": remaining,
            "message": f"Cast {spell_name} (level {spell_level} slot used, {remaining} remaining)"
        }

    def start_concentration(self, spell_name: str):
        """Start concentrating on a spell (breaks previous concentration)."""
        if self.is_concentrating and self.concentration_spell:
            old_spell = self.concentration_spell
            self.break_concentration()
            # Could return info about breaking old concentration

        self.is_concentrating = True
        self.concentration_spell = spell_name

    def break_concentration(self) -> Optional[str]:
        """Break concentration. Returns name of spell that was broken."""
        if self.is_concentrating:
            spell = self.concentration_spell
            self.is_concentrating = False
            self.concentration_spell = None
            return spell
        return None

    def concentration_check(self, damage_taken: int, dc: Optional[int] = None) -> bool:
        """
        Make a concentration check after taking damage.
        DC = max(10, damage_taken / 2)

        For now, returns True (success) 50% of the time.
        In full implementation, would roll CON save.
        """
        if not self.is_concentrating:
            return True

        if dc is None:
            dc = max(10, damage_taken // 2)

        # Simplified: would roll CON save here
        # For now, 50% chance
        import random
        success = random.random() > 0.5

        if not success:
            self.break_concentration()

        return success

    # Inventory Management
    def add_item(self, item_name: str, quantity: int = 1):
        """Add item(s) to inventory."""
        if item_name in self.inventory:
            self.inventory[item_name] += quantity
        else:
            self.inventory[item_name] = quantity

    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """Remove item(s) from inventory. Returns True if successful."""
        if item_name not in self.inventory:
            return False

        if self.inventory[item_name] < quantity:
            return False

        self.inventory[item_name] -= quantity
        if self.inventory[item_name] == 0:
            del self.inventory[item_name]

        return True

    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Check if character has item(s)."""
        return self.inventory.get(item_name, 0) >= quantity

    def equip_item(self, slot: str, item_name: str) -> Optional[str]:
        """Equip an item to a slot. Returns previously equipped item if any."""
        old_item = self.equipped.get(slot)
        self.equipped[slot] = item_name
        return old_item

    def unequip_item(self, slot: str) -> Optional[str]:
        """Unequip item from slot. Returns the item that was equipped."""
        return self.equipped.pop(slot, None)

    # Conditions
    def add_condition(self, condition: Condition):
        """Add a condition to the character."""
        condition_name = condition.value
        if condition_name not in self.conditions:
            self.conditions.append(condition_name)

            # Special handling for unconscious
            if condition == Condition.UNCONSCIOUS:
                self.current_hp = 0

    def remove_condition(self, condition: Condition) -> bool:
        """Remove a condition. Returns True if condition was present."""
        condition_name = condition.value
        if condition_name in self.conditions:
            self.conditions.remove(condition_name)
            return True
        return False

    def has_condition(self, condition: Condition) -> bool:
        """Check if character has a specific condition."""
        return condition.value in self.conditions

    # Rest Mechanics
    def short_rest(self, hit_dice_spent: int = 0) -> Dict[str, Any]:
        """
        Take a short rest.

        Can spend hit dice to heal (1d8 + CON mod per die, simplified here as max_hp/level).
        """
        if hit_dice_spent > self.hit_dice_current:
            hit_dice_spent = self.hit_dice_current

        if hit_dice_spent <= 0:
            return {
                "hit_dice_spent": 0,
                "hp_restored": 0,
                "message": "Short rest taken (no hit dice spent)"
            }

        # Simplified: restore (max_hp / level) per hit die
        # In real D&D, would roll hit dice
        healing_per_die = max(1, self.max_hp // max(1, self.level))
        total_healing = healing_per_die * hit_dice_spent

        self.hit_dice_current -= hit_dice_spent
        heal_result = self.heal(total_healing)

        return {
            "hit_dice_spent": hit_dice_spent,
            "hit_dice_remaining": self.hit_dice_current,
            "hp_restored": heal_result["healed"],
            "current_hp": self.current_hp,
            "message": f"Short rest: spent {hit_dice_spent} hit dice, restored {heal_result['healed']} HP"
        }

    def long_rest(self) -> Dict[str, Any]:
        """
        Take a long rest.

        Restores all HP, spell slots, and half of hit dice.
        """
        # Restore HP
        hp_restored = self.max_hp - self.current_hp
        self.current_hp = self.max_hp

        # Restore spell slots
        self.spell_slots.long_rest()

        # Restore hit dice (half of max, minimum 1)
        dice_restored = max(1, self.hit_dice_max // 2)
        old_dice = self.hit_dice_current
        self.hit_dice_current = min(self.hit_dice_current + dice_restored, self.hit_dice_max)
        dice_restored = self.hit_dice_current - old_dice

        # Remove exhaustion levels (would reduce by 1 in full rules)
        # Clear non-permanent conditions
        self.conditions = []

        # Reset death saves
        self.death_saves.reset()

        return {
            "hp_restored": hp_restored,
            "hit_dice_restored": dice_restored,
            "spell_slots_restored": True,
            "message": f"Long rest complete! HP fully restored, spell slots recharged, {dice_restored} hit dice restored"
        }

    # Experience and Leveling
    def add_experience(self, xp: int) -> Dict[str, Any]:
        """Add experience points. Returns level-up info if applicable."""
        self.experience_points += xp

        # Simplified leveling (1000 XP per level)
        # Real D&D has specific XP thresholds
        xp_for_next = self.level * 1000

        if self.experience_points >= xp_for_next:
            return {
                "xp_gained": xp,
                "total_xp": self.experience_points,
                "level_up": True,
                "message": f"Gained {xp} XP! Ready to level up!"
            }

        return {
            "xp_gained": xp,
            "total_xp": self.experience_points,
            "xp_to_next_level": xp_for_next - self.experience_points,
            "level_up": False,
            "message": f"Gained {xp} XP ({self.experience_points}/{xp_for_next})"
        }

    # State queries
    def is_alive(self) -> bool:
        """Check if character is alive."""
        return not self.death_saves.is_dead()

    def is_conscious(self) -> bool:
        """Check if character is conscious."""
        return self.current_hp > 0

    def get_status_summary(self) -> str:
        """Get a text summary of character's current state."""
        lines = [f"=== {self.character_name} ==="]
        lines.append(f"HP: {self.current_hp}/{self.max_hp}" +
                    (f" (+{self.temp_hp} temp)" if self.temp_hp > 0 else ""))

        # Spell slots
        available_slots = self.spell_slots.get_available()
        if available_slots:
            slot_str = ", ".join([f"L{lvl}: {curr}/{max_}"
                                  for lvl, (curr, max_) in available_slots.items()])
            lines.append(f"Spell Slots: {slot_str}")

        # Conditions
        if self.conditions:
            lines.append(f"Conditions: {', '.join(self.conditions)}")

        # Concentration
        if self.is_concentrating:
            lines.append(f"Concentrating on: {self.concentration_spell}")

        # Death saves
        if not self.is_conscious():
            lines.append(f"Death Saves: {self.death_saves.successes} successes, {self.death_saves.failures} failures")

        # XP
        xp_next = self.level * 1000
        lines.append(f"Level {self.level} | XP: {self.experience_points}/{xp_next}")

        return "\n".join(lines)

    # Serialization
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = {
            "character_name": self.character_name,
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "temp_hp": self.temp_hp,
            "spell_slots": asdict(self.spell_slots),
            "hit_dice_current": self.hit_dice_current,
            "hit_dice_max": self.hit_dice_max,
            "inventory": self.inventory,
            "gold": self.gold,
            "experience_points": self.experience_points,
            "level": self.level,
            "conditions": self.conditions,
            "death_saves": asdict(self.death_saves),
            "is_concentrating": self.is_concentrating,
            "concentration_spell": self.concentration_spell,
            "equipped": self.equipped
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "CharacterState":
        """Create CharacterState from dictionary."""
        spell_slots = SpellSlots(**data.get("spell_slots", {}))
        death_saves = DeathSaves(**data.get("death_saves", {}))

        return cls(
            character_name=data["character_name"],
            current_hp=data.get("current_hp", 0),
            max_hp=data.get("max_hp", 0),
            temp_hp=data.get("temp_hp", 0),
            spell_slots=spell_slots,
            hit_dice_current=data.get("hit_dice_current", 0),
            hit_dice_max=data.get("hit_dice_max", 0),
            inventory=data.get("inventory", {}),
            gold=data.get("gold", 50),
            experience_points=data.get("experience_points", 0),
            level=data.get("level", 1),
            conditions=data.get("conditions", []),
            death_saves=death_saves,
            is_concentrating=data.get("is_concentrating", False),
            concentration_spell=data.get("concentration_spell"),
            equipped=data.get("equipped", {})
        )

    def save_to_file(self, filepath: Path):
        """Save state to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: Path) -> "CharacterState":
        """Load state from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class CombatState:
    """
    Manages combat state for D&D encounters.

    Tracks initiative order, current turn, round number, and active effects.
    """
    in_combat: bool = False
    round_number: int = 0

    # Initiative: {character_name: initiative_roll}
    initiative_order: List[Tuple[str, int]] = field(default_factory=list)
    current_turn_index: int = 0

    # Active effects: {effect_name: (target, duration_rounds, description)}
    active_effects: Dict[str, Tuple[str, int, str]] = field(default_factory=dict)

    def start_combat(self, initiatives: Dict[str, int]):
        """
        Start combat with initiative rolls.

        Args:
            initiatives: {character_name: initiative_roll}
        """
        self.in_combat = True
        self.round_number = 1
        self.current_turn_index = 0

        # Sort by initiative (highest first)
        self.initiative_order = sorted(
            initiatives.items(),
            key=lambda x: x[1],
            reverse=True
        )

    def next_turn(self) -> Optional[str]:
        """
        Advance to next turn. Returns name of character whose turn it is.
        Returns None if no one in combat.
        """
        if not self.in_combat or not self.initiative_order:
            return None

        self.current_turn_index += 1

        # New round
        if self.current_turn_index >= len(self.initiative_order):
            self.current_turn_index = 0
            self.round_number += 1
            self.tick_effects()

        return self.initiative_order[self.current_turn_index][0]

    def get_current_turn(self) -> Optional[str]:
        """Get name of character whose turn it is."""
        if not self.in_combat or not self.initiative_order:
            return None
        return self.initiative_order[self.current_turn_index][0]

    def add_effect(self, effect_name: str, target: str, duration: int, description: str = ""):
        """Add an active effect (buff/debuff)."""
        self.active_effects[effect_name] = (target, duration, description)

    def remove_effect(self, effect_name: str):
        """Remove an active effect."""
        self.active_effects.pop(effect_name, None)

    def tick_effects(self):
        """Decrease duration of all effects by 1 round. Remove expired effects."""
        expired = []
        for effect_name, (target, duration, desc) in self.active_effects.items():
            duration -= 1
            if duration <= 0:
                expired.append(effect_name)
            else:
                self.active_effects[effect_name] = (target, duration, desc)

        for effect_name in expired:
            self.remove_effect(effect_name)

    def end_combat(self):
        """End combat and reset state."""
        self.in_combat = False
        self.round_number = 0
        self.initiative_order = []
        self.current_turn_index = 0
        self.active_effects = {}

    def get_combat_summary(self) -> str:
        """Get text summary of combat state."""
        if not self.in_combat:
            return "Not in combat"

        lines = [f"=== Combat Round {self.round_number} ==="]
        lines.append("Initiative Order:")

        for idx, (name, init) in enumerate(self.initiative_order):
            marker = ">>> " if idx == self.current_turn_index else "    "
            lines.append(f"{marker}{name} ({init})")

        if self.active_effects:
            lines.append("\nActive Effects:")
            for effect, (target, duration, desc) in self.active_effects.items():
                lines.append(f"  {effect} on {target} ({duration} rounds) - {desc}")

        return "\n".join(lines)


@dataclass
class PartyState:
    """
    Manages a party of multiple characters.

    Tracks all party members and shared resources.
    """
    party_name: str = "Adventuring Party"

    # Character states by name
    characters: Dict[str, CharacterState] = field(default_factory=dict)

    # Shared party inventory
    shared_inventory: Dict[str, int] = field(default_factory=dict)

    # Party gold
    gold: int = 0

    def add_character(self, character_state: CharacterState):
        """Add a character to the party."""
        self.characters[character_state.character_name] = character_state

    def remove_character(self, name: str) -> Optional[CharacterState]:
        """Remove a character from the party. Returns the character state."""
        return self.characters.pop(name, None)

    def get_character(self, name: str) -> Optional[CharacterState]:
        """Get a character's state by name."""
        return self.characters.get(name)

    def get_all_characters(self) -> List[CharacterState]:
        """Get all character states."""
        return list(self.characters.values())

    def get_alive_characters(self) -> List[CharacterState]:
        """Get all living characters."""
        return [char for char in self.characters.values() if char.is_alive()]

    def get_conscious_characters(self) -> List[CharacterState]:
        """Get all conscious characters."""
        return [char for char in self.characters.values() if char.is_conscious()]

    def add_shared_item(self, item_name: str, quantity: int = 1):
        """Add item to shared party inventory."""
        if item_name in self.shared_inventory:
            self.shared_inventory[item_name] += quantity
        else:
            self.shared_inventory[item_name] = quantity

    def remove_shared_item(self, item_name: str, quantity: int = 1) -> bool:
        """Remove item from shared inventory. Returns True if successful."""
        if item_name not in self.shared_inventory:
            return False
        if self.shared_inventory[item_name] < quantity:
            return False

        self.shared_inventory[item_name] -= quantity
        if self.shared_inventory[item_name] == 0:
            del self.shared_inventory[item_name]
        return True

    def add_gold(self, amount: int):
        """Add gold to party funds."""
        self.gold += amount

    def remove_gold(self, amount: int) -> bool:
        """Remove gold from party funds. Returns True if successful."""
        if self.gold < amount:
            return False
        self.gold -= amount
        return True

    def distribute_xp(self, total_xp: int) -> Dict[str, Dict]:
        """Distribute XP evenly among all alive party members."""
        alive = self.get_alive_characters()
        if not alive:
            return {}

        xp_per_char = total_xp // len(alive)
        results = {}

        for char in alive:
            result = char.add_experience(xp_per_char)
            results[char.character_name] = result

        return results

    def party_short_rest(self) -> Dict[str, Dict]:
        """All party members take a short rest."""
        results = {}
        for char in self.characters.values():
            # Let each character decide how many hit dice to spend
            # For now, spend 1 if available
            dice_to_spend = 1 if char.hit_dice_current > 0 and char.current_hp < char.max_hp else 0
            results[char.character_name] = char.short_rest(dice_to_spend)
        return results

    def party_long_rest(self) -> Dict[str, Dict]:
        """All party members take a long rest."""
        results = {}
        for char in self.characters.values():
            results[char.character_name] = char.long_rest()
        return results

    def get_party_summary(self) -> str:
        """Get text summary of entire party."""
        lines = [f"=== {self.party_name} ==="]
        lines.append(f"Party Gold: {self.gold} gp")
        lines.append("")

        for char in self.characters.values():
            status = "DEAD" if not char.is_alive() else \
                    "UNCONSCIOUS" if not char.is_conscious() else "OK"
            lines.append(f"{char.character_name} ({status}): {char.current_hp}/{char.max_hp} HP")

        if self.shared_inventory:
            lines.append("\nShared Inventory:")
            for item, qty in self.shared_inventory.items():
                lines.append(f"  {item} x{qty}")

        return "\n".join(lines)


@dataclass
class GameSession:
    """
    High-level game session state.

    Tracks location, quests, NPCs, and overall game state.
    Now includes world map for persistent location tracking.
    """
    session_name: str = "New Adventure"

    # Base character stats (STR, DEX, equipment) - keyed by character name
    # Works for both solo and party mode
    base_character_stats: Dict[str, Any] = field(default_factory=dict)  # {name: Character from character_creator}

    # Single character state (for non-party mode)
    character_state: Optional['CharacterState'] = None

    # Party and combat
    party: PartyState = field(default_factory=PartyState)
    combat: CombatState = field(default_factory=CombatState)

    # Location and world map
    current_location: str = "Unknown"
    scene_description: str = ""
    world_map: Dict[str, Location] = field(default_factory=dict)  # {location_name: Location}
    
    # Quest tracking
    active_quests: List[Dict[str, str]] = field(default_factory=list)  # [{name, description, status}]
    completed_quests: List[str] = field(default_factory=list)

    # NPCs present (temporary, for current scene)
    npcs_present: List[str] = field(default_factory=list)

    # Time tracking (in-game)
    day: int = 1
    time_of_day: str = "morning"  # morning, afternoon, evening, night

    # Encounter tracking (prevents encounter spam)
    turns_since_last_encounter: int = 0
    last_encounter_location: str = ""

    # Session notes
    notes: List[str] = field(default_factory=list)

    def add_quest(self, name: str, description: str):
        """Add a new quest."""
        self.active_quests.append({
            "name": name,
            "description": description,
            "status": "active"
        })

    def complete_quest(self, quest_name: str):
        """Mark a quest as completed."""
        for quest in self.active_quests:
            if quest["name"] == quest_name:
                quest["status"] = "completed"
                self.completed_quests.append(quest_name)
                break

    def add_note(self, note: str):
        """Add a session note."""
        self.notes.append(f"[Day {self.day}, {self.time_of_day}] {note}")

    def advance_time(self):
        """Advance time of day."""
        times = ["morning", "afternoon", "evening", "night"]
        current_idx = times.index(self.time_of_day)

        if current_idx == len(times) - 1:
            # New day
            self.day += 1
            self.time_of_day = "morning"
        else:
            self.time_of_day = times[current_idx + 1]

    def set_location(self, location: str, description: str = ""):
        """
        Set current location (legacy method for backward compatibility).
        
        If location doesn't exist in world_map, creates it.
        """
        self.current_location = location
        if description:
            self.scene_description = description
        
        # Create location in world map if it doesn't exist
        if location not in self.world_map:
            # Try to infer type from name
            location_type = LocationType.TOWN  # Default
            if "tavern" in location.lower() or "inn" in location.lower():
                location_type = LocationType.TAVERN
            elif "shop" in location.lower() or "market" in location.lower():
                location_type = LocationType.SHOP
            elif "temple" in location.lower():
                location_type = LocationType.TEMPLE
            elif "guild" in location.lower():
                location_type = LocationType.GUILD_HALL
            elif "dungeon" in location.lower() or "cave" in location.lower():
                location_type = LocationType.DUNGEON
            
            self.world_map[location] = Location(
                name=location,
                location_type=location_type,
                description=description or f"You are in {location}."
            )
        
        # Record visit
        if location in self.world_map:
            self.world_map[location].record_visit(self.day)
        
        self.add_note(f"Arrived at {location}")
    
    def add_location(self, location: Location):
        """Add a location to the world map."""
        self.world_map[location.name] = location
    
    def get_location(self, location_name: str) -> Optional[Location]:
        """Get a location from the world map."""
        return self.world_map.get(location_name)
    
    def get_current_location_obj(self) -> Optional[Location]:
        """Get the current Location object."""
        return self.world_map.get(self.current_location)
    
    def connect_locations(self, loc1: str, loc2: str):
        """Create a bidirectional connection between two locations."""
        if loc1 in self.world_map and loc2 in self.world_map:
            self.world_map[loc1].add_connection(loc2)
            self.world_map[loc2].add_connection(loc1)
    
    def travel_to(self, destination: str) -> Tuple[bool, str]:
        """
        Travel to a connected location.
        
        Returns:
            (success, message)
        """
        current_loc = self.get_current_location_obj()
        
        if not current_loc:
            return False, f"Current location '{self.current_location}' not found in world map."
        
        # Check if destination is connected
        if destination not in current_loc.connections:
            available = ", ".join(current_loc.connections) if current_loc.connections else "none"
            return False, f"Cannot travel to '{destination}' from here. Available: {available}"
        
        # Check if destination exists
        if destination not in self.world_map:
            return False, f"Destination '{destination}' doesn't exist."
        
        # Travel!
        dest_loc = self.world_map[destination]
        self.current_location = destination
        self.scene_description = dest_loc.description
        dest_loc.record_visit(self.day)
        
        self.add_note(f"Traveled to {destination}")
        
        return True, f"You travel to {destination}. {dest_loc.description}"
    
    def get_available_destinations(self) -> List[str]:
        """Get list of locations you can travel to from current location."""
        current_loc = self.get_current_location_obj()
        if current_loc:
            return current_loc.connections
        return []
    
    def get_discovered_locations(self) -> List[str]:
        """Get list of all discovered locations."""
        return [name for name, loc in self.world_map.items() if loc.is_discovered]
    
    def mark_enemy_defeated_at_current_location(self, enemy_name: str):
        """Mark an enemy as defeated at the current location."""
        current_loc = self.get_current_location_obj()
        if current_loc:
            current_loc.mark_enemy_defeated(enemy_name)
    
    def is_enemy_defeated_here(self, enemy_name: str) -> bool:
        """Check if an enemy was already defeated at current location."""
        current_loc = self.get_current_location_obj()
        if current_loc:
            return current_loc.is_enemy_defeated(enemy_name)
        return False

    def get_session_summary(self) -> str:
        """Get comprehensive session summary."""
        lines = [f"=== {self.session_name} ==="]
        lines.append(f"Day {self.day}, {self.time_of_day}")
        lines.append(f"Location: {self.current_location}")

        if self.scene_description:
            lines.append(f"\n{self.scene_description}")

        # Party summary
        lines.append(f"\n{self.party.get_party_summary()}")

        # Combat
        if self.combat.in_combat:
            lines.append(f"\n{self.combat.get_combat_summary()}")

        # Quests
        if self.active_quests:
            lines.append("\nActive Quests:")
            for quest in self.active_quests:
                if quest["status"] == "active":
                    lines.append(f"  - {quest['name']}: {quest['description']}")

        return "\n".join(lines)
