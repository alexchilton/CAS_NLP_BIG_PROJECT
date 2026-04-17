"""
Play Game tab UI component.
"""

import gradio as gr
from typing import Dict, Any


def create_play_tab(get_available_characters_func, debug_scenarios, debug_mode: bool = False) -> Dict[str, Any]:
    """
    Create the Play Game tab UI.

    Args:
        get_available_characters_func: Function to get list of available characters
        debug_scenarios: List of debug scenario tuples (name, location, npcs, items)
        debug_mode: Whether to show debug UI elements

    Returns:
        Dict containing all UI components that need event handler wiring
    """
    components = {}

    with gr.Tab("🎮 Play Game"):
        # TOP SECTION: Gameplay Mode (left) | Game Session (right)
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Gameplay Mode")

                components['mode_toggle'] = gr.Radio(
                    choices=["🎭 Single Character", "🎲 Party Mode"],
                    value="🎭 Single Character",
                    label="Play Mode",
                    info="Single Character: Traditional one-player mode | Party Mode: Multi-character adventure"
                )

                gr.Markdown("---")

                # Character mode UI
                components['character_dropdown'] = gr.Dropdown(
                    choices=get_available_characters_func(),
                    value=get_available_characters_func()[0] if get_available_characters_func() else None,
                    label="Choose Your Character",
                    visible=True
                )

                # Debug scenario dropdown (only visible in debug mode)
                components['debug_scenario_dropdown'] = gr.Dropdown(
                    choices=[s[0] for s in debug_scenarios],
                    value=None,
                    label="🧪 Debug Scenario (Optional)",
                    info="Load character in specific test scenario for combat testing",
                    visible=debug_mode
                )

                with gr.Row():
                    components['load_btn'] = gr.Button("Load Character", variant="primary", scale=2)
                    components['delete_btn'] = gr.Button("🗑️ Delete", variant="stop", scale=1)

                components['load_party_btn'] = gr.Button("Load Party", variant="primary", visible=False)

                components['delete_status'] = gr.Textbox(label="Delete Status", interactive=False, visible=False)

            with gr.Column(scale=2):
                gr.Markdown("## Game Session")

                # Initiative Tracker (visible when in combat)
                with gr.Accordion("⚔️ Initiative Tracker", open=False, visible=False) as combat_accordion:
                    components['initiative_display'] = gr.Markdown("Not in combat")

                    with gr.Row():
                        components['next_turn_btn'] = gr.Button("⏭️ Next Turn", variant="secondary", scale=1)
                        components['end_combat_btn'] = gr.Button("🛑 End Combat", variant="stop", scale=1)

                components['combat_accordion'] = combat_accordion

                components['chatbot'] = gr.Chatbot(
                    height=500,
                    label="Game Master",
                    show_label=True
                )

                with gr.Row():
                    components['msg_input'] = gr.Textbox(
                        placeholder="Type your action or command here... (e.g., 'I look around' or '/help')",
                        label="Your Action",
                        show_label=False,
                        scale=4
                    )
                    components['submit_btn'] = gr.Button("Send", variant="primary", scale=1)

                # Quick Action Buttons
                with gr.Row():
                    components['attack_btn'] = gr.Button("⚔️ Attack", variant="secondary", scale=1)
                    components['cast_btn'] = gr.Button("✨ Cast Spell", variant="secondary", scale=1)
                    components['use_item_btn'] = gr.Button("🎒 Use Item", variant="secondary", scale=1)
                    components['help_btn'] = gr.Button("❓ Help", variant="secondary", scale=1)

                with gr.Row():
                    components['clear_btn'] = gr.Button("Clear History")
                    gr.Markdown("**Quick Commands:** `/help` | `/stats` | `/map` | `/explore` | `/buy <item>` | `/sell <item>`")

        # BOTTOM SECTION: 3-Column Character Sheet (full width)
        gr.Markdown("---")
        gr.Markdown("## Character Sheet")

        with gr.Row():
            # Column 1: Character Info + Portrait
            with gr.Column(scale=1):
                components['char_col1'] = gr.Markdown("No character loaded")

                gr.Markdown("---")

                # Character Image (moved here from sidebar)
                components['char_image'] = gr.Image(
                    label="Character Portrait",
                    type="filepath",
                    interactive=False,
                    height=200
                )

            # Column 2: Equipment/Inventory + RAG Lookup
            with gr.Column(scale=1):
                components['char_col2'] = gr.Markdown("")

                gr.Markdown("---")

                # RAG Lookup Panel (moved here from sidebar)
                with gr.Accordion("📖 Quick Spell & Item Lookup", open=False) as rag_lookup_accordion:
                    gr.Markdown("*Look up spell details, item properties, and rules from D&D 5e SRD*")

                    with gr.Row():
                        components['rag_lookup_input'] = gr.Textbox(
                            placeholder="Enter spell or item name (e.g., 'Magic Missile', 'Longsword')",
                            label="Spell/Item Name",
                            scale=3
                        )
                        components['rag_lookup_btn'] = gr.Button("🔍 Lookup", variant="primary", scale=1)

                    components['rag_lookup_output'] = gr.Markdown("*Enter a spell or item name above to see details*")

                components['rag_lookup_accordion'] = rag_lookup_accordion

            # Column 3: Spells/Class Info
            with gr.Column(scale=1):
                components['char_col3'] = gr.Markdown("")

        # BOTTOM SECTION: 3-Column Tips & Examples
        gr.Markdown("---")

        with gr.Row():
            # Column 1: Example Actions
            with gr.Column(scale=1):
                gr.Markdown("""
### 📖 Example Actions
- "I look around and check my surroundings"
- "I draw my weapon and prepare for combat"
- "I cast Magic Missile at the goblin"
- "I attack with my longsword"
                """)

            # Column 2: Party Mode Tips
            with gr.Column(scale=1):
                gr.Markdown("""
### 🎭 Party Mode Tips
- First add characters in the Party Management tab
- Switch to "Party Mode" above and click "Load Party"
- In party mode, the GM manages the entire group
- Type actions like "We investigate the cave" or "The party attacks"
- Use `/stats` to see all party members
                """)

            # Column 3: RAG Commands
            with gr.Column(scale=1):
                gr.Markdown("""
### 🔍 RAG Commands
- `/rag Magic Missile` - Look up spell details
- `/rag Goblin` - Look up monster stats
- `/rag Fighter` - Look up class features
                """)

    return components
