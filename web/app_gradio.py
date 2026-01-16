#!/usr/bin/env python3
"""
D&D Character-Aware Game - Gradio Web Interface (Modular)

Streamlined web UI using extracted modular components and handlers.
"""

import os
# Suppress tokenizer warning
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import gradio as gr
import random
from pathlib import Path
from typing import Optional, Tuple

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Core DND RAG system imports
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.character_creator import Character
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.systems.game_state import CharacterState, PartyState
from dnd_rag_system.config import settings

# Component imports
from web.components.play_tab import create_play_tab
from web.components.create_tab import create_character_tab
from web.components.party_tab import create_party_tab

# Handler imports
from web.handlers.character_handlers import (
    get_available_characters,
    delete_character,
    load_character,
    load_character_with_debug,
    create_character as create_character_handler
)
from web.handlers.combat_handlers import (
    get_initiative_tracker,
    handle_next_turn,
    handle_end_combat
)
from web.handlers.chat_handlers import (
    handle_rag_lookup,
    chat,
    clear_history,
    roll_random_stats
)
from web.handlers.party_handlers import (
    load_party_mode,
    add_to_party,
    remove_from_party,
    get_party_summary
)

# Formatter imports
from web.formatters.character_formatter import format_character_sheet
from web.formatters.party_formatter import format_party_sheet, get_all_character_sheets

# ============================================================================
# INITIALIZATION
# ============================================================================

print("🎲 Initializing D&D RAG System...")
db = ChromaDBManager()
gm = GameMaster(db)

# Paths
CHARACTERS_DIR = Path(__file__).parent.parent / "characters"
CHARACTERS_DIR.mkdir(exist_ok=True)

# Global state
current_character = None
conversation_history = []
party = PartyState(party_name="Adventuring Party")
party_characters = {}  # {char_name: Character} for display
gameplay_mode = "character"  # "character" or "party"

# ============================================================================
# CONSTANTS
# ============================================================================

# Starting locations for new games - MIX of peaceful and combat-ready locations!
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

# Combat-appropriate locations where monsters would naturally appear
COMBAT_LOCATIONS = [
    ("Goblin Cave Entrance", "You stand at the mouth of a dark cave. The stench of unwashed goblins wafts out from the darkness. Crude wooden stakes mark goblin territory. You hear chittering and the clang of crude weapons echoing from within."),
    ("Ancient Ruins", "Crumbling stone pillars rise from overgrown weeds. This was once a great temple, now fallen to ruin. Skeletons and undead are known to haunt these grounds, guarding forgotten treasures."),
    ("Dark Forest Clearing", "You emerge into a small clearing surrounded by ancient, gnarled trees. The forest floor is littered with bones. Fresh wolf tracks circle the area. This is dangerous territory."),
    ("Abandoned Mine Shaft", "The entrance to an old mining tunnel, long since abandoned. Support beams creak ominously. Miners' tools lie scattered about. Something moves in the shadows - perhaps giant rats, or worse."),
    ("Rocky Mountain Pass", "A narrow path winds between towering cliffs. Loose rocks make footing treacherous. Ogres and trolls are known to ambush travelers here, and you can see crude cave entrances dotting the cliff faces."),
    ("Sunken Graveyard", "An old cemetery, half-swallowed by swamp. Weathered tombstones lean at odd angles. The ground shifts underfoot. On nights like this, the dead sometimes rise from their graves."),
    ("Dragon's Lair Approach", "You stand before a massive cavern carved into the mountainside. Scorch marks blacken the rocks. A pile of charred bones lies near the entrance. The air shimmers with heat, and you hear the deep, rhythmic breathing of something massive within."),
]

# DEBUG TEST SCENARIOS - For manual testing combat/features
# Format: (scenario_name, location_name, npcs_to_spawn, items_to_add)
DEBUG_SCENARIOS = [
    ("Random Start", None, [], []),  # Default - random location
    ("Goblin Fight", "Goblin Cave Entrance", ["Goblin"], []),
    ("Goblin with Treasure", "Goblin Cave Entrance", ["Goblin"], ["Hidden Chest"]),
    ("Goblin Wolf Rider", "Forest Ambush Site", ["Goblin", "Wolf"], ["Rope", "Torch"]),  # Multi-enemy test
    ("Wolf Pack", "Dark Forest Clearing", ["Wolf", "Wolf"], []),
    ("Skeleton Guardian", "Ancient Ruins", ["Skeleton"], ["Ancient Sword"]),
    ("Dragon Encounter", "Dragon's Lair Approach", ["Young Red Dragon"], ["Dragon Hoard"]),
    ("Safe Inn", "The Prancing Pony Inn", ["Innkeeper Butterbur"], ["Healing Potion"]),
    ("Shopping District", "The Market Square", ["Merchant", "Blacksmith"], []),
]

