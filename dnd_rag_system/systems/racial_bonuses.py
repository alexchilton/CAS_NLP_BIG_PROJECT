"""
Racial Bonuses from RAG

Load D&D 5e racial traits and bonuses from ChromaDB.
Handles ability score increases, darkvision, speed, languages, and other racial features.
"""

import json
import re
from typing import Dict, Optional, List
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.chroma_manager import ChromaDBManager


# Fallback data: Correct D&D 5e racial bonuses
# Used when RAG data is unavailable or incorrect
FALLBACK_RACIAL_DATA = {
    "Dwarf": {
        "ability_increases": {"constitution": 2},
        "darkvision": 60,
        "speed": 25,
        "size": "Medium",
        "languages": ["Common", "Dwarvish"],
        "traits": ["Dwarven Resilience", "Dwarven Combat Training", "Stonecunning"]
    },
    "Elf": {
        "ability_increases": {"dexterity": 2},
        "darkvision": 60,
        "speed": 30,
        "size": "Medium",
        "languages": ["Common", "Elvish"],
        "traits": ["Keen Senses", "Fey Ancestry", "Trance"]
    },
    "Halfling": {
        "ability_increases": {"dexterity": 2},
        "darkvision": 0,
        "speed": 25,
        "size": "Small",
        "languages": ["Common", "Halfling"],
        "traits": ["Lucky", "Brave", "Halfling Nimbleness"]
    },
    "Human": {
        "ability_increases": {"strength": 1, "dexterity": 1, "constitution": 1,
                             "intelligence": 1, "wisdom": 1, "charisma": 1},
        "darkvision": 0,
        "speed": 30,
        "size": "Medium",
        "languages": ["Common", "One extra language"],
        "traits": []
    },
    "Dragonborn": {
        "ability_increases": {"strength": 2, "charisma": 1},
        "darkvision": 0,
        "speed": 30,
        "size": "Medium",
        "languages": ["Common", "Draconic"],
        "traits": ["Draconic Ancestry", "Breath Weapon", "Damage Resistance"]
    },
    "Gnome": {
        "ability_increases": {"intelligence": 2},
        "darkvision": 60,
        "speed": 25,
        "size": "Small",
        "languages": ["Common", "Gnomish"],
        "traits": ["Gnome Cunning"]
    },
    "Half-Elf": {
        "ability_increases": {"charisma": 2},  # Plus two other abilities +1 (player choice)
        "darkvision": 60,
        "speed": 30,
        "size": "Medium",
        "languages": ["Common", "Elvish", "One extra language"],
        "traits": ["Skill Versatility", "Fey Ancestry"]
    },
    "Half-Orc": {
        "ability_increases": {"strength": 2, "constitution": 1},
        "darkvision": 60,
        "speed": 30,
        "size": "Medium",
        "languages": ["Common", "Orc"],
        "traits": ["Menacing", "Relentless Endurance", "Savage Attacks"]
    },
    "Tiefling": {
        "ability_increases": {"charisma": 2, "intelligence": 1},
        "darkvision": 60,
        "speed": 30,
        "size": "Medium",
        "languages": ["Common", "Infernal"],
        "traits": ["Hellish Resistance", "Infernal Legacy"]
    }
}


@dataclass
class RacialTraits:
    """Racial traits loaded from RAG."""
    race_name: str
    ability_increases: Dict[str, int]  # {"strength": 2, "dexterity": 1}
    darkvision: int  # Range in feet (0 if none)
    speed: int  # Base walking speed in feet
    size: str  # "Small", "Medium", etc.
    languages: List[str]  # ["Common", "Elvish"]
    special_traits: List[str]  # Additional racial features
    raw_text: str  # Full description from RAG


