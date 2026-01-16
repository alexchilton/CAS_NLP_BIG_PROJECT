"""
Party management event handlers.
"""

import random
from typing import Tuple, List
from pathlib import Path
import gradio as gr

from dnd_rag_system.systems.game_state import CharacterState, PartyState
from dnd_rag_system.constants import CharacterClasses
from .character_handlers import load_character_from_json
from web.formatters.party_formatter import format_party_sheet


# Constants for party handlers
STARTING_LOCATIONS = [
    # Peaceful locations (for shopping/rest)
    ("The Prancing Pony Inn", "A cozy tavern bustling with travelers and merchants. The smell of roasted meat and ale fills the air. A shopkeeper behind the bar sells basic supplies."),
    ("The Market Square", "A busy marketplace with stalls selling adventuring gear, potions, and supplies. Merchants call out their wares. Perfect for shopping before an adventure!"),
    ("The Town Gates", "The entrance to town, where the road stretches out toward adventure. Guards keep watch. A general store sits just inside the gates."),
    # Combat-ready locations (for immediate action!)
    ("Goblin Cave Entrance", "You stand at the mouth of a dark cave. The stench of unwashed goblins wafts out from the darkness. Crude wooden stakes mark goblin territory. You hear chittering and the clang of crude weapons echoing from within."),
    ("Ancient Ruins", "Crumbling stone pillars rise from overgrown weeds. This was once a great temple, now fallen to ruin. Skeletons and undead are known to haunt these grounds, guarding forgotten treasures."),
    ("Dark Forest Clearing", "You emerge into a small clearing surrounded by ancient, gnarled trees. The forest floor is littered with bones. Fresh wolf tracks circle the area. This is dangerous territory."),
]

CHARACTERS_DIR = Path(__file__).parent.parent.parent / "characters"


def load_party_mode(party_characters, party, gm, gameplay_mode_setter, conversation_history_setter) -> Tuple[str, str, str, gr.update, list]:
    """
    Load party mode and set GM context for party-based gameplay.

    Args:
        party_characters: Dict of {char_name: Character}
        party: PartyState object
        gm: GameMaster instance
        gameplay_mode_setter: Function to set gameplay mode
        conversation_history_setter: Function to set conversation history

    Returns:
        Tuple of (char_col1, char_col2, char_col3, msg_input_update, chat_history)
    """
    conversation_history_setter([])
    gameplay_mode_setter("party")

    if not party_characters:
        return (
            "⚠️ No party members! Please add characters in the Party Management tab first.",
            "",  # char_col2
            "",  # char_col3
            gr.update(interactive=True),  # Keep msg_input interactive
            []
        )

    # Set random starting location for the party
    location_name, location_desc = random.choice(STARTING_LOCATIONS)
    gm.set_location(location_name, location_desc)

    # Build party context for GM
    party_info = []
    for char_name, char in party_characters.items():
        mods = char.get_modifiers()

        # Get dynamic HP from party state
        char_state = party.get_character(char_name)
        if char_state:
            hp_display = f"{char_state.current_hp}/{char_state.max_hp}"
        else:
            hp_display = f"{char.hit_points}/{char.hit_points}"

        party_info.append(f"""
**{char.name}** - {char.race} {char.character_class}, Level {char.level}
- HP: {hp_display}  |  AC: {char.armor_class}  |  Prof Bonus: +{char.proficiency_bonus}
- STR: {char.strength} ({mods['strength']:+d})  |  DEX: {char.dexterity} ({mods['dexterity']:+d})  |  CON: {char.constitution} ({mods['constitution']:+d})
- INT: {char.intelligence} ({mods['intelligence']:+d})  |  WIS: {char.wisdom} ({mods['wisdom']:+d})  |  CHA: {char.charisma} ({mods['charisma']:+d})
- Equipment: {', '.join(char.equipment[:3])}""")

    context = f"""The party consists of {len(party_characters)} adventurers:

{chr(10).join(party_info)}

Party Gold: {party.gold} GP"""

    gm.set_context(context)

    # Create welcome message for party mode
    party_names = ", ".join(party_characters.keys())
    welcome_message = f"""**🎭 Welcome, Adventurers!**

Your party of {len(party_characters)} finds themselves in **{location_name}**.

**Party Members:** {party_names}

{location_desc}

The party has **{party.gold} gold pieces** in the shared purse.

What would you like your party to do?

*Type `/help` to see available commands, or describe your party's action!*"""

    # Return party summary (in col1 only), interactive input, and welcome message
    initial_chat = [{"role": "assistant", "content": welcome_message}]
    return (
        format_party_sheet(party_characters, party),  # char_col1
        "",  # char_col2 (empty in party mode)
        "",  # char_col3 (empty in party mode)
        gr.update(interactive=True, value=""),  # Explicitly keep it interactive
        initial_chat  # Add welcome message to chat
    )


