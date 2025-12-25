#!/usr/bin/env python3
"""
D&D Character-Aware Game - Gradio Web Interface

Web UI for playing D&D with RAG-enhanced AI GM and character tracking.
Includes character creation, loading, and image display.
"""

import os
# Suppress tokenizer warning
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import gradio as gr
import json
import random
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import asdict

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.character_creator import Character, CharacterCreator
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.config import settings

# Initialize system
print("🎲 Initializing D&D RAG System...")
db = ChromaDBManager()
gm = GameMaster(db)

# Paths
CHARACTERS_DIR = Path(__file__).parent.parent / "characters"
CHARACTERS_DIR.mkdir(exist_ok=True)

# Global state
current_character = None
conversation_history = []


def load_character_from_json(filepath: Path) -> Optional[Character]:
    """Load character from JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return Character(**data)
    except Exception as e:
        print(f"Error loading character from {filepath}: {e}")
        return None


def save_character_to_json(character: Character, filename: str) -> str:
    """Save character to JSON file."""
    filepath = CHARACTERS_DIR / filename
    try:
        with open(filepath, 'w') as f:
            json.dump(asdict(character), f, indent=2)
        return str(filepath)
    except Exception as e:
        return f"Error saving character: {e}"


def get_available_characters() -> List[str]:
    """Get list of available character files."""
    characters = []

    # Load pre-made characters
    thorin_path = CHARACTERS_DIR / "thorin_stormshield.json"
    elara_path = CHARACTERS_DIR / "elara_moonwhisper.json"

    if thorin_path.exists():
        characters.append("Thorin Stormshield (Dwarf Fighter)")
    if elara_path.exists():
        characters.append("Elara Moonwhisper (Elf Wizard)")

    # Load custom characters
    for json_file in CHARACTERS_DIR.glob("*.json"):
        if json_file.name not in ["thorin_stormshield.json", "elara_moonwhisper.json"]:
            char = load_character_from_json(json_file)
            if char:
                characters.append(f"{char.name} ({char.race} {char.character_class})")

    return characters


def load_character(character_choice: str) -> Tuple[str, str, list, Optional[str]]:
    """Load selected character and update context."""
    global current_character, conversation_history

    conversation_history = []

    # Map character choice to file
    if "Thorin" in character_choice:
        filepath = CHARACTERS_DIR / "thorin_stormshield.json"
    elif "Elara" in character_choice:
        filepath = CHARACTERS_DIR / "elara_moonwhisper.json"
    else:
        # Try to find by character name
        name = character_choice.split("(")[0].strip()
        filepath = CHARACTERS_DIR / f"{name.lower().replace(' ', '_')}.json"

    current_character = load_character_from_json(filepath)

    if not current_character:
        return "Error loading character", "", [], None

    # Set GM context
    char = current_character
    mods = char.get_modifiers()

    context = f"""The player is {char.name}, a level {char.level} {char.race} {char.character_class}.

PLAYER CHARACTER STATS:
- HP: {char.hit_points}/{char.hit_points}  |  AC: {char.armor_class}  |  Prof Bonus: +{char.proficiency_bonus}
- STR: {char.strength} ({mods['strength']:+d})  |  DEX: {char.dexterity} ({mods['dexterity']:+d})  |  CON: {char.constitution} ({mods['constitution']:+d})
- INT: {char.intelligence} ({mods['intelligence']:+d})  |  WIS: {char.wisdom} ({mods['wisdom']:+d})  |  CHA: {char.charisma} ({mods['charisma']:+d})

EQUIPMENT: {', '.join(char.equipment[:5])}
"""

    if char.spells:
        context += f"\nSPELLS: {', '.join(char.spells[:5])}"

    gm.set_context(context)

    # Get character image if exists
    char_image = None
    if char.image_path and Path(char.image_path).exists():
        char_image = char.image_path

    # Return character sheet, clear input, empty chat, and image
    return format_character_sheet(), "", [], char_image


def format_character_sheet() -> str:
    """Format character sheet for display."""
    if not current_character:
        return "No character selected"

    char = current_character
    mods = char.get_modifiers()

    sheet = f"""# {char.name}
