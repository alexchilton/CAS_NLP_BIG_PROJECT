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

# Session state import
from web.session_state import SessionState, create_session_state

# ============================================================================
# INITIALIZATION
# ============================================================================

print("🎲 Initializing D&D RAG System...")
db = ChromaDBManager()  # Shared ChromaDB (thread-safe for reads)

# Paths
CHARACTERS_DIR = Path(__file__).parent.parent / "characters"
CHARACTERS_DIR.mkdir(exist_ok=True)

# ============================================================================
# CONSTANTS (imported from centralized config)
# ============================================================================

STARTING_LOCATIONS = settings.STARTING_LOCATIONS
COMBAT_LOCATIONS = settings.COMBAT_LOCATIONS
DEBUG_SCENARIOS = settings.DEBUG_SCENARIOS

# ============================================================================
# HELPER FUNCTIONS & WRAPPERS
# ============================================================================

def ensure_session(session: Optional['SessionState']) -> 'SessionState':
    """Ensure session is initialized (lazy initialization to avoid Gradio pickling issues)."""
    if session is None:
        return create_session_state()
    return session


def get_current_sheet(session: Optional['SessionState']) -> tuple:
    """Get character sheet based on current mode."""
    session = ensure_session(session)
    if session.gameplay_mode == "party":
        return (format_party_sheet(session.party_characters, session.party), "", "")
    else:
        if session.current_character and session.gm.session.character_state:
            return format_character_sheet(session.current_character, session.gm.session.character_state, db)
        else:
            return ("No character loaded", "", "")


def get_initiative_tracker_wrapper(session: Optional['SessionState']) -> Tuple[str, gr.update]:
    """Wrapper for get_initiative_tracker handler with session state."""
    session = ensure_session(session)
    return get_initiative_tracker(session.gm, session.gameplay_mode, session.party_characters, session.party)


def get_available_characters_wrapper() -> list:
    """Wrapper for get_available_characters handler."""
    return get_available_characters(CHARACTERS_DIR)


def get_party_summary_wrapper(session: Optional['SessionState']) -> str:
    """Wrapper for get_party_summary handler with session state."""
    session = ensure_session(session)
    return get_party_summary(session.party_characters, session.party)


def get_all_character_sheets_wrapper(session: Optional['SessionState']) -> str:
    """Wrapper for get_all_character_sheets handler with session state."""
    session = ensure_session(session)
    return get_all_character_sheets(session.party_characters, session.party)


# ============================================================================
# EVENT HANDLER WRAPPERS (for global state management)
# ============================================================================

def load_character_wrapper(character_choice: str, session: Optional['SessionState']) -> Tuple[str, str, str, str, list, Optional[str], 'SessionState']:
    """Wrapper for load_character handler with session state."""
    session = ensure_session(session)
    session.conversation_history = []
    session.gameplay_mode = "character"

    result = load_character(
        character_choice,
        CHARACTERS_DIR,
        STARTING_LOCATIONS,
        COMBAT_LOCATIONS,
        session.gm,
        db,
        format_character_sheet
    )

    # Update session current_character
    if session.gm.session.character_state:
        char_name = session.gm.session.character_state.character_name
        if char_name in session.gm.session.base_character_stats:
            session.current_character = session.gm.session.base_character_stats[char_name]

    return (*result, session)


def load_character_with_debug_wrapper(character_choice: str, scenario_choice: Optional[str], session: Optional['SessionState']) -> Tuple[str, str, str, str, list, Optional[str], 'SessionState']:
    """Wrapper for load_character_with_debug handler with session state."""
    session = ensure_session(session)
    session.conversation_history = []
    session.gameplay_mode = "character"

    result = load_character_with_debug(
        character_choice,
        scenario_choice,
        CHARACTERS_DIR,
        STARTING_LOCATIONS,
        COMBAT_LOCATIONS,
        DEBUG_SCENARIOS,
        session.gm,
        db,
        format_character_sheet,
        lambda char_choice: load_character_wrapper(char_choice, session)
    )

    # Update session current_character
    if session.gm.session.character_state:
        char_name = session.gm.session.character_state.character_name
        if char_name in session.gm.session.base_character_stats:
            session.current_character = session.gm.session.base_character_stats[char_name]

    return (*result, session)


