"""
Party Management tab UI component.
"""

import gradio as gr
from typing import Dict, Any


def create_party_tab(get_available_characters_func, get_party_summary_func) -> Dict[str, Any]:
    """
    Create the Party Management tab UI.

    Args:
        get_available_characters_func: Function to get list of available characters
        get_party_summary_func: Function to get party summary display

    Returns:
        Dict containing all UI components that need event handler wiring
    """
    components = {}

    with gr.Tab("🎭 Party Management"):
        gr.Markdown("""
        ## Manage Your Adventuring Party

        Create a band of adventurers! Add multiple characters to your party and view their stats.
        Each character can be viewed individually, and the party shares gold and inventory.
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Add Characters to Party")

                components['party_char_selector'] = gr.Dropdown(
                    choices=get_available_characters_func(),
                    multiselect=True,
                    label="Select Characters",
                    info="Choose one or more characters to add to your party"
                )

                components['add_party_btn'] = gr.Button("➕ Add to Party", variant="primary", size="lg")

                gr.Markdown("---")

                gr.Markdown("### Remove from Party")

                components['remove_char_selector'] = gr.Dropdown(
                    choices=[],
                    label="Select Character to Remove",
                    info="Choose a character to remove from the party"
                )

                components['remove_party_btn'] = gr.Button("➖ Remove from Party", variant="secondary")

                components['party_status'] = gr.Textbox(label="Status", interactive=False, lines=3)

            with gr.Column(scale=2):
                gr.Markdown("### Party Overview")

                components['party_summary_display'] = gr.Markdown(get_party_summary_func())

                gr.Markdown("---")

                gr.Markdown("### Party Member Sheets")

                with gr.Accordion("View All Character Sheets", open=False):
                    components['party_sheets_display'] = gr.Markdown("No characters in party")

        gr.Markdown("""
        ---

        **Party Features:**
        - Add multiple characters to form a party
        - Shared gold and inventory pool
        - View individual character stats
        - Track party health and status
        """)

    return components