def normalize_ability_name(ability: str) -> str:
    """
    Normalize ability score names (handle OCR errors and variations).

    Args:
        ability: Ability name (might have typos)

    Returns:
        Standardized ability name
    """
    ability_lower = ability.lower().strip()

    # Handle common OCR errors and variations
    mappings = {
        "str": "strength",
        "dex": "dexterity",
        "con": "constitution",
        "int": "intelligence",
        "wis": "wisdom",
        "cha": "charisma",
        # OCR errors
        "oexterity": "dexterity",  # Common OCR error
        "oexterity": "dexterity",
        "inlelligence": "intelligence",
        "conslilulio": "constitution",
    }

    # Check mappings first
    if ability_lower in mappings:
        return mappings[ability_lower]

    # Fuzzy matching for ability names
    for standard_ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
        if standard_ability in ability_lower or ability_lower in standard_ability:
            return standard_ability

    return ability_lower


def parse_ability_increases(metadata: Dict) -> Dict[str, int]:
    """
    Parse ability score increases from metadata.

    Args:
        metadata: RAG metadata containing ability_increases

    Returns:
        Dictionary of ability score increases
    """
    increases = {}

    # Try to get from metadata
    if "ability_increases" in metadata:
        try:
            # Parse JSON string
            ability_data = metadata["ability_increases"]
            if isinstance(ability_data, str):
                ability_dict = json.loads(ability_data)
            else:
                ability_dict = ability_data

            # Normalize ability names
            for ability, value in ability_dict.items():
                normalized = normalize_ability_name(ability)
                increases[normalized] = int(value)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Warning: Could not parse ability increases: {e}")

    return increases