def load_character_with_location(character_choice: str, session: Optional['SessionState'], location_name: Optional[str] = None) -> Tuple[str, str, str, 'SessionState']:
    """
    Load character and set specific starting location (for testing).
    
    Args:
        character_choice: Character selection string
        session: The current session state.
        location_name: Optional location name. If None, uses random.
    
    Returns:
        Tuple of (location_name, location_desc, character_name, updated_session)
    """
    session = ensure_session(session)
    session.conversation_history = []
    session.gameplay_mode = "character"
    
    from web.handlers.character_handlers import load_character_with_location as handler_load_char_loc
    
    loc_name, loc_desc, char_name, character, char_state = handler_load_char_loc(
        character_choice,
        CHARACTERS_DIR,
        STARTING_LOCATIONS,
        COMBAT_LOCATIONS,
        session.gm, # Use gm from session
        location_name
    )
    
    # Update session current_character
    if char_name in session.gm.session.base_character_stats:
        session.current_character = session.gm.session.base_character_stats[char_name]
    
    return loc_name, loc_desc, char_name, session


def delete_character_wrapper(character_choice: str) -> Tuple[str, gr.update]:
    """Wrapper for delete_character handler."""
    return delete_character(character_choice, CHARACTERS_DIR)


def handle_rag_lookup_wrapper(query: str, session: Optional['SessionState']) -> str:
    """Wrapper for handle_rag_lookup handler with session state."""
    session = ensure_session(session)
    return handle_rag_lookup(query, session.gm, db)


def chat_wrapper(message: str, history: list, session: Optional['SessionState']) -> Tuple[list, str, gr.update, str, str, str, 'SessionState']:
    """Wrapper for chat handler with session state."""
    session = ensure_session(session)
    result = chat(
        message,
        history,
        session.gameplay_mode,
        session.current_character,
        session.party_characters,
        session.conversation_history,
        session.gm,
        lambda: get_initiative_tracker_wrapper(session),
        lambda: get_current_sheet(session)
    )

    return (*result, session)


def clear_history_wrapper(session: Optional['SessionState']) -> Tuple[list, 'SessionState']:
    """Wrapper for clear_history handler with session state."""
    session = ensure_session(session)
    result = clear_history(session.conversation_history)
    return (result, session)


def handle_next_turn_wrapper(history: list, session: Optional['SessionState']) -> Tuple[list, str, gr.update, str, str, str, 'SessionState']:
    """Wrapper for handle_next_turn handler with session state."""
    session = ensure_session(session)
    result = handle_next_turn(
        history,
        session.gm,
        lambda: get_initiative_tracker_wrapper(session),
        lambda: get_current_sheet(session)
    )
    return (*result, session)


def handle_end_combat_wrapper(history: list, session: Optional['SessionState']) -> Tuple[list, str, gr.update, str, str, str, 'SessionState']:
    """Wrapper for handle_end_combat handler with session state."""
    session = ensure_session(session)
    result = handle_end_combat(
        history,
        session.gm,
        lambda: get_initiative_tracker_wrapper(session),
        lambda: get_current_sheet(session)
    )
    return (*result, session)


def load_party_mode_wrapper(session: Optional['SessionState']) -> Tuple[str, str, str, gr.update, list, 'SessionState']:
    """Wrapper for load_party_mode handler with session state."""
    session = ensure_session(session)
    def set_gameplay_mode(mode: str):
        session.gameplay_mode = mode

    def set_conversation_history(history: list):
        session.conversation_history = history

    result = load_party_mode(
        session.party_characters,
        session.party,
        session.gm,
        set_gameplay_mode,
        set_conversation_history
    )

    return (*result, session)


def add_to_party_wrapper(character_choices: list, session: Optional['SessionState']) -> Tuple[str, 'SessionState']:
    """Wrapper for add_to_party handler with session state."""
    session = ensure_session(session)
    result, updated_party_chars, updated_party = add_to_party(
        character_choices,
        session.party_characters,
        session.party
    )

    # Update session state
    session.party_characters = updated_party_chars
    session.party = updated_party

    return (result, session)


