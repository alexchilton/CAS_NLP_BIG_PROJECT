"""
Character loading, creation, and management handlers.
"""

import json
import random
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import asdict

import gradio as gr

from dnd_rag_system.systems.character_creator import Character
from dnd_rag_system.systems.game_state import CharacterState
from dnd_rag_system.constants import CharacterClasses
from dnd_rag_system.systems.game_state import initialize_spell_slots_from_class
from dnd_rag_system.systems.racial_bonuses import load_racial_traits, get_racial_bonus_summary
from dnd_rag_system.systems.rag_character_enhancer import enhance_character_with_rag


def load_character_from_json(filepath: Path) -> Optional[Character]:
    """Load character from JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return Character(**data)
    except Exception as e:
        print(f"Error loading character from {filepath}: {e}")
        return None


def save_character_to_json(character: Character, filepath: Path) -> str:
    """Save character to JSON file."""
    try:
        with open(filepath, 'w') as f:
            json.dump(asdict(character), f, indent=2)
        return str(filepath)
    except Exception as e:
        return f"Error saving character: {e}"


def get_available_characters(characters_dir: Path) -> list:
    """Get list of available character files."""
    characters = []

    # Load pre-made characters
    thorin_path = characters_dir / "thorin_stormshield.json"
    elara_path = characters_dir / "elara_moonwhisper.json"

    if thorin_path.exists():
        characters.append("Thorin Stormshield (Dwarf Fighter)")
    if elara_path.exists():
        characters.append("Elara Moonwhisper (Elf Wizard)")

    # Load custom characters
    for json_file in characters_dir.glob("*.json"):
        if json_file.name not in ["thorin_stormshield.json", "elara_moonwhisper.json"]:
            char = load_character_from_json(json_file)
            if char:
                characters.append(f"{char.name} ({char.race} {char.character_class})")

    return characters


def delete_character(character_choice: str, characters_dir: Path) -> Tuple[str, gr.update]:
    """
    Delete a character file.

    Args:
        character_choice: Character selection string
        characters_dir: Directory containing character files

    Returns:
        Tuple of (status message, updated dropdown)
    """
    if not character_choice:
        return "⚠️ No character selected", gr.update()

    # Prevent deletion of pre-made characters
    if "Thorin" in character_choice or "Elara" in character_choice:
        return "❌ Cannot delete pre-made characters (Thorin, Elara)", gr.update()

    # Map character choice to file
    try:
        name = character_choice.split("(")[0].strip()
        filepath = characters_dir / f"{name.lower().replace(' ', '_')}.json"

        if filepath.exists():
            filepath.unlink()  # Delete the file

            # Update character list
            new_choices = get_available_characters(characters_dir)
            new_value = new_choices[0] if new_choices else None

            return (
                f"✅ Character '{name}' deleted successfully",
                gr.update(choices=new_choices, value=new_value)
            )
        else:
            return f"❌ Character file not found: {filepath}", gr.update()

    except Exception as e:
        return f"❌ Error deleting character: {e}", gr.update()


def load_character_with_location(
    character_choice: str,
    characters_dir: Path,
    starting_locations: list,
    combat_locations: list,
    gm,
    location_name: Optional[str] = None
) -> Tuple[str, str, str, Character, CharacterState]:
    """
    Load character and set specific starting location (for testing).

    Args:
        character_choice: Character selection string
        characters_dir: Directory containing character files
        starting_locations: List of (location_name, location_desc) tuples
        combat_locations: List of combat-specific locations
        gm: GameMaster instance
        location_name: Optional location name

    Returns:
        Tuple of (location_name, location_desc, character_name, character, character_state)
    """
    import os

    # Map character choice to file
    if "Thorin" in character_choice:
        filepath = characters_dir / "thorin_stormshield.json"
    elif "Elara" in character_choice:
        filepath = characters_dir / "elara_moonwhisper.json"
    else:
        name = character_choice.split("(")[0].strip()
        filepath = characters_dir / f"{name.lower().replace(' ', '_')}.json"

    current_character = load_character_from_json(filepath)

    if not current_character:
        raise ValueError(f"Could not load character from {filepath}")

    # Create CharacterState
    char = current_character
    # Calculate starting XP: (level - 1) * 1000
    # Level 1 = 0 XP, Level 2 = 1000 XP, Level 10 = 9000 XP, etc.
    starting_xp = (char.level - 1) * 1000
    char_state = CharacterState(
        character_name=char.name,
        max_hp=char.hit_points,
        current_hp=char.hit_points,
        level=char.level,
        experience_points=starting_xp,
        inventory={item: 1 for item in char.equipment},
        gold=getattr(char, 'gold', 50)
    )

    # Add race and class
    char_state.race = char.race
    char_state.character_class = char.character_class

    # Set spellcasting_class for spellcasters
    SPELLCASTING_CLASSES = [
        CharacterClasses.WIZARD, CharacterClasses.SORCERER,
        CharacterClasses.WARLOCK, CharacterClasses.CLERIC,
        CharacterClasses.DRUID, CharacterClasses.BARD,
        CharacterClasses.PALADIN, CharacterClasses.RANGER
    ]
    if char.character_class in SPELLCASTING_CLASSES:
        char_state.spellcasting_class = char.character_class

        # Initialize spell slots
        try:
            char_state.spell_slots = initialize_spell_slots_from_class(char.character_class, char.level)
            print(f"✨ Initialized spell slots for {char.name} ({char.character_class} level {char.level})")
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize spell slots for {char.name}: {e}")

    # Add spells to character state
    if char.spells:
        char_state.spells = char.spells
        char_state.known_spells = list(char.spells)

        # AUTO-PREPARE SPELLS
        if char_state.spellcasting_class:
            if char_state.is_prepared_caster():
                ability_score = getattr(char, char_state.spellcasting_ability.lower(), 10)
                ability_mod = char.get_ability_modifier(ability_score)
                max_prepared = char_state.get_max_prepared_spells(ability_mod)

                combat_keywords = ['missile', 'bolt', 'ray', 'arrow', 'strike', 'blast', 'fire', 'ice', 'lightning']
                utility_keywords = ['shield', 'armor', 'detect', 'identify', 'light', 'mage hand']

                sorted_spells = sorted(char.spells, key=lambda s: (
                    0 if any(kw in s.lower() for kw in combat_keywords) else
                    1 if any(kw in s.lower() for kw in utility_keywords) else 2,
                    s.lower()
                ))

                char_state.prepared_spells = sorted_spells[:max_prepared]
                print(f"🎯 Auto-prepared {len(char_state.prepared_spells)} spells for {char.name}")
            else:
                char_state.prepared_spells = list(char.spells)

        print(f"📖 Loaded {len(char.spells)} spells for {char.name}")

    # Load into game session
    gm.session.base_character_stats[char.name] = char
    gm.session.character_state = char_state
    gm.session.npcs_present = []

    # Set starting location
    env_location = os.getenv("TEST_START_LOCATION")
    env_location_desc = os.getenv("TEST_LOCATION_DESC")

    if env_location:
        location_name = env_location
        print(f"🧪 Test mode: Starting at {location_name}")

    if location_name:
        all_locations = starting_locations + combat_locations
        found_location = None
        for loc_name, loc_desc in all_locations:
            if loc_name.lower() == location_name.lower() or location_name.lower() in loc_name.lower():
                found_location = (loc_name, loc_desc)
                break

        if found_location:
            location_name, location_desc = found_location
        else:
            if env_location_desc:
                location_desc = env_location_desc
            else:
                location_desc = f"You find yourself at {location_name}."
    else:
        location_name, location_desc = random.choice(starting_locations)

    gm.set_location(location_name, location_desc)

    # NPC spawning logic
    env_npcs = os.getenv("TEST_NPCS")
    if env_npcs:
        test_npcs = [npc.strip() for npc in env_npcs.split(',')]
        for npc in test_npcs:
            if npc and npc not in gm.session.npcs_present:
                gm.session.npcs_present.append(npc)
        print(f"🧪 Added NPCs from TEST_NPCS: {test_npcs}")
    else:
        friendly_location_npcs = {
            "The Prancing Pony Inn": ["Innkeeper Butterbur", "Traveling Merchant"],
            "The Market Square": ["Merchant", "Blacksmith", "Potion Seller"],
            "The Town Gates": ["Town Guard", "General Store Shopkeeper"],
        }

        for loc_key, npcs in friendly_location_npcs.items():
            if loc_key.lower() in location_name.lower() or location_name.lower() in loc_key.lower():
                for npc in npcs:
                    if npc not in gm.session.npcs_present:
                        gm.session.npcs_present.append(npc)
                print(f"🏘️ Added friendly NPCs to {location_name}: {npcs}")
                break

    # Add items to location
    env_items = os.getenv("TEST_ITEMS")
    if env_items:
        if ':' in env_items:
            container, items_str = env_items.split(':', 1)
            items = [item.strip() for item in items_str.split(',')]

            if "hidden chest" in container.lower():
                gm.session.scene_description += f"\n\n🎁 There appears to be a {container} here."
            else:
                gm.session.scene_description += f"\n\n{container} can be found here."

            if not hasattr(gm.session, 'location_items'):
                gm.session.location_items = {}
            gm.session.location_items[container] = items
            print(f"🧪 Added {container} with items: {items}")
        else:
            items = [item.strip() for item in env_items.split(',')]
            if not hasattr(gm.session, 'location_items'):
                gm.session.location_items = {}
            gm.session.location_items['ground'] = items
            print(f"🧪 Added items to location: {items}")

    return location_name, location_desc, char.name, current_character, char_state


def load_character(
    character_choice: str,
    characters_dir: Path,
    starting_locations: list,
    combat_locations: list,
    gm,
    db,
    format_character_sheet_func
) -> Tuple[str, str, str, str, list, Optional[str]]:
    """
    Load selected character and update context (Gradio UI wrapper).

    Returns:
        Tuple of (char_col1, char_col2, char_col3, msg_input_value, chat_history, char_image)
    """
    try:
        location_name, location_desc, char_name, char, char_state = load_character_with_location(
            character_choice, characters_dir, starting_locations, combat_locations, gm
        )
    except ValueError as e:
        return f"Error loading character: {e}", "", "", "", [], None

    if not char:
        return "Error loading character", "", "", "", [], None

    # Set GM context
    mods = char.get_modifiers()
    context = f"""The player is {char.name}, a level {char.level} {char.race} {char.character_class}.