# ============================================================================
# HELPER FUNCTIONS & WRAPPERS
# ============================================================================

def get_current_sheet() -> tuple:
    """Get character sheet based on current mode."""
    global current_character, party_characters, party, gameplay_mode

    if gameplay_mode == "party":
        return (format_party_sheet(party_characters, party), "", "")
    else:
        if current_character and gm.session.character_state:
            return format_character_sheet(current_character, gm.session.character_state, db)
        else:
            return ("No character loaded", "", "")


def get_initiative_tracker_wrapper() -> Tuple[str, gr.update]:
    """Wrapper for get_initiative_tracker handler."""
    global gameplay_mode, party_characters, party
    return get_initiative_tracker(gm, gameplay_mode, party_characters, party)


def get_available_characters_wrapper() -> list:
    """Wrapper for get_available_characters handler."""
    return get_available_characters(CHARACTERS_DIR)


def get_party_summary_wrapper() -> str:
    """Wrapper for get_party_summary handler."""
    global party_characters, party
    return get_party_summary(party_characters, party)


def get_all_character_sheets_wrapper() -> str:
    """Wrapper for get_all_character_sheets handler."""
    global party_characters, party
    return get_all_character_sheets(party_characters, party)


# ============================================================================
# EVENT HANDLER WRAPPERS (for global state management)
# ============================================================================

def load_character_wrapper(character_choice: str) -> Tuple[str, str, str, str, list, Optional[str]]:
    """Wrapper for load_character handler with global state."""
    global current_character, conversation_history, gameplay_mode

    conversation_history = []
    gameplay_mode = "character"

    result = load_character(
        character_choice,
        CHARACTERS_DIR,
        STARTING_LOCATIONS,
        COMBAT_LOCATIONS,
        gm,
        db,
        format_character_sheet
    )

    # Update global current_character
    if gm.session.character_state:
        char_name = gm.session.character_state.character_name
        if char_name in gm.session.base_character_stats:
            current_character = gm.session.base_character_stats[char_name]

    return result


def load_character_with_debug_wrapper(character_choice: str, scenario_choice: Optional[str]) -> Tuple[str, str, str, str, list, Optional[str]]:
    """Wrapper for load_character_with_debug handler with global state."""
    global current_character, conversation_history, gameplay_mode

    conversation_history = []
    gameplay_mode = "character"

    result = load_character_with_debug(
        character_choice,
        scenario_choice,
        CHARACTERS_DIR,
        STARTING_LOCATIONS,
        COMBAT_LOCATIONS,
        DEBUG_SCENARIOS,
        gm,
        db,
        format_character_sheet,
        load_character_wrapper
    )

    # Update global current_character
    if gm.session.character_state:
        char_name = gm.session.character_state.character_name
        if char_name in gm.session.base_character_stats:
            current_character = gm.session.base_character_stats[char_name]

    return result


