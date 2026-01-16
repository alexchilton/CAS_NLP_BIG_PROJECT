"""
Event handlers for Gradio UI interactions.
"""

from .character_handlers import (
    load_character_from_json,
    save_character_to_json,
    get_available_characters,
    delete_character,
    load_character_with_location,
    load_character,
    load_character_with_debug,
    create_character
)

from .chat_handlers import chat, handle_rag_lookup, clear_history, roll_random_stats
from .combat_handlers import get_initiative_tracker, handle_next_turn, handle_end_combat
from .party_handlers import load_party_mode, add_to_party, remove_from_party, get_party_summary

__all__ = [
    # Character handlers
    'load_character_from_json',
    'save_character_to_json',
    'get_available_characters',
    'delete_character',
    'load_character_with_location',
    'load_character',
    'load_character_with_debug',
    'create_character',
    # Chat handlers
    'chat',
    'handle_rag_lookup',
    'clear_history',
    'roll_random_stats',
    # Combat handlers
    'get_initiative_tracker',
    'handle_next_turn',
    'handle_end_combat',
    # Party handlers
    'load_party_mode',
    'add_to_party',
    'remove_from_party',
    'get_party_summary',
]