PLAYER CHARACTER STATS:
- HP: {char_state.current_hp}/{char_state.max_hp}  |  AC: {char.armor_class}  |  Prof Bonus: +{char.proficiency_bonus}
- STR: {char.strength} ({mods['strength']:+d})  |  DEX: {char.dexterity} ({mods['dexterity']:+d})  |  CON: {char.constitution} ({mods['constitution']:+d})
- INT: {char.intelligence} ({mods['intelligence']:+d})  |  WIS: {char.wisdom} ({mods['wisdom']:+d})  |  CHA: {char.charisma} ({mods['charisma']:+d})

EQUIPMENT: {', '.join(char.equipment[:5])}
INVENTORY: {', '.join([f"{item} ({qty})" for item, qty in char_state.inventory.items() if item not in char.equipment][:5]) or "Empty"}
"""

    if char.spells:
        context += f"\nSPELLS: {', '.join(char.spells[:5])}"

    gm.set_context(context)

    # Get character image if exists
    char_image = None
    if char.image_path and Path(char.image_path).exists():
        char_image = char.image_path

    # Create welcome message
    welcome_message = f"""**Welcome, {char.name}!**

You find yourself in **{location_name}**.

{location_desc}

You have **{char_state.gold} gold pieces** in your purse."""

    if gm.session.npcs_present:
        npc_list = ", ".join(gm.session.npcs_present)
        welcome_message += f"\n\n⚠️ **You see:** {npc_list}!"

    welcome_message += """\n\nWhat would you like to do?