def add_to_party(character_choices: List[str], party_characters, party) -> Tuple[str, dict, dict]:
    """
    Add selected characters to the party.

    Args:
        character_choices: List of character choice strings
        party_characters: Dict of {char_name: Character}
        party: PartyState object

    Returns:
        Tuple of (status_message, updated_party_characters, updated_party)
    """
    if not character_choices:
        return "⚠️ No characters selected", party_characters, party

    added_count = 0
    for choice in character_choices:
        # Map character choice to file
        if "Thorin" in choice:
            filepath = CHARACTERS_DIR / "thorin_stormshield.json"
        elif "Elara" in choice:
            filepath = CHARACTERS_DIR / "elara_moonwhisper.json"
        else:
            name = choice.split("(")[0].strip()
            filepath = CHARACTERS_DIR / f"{name.lower().replace(' ', '_')}.json"

        char = load_character_from_json(filepath)
        if char and char.name not in party_characters:
            # Store Character for display
            party_characters[char.name] = char

            # Create CharacterState for game mechanics
            char_state = CharacterState(
                character_name=char.name,
                max_hp=char.hit_points,
                level=char.level
            )

            # Set spellcasting_class for spellcasters
            SPELLCASTING_CLASSES = [
                CharacterClasses.WIZARD,
                CharacterClasses.SORCERER,
                CharacterClasses.WARLOCK,
                CharacterClasses.CLERIC,
                CharacterClasses.DRUID,
                CharacterClasses.BARD,
                CharacterClasses.PALADIN,
                CharacterClasses.RANGER
            ]
            if char.character_class in SPELLCASTING_CLASSES:
                char_state.spellcasting_class = char.character_class

            party.add_character(char_state)
            added_count += 1

    party_summary = get_party_summary(party_characters, party)
    return f"✅ Added {added_count} character(s) to party!\n\n{party_summary}", party_characters, party


def remove_from_party(character_name: str, party_characters, party) -> Tuple[str, dict, dict]:
    """
    Remove a character from the party.

    Args:
        character_name: Name of character to remove
        party_characters: Dict of {char_name: Character}
        party: PartyState object

    Returns:
        Tuple of (status_message, updated_party_characters, updated_party)
    """
    if character_name in party_characters:
        del party_characters[character_name]
        party.remove_character(character_name)
        return f"✅ Removed {character_name} from party\n\n{get_party_summary(party_characters, party)}", party_characters, party
    else:
        return f"⚠️ {character_name} is not in the party", party_characters, party


def get_party_summary(party_characters, party) -> str:
    """
    Get formatted party summary.

    Args:
        party_characters: Dict of {char_name: Character}
        party: PartyState object

    Returns:
        Markdown string with party summary
    """
    if not party_characters:
        return "**No characters in party**\n\nAdd characters from the dropdown above."

    summary = f"# 🎭 {party.party_name}\n\n"
    summary += f"**Party Size:** {len(party_characters)} adventurer(s)\n"
    summary += f"**Party Gold:** {party.gold} GP\n\n"
    summary += "---\n\n"

    for char_name, char in party_characters.items():
        char_state = party.get_character(char_name)
        status = "✅ Ready" if char_state and char_state.is_alive() else "❌ Dead"

        # Get dynamic HP
        if char_state:
            hp_display = f"{char_state.current_hp}/{char_state.max_hp}"
        else:
            hp_display = str(char.hit_points)

        summary += f"### {char.name} ({status})\n"
        summary += f"**{char.race} {char.character_class}, Level {char.level}**\n"
        summary += f"- HP: {hp_display} | AC: {char.armor_class}\n"
        summary += f"- Background: {char.background}\n\n"

    if party.shared_inventory:
        summary += "### 🎒 Shared Inventory\n"
        for item, qty in party.shared_inventory.items():
            summary += f"- {item} x{qty}\n"

    return summary
