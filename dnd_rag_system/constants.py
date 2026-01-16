"""
Constants for D&D RAG System

Centralized location for all magic strings, commands, and keywords.
Refactoring magic strings to constants improves:
- Maintainability: Change in one place
- Safety: Typos caught at import time
- Discoverability: IDE autocomplete shows available commands
- Consistency: Same string used everywhere
"""

# ============================================================================
# COMMANDS - Player-facing slash commands
# ============================================================================

class Commands:
    """Player slash commands used in game interface."""
    
    # Combat Commands
    START_COMBAT = '/start_combat'
    NEXT_TURN = '/next_turn'
    END_COMBAT = '/end_combat'
    INITIATIVE = '/initiative'
    FLEE = '/flee'
    
    # Character Actions
    STATS = '/stats'
    CHARACTER = '/character'
    CAST = '/cast'
    USE = '/use'
    PICKUP = '/pickup'
    EQUIP = '/equip'
    
    # Resting
    REST = '/rest'
    SHORT_REST = '/short_rest'
    LONG_REST = '/long_rest'
    
    # Health & Saving Throws
    DEATH_SAVE = '/death_save'
    HEAL = '/heal'
    
    # Progression
    LEVEL_UP = '/level_up'
    
    # Exploration
    TRAVEL = '/travel'
    EXPLORE = '/explore'
    MAP = '/map'
    LOCATIONS = '/locations'
    
    # Shop System
    BUY = '/buy'
    SELL = '/sell'
    SHOP = '/shop'
    
    # Information & Help
    HELP = '/help'
    CONTEXT = '/context'
    HISTORY = '/history'
    RAG = '/rag'
    
    # Session Management
    SAVE = '/save'
    LOAD = '/load'
    QUIT = '/quit'
    EXIT = '/exit'
    
    @classmethod
    def all_commands(cls):
        """Return list of all commands for validation."""
        return [
            value for name, value in vars(cls).items()
            if not name.startswith('_') and isinstance(value, str) and value.startswith('/')
        ]
    
    @classmethod
    def combat_commands(cls):
        """Return list of combat-related commands."""
        return [
            cls.START_COMBAT,
            cls.NEXT_TURN,
            cls.END_COMBAT,
            cls.INITIATIVE,
            cls.FLEE,
        ]
    
    @classmethod
    def unconscious_allowed_commands(cls):
        """Commands allowed when character is unconscious."""
        return [
            cls.HELP,
            cls.STATS,
            cls.CHARACTER,
            cls.CONTEXT,
            cls.DEATH_SAVE,
            cls.INITIATIVE,
        ]


# ============================================================================
# ITEM EFFECTS - Magic item effect keys
# ============================================================================

class ItemEffects:
    """Magic item effect type constants."""
    
    # Armor Class
    AC_BONUS = 'ac_bonus'
    
    # Attack & Damage
    ATTACK_BONUS = 'attack_bonus'
    DAMAGE_BONUS = 'damage_bonus'
    
    # Saving Throws
    SAVING_THROW_BONUS = 'saving_throw_bonus'
    
    # Elemental Damage
    FIRE_DAMAGE = 'fire_damage'
    COLD_DAMAGE = 'cold_damage'
    LIGHTNING_DAMAGE = 'lightning_damage'
    POISON_DAMAGE = 'poison_damage'
    ACID_DAMAGE = 'acid_damage'
    NECROTIC_DAMAGE = 'necrotic_damage'
    RADIANT_DAMAGE = 'radiant_damage'
    
    # Resistances
    RESISTANCE = 'resistance'
    FIRE_RESISTANCE = 'fire_resistance'
    COLD_RESISTANCE = 'cold_resistance'
    POISON_RESISTANCE = 'poison_resistance'
    
    # Special Abilities
    STEALTH_ADVANTAGE = 'stealth_advantage'
    SPEED_DOUBLE = 'speed_double'
    FLYING_SPEED = 'flying_speed'
    INVISIBILITY = 'invisibility'
    TEMP_HP = 'temp_hp'
    HEALING = 'healing'
    DARKVISION = 'darkvision'
    
    # Immunities
    IMMUNE_POISON = 'immune_poison'
    IMMUNE_DISEASE = 'immune_disease'