*Type `/help` to see available commands, or describe your action!*"""

    # Gradio Chatbot format: list of tuples [(user_msg, bot_msg)]
    initial_chat = [(None, welcome_message)]
    col1, col2, col3 = format_character_sheet_func(char, char_state, db)
    return col1, col2, col3, "", initial_chat, char_image


def load_character_with_debug(
    character_choice: str,
    scenario_choice: Optional[str],
    characters_dir: Path,
    starting_locations: list,
    combat_locations: list,
    debug_scenarios: list,
    gm,
    db,
    format_character_sheet_func,
    load_character_func
) -> Tuple[str, str, str, str, list, Optional[str]]:
    """
    Load character with optional debug scenario.

    Returns:
        Tuple of (char_col1, char_col2, char_col3, msg_input_value, chat_history, char_image)
    """
    if not scenario_choice or scenario_choice == "":
        return load_character_func(character_choice)

    # Find the scenario
    scenario = None
    for s in debug_scenarios:
        if s[0] == scenario_choice:
            scenario = s
            break

    if not scenario:
        return ("", "", "", "Invalid scenario", [], None)

    scenario_name, location_name, npcs, items = scenario

    # Clear old session state
    gm.session.npcs_present = []
    _, _ = gm.combat_manager.end_combat()
    gm.message_history = []

    # Load character with specific location
    location_name_result, location_desc, char_name, char, char_state = load_character_with_location(
        character_choice, characters_dir, starting_locations, combat_locations, gm, location_name
    )

    # Add NPCs for this scenario
    gm.session.npcs_present = npcs.copy()

    # Add items to location
    if items:
        current_loc = gm.session.get_current_location_obj()
        if current_loc:
            for item in items:
                current_loc.add_item(item)
        else:
            gm.session.location_items = items.copy()

    # Set GM context
    mods = char.get_modifiers()
    context = f"""The player is {char.name}, a level {char.level} {char.race} {char.character_class}.