def load_character_with_location(character_choice: str, location_name: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Load character and set specific starting location (for testing).
    
    Args:
        character_choice: Character selection string
        location_name: Optional location name. If None, uses random.
    
    Returns:
        Tuple of (location_name, location_desc, character_name)
    """
    global current_character, conversation_history, gameplay_mode
    
    conversation_history = []
    gameplay_mode = "character"
    
    from web.handlers.character_handlers import load_character_with_location as handler_load_char_loc
    
    loc_name, loc_desc, char_name, character, char_state = handler_load_char_loc(
        character_choice,
        CHARACTERS_DIR,
        STARTING_LOCATIONS,
        COMBAT_LOCATIONS,
        gm,
        location_name
    )
    
    # Update global current_character
    if char_name in gm.session.base_character_stats:
        current_character = gm.session.base_character_stats[char_name]
    
    return loc_name, loc_desc, char_name


def delete_character_wrapper(character_choice: str) -> Tuple[str, gr.update]:
    """Wrapper for delete_character handler."""
    return delete_character(character_choice, CHARACTERS_DIR)


def handle_rag_lookup_wrapper(query: str) -> str:
    """Wrapper for handle_rag_lookup handler."""
    return handle_rag_lookup(query, gm, db)


def chat_wrapper(message: str, history: list) -> Tuple[list, str, gr.update, str, str, str]:
    """Wrapper for chat handler with global state."""
    global gameplay_mode, current_character, party_characters, conversation_history

    return chat(
        message,
        history,
        gameplay_mode,
        current_character,
        party_characters,
        conversation_history,
        gm,
        get_initiative_tracker_wrapper,
        get_current_sheet
    )


def clear_history_wrapper() -> list:
    """Wrapper for clear_history handler."""
    global conversation_history
    return clear_history(conversation_history)


def handle_next_turn_wrapper(history: list) -> Tuple[list, str, gr.update, str, str, str]:
    """Wrapper for handle_next_turn handler."""
    return handle_next_turn(history, gm, get_initiative_tracker_wrapper, get_current_sheet)


def handle_end_combat_wrapper(history: list) -> Tuple[list, str, gr.update, str, str, str]:
    """Wrapper for handle_end_combat handler."""
    return handle_end_combat(history, gm, get_initiative_tracker_wrapper, get_current_sheet)


def load_party_mode_wrapper() -> Tuple[str, str, str, gr.update, list]:
    """Wrapper for load_party_mode handler with global state."""
    global party_characters, party, gameplay_mode, conversation_history

    def set_gameplay_mode(mode: str):
        global gameplay_mode
        gameplay_mode = mode

    def set_conversation_history(history: list):
        global conversation_history
        conversation_history = history

    return load_party_mode(
        party_characters,
        party,
        gm,
        set_gameplay_mode,
        set_conversation_history
    )


def add_to_party_wrapper(character_choices: list) -> Tuple[str, dict, dict]:
    """Wrapper for add_to_party handler with global state."""
    global party_characters, party

    result, updated_party_chars, updated_party = add_to_party(
        character_choices,
        party_characters,
        party
    )

    # Update global state
    party_characters = updated_party_chars
    party = updated_party

    return result


def remove_from_party_wrapper(character_name: str) -> Tuple[str, dict, dict]:
    """Wrapper for remove_from_party handler with global state."""
    global party_characters, party

    result, updated_party_chars, updated_party = remove_from_party(
        character_name,
        party_characters,
        party
    )

    # Update global state
    party_characters = updated_party_chars
    party = updated_party

    return result


def create_character_wrapper(
    name: str, race: str, char_class: str, level: int,
    alignment: str, background: str,
    str_val: int, dex_val: int, con_val: int,
    int_val: int, wis_val: int, cha_val: int
) -> Tuple[str, gr.update, gr.update]:
    """Wrapper for create_character handler."""
    status_msg, char_dropdown_update = create_character_handler(
        name, race, char_class, level,
        alignment, background,
        str_val, dex_val, con_val,
        int_val, wis_val, cha_val,
        CHARACTERS_DIR,
        db
    )
    # Return same dropdown update for both play and party tabs
    return (status_msg, char_dropdown_update, char_dropdown_update)


# ============================================================================
# GRADIO UI
# ============================================================================

try:
    demo = gr.Blocks(title="D&D Character-Aware Game", theme=gr.themes.Soft())

    with demo:
        gr.Markdown("""
        # 🎲 D&D Character-Aware Game with RAG-Enhanced AI GM

        **Play D&D solo or with a party!** Create characters, explore the world, battle monsters, and let the AI Game Master guide your adventure.

        - **Character Mode**: Play with a single character
        - **Party Mode**: Adventure with multiple characters
        - **RAG-Enhanced**: Real D&D 5e SRD rules and content
        """)

        # ========================================================================
        # CREATE TABS
        # ========================================================================

        with gr.Tabs():
            # Play Game Tab
            play_components = create_play_tab(
                get_available_characters_wrapper,
                DEBUG_SCENARIOS,
                settings.DEBUG_MODE
            )

            # Create Character Tab
            create_components = create_character_tab(
                settings.DND_RACES,
                settings.DND_CLASSES
            )

            # Party Management Tab
            party_components = create_party_tab(
                get_available_characters_wrapper,
                get_party_summary_wrapper
            )

        # ========================================================================
        # EVENT HANDLERS - PLAY GAME TAB
        # ========================================================================

        # Mode toggle handler
        def toggle_mode(mode):
            """Toggle between character and party mode UI."""
            is_character_mode = (mode == "🎭 Single Character")
            return (
                gr.update(visible=is_character_mode),  # character_dropdown
                gr.update(visible=is_character_mode),  # load_btn
                gr.update(visible=is_character_mode),  # delete_btn
                gr.update(visible=not is_character_mode)  # load_party_btn
            )

        play_components['mode_toggle'].change(
            toggle_mode,
            inputs=[play_components['mode_toggle']],
            outputs=[
                play_components['character_dropdown'],
                play_components['load_btn'],
                play_components['delete_btn'],
                play_components['load_party_btn']
            ]
        )

        # Load character button
        play_components['load_btn'].click(
            load_character_with_debug_wrapper,
            inputs=[play_components['character_dropdown'], play_components['debug_scenario_dropdown']],
            outputs=[
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                play_components['msg_input'],
                play_components['chatbot'],
                play_components['char_image']
            ]
        )

        # Load party button
        play_components['load_party_btn'].click(
            load_party_mode_wrapper,
            inputs=[],
            outputs=[
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                play_components['msg_input'],
                play_components['chatbot']
            ]
        )

        # Delete character button
        play_components['delete_btn'].click(
            delete_character_wrapper,
            inputs=[play_components['character_dropdown']],
            outputs=[play_components['delete_status'], play_components['character_dropdown']]
        ).then(
            lambda: gr.update(visible=True),
            outputs=[play_components['delete_status']]
        )

        # RAG Lookup button
        play_components['rag_lookup_btn'].click(
            handle_rag_lookup_wrapper,
            inputs=[play_components['rag_lookup_input']],
            outputs=[play_components['rag_lookup_output']]
        )

        # Chat submit button
        play_components['submit_btn'].click(
            chat_wrapper,
            inputs=[play_components['msg_input'], play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        ).then(
            lambda: "",
            outputs=[play_components['msg_input']]
        )

        # Chat message input (Enter key)
        play_components['msg_input'].submit(
            chat_wrapper,
            inputs=[play_components['msg_input'], play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        ).then(
            lambda: "",
            outputs=[play_components['msg_input']]
        )

        # Combat control buttons
        play_components['next_turn_btn'].click(
            handle_next_turn_wrapper,
            inputs=[play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        )

        play_components['end_combat_btn'].click(
            handle_end_combat_wrapper,
            inputs=[play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        )

        # Clear history button
        play_components['clear_btn'].click(
            clear_history_wrapper,
            outputs=[play_components['chatbot']]
        )

        # Quick action buttons
        play_components['attack_btn'].click(
            lambda: "I attack ",
            outputs=[play_components['msg_input']]
        )

        play_components['cast_btn'].click(
            lambda history: chat_wrapper("/spells", history),
            inputs=[play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        )

        play_components['use_item_btn'].click(
            lambda: "I use ",
            outputs=[play_components['msg_input']]
        )

        play_components['help_btn'].click(
            lambda history: chat_wrapper("/help", history),
            inputs=[play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        )

        # ========================================================================
        # EVENT HANDLERS - CREATE CHARACTER TAB
        # ========================================================================

        create_components['roll_stats_btn'].click(
            roll_random_stats,
            inputs=[],
            outputs=[
                create_components['str_slider'],
                create_components['dex_slider'],
                create_components['con_slider'],
                create_components['int_slider'],
                create_components['wis_slider'],
                create_components['cha_slider']
            ]
        )

        create_components['create_btn'].click(
            create_character_wrapper,
            inputs=[
                create_components['char_name'],
                create_components['char_race'],
                create_components['char_class'],
                create_components['char_level'],
                create_components['char_alignment'],
                create_components['char_background'],
                create_components['str_slider'],
                create_components['dex_slider'],
                create_components['con_slider'],
                create_components['int_slider'],
                create_components['wis_slider'],
                create_components['cha_slider']
            ],
            outputs=[
                create_components['create_output'],
                play_components['character_dropdown'],
                party_components['party_char_selector']  # Update party selector too
            ]
        )

        # ========================================================================
        # EVENT HANDLERS - PARTY MANAGEMENT TAB
        # ========================================================================

        def add_and_update(character_choices):
            """Add characters to party and update all displays."""
            result = add_to_party_wrapper(character_choices)
            summary = get_party_summary_wrapper()
            sheets = get_all_character_sheets_wrapper()

            # Update remove dropdown with current party members
            party_member_names = list(party_characters.keys())

            return (
                result,  # party_status
                summary,  # party_summary_display
                sheets,  # party_sheets_display
                gr.update(choices=party_member_names)  # remove_char_selector
            )

        def remove_and_update(character_name):
            """Remove character from party and update all displays."""
            if not character_name:
                return (
                    "⚠️ Please select a character to remove",
                    get_party_summary_wrapper(),
                    get_all_character_sheets_wrapper(),
                    gr.update()
                )

            result = remove_from_party_wrapper(character_name)
            summary = get_party_summary_wrapper()
            sheets = get_all_character_sheets_wrapper()

            # Update remove dropdown with current party members
            party_member_names = list(party_characters.keys())

            return (
                result,  # party_status
                summary,  # party_summary_display
                sheets,  # party_sheets_display
                gr.update(choices=party_member_names, value=None)  # remove_char_selector
            )

        party_components['add_party_btn'].click(
            add_and_update,
            inputs=[party_components['party_char_selector']],
            outputs=[
                party_components['party_status'],
                party_components['party_summary_display'],
                party_components['party_sheets_display'],
                party_components['remove_char_selector']
            ]
        )

        party_components['remove_party_btn'].click(
            remove_and_update,
            inputs=[party_components['remove_char_selector']],
            outputs=[
                party_components['party_status'],
                party_components['party_summary_display'],
                party_components['party_sheets_display'],
                party_components['remove_char_selector']
            ]
        )

except TypeError:
    # Fallback for older Gradio versions that don't support theme parameter
    demo = gr.Blocks(title="D&D Character-Aware Game")

    with demo:
        gr.Markdown("""
        # 🎲 D&D Character-Aware Game with RAG-Enhanced AI GM

        **Play D&D solo or with a party!** Create characters, explore the world, battle monsters, and let the AI Game Master guide your adventure.

        - **Character Mode**: Play with a single character
        - **Party Mode**: Adventure with multiple characters
        - **RAG-Enhanced**: Real D&D 5e SRD rules and content
        """)

        # ========================================================================
        # CREATE TABS
        # ========================================================================

        with gr.Tabs():
            # Play Game Tab
            play_components = create_play_tab(
                get_available_characters_wrapper,
                DEBUG_SCENARIOS,
                settings.DEBUG_MODE
            )

            # Create Character Tab
            create_components = create_character_tab(
                settings.DND_RACES,
                settings.DND_CLASSES
            )

            # Party Management Tab
            party_components = create_party_tab(
                get_available_characters_wrapper,
                get_party_summary_wrapper
            )

        # ========================================================================
        # EVENT HANDLERS - PLAY GAME TAB
        # ========================================================================

        # Mode toggle handler
        def toggle_mode(mode):
            """Toggle between character and party mode UI."""
            is_character_mode = (mode == "🎭 Single Character")
            return (
                gr.update(visible=is_character_mode),  # character_dropdown
                gr.update(visible=is_character_mode),  # load_btn
                gr.update(visible=is_character_mode),  # delete_btn
                gr.update(visible=not is_character_mode)  # load_party_btn
            )

        play_components['mode_toggle'].change(
            toggle_mode,
            inputs=[play_components['mode_toggle']],
            outputs=[
                play_components['character_dropdown'],
                play_components['load_btn'],
                play_components['delete_btn'],
                play_components['load_party_btn']
            ]
        )

        # Load character button
        play_components['load_btn'].click(
            load_character_with_debug_wrapper,
            inputs=[play_components['character_dropdown'], play_components['debug_scenario_dropdown']],
            outputs=[
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                play_components['msg_input'],
                play_components['chatbot'],
                play_components['char_image']
            ]
        )

        # Load party button
        play_components['load_party_btn'].click(
            load_party_mode_wrapper,
            inputs=[],
            outputs=[
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                play_components['msg_input'],
                play_components['chatbot']
            ]
        )

        # Delete character button
        play_components['delete_btn'].click(
            delete_character_wrapper,
            inputs=[play_components['character_dropdown']],
            outputs=[play_components['delete_status'], play_components['character_dropdown']]
        ).then(
            lambda: gr.update(visible=True),
            outputs=[play_components['delete_status']]
        )

        # RAG Lookup button
        play_components['rag_lookup_btn'].click(
            handle_rag_lookup_wrapper,
            inputs=[play_components['rag_lookup_input']],
            outputs=[play_components['rag_lookup_output']]
        )

        # Chat submit button
        play_components['submit_btn'].click(
            chat_wrapper,
            inputs=[play_components['msg_input'], play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        ).then(
            lambda: "",
            outputs=[play_components['msg_input']]
        )

        # Chat message input (Enter key)
        play_components['msg_input'].submit(
            chat_wrapper,
            inputs=[play_components['msg_input'], play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        ).then(
            lambda: "",
            outputs=[play_components['msg_input']]
        )

        # Combat control buttons
        play_components['next_turn_btn'].click(
            handle_next_turn_wrapper,
            inputs=[play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        )

        play_components['end_combat_btn'].click(
            handle_end_combat_wrapper,
            inputs=[play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        )

        # Clear history button
        play_components['clear_btn'].click(
            clear_history_wrapper,
            outputs=[play_components['chatbot']]
        )

        # Quick action buttons
        play_components['attack_btn'].click(
            lambda: "I attack ",
            outputs=[play_components['msg_input']]
        )

        play_components['cast_btn'].click(
            lambda history: chat_wrapper("/spells", history),
            inputs=[play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        )

        play_components['use_item_btn'].click(
            lambda: "I use ",
            outputs=[play_components['msg_input']]
        )

        play_components['help_btn'].click(
            lambda history: chat_wrapper("/help", history),
            inputs=[play_components['chatbot']],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3']
            ]
        )

        # ========================================================================
        # EVENT HANDLERS - CREATE CHARACTER TAB
        # ========================================================================

        create_components['roll_stats_btn'].click(
            roll_random_stats,
            inputs=[],
            outputs=[
                create_components['str_slider'],
                create_components['dex_slider'],
                create_components['con_slider'],
                create_components['int_slider'],
                create_components['wis_slider'],
                create_components['cha_slider']
            ]
        )

        create_components['create_btn'].click(
            create_character_wrapper,
            inputs=[
                create_components['char_name'],
                create_components['char_race'],
                create_components['char_class'],
                create_components['char_level'],
                create_components['char_alignment'],
                create_components['char_background'],
                create_components['str_slider'],
                create_components['dex_slider'],
                create_components['con_slider'],
                create_components['int_slider'],
                create_components['wis_slider'],
                create_components['cha_slider']
            ],
            outputs=[
                create_components['create_output'],
                play_components['character_dropdown'],
                party_components['party_char_selector']  # Update party selector too
            ]
        )

        # ========================================================================
        # EVENT HANDLERS - PARTY MANAGEMENT TAB
        # ========================================================================

        def add_and_update(character_choices):
            """Add characters to party and update all displays."""
            result = add_to_party_wrapper(character_choices)
            summary = get_party_summary_wrapper()
            sheets = get_all_character_sheets_wrapper()

            # Update remove dropdown with current party members
            party_member_names = list(party_characters.keys())

            return (
                result,  # party_status
                summary,  # party_summary_display
                sheets,  # party_sheets_display
                gr.update(choices=party_member_names)  # remove_char_selector
            )

        def remove_and_update(character_name):
            """Remove character from party and update all displays."""
            if not character_name:
                return (
                    "⚠️ Please select a character to remove",
                    get_party_summary_wrapper(),
                    get_all_character_sheets_wrapper(),
                    gr.update()
                )

            result = remove_from_party_wrapper(character_name)
            summary = get_party_summary_wrapper()
            sheets = get_all_character_sheets_wrapper()

            # Update remove dropdown with current party members
            party_member_names = list(party_characters.keys())

            return (
                result,  # party_status
                summary,  # party_summary_display
                sheets,  # party_sheets_display
                gr.update(choices=party_member_names, value=None)  # remove_char_selector
            )

        party_components['add_party_btn'].click(
            add_and_update,
            inputs=[party_components['party_char_selector']],
            outputs=[
                party_components['party_status'],
                party_components['party_summary_display'],
                party_components['party_sheets_display'],
                party_components['remove_char_selector']
            ]
        )

        party_components['remove_party_btn'].click(
            remove_and_update,
            inputs=[party_components['remove_char_selector']],
            outputs=[
                party_components['party_status'],
                party_components['party_summary_display'],
                party_components['party_sheets_display'],
                party_components['remove_char_selector']
            ]
        )

# ============================================================================
# LAUNCH
# ============================================================================

if __name__ == "__main__":
    # Launch
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