**{char.race} {char.character_class}, Level {char.level}**
*{char.background} | {char.alignment}*

---

### Combat Stats
- **HP**: {char.hit_points}
- **AC**: {char.armor_class}
- **Proficiency Bonus**: +{char.proficiency_bonus}

### Ability Scores
| Ability | Score | Modifier |
|---------|-------|----------|
| STR | {char.strength} | {mods['strength']:+d} |
| DEX | {char.dexterity} | {mods['dexterity']:+d} |
| CON | {char.constitution} | {mods['constitution']:+d} |
| INT | {char.intelligence} | {mods['intelligence']:+d} |
| WIS | {char.wisdom} | {mods['wisdom']:+d} |
| CHA | {char.charisma} | {mods['charisma']:+d} |

### Equipment
{chr(10).join('- ' + item for item in char.equipment)}

"""

    if char.spells:
        sheet += f"""### Spells
{chr(10).join('- ' + spell for spell in char.spells)}
"""

    return sheet


def create_character(name: str, race: str, char_class: str, background: str,
                     alignment: str, str_val: int, dex_val: int, con_val: int,
                     int_val: int, wis_val: int, cha_val: int) -> Tuple[str, str]:
    """Create a new character with given parameters."""
    global current_character

    if not name:
        return "❌ Please enter a character name", gr.update()

    # Create character
    character = Character(
        name=name,
        race=race,
        character_class=char_class,
        level=1,
        strength=str_val,
        dexterity=dex_val,
        constitution=con_val,
        intelligence=int_val,
        wisdom=wis_val,
        charisma=cha_val,
        background=background,
        alignment=alignment
    )

    # Calculate derived stats
    hit_die_map = {
        "Wizard": 6, "Sorcerer": 6,
        "Rogue": 8, "Bard": 8, "Cleric": 8, "Druid": 8, "Monk": 8, "Warlock": 8,
        "Fighter": 10, "Paladin": 10, "Ranger": 10,
        "Barbarian": 12
    }
    hit_die = hit_die_map.get(char_class, 8)
    character.hit_points = character.calculate_hit_points(hit_die)

    dex_mod = character.get_ability_modifier(dex_val)
    character.armor_class = 10 + dex_mod

    # Add basic equipment
    equipment_map = {
        "Fighter": ["Longsword", "Shield", "Chainmail", "Backpack", "50 GP"],
        "Wizard": ["Quarterstaff", "Spellbook", "Robes", "Component Pouch", "25 GP"],
        "Rogue": ["Shortsword", "Leather Armor", "Thieves' Tools", "Backpack", "40 GP"],
        "Cleric": ["Mace", "Shield", "Chainmail", "Holy Symbol", "30 GP"],
        "Paladin": ["Longsword", "Shield", "Plate Armor", "Holy Symbol", "40 GP"],
        "Ranger": ["Longbow", "Arrows (20)", "Leather Armor", "Backpack", "40 GP"],
        "Barbarian": ["Greataxe", "Javelin (4)", "Leather Armor", "Backpack", "50 GP"],
        "Bard": ["Rapier", "Lute", "Leather Armor", "Backpack", "35 GP"],
        "Sorcerer": ["Quarterstaff", "Component Pouch", "Robes", "Backpack", "30 GP"],
        "Warlock": ["Dagger", "Component Pouch", "Leather Armor", "Backpack", "35 GP"],
        "Druid": ["Quarterstaff", "Druidic Focus", "Leather Armor", "Backpack", "30 GP"],
        "Monk": ["Quarterstaff", "Darts (10)", "Robes", "Backpack", "20 GP"]
    }
    character.equipment = equipment_map.get(char_class, ["Basic gear", "50 GP"])

    # Save character
    filename = f"{name.lower().replace(' ', '_')}.json"
    save_result = save_character_to_json(character, filename)

    # Set as current character
    current_character = character

    # Update character list
    new_choices = get_available_characters()

    return (
        f"✅ Character '{name}' created successfully!\nSaved to: {save_result}",
        gr.update(choices=new_choices, value=f"{name} ({race} {char_class})")
    )


def chat(message: str, history: list) -> list:
    """Handle chat messages."""
    global conversation_history

    if not current_character:
        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": "⚠️ Please load a character first"}
        ]

    if not message.strip():
        return history

    # Handle special commands
    if message.startswith("/"):
        cmd = message.lower().strip()

        if cmd == "/help":
            help_text = """**Available Commands:**