PLAYER CHARACTER STATS:
- HP: {char_state.current_hp}/{char_state.max_hp}  |  AC: {char.armor_class}  |  Prof Bonus: +{char.proficiency_bonus}
- STR: {char.strength} ({mods['strength']:+d})  |  DEX: {char.dexterity} ({mods['dexterity']:+d})  |  CON: {char.constitution} ({mods['constitution']:+d})
- INT: {char.intelligence} ({mods['intelligence']:+d})  |  WIS: {char.wisdom} ({mods['wisdom']:+d})  |  CHA: {char.charisma} ({mods['charisma']:+d})

EQUIPMENT: {', '.join(char.equipment[:5])}
INVENTORY: {', '.join([f"{item} ({qty})" for item, qty in char_state.inventory.items() if item not in char.equipment][:5]) or "Empty"}
"""

    if char.spells:
        context += f"\nSPELLS: {', '.join(char.spells[:5])}"

    gm.set_context(context)

    # Create welcome message
    location = gm.session.current_location
    desc = gm.session.scene_description

    npcs_text = f"\n⚠️  **You see:** {', '.join(npcs)}!" if npcs else ""
    if items:
        if len(items) == 1:
            items_text = f"\n🎒 **You notice:** A {items[0]} is here."
        else:
            items_list = ', '.join(items[:-1]) + f" and {items[-1]}"
            items_text = f"\n🎒 **You notice:** {items_list} are here."
    else:
        items_text = ""

    welcome_message = f"""🧪 **DEBUG SCENARIO: {scenario_name}**

Welcome, {char.name}!
You find yourself in **{location}**.
{desc}
{npcs_text}{items_text}

You have **{char_state.gold} gold pieces** in your purse.

