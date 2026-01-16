"""
Create Character tab UI component.
"""

import gradio as gr
from typing import Dict, Any, List


def create_character_tab(dnd_races: List[str], dnd_classes: List[str]) -> Dict[str, Any]:
    """
    Create the Create Character tab UI.

    Args:
        dnd_races: List of available D&D races
        dnd_classes: List of available D&D classes

    Returns:
        Dict containing all UI components that need event handler wiring
    """
    components = {}

    with gr.Tab("✨ Create Character"):
        gr.Markdown("""
        ## Create Your D&D Character

        Fill in the fields below to create a new character. Your character will be saved and available in the character dropdown.
        """)

        with gr.Row():
            with gr.Column():
                components['char_name'] = gr.Textbox(label="Character Name", placeholder="e.g., Gandalf the Grey")

                with gr.Row():
                    components['char_race'] = gr.Dropdown(
                        choices=dnd_races,
                        value="Human",
                        label="Race"
                    )
                    components['char_class'] = gr.Dropdown(
                        choices=dnd_classes,
                        value="Fighter",
                        label="Class"
                    )

                with gr.Row():
                    components['char_level'] = gr.Slider(
                        minimum=1,
                        maximum=20,
                        value=1,
                        step=1,
                        label="Level",
                        info="Character level (1-20)"
                    )
                    components['char_alignment'] = gr.Dropdown(
                        choices=[
                            "Lawful Good", "Neutral Good", "Chaotic Good",
                            "Lawful Neutral", "True Neutral", "Chaotic Neutral",
                            "Lawful Evil", "Neutral Evil", "Chaotic Evil"
                        ],
                        value="True Neutral",
                        label="Alignment"
                    )

                components['char_background'] = gr.Textbox(label="Background", placeholder="e.g., Soldier, Sage, Folk Hero")

            with gr.Column():
                gr.Markdown("### Ability Scores")
                gr.Markdown("*Standard array: 15, 14, 13, 12, 10, 8 | Or roll random with 3d6*")

                components['roll_stats_btn'] = gr.Button("🎲 Roll Random Stats (3d6)", variant="secondary", size="sm")

                with gr.Row():
                    components['str_slider'] = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Strength")
                    components['dex_slider'] = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Dexterity")

                with gr.Row():
                    components['con_slider'] = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Constitution")
                    components['int_slider'] = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Intelligence")

                with gr.Row():
                    components['wis_slider'] = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Wisdom")
                    components['cha_slider'] = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Charisma")

        components['create_btn'] = gr.Button("Create Character", variant="primary", size="lg")
        components['create_output'] = gr.Textbox(label="Status", interactive=False)

        gr.Markdown("""
        ---

        **Note:** Equipment and spells will be automatically assigned based on your class.
        Character images can be added later via the GAN generation feature (coming soon).
        """)

    return components