- `/help` - Show this help
- `/context` - Show current scene context
- `/stats` - Show character stats
- `/rag <query>` - Search D&D rules (e.g., `/rag fireball`)

Otherwise, just type your action and press Enter!"""
            return history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": help_text}
            ]

        elif cmd == "/context":
            context_text = gm.session.context
            return history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": f"**Current Context:**\n\n{context_text}"}
            ]

        elif cmd == "/stats":
            stats = format_character_sheet()
            return history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": stats}
            ]

        elif cmd.startswith("/rag "):
            query = cmd[5:].strip()
            if query:
                results = gm.search_rag(query, n_results=2)
                formatted = gm.format_rag_context(results)
                return history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": f"**RAG Search Results:**\n\n{formatted}"}
                ]
            else:
                return history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "Usage: `/rag <query>` (e.g., `/rag magic missile`)"}
                ]

        else:
            return history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": f"Unknown command: {cmd}\nType `/help` for available commands"}
            ]

    # Generate GM response
    try:
        response = gm.generate_response(message, use_rag=True)
        conversation_history.append((message, response))
        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response}
        ]
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        # Only add Ollama instructions if running locally
        if not (os.getenv("SPACE_ID") or os.getenv("SPACE_AUTHOR_NAME") or os.getenv("HF_SPACE")):
            error_msg += "\n\nMake sure Ollama is running and the model is installed:\n`ollama pull hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M`"
        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_msg}
        ]


def clear_history() -> list:
    """Clear conversation history."""
    global conversation_history
    conversation_history = []
    return []


def roll_random_stats() -> Tuple[int, int, int, int, int, int]:
    """
    Roll random ability scores using 3d6 method.

    Returns tuple of (STR, DEX, CON, INT, WIS, CHA)
    """
    def roll_3d6():
        return sum(random.randint(1, 6) for _ in range(3))

    return (
        roll_3d6(),  # Strength
        roll_3d6(),  # Dexterity
        roll_3d6(),  # Constitution
        roll_3d6(),  # Intelligence
        roll_3d6(),  # Wisdom
        roll_3d6(),  # Charisma
    )


# Create Gradio interface
with gr.Blocks(title="D&D RAG Game Master") as demo:
    gr.Markdown("""
    # 🎲 D&D Character-Aware Game Master

    Play D&D with an AI Game Master powered by RAG (Retrieval-Augmented Generation).

    **Features:**
    - Play as pre-made characters (Thorin, Elara)
    - Create your own custom characters
    - Character images (placeholder for future GAN generation)
    - RAG-powered rule lookups
    """)

    with gr.Tabs():
        # Tab 1: Play Game
        with gr.Tab("🎮 Play Game"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("## Character")

                    character_dropdown = gr.Dropdown(
                        choices=get_available_characters(),
                        value=get_available_characters()[0] if get_available_characters() else None,
                        label="Choose Your Character"
                    )

                    load_btn = gr.Button("Load Character", variant="primary")

                    # Character Image
                    char_image = gr.Image(
                        label="Character Portrait",
                        type="filepath",
                        interactive=False,
                        height=200
                    )

                    gr.Markdown("*Image will be generated via GAN in future update*")

                    gr.Markdown("---")

                    character_sheet = gr.Markdown("No character loaded")

                with gr.Column(scale=2):
                    gr.Markdown("## Game Session")

                    chatbot = gr.Chatbot(
                        height=500,
                        label="Game Master",
                        show_label=True
                    )

                    with gr.Row():
                        msg_input = gr.Textbox(
                            placeholder="Type your action or command here... (e.g., 'I look around' or '/help')",
                            label="Your Action",
                            show_label=False,
                            scale=4
                        )
                        submit_btn = gr.Button("Send", variant="primary", scale=1)

                    with gr.Row():
                        clear_btn = gr.Button("Clear History")
                        gr.Markdown("**Quick Commands:** `/help` | `/context` | `/stats` | `/rag <query>`")

            gr.Markdown("""
            ---

            ### 📖 Example Actions
            - "I look around and check my surroundings"
            - "I draw my weapon and prepare for combat"
            - "I cast Magic Missile at the goblin"
            - "I attack with my longsword"

            ### 🔍 RAG Commands
            - `/rag Magic Missile` - Look up spell details
            - `/rag Goblin` - Look up monster stats
            - `/rag Fighter` - Look up class features
            """)

        # Tab 2: Create Character
        with gr.Tab("✨ Create Character"):
            gr.Markdown("""
            ## Create Your D&D Character

            Fill in the fields below to create a new character. Your character will be saved and available in the character dropdown.
            """)

            with gr.Row():
                with gr.Column():
                    char_name = gr.Textbox(label="Character Name", placeholder="e.g., Gandalf the Grey")

                    with gr.Row():
                        char_race = gr.Dropdown(
                            choices=settings.DND_RACES,
                            value="Human",
                            label="Race"
                        )
                        char_class = gr.Dropdown(
                            choices=settings.DND_CLASSES,
                            value="Fighter",
                            label="Class"
                        )

                    with gr.Row():
                        char_background = gr.Textbox(label="Background", placeholder="e.g., Soldier, Sage, Folk Hero")
                        char_alignment = gr.Textbox(label="Alignment", placeholder="e.g., Lawful Good, Chaotic Neutral")

                with gr.Column():
                    gr.Markdown("### Ability Scores")
                    gr.Markdown("*Standard array: 15, 14, 13, 12, 10, 8 | Or roll random with 3d6*")

                    roll_stats_btn = gr.Button("🎲 Roll Random Stats (3d6)", variant="secondary", size="sm")

                    with gr.Row():
                        str_slider = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Strength")
                        dex_slider = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Dexterity")

                    with gr.Row():
                        con_slider = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Constitution")
                        int_slider = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Intelligence")

                    with gr.Row():
                        wis_slider = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Wisdom")
                        cha_slider = gr.Slider(minimum=3, maximum=18, value=10, step=1, label="Charisma")

            create_btn = gr.Button("Create Character", variant="primary", size="lg")
            create_output = gr.Textbox(label="Status", interactive=False)

            gr.Markdown("""
            ---

            **Note:** Equipment and spells will be automatically assigned based on your class.
            Character images can be added later via the GAN generation feature (coming soon).
            """)

    # Event handlers - Play Game Tab
    load_btn.click(
        load_character,
        inputs=[character_dropdown],
        outputs=[character_sheet, msg_input, chatbot, char_image]
    )

    submit_btn.click(
        chat,
        inputs=[msg_input, chatbot],
        outputs=[chatbot]
    ).then(
        lambda: "",
        outputs=[msg_input]
    )

    msg_input.submit(
        chat,
        inputs=[msg_input, chatbot],
        outputs=[chatbot]
    ).then(
        lambda: "",
        outputs=[msg_input]
    )

    clear_btn.click(
        clear_history,
        outputs=[chatbot]
    )

    # Event handlers - Create Character Tab
    roll_stats_btn.click(
        roll_random_stats,
        inputs=[],
        outputs=[str_slider, dex_slider, con_slider, int_slider, wis_slider, cha_slider]
    )

    create_btn.click(
        create_character,
        inputs=[
            char_name, char_race, char_class, char_background, char_alignment,
            str_slider, dex_slider, con_slider, int_slider, wis_slider, cha_slider
        ],
        outputs=[create_output, character_dropdown]
    )


if __name__ == "__main__":
    # Launch
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
