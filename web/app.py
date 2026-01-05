#!/usr/bin/env python3
"""
D&D Character-Aware Game - Gradio Web Interface (HF Spaces Version)

Web UI for playing D&D with RAG-enhanced AI GM and character tracking.
Uses Hugging Face Inference API instead of local Ollama.
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
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster

# Initialize system
print("🎲 Initializing D&D RAG System...")
db = ChromaDBManager()

# Get HF token from environment (only needed if USE_HF_API=true)
hf_token = os.getenv("HF_TOKEN")
use_hf = os.getenv("USE_HF_API", "false").lower() == "true"

if use_hf and not hf_token:
    print("⚠️ Warning: USE_HF_API=true but HF_TOKEN not found. Set it in Space settings.")

gm = GameMaster(db, hf_token=hf_token)

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

**Information:**
- `/help` - Show this help
- `/stats` - Show character stats
- `/context` - Show current scene context
- `/rag <query>` - Search D&D rules (e.g., `/rag fireball`)

**World Navigation:**
- `/map` - Show world map and discovered locations
- `/explore` - Discover new locations from current area
- `/travel <location>` - Travel to a connected location

**Shopping:**
- `/buy <item>` - Purchase an item from a shop
- `/sell <item>` - Sell an item from your inventory

**Items & Potions:**
- `/use <item>` - Use a potion or item (e.g., `/use healing potion`)

**Spellcasting:**
- `/cast <spell>` - Cast a spell on yourself (e.g., `/cast shield`)
- `/cast <spell> on <target>` - Cast a spell on a target (e.g., `/cast cure wounds on Thorin`)

**Rest & Recovery:**
- `/rest` or `/short_rest` - Take a short rest (1 hour, spend hit dice to heal)
- `/long_rest` - Take a long rest (8 hours, restore all HP and spell slots)

**Combat:**
- `/start_combat <enemies>` - Start combat with initiative rolls
- `/next_turn` or `/next` - Advance to next turn in combat
- `/initiative` - Show initiative tracker
- `/end_combat` - End combat

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
        error_msg = f"Error: {str(e)}\n\nMake sure HF_TOKEN is set in Space settings."
        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_msg}
        ]


def clear_history():
    """Clear conversation history."""
    global conversation_history
    conversation_history = []
    return []


# Create Gradio interface
mode_text = "🌐 Hugging Face API" if use_hf else "🖥️ Local Ollama"

with gr.Blocks(title="D&D RAG Game Master") as demo:
    gr.Markdown(f"""
    # 🎲 D&D Character-Aware Game Master

    Play D&D with an AI Game Master powered by RAG (Retrieval-Augmented Generation) and Qwen3-4B-RPG-Roleplay-V2.

    **Mode:** {mode_text}

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
                gr.Markdown("**Quick Commands:** `/help` | `/stats` | `/map` | `/explore` | `/buy <item>` | `/sell <item>`")

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

    **Powered by:** ChromaDB RAG + Hugging Face (Qwen2.5-14B-Instruct)
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
    demo.launch()
