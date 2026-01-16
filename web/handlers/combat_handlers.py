"""
Combat-related event handlers.
"""

from typing import Tuple
import gradio as gr


def get_initiative_tracker(gm, gameplay_mode, party_characters, party_state) -> Tuple[str, gr.update]:
    """
    Get initiative tracker display and combat status.

    Args:
        gm: GameMaster instance
        gameplay_mode: Current gameplay mode ("character" or "party")
        party_characters: Dict of party characters (for party mode)
        party_state: PartyState object (for party mode)

    Returns:
        Tuple of (initiative_display_text, accordion_update)
    """
    in_combat = gm.combat_manager.is_in_combat()

    # DEBUG: Log accordion visibility state
    print(f"🔍 get_initiative_tracker: in_combat={in_combat}")

    if in_combat:
        # Get initiative tracker with party info if in party mode
        if gameplay_mode == "party" and party_characters:
            tracker = gm.combat_manager.get_initiative_tracker(party_state)
        else:
            tracker = gm.combat_manager.get_initiative_tracker()

        print(f"   ✅ Returning accordion visible=True, open=True")
        print(f"   📋 Tracker preview: {tracker[:100]}...")
        return tracker, gr.update(visible=True, open=True)
    else:
        print(f"   ❌ Returning accordion visible=False")
        return "⚔️ Not currently in combat\n\nUse `/start_combat Goblin, Orc` to begin combat", gr.update(visible=False)


def handle_next_turn(history: list, gm, get_initiative_tracker_func, get_current_sheet_func) -> Tuple[list, str, gr.update, str, str, str]:
    """
    Handle Next Turn button click.

    Args:
        history: Chat history
        gm: GameMaster instance
        get_initiative_tracker_func: Function to get initiative tracker
        get_current_sheet_func: Function to get current character sheet

    Returns:
        Tuple of (updated_history, initiative_display, accordion_update, char_col1, char_col2, char_col3)
    """
    if not gm.combat_manager.is_in_combat():
        return (
            history + [
                {"role": "assistant", "content": "⚠️ Not in combat! Use `/start_combat` to begin."}
            ],
            *get_initiative_tracker_func(),
            *get_current_sheet_func()
        )

    # Advance turn
    response = gm.generate_response("/next_turn", use_rag=False)

    new_history = history + [
        {"role": "assistant", "content": response}
    ]

    return (new_history, *get_initiative_tracker_func(), *get_current_sheet_func())


def handle_end_combat(history: list, gm, get_initiative_tracker_func, get_current_sheet_func) -> Tuple[list, str, gr.update, str, str, str]:
    """
    Handle End Combat button click.

    Args:
        history: Chat history
        gm: GameMaster instance
        get_initiative_tracker_func: Function to get initiative tracker
        get_current_sheet_func: Function to get current character sheet

    Returns:
        Tuple of (updated_history, initiative_display, accordion_update, char_col1, char_col2, char_col3)
    """
    if not gm.combat_manager.is_in_combat():
        return (
            history + [
                {"role": "assistant", "content": "⚠️ Not in combat!"}
            ],
            *get_initiative_tracker_func(),
            *get_current_sheet_func()
        )

    # End combat
    response = gm.generate_response("/end_combat", use_rag=False)

    new_history = history + [
        {"role": "assistant", "content": response}
    ]

    return (new_history, *get_initiative_tracker_func(), *get_current_sheet_func())