# ============================================================================
# EQUIPMENT SLOTS - Character equipment locations
# ============================================================================

class EquipmentSlots:
    """Equipment slot constants for character inventory."""
    
    # Armor & Weapons
    ARMOR = 'armor'
    WEAPON = 'weapon'
    SHIELD = 'shield'
    
    # Accessories
    BOOTS = 'boots'
    CLOAK = 'cloak'
    GLOVES = 'gloves'
    HELM = 'helm'
    HELMET = 'helmet'
    AMULET = 'amulet'
    NECKLACE = 'necklace'
    RING = 'ring'
    BELT = 'belt'
    GIRDLE = 'girdle'
    BRACERS = 'bracers'
    
    # Alternative names (for flexible matching)
    SLOT_ALIASES = {
        'helmet': 'helm',
        'necklace': 'amulet',
        'girdle': 'belt',
    }


# ============================================================================
# LOCATION TYPES - World location categories
# ============================================================================

class LocationTypes:
    """Location type constants."""
    
    # Settlements
    TAVERN = 'tavern'
    INN = 'inn'
    SHOP = 'shop'
    MARKET = 'market'
    TEMPLE = 'temple'
    GUILD = 'guild'
    TOWN = 'town'
    CITY = 'city'
    VILLAGE = 'village'
    
    # Wilderness
    FOREST = 'forest'
    MOUNTAIN = 'mountain'
    PLAINS = 'plains'
    SWAMP = 'swamp'
    DESERT = 'desert'
    
    # Dangerous Areas
    DUNGEON = 'dungeon'
    CAVE = 'cave'
    RUINS = 'ruins'
    TOMB = 'tomb'
    LAIR = 'lair'
    
    # Roads
    ROAD = 'road'
    PATH = 'path'
    CROSSROADS = 'crossroads'


# ============================================================================
# SPELL KEYWORDS - Spell-related detection
# ============================================================================

class SpellKeywords:
    """Keywords related to spell casting and magic."""
    
    # Spell Levels
    CANTRIP = 'cantrip'
    
    # Spell Properties
    CONCENTRATION = 'concentration'
    RITUAL = 'ritual'
    
    # Healing Keywords
    HEALING = 'healing'
    CURE = 'cure'
    RESTORE = 'restore'
    
    # Targeting
    SELF = 'self'
    TOUCH = 'touch'
    RANGE = 'range'
    AREA = 'area'


# ============================================================================
# DAMAGE TYPES - Combat damage categories
# ============================================================================

class DamageTypes:
    """D&D 5e damage type constants."""
    
    # Physical
    BLUDGEONING = 'bludgeoning'
    PIERCING = 'piercing'
    SLASHING = 'slashing'
    
    # Elemental
    FIRE = 'fire'
    COLD = 'cold'
    LIGHTNING = 'lightning'
    THUNDER = 'thunder'
    
    # Magical
    ACID = 'acid'
    POISON = 'poison'
    NECROTIC = 'necrotic'
    RADIANT = 'radiant'
    PSYCHIC = 'psychic'
    FORCE = 'force'


# ============================================================================
# CHARACTER CLASSES - D&D 5e classes
# ============================================================================

class CharacterClasses:
    """D&D 5e character class constants."""
    
    BARBARIAN = 'Barbarian'
    BARD = 'Bard'
    CLERIC = 'Cleric'
    DRUID = 'Druid'
    FIGHTER = 'Fighter'
    MONK = 'Monk'
    PALADIN = 'Paladin'
    RANGER = 'Ranger'
    ROGUE = 'Rogue'
    SORCERER = 'Sorcerer'
    WARLOCK = 'Warlock'
    WIZARD = 'Wizard'


