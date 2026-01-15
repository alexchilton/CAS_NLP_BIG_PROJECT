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
        """Check if item is currently at this location (case-insensitive)."""
        return any(item.lower() == item_name.lower() for item in self.available_items)
    
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
            "available_items": self.available_items,
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
            available_items=data.get("available_items", []),
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

    # Spell knowledge and preparation (D&D 5e)
    spellcasting_class: Optional[str] = None  # "Wizard", "Sorcerer", etc. (None = non-caster)
    spellcasting_ability: str = "INT"  # INT, WIS, or CHA
    known_spells: List[str] = field(default_factory=list)  # All spells known (for all casters)
    prepared_spells: List[str] = field(default_factory=list)  # Currently prepared (Wizard/Cleric/Druid/Paladin)

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
                   requires_concentration: bool = False,
                   skip_validation: bool = False) -> Dict[str, Any]:
        """
        Cast a spell, consuming a spell slot.

        Args:
            spell_level: Level of spell slot to use
            spell_name: Name of spell to cast
            requires_concentration: Whether spell requires concentration
            skip_validation: Skip spell known/prepared check (for backwards compatibility)

        Returns:
            Dict with success status and message
        """
        # Validate spell is known/prepared (unless skipped for backwards compatibility)
        if not skip_validation and self.spellcasting_class:
            can_cast, reason = self.can_cast_spell(spell_name)
            if not can_cast:
                return {
                    "success": False,
                    "message": reason
                }

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

    # Spell Learning and Preparation
    def is_prepared_caster(self) -> bool:
        """
        Check if this character uses prepared spells (Wizard, Cleric, Druid, Paladin).

        Returns:
            True if prepared caster, False if known caster or non-caster
        """
        if not self.spellcasting_class:
            return False

        prepared_classes = ["Wizard", "Cleric", "Druid", "Paladin"]
        return self.spellcasting_class in prepared_classes

    def is_known_caster(self) -> bool:
        """
        Check if this character uses known spells (Sorcerer, Bard, Warlock, Ranger).

        Returns:
            True if known caster, False otherwise
        """
        if not self.spellcasting_class:
            return False

        known_classes = ["Sorcerer", "Bard", "Warlock", "Ranger"]
        return self.spellcasting_class in known_classes

    def get_max_prepared_spells(self, ability_modifier: int) -> int:
        """
        Calculate maximum number of prepared spells.

        For prepared casters: ability_modifier + class_level (minimum 1)
        For known casters: returns number of known spells (unlimited prepared)

        Args:
            ability_modifier: Spellcasting ability modifier (INT, WIS, or CHA)

        Returns:
            Maximum number of prepared spells
        """
        if not self.spellcasting_class:
            return 0

        if self.is_prepared_caster():
            # Prepared casters: ability mod + level (min 1)
            return max(1, ability_modifier + self.level)
        else:
            # Known casters can cast any known spell
            return len(self.known_spells)

    def learn_spell(self, spell_name: str) -> Dict[str, Any]:
        """
        Learn a new spell.

        For all casters: adds to known_spells list
        For prepared casters: must still prepare daily
        For known casters: can cast immediately

        Args:
            spell_name: Name of spell to learn

        Returns:
            Dict with success status and message
        """
        if not self.spellcasting_class:
            return {
                "success": False,
                "message": f"{self.character_name} is not a spellcaster"
            }

        # Check if already known
        if spell_name in self.known_spells:
            return {
                "success": False,
                "message": f"Already know {spell_name}"
            }

        # Add to known spells
        self.known_spells.append(spell_name)

        # For known casters, automatically prepare it
        if self.is_known_caster():
            if spell_name not in self.prepared_spells:
                self.prepared_spells.append(spell_name)

        return {
            "success": True,
            "spell_name": spell_name,
            "message": f"Learned {spell_name}!" +
                      (" (automatically prepared)" if self.is_known_caster() else " (must prepare to cast)")
        }

    def prepare_spell(self, spell_name: str, ability_modifier: int) -> Dict[str, Any]:
        """
        Prepare a spell for casting (prepared casters only).

        Args:
            spell_name: Name of spell to prepare
            ability_modifier: Spellcasting ability modifier

        Returns:
            Dict with success status and message
        """
        if not self.is_prepared_caster():
            return {
                "success": False,
                "message": f"{self.spellcasting_class} uses known spells, not prepared spells"
            }

        # Check if spell is known
        if spell_name not in self.known_spells:
            return {
                "success": False,
                "message": f"Don't know {spell_name}. Must learn it first (find scroll, level up, etc.)"
            }

        # Check if already prepared
        if spell_name in self.prepared_spells:
            return {
                "success": False,
                "message": f"{spell_name} is already prepared"
            }

        # Check preparation limit
        max_prepared = self.get_max_prepared_spells(ability_modifier)
        if len(self.prepared_spells) >= max_prepared:
            return {
                "success": False,
                "message": f"Already have {max_prepared} spells prepared (limit reached). Unprepare a spell first."
            }

        # Prepare the spell
        self.prepared_spells.append(spell_name)

        return {
            "success": True,
            "spell_name": spell_name,
            "prepared_count": len(self.prepared_spells),
            "max_prepared": max_prepared,
            "message": f"Prepared {spell_name} ({len(self.prepared_spells)}/{max_prepared} spells prepared)"
        }

    def unprepare_spell(self, spell_name: str) -> Dict[str, Any]:
        """
        Unprepare a spell (prepared casters only).

        Args:
            spell_name: Name of spell to unprepare

        Returns:
            Dict with success status and message
        """
        if not self.is_prepared_caster():
            return {
                "success": False,
                "message": f"{self.spellcasting_class} uses known spells, not prepared spells"
            }

        if spell_name not in self.prepared_spells:
            return {
                "success": False,
                "message": f"{spell_name} is not prepared"
            }

        self.prepared_spells.remove(spell_name)

        return {
            "success": True,
            "spell_name": spell_name,
            "message": f"Unprepared {spell_name}"
        }

    def can_cast_spell(self, spell_name: str) -> Tuple[bool, str]:
        """
        Check if character can cast a specific spell.

        Validates:
        - Character is a spellcaster
        - Spell is known
        - Spell is prepared (if prepared caster)

        Does NOT check spell slots (use has_slot() separately)

        Args:
            spell_name: Name of spell to check

        Returns:
            Tuple of (can_cast, reason)
        """
        if not self.spellcasting_class:
            return False, f"{self.character_name} is not a spellcaster"

        # Check if spell is known
        if spell_name not in self.known_spells:
            return False, f"Don't know {spell_name}"

        # For prepared casters, must be prepared
        if self.is_prepared_caster():
            if spell_name not in self.prepared_spells:
                return False, f"{spell_name} is not prepared. Use /prepare_spell to prepare it."

        return True, "Can cast"

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
                "leveled_up": True,  # Changed to match convention
                "new_level": self.level + 1,  # What level they can advance to
                "message": f"Gained {xp} XP! Ready to level up!"
            }

        return {
            "xp_gained": xp,
            "total_xp": self.experience_points,
            "xp_to_next_level": xp_for_next - self.experience_points,
            "leveled_up": False,
            "message": f"Gained {xp} XP ({self.experience_points}/{xp_for_next})"
        }

    def level_up(self, character_class: str, hit_die_size: int = 8, con_modifier: int = 0) -> Dict[str, Any]:
        """
        Level up the character.

        Args:
            character_class: Character class for spell slot lookup (e.g., "Wizard")
            hit_die_size: Size of hit die (d6=6, d8=8, d10=10, d12=12)
            con_modifier: Constitution modifier for HP calculation

        Returns:
            Dict with level-up results
        """
        # Check if character has enough XP
        xp_needed = self.level * 1000
        if self.experience_points < xp_needed:
            return {
                "success": False,
                "message": f"Not enough XP to level up! Need {xp_needed}, have {self.experience_points}"
            }

        old_level = self.level
        new_level = old_level + 1

        # Roll for HP increase (hit die + CON modifier, minimum 1)
        import random
        hp_roll = random.randint(1, hit_die_size)
        hp_increase = max(1, hp_roll + con_modifier)

        # Update character stats
        self.level = new_level
        self.max_hp += hp_increase
        self.current_hp += hp_increase  # Heal character when leveling up
        self.hit_dice_max = new_level  # Hit dice max equals level

        # Update proficiency bonus (increases at levels 5, 9, 13, 17)
        old_prof_bonus = 2 + ((old_level - 1) // 4)
        new_prof_bonus = 2 + ((new_level - 1) // 4)
        prof_bonus_increased = (new_prof_bonus > old_prof_bonus)

        # Update spell slots using RAG lookup
        spell_slots_updated = False
        new_spell_slots = None
        try:
            # Import here to avoid circular dependency
            new_spell_slots = initialize_spell_slots_from_class(character_class, new_level)

            # Copy over current spell slot usage from old slots
            # Only update max slots, preserve current usage where possible
            for level_num in range(1, 10):
                new_max = getattr(new_spell_slots, f"level_{level_num}")
                old_max = getattr(self.spell_slots, f"level_{level_num}")
                old_current = getattr(self.spell_slots, f"current_{level_num}")

                if new_max > old_max:
                    # Gained new slots - give them fully charged
                    setattr(new_spell_slots, f"current_{level_num}", new_max)
                elif new_max == old_max:
                    # Same number of slots - preserve current usage
                    setattr(new_spell_slots, f"current_{level_num}", old_current)
                else:
                    # Lost slots (shouldn't happen) - cap at new max
                    setattr(new_spell_slots, f"current_{level_num}", min(old_current, new_max))

            self.spell_slots = new_spell_slots
            spell_slots_updated = True
        except Exception as e:
            # If spell slot lookup fails, keep existing slots
            spell_slots_updated = False

        # Build result message
        result = {
            "success": True,
            "old_level": old_level,
            "new_level": new_level,
            "hp_roll": hp_roll,
            "hp_increase": hp_increase,
            "new_max_hp": self.max_hp,
            "proficiency_bonus": new_prof_bonus,
            "prof_bonus_increased": prof_bonus_increased,
            "spell_slots_updated": spell_slots_updated,
            "new_spell_slots": new_spell_slots.get_available() if new_spell_slots else None,
            "message": f"Level up! Now level {new_level}. HP +{hp_increase} (rolled {hp_roll}+{con_modifier})"
        }

        return result

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
            "spellcasting_class": self.spellcasting_class,
            "spellcasting_ability": self.spellcasting_ability,
            "known_spells": self.known_spells,
            "prepared_spells": self.prepared_spells,
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
            spellcasting_class=data.get("spellcasting_class"),
            spellcasting_ability=data.get("spellcasting_ability", "INT"),
            known_spells=data.get("known_spells", []),
            prepared_spells=data.get("prepared_spells", []),
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

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "in_combat": self.in_combat,
            "round_number": self.round_number,
            "initiative_order": self.initiative_order,
            "current_turn_index": self.current_turn_index,
            "active_effects": {
                name: list(data) for name, data in self.active_effects.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CombatState":
        """Create CombatState from dictionary."""
        combat = cls(
            in_combat=data.get("in_combat", False),
            round_number=data.get("round_number", 0),
            initiative_order=data.get("initiative_order", []),
            current_turn_index=data.get("current_turn_index", 0)
        )

        # Reconstruct active effects (convert lists back to tuples)
        combat.active_effects = {
            name: tuple(effect_data)
            for name, effect_data in data.get("active_effects", {}).items()
        }

        return combat


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

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "party_name": self.party_name,
            "characters": {name: char.to_dict() for name, char in self.characters.items()},
            "shared_inventory": self.shared_inventory,
            "gold": self.gold
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PartyState":
        """Create PartyState from dictionary."""
        party = cls(
            party_name=data.get("party_name", "Adventuring Party"),
            shared_inventory=data.get("shared_inventory", {}),
            gold=data.get("gold", 0)
        )

        # Reconstruct character states
        for name, char_data in data.get("characters", {}).items():
            party.characters[name] = CharacterState.from_dict(char_data)

        return party


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
        
        # Try case-insensitive matching for user convenience
        destination_lower = destination.lower()
        matched_destination = None
        
        # Check connections case-insensitively
        for conn in current_loc.connections:
            if conn.lower() == destination_lower:
                matched_destination = conn
                break
        
        if not matched_destination:
            available = ", ".join(current_loc.connections) if current_loc.connections else "none"
            return False, f"Cannot travel to '{destination}' from here. Available: {available}"
        
        # Check if destination exists (use matched name)
        if matched_destination not in self.world_map:
            return False, f"Destination '{matched_destination}' doesn't exist."
        
        # Update destination to use correct casing
        destination = matched_destination
        
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

    def save_to_json(self, filepath: Path):
        """
        Save complete game session to JSON file.

        This saves everything:
        - World map (all locations)
        - Character state
        - Party state (all party members)
        - Combat state (if in combat)
        - Quests, NPCs, time, etc.

        Args:
            filepath: Path to save file (e.g., Path("saves/game1.json"))
        """
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        save_data = {
            "version": "1.0",  # For future compatibility
            "session_name": self.session_name,
            "current_location": self.current_location,
            "scene_description": self.scene_description,

            # World map (serialize all locations)
            "world_map": {
                name: loc.to_dict() for name, loc in self.world_map.items()
            },

            # Character state (single character mode)
            "character_state": self.character_state.to_dict() if self.character_state else None,

            # Party and combat
            "party": self.party.to_dict(),
            "combat": self.combat.to_dict(),

            # Quests
            "active_quests": self.active_quests,
            "completed_quests": self.completed_quests,

            # NPCs and time
            "npcs_present": self.npcs_present,
            "day": self.day,
            "time_of_day": self.time_of_day,

            # Encounter tracking
            "turns_since_last_encounter": self.turns_since_last_encounter,
            "last_encounter_location": self.last_encounter_location,

            # Notes
            "notes": self.notes
        }

        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: Path) -> "GameSession":
        """
        Load complete game session from JSON file.

        Args:
            filepath: Path to save file

        Returns:
            GameSession with all state restored
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Create session
        session = cls(
            session_name=data.get("session_name", "Loaded Game"),
            current_location=data.get("current_location", "Unknown"),
            scene_description=data.get("scene_description", ""),
            day=data.get("day", 1),
            time_of_day=data.get("time_of_day", "morning"),
            turns_since_last_encounter=data.get("turns_since_last_encounter", 0),
            last_encounter_location=data.get("last_encounter_location", "")
        )

        # Restore world map
        session.world_map = {
            name: Location.from_dict(loc_data)
            for name, loc_data in data.get("world_map", {}).items()
        }

        # Restore character state
        if data.get("character_state"):
            session.character_state = CharacterState.from_dict(data["character_state"])

        # Restore party
        session.party = PartyState.from_dict(data.get("party", {}))

        # Restore combat
        session.combat = CombatState.from_dict(data.get("combat", {}))

        # Restore quests
        session.active_quests = data.get("active_quests", [])
        session.completed_quests = data.get("completed_quests", [])

        # Restore NPCs and notes
        session.npcs_present = data.get("npcs_present", [])
        session.notes = data.get("notes", [])

        return session


# Helper functions for spell slot initialization
def initialize_spell_slots_from_class(character_class: str, character_level: int) -> SpellSlots:
    """
    Initialize spell slots based on character class and level.
    
    Uses D&D 5e spell slot progression tables.
    
    Args:
        character_class: Character class (e.g., "Wizard", "Paladin")
        character_level: Character level (1-20)
    
    Returns:
        SpellSlots object with appropriate slots for class/level
    """
    # Import here to avoid circular dependency
    from dnd_rag_system.core.chroma_manager import ChromaDBManager
    from dnd_rag_system.systems.spell_manager import SpellManager
    
    # Get spell slot progression
    db = ChromaDBManager()
    spell_mgr = SpellManager(db)
    slots_dict = spell_mgr.get_spell_slots_for_level(character_class, character_level)
    
    # Create SpellSlots object
    kwargs = {}
    for spell_level, num_slots in slots_dict.items():
        kwargs[f"level_{spell_level}"] = num_slots
    
    return SpellSlots(**kwargs)