def remove_from_party_wrapper(character_name: str, session: Optional['SessionState']) -> Tuple[str, 'SessionState']:
    """Wrapper for remove_from_party handler with session state."""
    session = ensure_session(session)
    result, updated_party_chars, updated_party = remove_from_party(
        character_name,
        session.party_characters,
        session.party
    )

    # Update session state
    session.party_characters = updated_party_chars
    session.party = updated_party

    return (result, session)


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
        # SESSION STATE (per-user isolation)
        # ========================================================================
        # Initialize with None to avoid Gradio pickling issues during UI creation
        # Session will be lazily initialized via ensure_session() on first use
        session_state = gr.State(None)

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
                lambda: "**No characters in party**\n\nAdd characters from the dropdown above."
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
            inputs=[play_components['character_dropdown'], play_components['debug_scenario_dropdown'], session_state],
            outputs=[
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                play_components['msg_input'],
                play_components['chatbot'],
                play_components['char_image'],
                session_state
            ]
        )

        # Load party button
        play_components['load_party_btn'].click(
            load_party_mode_wrapper,
            inputs=[session_state],
            outputs=[
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                play_components['msg_input'],
                play_components['chatbot'],
                session_state
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
            inputs=[play_components['rag_lookup_input'], session_state],
            outputs=[play_components['rag_lookup_output']]
        )

        # Chat submit button
        play_components['submit_btn'].click(
            chat_wrapper,
            inputs=[play_components['msg_input'], play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
            ]
        ).then(
            lambda: "",
            outputs=[play_components['msg_input']]
        )

        # Chat message input (Enter key)
        play_components['msg_input'].submit(
            chat_wrapper,
            inputs=[play_components['msg_input'], play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
            ]
        ).then(
            lambda: "",
            outputs=[play_components['msg_input']]
        )

        # Combat control buttons
        play_components['next_turn_btn'].click(
            handle_next_turn_wrapper,
            inputs=[play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
            ]
        )

        play_components['end_combat_btn'].click(
            handle_end_combat_wrapper,
            inputs=[play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
            ]
        )

        # Clear history button
        play_components['clear_btn'].click(
            clear_history_wrapper,
            inputs=[session_state],
            outputs=[play_components['chatbot'], session_state]
        )

        # Quick action buttons
        play_components['attack_btn'].click(
            lambda: "I attack ",
            outputs=[play_components['msg_input']]
        )

        play_components['cast_btn'].click(
            lambda history, session: chat_wrapper("/spells", history, session),
            inputs=[play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
            ]
        )

        play_components['use_item_btn'].click(
            lambda: "I use ",
            outputs=[play_components['msg_input']]
        )

        play_components['help_btn'].click(
            lambda history, session: chat_wrapper("/help", history, session),
            inputs=[play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
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

        def add_and_update(character_choices, session):
            """Add characters to party and update all displays."""
            result, session = add_to_party_wrapper(character_choices, session)
            summary = get_party_summary_wrapper(session)
            sheets = get_all_character_sheets_wrapper(session)

            # Update remove dropdown with current party members
            session = ensure_session(session)
            party_member_names = list(session.party_characters.keys())

            return (
                result,  # party_status
                summary,  # party_summary_display
                sheets,  # party_sheets_display
                gr.update(choices=party_member_names),  # remove_char_selector
                session
            )

        def remove_and_update(character_name, session):
            """Remove character from party and update all displays."""
            session = ensure_session(session)
            if not character_name:
                return (
                    "⚠️ Please select a character to remove",
                    get_party_summary_wrapper(session),
                    get_all_character_sheets_wrapper(session),
                    gr.update(),
                    session
                )

            result, session = remove_from_party_wrapper(character_name, session)
            summary = get_party_summary_wrapper(session)
            sheets = get_all_character_sheets_wrapper(session)

            # Update remove dropdown with current party members
            party_member_names = list(session.party_characters.keys())

            return (
                result,  # party_status
                summary,  # party_summary_display
                sheets,  # party_sheets_display
                gr.update(choices=party_member_names, value=None),  # remove_char_selector
                session
            )

        party_components['add_party_btn'].click(
            add_and_update,
            inputs=[party_components['party_char_selector'], session_state],
            outputs=[
                party_components['party_status'],
                party_components['party_summary_display'],
                party_components['party_sheets_display'],
                party_components['remove_char_selector'],
                session_state
            ]
        )

        party_components['remove_party_btn'].click(
            remove_and_update,
            inputs=[party_components['remove_char_selector'], session_state],
            outputs=[
                party_components['party_status'],
                party_components['party_summary_display'],
                party_components['party_sheets_display'],
                party_components['remove_char_selector'],
                session_state
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
        # SESSION STATE (per-user isolation)
        # ========================================================================
        # Initialize with None to avoid Gradio pickling issues during UI creation
        # Session will be lazily initialized via ensure_session() on first use
        session_state = gr.State(None)

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
                lambda: "**No characters in party**\n\nAdd characters from the dropdown above."
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
            inputs=[play_components['character_dropdown'], play_components['debug_scenario_dropdown'], session_state],
            outputs=[
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                play_components['msg_input'],
                play_components['chatbot'],
                play_components['char_image'],
                session_state
            ]
        )

        # Load party button
        play_components['load_party_btn'].click(
            load_party_mode_wrapper,
            inputs=[session_state],
            outputs=[
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                play_components['msg_input'],
                play_components['chatbot'],
                session_state
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
            inputs=[play_components['rag_lookup_input'], session_state],
            outputs=[play_components['rag_lookup_output']]
        )

        # Chat submit button
        play_components['submit_btn'].click(
            chat_wrapper,
            inputs=[play_components['msg_input'], play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
            ]
        ).then(
            lambda: "",
            outputs=[play_components['msg_input']]
        )

        # Chat message input (Enter key)
        play_components['msg_input'].submit(
            chat_wrapper,
            inputs=[play_components['msg_input'], play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
            ]
        ).then(
            lambda: "",
            outputs=[play_components['msg_input']]
        )

        # Combat control buttons
        play_components['next_turn_btn'].click(
            handle_next_turn_wrapper,
            inputs=[play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
            ]
        )

        play_components['end_combat_btn'].click(
            handle_end_combat_wrapper,
            inputs=[play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
            ]
        )

        # Clear history button
        play_components['clear_btn'].click(
            clear_history_wrapper,
            inputs=[session_state],
            outputs=[play_components['chatbot'], session_state]
        )

        # Quick action buttons
        play_components['attack_btn'].click(
            lambda: "I attack ",
            outputs=[play_components['msg_input']]
        )

        play_components['cast_btn'].click(
            lambda history, session: chat_wrapper("/spells", history, session),
            inputs=[play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
            ]
        )

        play_components['use_item_btn'].click(
            lambda: "I use ",
            outputs=[play_components['msg_input']]
        )

        play_components['help_btn'].click(
            lambda history, session: chat_wrapper("/help", history, session),
            inputs=[play_components['chatbot'], session_state],
            outputs=[
                play_components['chatbot'],
                play_components['initiative_display'],
                play_components['combat_accordion'],
                play_components['char_col1'],
                play_components['char_col2'],
                play_components['char_col3'],
                session_state
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

        def add_and_update(character_choices, session):
            """Add characters to party and update all displays."""
            result, session = add_to_party_wrapper(character_choices, session)
            summary = get_party_summary_wrapper(session)
            sheets = get_all_character_sheets_wrapper(session)

            # Update remove dropdown with current party members
            session = ensure_session(session)
            party_member_names = list(session.party_characters.keys())

            return (
                result,  # party_status
                summary,  # party_summary_display
                sheets,  # party_sheets_display
                gr.update(choices=party_member_names),  # remove_char_selector
                session
            )

        def remove_and_update(character_name, session):
            """Remove character from party and update all displays."""
            session = ensure_session(session)
            if not character_name:
                return (
                    "⚠️ Please select a character to remove",
                    get_party_summary_wrapper(session),
                    get_all_character_sheets_wrapper(session),
                    gr.update(),
                    session
                )

            result, session = remove_from_party_wrapper(character_name, session)
            summary = get_party_summary_wrapper(session)
            sheets = get_all_character_sheets_wrapper(session)

            # Update remove dropdown with current party members
            party_member_names = list(session.party_characters.keys())

            return (
                result,  # party_status
                summary,  # party_summary_display
                sheets,  # party_sheets_display
                gr.update(choices=party_member_names, value=None),  # remove_char_selector
                session
            )

        party_components['add_party_btn'].click(
            add_and_update,
            inputs=[party_components['party_char_selector'], session_state],
            outputs=[
                party_components['party_status'],
                party_components['party_summary_display'],
                party_components['party_sheets_display'],
                party_components['remove_char_selector'],
                session_state
            ]
        )

        party_components['remove_party_btn'].click(
            remove_and_update,
            inputs=[party_components['remove_char_selector'], session_state],
            outputs=[
                party_components['party_status'],
                party_components['party_summary_display'],
                party_components['party_sheets_display'],
                party_components['remove_char_selector'],
                session_state
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
