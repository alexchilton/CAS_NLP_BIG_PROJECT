"""
Party sheet formatting functions.
"""


def format_party_sheet(party_characters, party_state) -> str:
    """
    Format party sheet for display in character panel.

    Args:
        party_characters: Dict of {char_name: Character}
        party_state: PartyState object with dynamic state

    Returns:
        Markdown string with party summary
    """
    if not party_characters:
        return "**No Party Loaded**\n\nAdd characters in the Party Management tab."

    sheet = f"# 🎭 Party Mode\n\n"
    sheet += f"**{party_state.party_name}**\n"
    sheet += f"**Party Size:** {len(party_characters)} adventurer(s)\n"
    sheet += f"**Party Gold:** {party_state.gold} GP\n\n"
    sheet += "---\n\n"

    for char_name, char in party_characters.items():
        mods = char.get_modifiers()

        # Get dynamic HP from party state
        char_state = party_state.get_character(char_name)
        if char_state:
            hp_display = f"{char_state.current_hp}/{char_state.max_hp}"
        else:
            hp_display = str(char.hit_points)

        sheet += f"### {char.name}\n"
        sheet += f"*{char.race} {char.character_class}, Level {char.level}*\n"
        sheet += f"- HP: {hp_display} | AC: {char.armor_class}\n"
        sheet += f"- STR {char.strength} ({mods['strength']:+d}) | DEX {char.dexterity} ({mods['dexterity']:+d}) | CON {char.constitution} ({mods['constitution']:+d})\n"
        sheet += f"- INT {char.intelligence} ({mods['intelligence']:+d}) | WIS {char.wisdom} ({mods['wisdom']:+d}) | CHA {char.charisma} ({mods['charisma']:+d})\n\n"

    return sheet


def get_all_character_sheets(party_characters, party_state) -> str:
    """
    Get all character sheets formatted for party mode.

    Args:
        party_characters: Dict of {char_name: Character}
        party_state: PartyState object

    Returns:
        Markdown string with all character sheets
    """
    from .character_formatter import format_character_sheet_for_char

    if not party_characters:
        return "No characters in party"

    sheets = []
    for char_name, char in party_characters.items():
        sheet = format_character_sheet_for_char(char, party_state)
        sheets.append(sheet)
        sheets.append("\n---\n\n")

    return "\n".join(sheets)