# ============================================================================
# CHARACTER RACES - D&D 5e races
# ============================================================================

class CharacterRaces:
    """D&D 5e character race constants."""
    
    DWARF = 'Dwarf'
    ELF = 'Elf'
    HALFLING = 'Halfling'
    HUMAN = 'Human'
    DRAGONBORN = 'Dragonborn'
    GNOME = 'Gnome'
    HALF_ELF = 'Half-Elf'
    HALF_ORC = 'Half-Orc'
    TIEFLING = 'Tiefling'


# ============================================================================
# ACTION KEYWORDS - Combat and exploration action detection
# ============================================================================

class ActionKeywords:
    """Keywords for detecting player action intent."""
    
    # Combat Actions
    ATTACK_KEYWORDS = [
        'attack', 'hit', 'strike', 'slash', 'stab', 'shoot', 'fire',
        'swing', 'punch', 'kick', 'smash', 'bash', 'cleave',
        'fire at', 'swing at', 'charge', 'lunge at', 'fight',
        'thrust', 'parry', 'block and attack'
    ]
    
    # Spell Casting
    SPELL_KEYWORDS = [
        'cast', 'casts', 'casting', 'spell', 'magic', 'conjure',
        'summon', 'invoke', 'channel',
        'magic missile', 'fireball', 'healing word',
        'cure wounds', 'eldritch blast', 'sacred flame', 'guiding bolt'
    ]
    
    # Stealing
    STEAL_KEYWORDS = [
        'steal', 'swipe', 'pilfer', 'pocket', 'snatch', 'lift',
        'pickpocket', 'filch', 'take', 'nick', 'pinch', 'sneak'
    ]
    
    # Item Use
    ITEM_USE_KEYWORDS = [
        'use', 'drink', 'eat', 'consume', 'apply', 'activate',
        'equip', 'wear', 'wield', 'ready', 'draw', 'grab', 'hold',
        'open', 'pull out', 'take out', 'reach for'
    ]
    
    # Conversation
    CONVERSATION_KEYWORDS = [
        'talk', 'speak', 'ask', 'tell', 'say', 'greet', 'chat',
        'discuss', 'converse', 'question', 'inquire', 'talk to',
        'speak to', 'say to', 'chat with', 'discuss with', 'address',
        'hello', 'hi', 'hey', '"'  # Quoted speech
    ]
    
    # Exploration
    EXPLORATION_KEYWORDS = [
        'look', 'search', 'examine', 'inspect', 'explore', 'investigate',
        'check', 'scan', 'survey', 'peer', 'study'
    ]


# ============================================================================
# CONDITION TYPES - Character status effects
# ============================================================================

class Conditions:
    """D&D 5e condition constants."""
    
    BLINDED = 'blinded'
    CHARMED = 'charmed'
    DEAFENED = 'deafened'
    FRIGHTENED = 'frightened'
    GRAPPLED = 'grappled'
    INCAPACITATED = 'incapacitated'
    INVISIBLE = 'invisible'
    PARALYZED = 'paralyzed'
    PETRIFIED = 'petrified'
    POISONED = 'poisoned'
    PRONE = 'prone'
    RESTRAINED = 'restrained'
    STUNNED = 'stunned'
    UNCONSCIOUS = 'unconscious'
    EXHAUSTED = 'exhausted'


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_command(text: str) -> bool:
    """Check if text starts with a valid command."""
    if not text or not text.strip():
        return False
    return text.strip().lower() in [cmd.lower() for cmd in Commands.all_commands()]


def normalize_slot(slot: str) -> str:
    """Normalize equipment slot name to canonical form."""
    slot_lower = slot.lower()
    return EquipmentSlots.SLOT_ALIASES.get(slot_lower, slot_lower)