What would you like to do?
*Type `/help` to see available commands, or describe your action!*"""

    # Get character image
    char_image = None
    if char.image_path and Path(char.image_path).exists():
        char_image = str(char.image_path)

    # Gradio Chatbot format: list of tuples [(user_msg, bot_msg)]
    initial_chat = [(None, welcome_message)]
    col1, col2, col3 = format_character_sheet_func(char, char_state, db)
    return col1, col2, col3, "", initial_chat, char_image


def create_character(
    name: str, race: str, char_class: str, level: int,
    alignment: str, background: str,
    str_val: int, dex_val: int, con_val: int,
    int_val: int, wis_val: int, cha_val: int,
    characters_dir: Path,
    db
) -> Tuple[str, gr.update]:
    """Create a new character with given parameters."""
    if not name:
        return "❌ Please enter a character name", gr.update()

    # Store original base scores
    base_scores = {
        'strength': str_val, 'dexterity': dex_val, 'constitution': con_val,
        'intelligence': int_val, 'wisdom': wis_val, 'charisma': cha_val
    }

    # Load racial traits and apply bonuses
    racial_traits = load_racial_traits(None, race)
    racial_bonuses_applied = ""
    racial_bonus_details = {}

    if racial_traits:
        for ability, bonus in racial_traits.ability_increases.items():
            racial_bonus_details[ability] = bonus
            if ability == "strength":
                str_val += bonus
            elif ability == "dexterity":
                dex_val += bonus
            elif ability == "constitution":
                con_val += bonus
            elif ability == "intelligence":
                int_val += bonus
            elif ability == "wisdom":
                wis_val += bonus
            elif ability == "charisma":
                cha_val += bonus

        racial_bonuses_applied = get_racial_bonus_summary(racial_traits)

    # Create character
    character = Character(
        name=name, race=race, character_class=char_class, level=int(level),
        strength=str_val, dexterity=dex_val, constitution=con_val,
        intelligence=int_val, wisdom=wis_val, charisma=cha_val,
        background=background, alignment=alignment, gold=100
    )

    # Apply RAG-enhanced class features
    try:
        enhance_character_with_rag(character)
        hit_die = character.hit_points // (1 + character.get_ability_modifier(character.constitution))
        rag_enhanced = True
    except Exception as e:
        print(f"RAG enhancement failed: {e}")
        hit_die_map = {
            "Wizard": 6, "Sorcerer": 6,
            "Rogue": 8, "Bard": 8, "Cleric": 8, "Druid": 8, "Monk": 8, "Warlock": 8,
            "Fighter": 10, "Paladin": 10, "Ranger": 10,
            "Barbarian": 12
        }
        hit_die = hit_die_map.get(char_class, 8)
        character.hit_points = character.calculate_hit_points(hit_die)
        rag_enhanced = False

    dex_mod = character.get_ability_modifier(dex_val)
    character.armor_class = 10 + dex_mod

    # Save character
    filename = f"{name.lower().replace(' ', '_')}.json"
    filepath = characters_dir / filename
    save_result = save_character_to_json(character, filepath)

    # Update character list
    new_choices = get_available_characters(characters_dir)

    # Format success message
    success_msg = f"""✅ **Character Created Successfully!**

**{name}** - {race} {char_class}, Level {level}
📁 Saved to: `{save_result}`

---

### 📊 Ability Scores (with racial bonuses)
"""

    for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
        base = base_scores[ability]
        final = getattr(character, ability)
        bonus = racial_bonus_details.get(ability, 0)

        if bonus > 0:
            success_msg += f"- **{ability.upper()}**: {base} + {bonus} = **{final}** ({character.get_ability_modifier(final):+d})\n"
        else:
            success_msg += f"- **{ability.upper()}**: {final} ({character.get_ability_modifier(final):+d})\n"

    success_msg += f"\n### 🎲 Class Features\n"
    success_msg += f"- **Hit Die**: 1d{hit_die} (HP: {character.hit_points})\n"
    success_msg += f"- **Armor Class**: {character.armor_class}\n"
    success_msg += f"- **Proficiency Bonus**: +{character.proficiency_bonus}\n"

    if character.class_features:
        success_msg += f"\n**Starting Features**: {', '.join(character.class_features[:3])}\n"

    if racial_bonuses_applied:
        success_msg += f"\n### 🧬 Racial Traits\n{racial_bonuses_applied}\n"

    if rag_enhanced:
        success_msg += f"\n✨ *Enhanced with D&D 5e SRD data*"

    return (
        success_msg,
        gr.update(choices=new_choices, value=f"{name} ({race} {char_class})")
    )
