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

        gr.Markdown("---")

        # ── Avatar Generator ──────────────────────────────────────────────────
        gr.Markdown("## Character Portrait")
        gr.Markdown("*Generate a portrait using Stable Diffusion (SDXL-Turbo). First run downloads ~6 GB; subsequent runs are fast.*")

        with gr.Row():
            with gr.Column(scale=1):
                components['avatar_mode'] = gr.Radio(
                    choices=["Auto (from character stats)", "Custom"],
                    value="Auto (from character stats)",
                    label="Generation mode",
                )

                with gr.Column(visible=False) as custom_col:
                    gr.Markdown("#### Customize your portrait")
                    with gr.Row():
                        components['avatar_hair']  = gr.Textbox(label="Hair color & style", placeholder="e.g. long silver braids")
                        components['avatar_eyes']  = gr.Textbox(label="Eye color", placeholder="e.g. amber")
                    with gr.Row():
                        components['avatar_skin']  = gr.Textbox(label="Skin / complexion", placeholder="e.g. tanned, scaled green")
                        components['avatar_mood']  = gr.Textbox(label="Expression / mood", placeholder="e.g. fierce, serene", value="determined")
                    components['avatar_clothes'] = gr.Textbox(label="Clothing details", placeholder="e.g. torn battle robes, ornate noble armor")
                    components['avatar_env']     = gr.Textbox(label="Environment / background", placeholder="e.g. misty forest, torch-lit dungeon", value="dramatic fantasy backdrop")
                    components['avatar_style']   = gr.Dropdown(
                        choices=[
                            "bright heroic (classic D&D art)",
                            "realistic painterly (dark fantasy)",
                            "anime / manga inspired",
                            "gritty grimdark",
                            "watercolor storybook",
                        ],
                        value="bright heroic (classic D&D art)",
                        label="Art style",
                    )
                    components['avatar_extra'] = gr.Textbox(label="Anything else (optional)", placeholder="e.g. glowing runes on skin")

                components['custom_col'] = custom_col

                components['avatar_btn'] = gr.Button("Generate Portrait", variant="primary")
                components['avatar_status'] = gr.Textbox(label="Generation status", interactive=False, lines=2)

            with gr.Column(scale=1):
                components['avatar_image'] = gr.Image(
                    label="Generated Portrait",
                    type="filepath",
                    interactive=False,
                    height=400,
                )

    return components
