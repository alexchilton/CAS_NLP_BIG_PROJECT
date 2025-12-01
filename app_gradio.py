#!/usr/bin/env python3
"""
D&D Character-Aware Game - Gradio Web Interface

Web UI for playing D&D with RAG-enhanced AI GM and character tracking.
"""

import os
# Suppress tokenizer warning
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import gradio as gr
import json
from pathlib import Path

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.character_creator import Character
from dnd_rag_system.systems.gm_dialogue import GameMaster


# Initialize system
print("🎲 Initializing D&D RAG System...")
db = ChromaDBManager()
gm = GameMaster(db)

# Pre-made characters
THORIN = Character(
    name="Thorin Stormshield",
    race="Dwarf",
    character_class="Fighter",
    level=3,
    strength=16,
    dexterity=12,
    constitution=16,
    intelligence=10,
    wisdom=13,
    charisma=8,
    hit_points=28,
    armor_class=18,
    proficiency_bonus=2,
    background="Soldier",
    alignment="Lawful Good",
    race_traits=["Dwarven Resilience", "Darkvision"],
    class_features=["Fighting Style: Defense", "Second Wind", "Action Surge"],
    proficiencies=["All armor", "All weapons", "Shields"],
    equipment=["Longsword", "Shield", "Plate Armor", "Backpack", "50 GP"],
    spells=[]
)

ELARA = Character(
    name="Elara Moonwhisper",
    race="Elf",
    character_class="Wizard",
    level=2,
    strength=8,
    dexterity=14,
    constitution=12,
    intelligence=17,
    wisdom=13,
    charisma=10,
    hit_points=14,
    armor_class=12,
    proficiency_bonus=2,
    background="Sage",
    alignment="Neutral Good",
    race_traits=["Darkvision", "Fey Ancestry"],
    class_features=["Spellcasting", "Arcane Recovery"],
    proficiencies=["Daggers", "Quarterstaffs", "Light crossbows"],
    equipment=["Quarterstaff", "Spellbook", "Component Pouch", "Scholar's Pack"],
    spells=["Fire Bolt", "Mage Hand", "Magic Missile", "Shield"]
)

# Global state
current_character = None
conversation_history = []


def load_character(character_choice):
    """Load selected character and update context."""
    global current_character, conversation_history

    conversation_history = []

    if character_choice == "Thorin Stormshield (Dwarf Fighter)":
        current_character = THORIN
    else:
        current_character = ELARA

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

    # Return character sheet
    return format_character_sheet(), "", []


def format_character_sheet():
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


def chat(message, history):
    """Handle chat messages."""
    global conversation_history

    if not current_character:
        return history + [("Please select a character first!", "")]

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
            return history + [(message, help_text)]

        elif cmd == "/context":
            context_text = gm.session.context
            return history + [(message, f"**Current Context:**\n\n{context_text}")]

        elif cmd == "/stats":
            stats = format_character_sheet()
            return history + [(message, stats)]

        elif cmd.startswith("/rag "):
            query = cmd[5:].strip()
            if query:
                results = gm.search_rag(query, n_results=2)
                formatted = gm.format_rag_context(results)
                return history + [(message, f"**RAG Search Results:**\n\n{formatted}")]
            else:
                return history + [(message, "Usage: `/rag <query>` (e.g., `/rag magic missile`)")]

        else:
            return history + [(message, f"Unknown command: {cmd}\nType `/help` for available commands")]

    # Generate GM response
    try:
        response = gm.generate_response(message, use_rag=True)
        conversation_history.append((message, response))
        return history + [(message, response)]
    except Exception as e:
        error_msg = f"Error: {str(e)}\n\nMake sure Ollama is running and the model is installed:\n`ollama pull hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M`"
        return history + [(message, error_msg)]


def clear_history():
    """Clear conversation history."""
    global conversation_history
    conversation_history = []
    return []


# Create Gradio interface
with gr.Blocks(title="D&D RAG Game Master") as demo:
    gr.Markdown("""
    # 🎲 D&D Character-Aware Game Master

    Play D&D with an AI Game Master powered by RAG (Retrieval-Augmented Generation) and the Qwen3-4B-RPG-Roleplay model.

    **How to Play:**
    1. Select a character
    2. Type your actions (e.g., "I look around", "I cast Magic Missile at the goblin")
    3. Use `/help` to see available commands
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## Character Selection")

            character_dropdown = gr.Dropdown(
                choices=["Thorin Stormshield (Dwarf Fighter)", "Elara Moonwhisper (Elf Wizard)"],
                value="Thorin Stormshield (Dwarf Fighter)",
                label="Choose Your Character"
            )

            load_btn = gr.Button("Load Character", variant="primary")

            gr.Markdown("---")

            character_sheet = gr.Markdown(format_character_sheet())

        with gr.Column(scale=2):
            gr.Markdown("## Game Session")

            chatbot = gr.Chatbot(
                height=500,
                label="Game Master",
                show_label=True,
                avatar_images=(None, "🎭")
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
    - "I cast Magic Missile at the goblin" (Elara)
    - "I attack with my longsword" (Thorin)

    ### 🔍 RAG Commands
    - `/rag Magic Missile` - Look up spell details
    - `/rag Goblin` - Look up monster stats
    - `/rag Fighter` - Look up class features

    **Powered by:** ChromaDB RAG + Ollama (Qwen3-4B-RPG-Roleplay-V2)
    """)

    # Event handlers
    load_btn.click(
        load_character,
        inputs=[character_dropdown],
        outputs=[character_sheet, msg_input, chatbot]
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


if __name__ == "__main__":
    # Load default character
    load_character("Thorin Stormshield (Dwarf Fighter)")

    # Launch
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