def parse_speed(metadata: Dict, text: str) -> int:
    """
    Parse base walking speed from metadata or text.

    Args:
        metadata: RAG metadata
        text: Full text description

    Returns:
        Speed in feet (default 30)
    """
    # Try metadata first
    if "speed" in metadata:
        speed_text = str(metadata["speed"])
        # Extract number from text like "30 feet" or "Your base walking speed is 30 feet"
        match = re.search(r'(\d+)\s*fe', speed_text)
        if match:
            return int(match.group(1))

    # Try to find in text
    match = re.search(r'speed\s+is\s*(\d+)\s*fe', text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Default to 30 feet
    return 30


def parse_darkvision(metadata: Dict, text: str) -> int:
    """
    Parse darkvision range from metadata or text.

    Args:
        metadata: RAG metadata
        text: Full text description

    Returns:
        Darkvision range in feet (0 if none)
    """
    # Try metadata first
    if "darkvision" in metadata:
        try:
            return int(metadata["darkvision"])
        except (ValueError, TypeError):
            pass

    # Try to find in text
    match = re.search(r'darkvision[:\s]*(\d+)\s*fe', text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Check if darkvision is mentioned at all
    if "darkvision" in text.lower():
        return 60  # Default darkvision range

    return 0


def parse_languages(metadata: Dict, text: str) -> List[str]:
    """
    Parse languages from metadata or text.

    Args:
        metadata: RAG metadata
        text: Full text description

    Returns:
        List of languages
    """
    languages = []

    # Try metadata first
    if "languages" in metadata:
        lang_text = str(metadata["languages"])
        # Split by comma
        languages = [lang.strip() for lang in lang_text.split(",") if lang.strip()]

    # If empty, try to find in text
    if not languages:
        match = re.search(r'languages?[:\s]*(.*?)(?:\.|$)', text, re.IGNORECASE)
        if match:
            lang_text = match.group(1)
            languages = [lang.strip() for lang in re.split(r'[,and]+', lang_text) if lang.strip()]

    return languages


def parse_size(metadata: Dict, text: str) -> str:
    """
    Parse size category from metadata or text.

    Args:
        metadata: RAG metadata
        text: Full text description

    Returns:
        Size category (default "Medium")
    """
    # Try metadata first
    if "size" in metadata and metadata["size"]:
        return str(metadata["size"]).capitalize()

    # Try to find in text
    for size in ["Small", "Medium", "Large", "Tiny", "Huge", "Gargantuan"]:
        if size.lower() in text.lower():
            return size

    # Default to Medium
    return "Medium"


def extract_special_traits(text: str, race_name: str) -> List[str]:
    """
    Extract special racial traits from text description.

    Args:
        text: Full text description
        race_name: Name of the race

    Returns:
        List of special trait descriptions
    """
    traits = []

    # Common racial traits to look for
    trait_keywords = [
        "fey ancestry", "trance", "keen senses", "naturally stealthy",
        "brave", "lucky", "nimble", "stonecunning", "dwarven resilience",
        "relentless endurance", "savage attacks", "breath weapon",
        "damage resistance", "hellish resistance"
    ]

    for keyword in trait_keywords:
        if keyword.lower() in text.lower():
            # Extract the sentence containing this trait
            sentences = re.split(r'[.!?]', text)
            for sentence in sentences:
                if keyword.lower() in sentence.lower():
                    traits.append(sentence.strip())
                    break

    return traits


def load_racial_traits(db: Optional[ChromaDBManager], race_name: str) -> Optional[RacialTraits]:
    """
    Load racial traits for a given race.

    Tries RAG first, falls back to hardcoded correct D&D 5e data if RAG fails or has bad data.

    Args:
        db: ChromaDB manager instance (optional - will use fallback if None)
        race_name: Name of the race (e.g., "Elf", "Dwarf")

    Returns:
        RacialTraits object or None if not found
    """
    # Try fallback data first for now (since RAG data has quality issues)
    if race_name in FALLBACK_RACIAL_DATA:
        fallback = FALLBACK_RACIAL_DATA[race_name]
        return RacialTraits(
            race_name=race_name,
            ability_increases=fallback["ability_increases"],
            darkvision=fallback["darkvision"],
            speed=fallback["speed"],
            size=fallback["size"],
            languages=fallback["languages"],
            special_traits=fallback["traits"],
            raw_text=f"Fallback data for {race_name} (RAG data quality issues)"
        )

    # Fallback if race not found
    print(f"Warning: No racial data found for {race_name}, using generic Medium humanoid")
    return RacialTraits(
        race_name=race_name,
        ability_increases={},
        darkvision=0,
        speed=30,
        size="Medium",
        languages=["Common"],
        special_traits=[],
        raw_text=f"Generic data for {race_name}"
    )


def get_racial_bonus_summary(traits: RacialTraits) -> str:
    """
    Get a formatted summary of racial bonuses.

    Args:
        traits: RacialTraits object

    Returns:
        Formatted string summary
    """
    lines = [f"**{traits.race_name} Racial Traits:**\n"]

    # Ability score increases
    if traits.ability_increases:
        increases_str = ", ".join(
            f"{ability.capitalize()} +{bonus}"
            for ability, bonus in sorted(traits.ability_increases.items())
        )
        lines.append(f"• **Ability Scores:** {increases_str}")

    # Speed
    lines.append(f"• **Speed:** {traits.speed} feet")

    # Size
    lines.append(f"• **Size:** {traits.size}")

    # Darkvision
    if traits.darkvision > 0:
        lines.append(f"• **Darkvision:** {traits.darkvision} feet")

    # Languages
    if traits.languages:
        langs_str = ", ".join(traits.languages)
        lines.append(f"• **Languages:** {langs_str}")

    # Special traits
    if traits.special_traits:
        lines.append(f"• **Special Traits:** {len(traits.special_traits)} racial features")

    return "\n".join(lines)


# Quick test/example
if __name__ == "__main__":
    from core.chroma_manager import ChromaDBManager

    db = ChromaDBManager()

    # Test with a few races
    for race in ["Elf", "Dwarf", "Halfling", "Dragonborn"]:
        print(f"\n{'='*60}")
        print(f"Loading traits for {race}...")
        print('='*60)

        traits = load_racial_traits(db, race)
        if traits:
            print(get_racial_bonus_summary(traits))
            print(f"\nAbility increases: {traits.ability_increases}")
        else:
            print(f"Could not load traits for {race}")
