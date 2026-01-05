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
from dnd_rag_system.systems.game_state import CharacterState, PartyState, SpellSlots
from dnd_rag_system.systems.racial_bonuses import load_racial_traits, get_racial_bonus_summary
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
party = PartyState(party_name="Adventuring Party")
party_characters = {}  # {char_name: Character} for display
gameplay_mode = "character"  # "character" or "party"

# Starting locations for new games - MIX of peaceful and combat-ready locations!
STARTING_LOCATIONS = [
    # Peaceful locations (for shopping/rest)
    ("The Prancing Pony Inn", "A cozy tavern bustling with travelers and merchants. The smell of roasted meat and ale fills the air. A shopkeeper behind the bar sells basic supplies."),
    ("The Market Square", "A busy marketplace with stalls selling adventuring gear, potions, and supplies. Merchants call out their wares. Perfect for shopping before an adventure!"),
    ("The Town Gates", "The entrance to town, where the road stretches out toward adventure. Guards keep watch. A general store sits just inside the gates."),
    # Combat-ready locations (for immediate action!)
    ("Goblin Cave Entrance", "You stand at the mouth of a dark cave. The stench of unwashed goblins wafts out from the darkness. Crude wooden stakes mark goblin territory. You hear chittering and the clang of crude weapons echoing from within."),
    ("Ancient Ruins", "Crumbling stone pillars rise from overgrown weeds. This was once a great temple, now fallen to ruin. Skeletons and undead are known to haunt these grounds, guarding forgotten treasures."),
    ("Dark Forest Clearing", "You emerge into a small clearing surrounded by ancient, gnarled trees. The forest floor is littered with bones. Fresh wolf tracks circle the area. This is dangerous territory."),
]

# Combat-appropriate locations where monsters would naturally appear
COMBAT_LOCATIONS = [
    ("Goblin Cave Entrance", "You stand at the mouth of a dark cave. The stench of unwashed goblins wafts out from the darkness. Crude wooden stakes mark goblin territory. You hear chittering and the clang of crude weapons echoing from within."),
    ("Ancient Ruins", "Crumbling stone pillars rise from overgrown weeds. This was once a great temple, now fallen to ruin. Skeletons and undead are known to haunt these grounds, guarding forgotten treasures."),
    ("Dark Forest Clearing", "You emerge into a small clearing surrounded by ancient, gnarled trees. The forest floor is littered with bones. Fresh wolf tracks circle the area. This is dangerous territory."),
    ("Abandoned Mine Shaft", "The entrance to an old mining tunnel, long since abandoned. Support beams creak ominously. Miners' tools lie scattered about. Something moves in the shadows - perhaps giant rats, or worse."),
    ("Rocky Mountain Pass", "A narrow path winds between towering cliffs. Loose rocks make footing treacherous. Ogres and trolls are known to ambush travelers here, and you can see crude cave entrances dotting the cliff faces."),
    ("Sunken Graveyard", "An old cemetery, half-swallowed by swamp. Weathered tombstones lean at odd angles. The ground shifts underfoot. On nights like this, the dead sometimes rise from their graves."),
    ("Dragon's Lair Approach", "You stand before a massive cavern carved into the mountainside. Scorch marks blacken the rocks. A pile of charred bones lies near the entrance. The air shimmers with heat, and you hear the deep, rhythmic breathing of something massive within."),
]

# DEBUG TEST SCENARIOS - For manual testing combat/features
# Format: (scenario_name, location_name, npcs_to_spawn, items_to_add)
DEBUG_SCENARIOS = [
    ("Random Start", None, [], []),  # Default - random location
    ("Goblin Fight", "Goblin Cave Entrance", ["Goblin"], []),
    ("Goblin with Treasure", "Goblin Cave Entrance", ["Goblin"], ["Hidden Chest"]),
    ("Goblin Wolf Rider", "Forest Ambush Site", ["Goblin", "Wolf"], ["Rope", "Torch"]),  # Multi-enemy test
    ("Wolf Pack", "Dark Forest Clearing", ["Wolf", "Wolf"], []),
    ("Skeleton Guardian", "Ancient Ruins", ["Skeleton"], ["Ancient Sword"]),
    ("Dragon Encounter", "Dragon's Lair Approach", ["Young Red Dragon"], ["Dragon Hoard"]),
    ("Safe Inn", "The Prancing Pony Inn", ["Innkeeper Butterbur"], ["Healing Potion"]),
    ("Shopping District", "The Market Square", ["Merchant", "Blacksmith"], []),
]


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


def delete_character(character_choice: str) -> Tuple[str, gr.update]:
    """
    Delete a character file.

    Args:
        character_choice: Character selection string

    Returns:
        Tuple of (status message, updated dropdown)
    """
    if not character_choice:
        return "⚠️ No character selected", gr.update()

    # Prevent deletion of pre-made characters
    if "Thorin" in character_choice or "Elara" in character_choice:
        return "❌ Cannot delete pre-made characters (Thorin, Elara)", gr.update()

    # Map character choice to file
    try:
        name = character_choice.split("(")[0].strip()
        filepath = CHARACTERS_DIR / f"{name.lower().replace(' ', '_')}.json"

        if filepath.exists():
            filepath.unlink()  # Delete the file

            # Update character list
            new_choices = get_available_characters()
            new_value = new_choices[0] if new_choices else None

            return (
                f"✅ Character '{name}' deleted successfully",
                gr.update(choices=new_choices, value=new_value)
            )
        else:
            return f"❌ Character file not found: {filepath}", gr.update()

    except Exception as e:
        return f"❌ Error deleting character: {e}", gr.update()


def load_character_with_location(character_choice: str, location_name: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Load character and set specific starting location (for testing).

    Args:
        character_choice: Character selection string
        location_name: Optional location name (e.g., "Goblin Cave Entrance"). If None, uses random.

    Returns:
        Tuple of (location_name, location_desc, character_name)
    """
    global current_character, conversation_history, gameplay_mode

    conversation_history = []
    gameplay_mode = "character"

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
        raise ValueError(f"Could not load character from {filepath}")

    # Create CharacterState and load into GameSession for Reality Check
    char = current_character
    char_state = CharacterState(
        character_name=char.name,
        max_hp=char.hit_points,
        current_hp=char.hit_points,
        level=char.level,
        inventory={item: 1 for item in char.equipment},  # Convert equipment list to inventory dict
        gold=getattr(char, 'gold', 50)  # Load gold from character JSON or default to 50
    )

    # Add race and class for personality-driven responses
    char_state.race = char.race
    char_state.character_class = char.character_class

    # Add spells to character state for spell validation
    if char.spells:
        char_state.spells = char.spells  # Add spells attribute dynamically

    # Load into game session
    gm.session.base_character_stats[char.name] = char  # Store base character stats by name
    gm.session.character_state = char_state
    gm.session.npcs_present = []  # Clear NPCs when loading new character

    # Set starting location - check environment variable first, then parameter, then random
    env_location = os.getenv("TEST_START_LOCATION")
    env_location_desc = os.getenv("TEST_LOCATION_DESC")

    if env_location:
        location_name = env_location
        print(f"🧪 Test mode: Starting at {location_name} (from TEST_START_LOCATION env var)")

    if location_name:
        # Search for location in all available locations
        all_locations = STARTING_LOCATIONS + COMBAT_LOCATIONS
        found_location = None
        for loc_name, loc_desc in all_locations:
            if loc_name.lower() == location_name.lower() or location_name.lower() in loc_name.lower():
                found_location = (loc_name, loc_desc)
                break

        if found_location:
            location_name, location_desc = found_location
        else:
            # Custom location - check for custom description or create generic one
            if env_location_desc:
                location_desc = env_location_desc
                print(f"🧪 Using custom location description from TEST_LOCATION_DESC")
            else:
                location_desc = f"You find yourself at {location_name}. The area is mysterious and unknown."
                print(f"🧪 Created custom location: {location_name}")
    else:
        # Random selection
        location_name, location_desc = random.choice(STARTING_LOCATIONS)

    gm.set_location(location_name, location_desc)

    # NPC spawning logic:
    # 1. If TEST_NPCS is set → use those (deterministic testing)
    # 2. Else if town/shop/inn → add friendly NPCs (merchants, shopkeepers)
    # 3. Else → no NPCs (player discovers combat encounters naturally)

    env_npcs = os.getenv("TEST_NPCS")
    if env_npcs:
        # TEST MODE: Use deterministic NPCs for testing
        test_npcs = [npc.strip() for npc in env_npcs.split(',')]
        for npc in test_npcs:
            if npc and npc not in gm.session.npcs_present:
                gm.session.npcs_present.append(npc)
        print(f"🧪 Added NPCs from TEST_NPCS: {test_npcs}")
    else:
        # NORMAL GAMEPLAY: Add friendly NPCs to towns/shops/inns
        friendly_location_npcs = {
            "The Prancing Pony Inn": ["Innkeeper Butterbur", "Traveling Merchant"],
            "The Market Square": ["Merchant", "Blacksmith", "Potion Seller"],
            "The Town Gates": ["Town Guard", "General Store Shopkeeper"],
        }

        for loc_key, npcs in friendly_location_npcs.items():
            if loc_key.lower() in location_name.lower() or location_name.lower() in loc_key.lower():
                for npc in npcs:
                    if npc not in gm.session.npcs_present:
                        gm.session.npcs_present.append(npc)
                print(f"🏘️ Added friendly NPCs to {location_name}: {npcs}")
                break

    # Add items to location if specified via TEST_ITEMS environment variable
    # Format: "Hidden Chest:Magic Ring of Protection, Healing Potion"
    # This allows setting up test scenarios like "hidden chest with magic ring"
    env_items = os.getenv("TEST_ITEMS")
    if env_items:
        # Parse items - can be simple list or container:items format
        if ':' in env_items:
            # Format: "Hidden Chest:Magic Ring, Gold Coins"
            container, items_str = env_items.split(':', 1)
            items = [item.strip() for item in items_str.split(',')]

            # Add container to location description
            if "hidden chest" in container.lower():
                gm.session.scene_description += f"\n\n🎁 There appears to be a {container} here."
            else:
                gm.session.scene_description += f"\n\n{container} can be found here."

            # Track items in session (for reality check)
            if not hasattr(gm.session, 'location_items'):
                gm.session.location_items = {}
            gm.session.location_items[container] = items
            print(f"🧪 Added {container} with items: {items}")
        else:
            # Simple comma-separated items
            items = [item.strip() for item in env_items.split(',')]
            if not hasattr(gm.session, 'location_items'):
                gm.session.location_items = {}
            gm.session.location_items['ground'] = items
            print(f"🧪 Added items to location: {items}")

    return location_name, location_desc, char.name


def load_character(character_choice: str) -> Tuple[str, str, list, Optional[str]]:
    """Load selected character and update context (Gradio UI wrapper)."""
    try:
        location_name, location_desc, char_name = load_character_with_location(character_choice)
    except ValueError as e:
        return f"Error loading character: {e}", "", [], None

    char = current_character
    if not char:
        return "Error loading character", "", [], None

    # Get character state from GM session
    char_state = gm.session.character_state

    # Set GM context
    mods = char.get_modifiers()

    # Use dynamic HP from character state
    context = f"""The player is {char.name}, a level {char.level} {char.race} {char.character_class}.

PLAYER CHARACTER STATS:
- HP: {char_state.current_hp}/{char_state.max_hp}  |  AC: {char.armor_class}  |  Prof Bonus: +{char.proficiency_bonus}
- STR: {char.strength} ({mods['strength']:+d})  |  DEX: {char.dexterity} ({mods['dexterity']:+d})  |  CON: {char.constitution} ({mods['constitution']:+d})
- INT: {char.intelligence} ({mods['intelligence']:+d})  |  WIS: {char.wisdom} ({mods['wisdom']:+d})  |  CHA: {char.charisma} ({mods['charisma']:+d})

EQUIPMENT: {', '.join(char.equipment[:5])}
INVENTORY: {', '.join([f"{item} ({qty})" for item, qty in char_state.inventory.items() if item not in char.equipment][:5]) or "Empty"}
"""

    if char.spells:
        context += f"\nSPELLS: {', '.join(char.spells[:5])}"

    gm.set_context(context)

    # Get character image if exists
    char_image = None
    if char.image_path and Path(char.image_path).exists():
        char_image = char.image_path

    # Create welcome message with starting location
    welcome_message = f"""**Welcome, {char.name}!**

You find yourself in **{location_name}**.

{location_desc}

You have **{char_state.gold} gold pieces** in your purse."""

    # Add NPC warning if NPCs are present
    if gm.session.npcs_present:
        npc_list = ", ".join(gm.session.npcs_present)
        welcome_message += f"\n\n⚠️ **You see:** {npc_list}!"

    welcome_message += """\n\nWhat would you like to do?

*Type `/help` to see available commands, or describe your action!*"""

    # Return character sheet, clear input, chat with welcome message, and image
    initial_chat = [{"role": "assistant", "content": welcome_message}]
    return format_character_sheet(), "", initial_chat, char_image


def load_character_with_debug(character_choice: str, scenario_choice: Optional[str]) -> Tuple[str, str, list, Optional[str]]:
    """
    Load character - routes to debug scenario if one is selected, otherwise normal load.
    
    Args:
        character_choice: Which character to load
        scenario_choice: Optional debug scenario (e.g., "Goblin Fight")
        
    Returns:
        Tuple of (character_sheet, status_message, chat_history, character_image)
    """
    global conversation_history
    
    # Clear global conversation history to prevent old messages from showing
    conversation_history = []
    
    # If no scenario selected or not in debug mode, use normal load
    if not scenario_choice or scenario_choice == "":
        return load_character(character_choice)
    
    # Load debug scenario
    global current_character
    
    # Find the scenario
    scenario = None
    for s in DEBUG_SCENARIOS:
        if s[0] == scenario_choice:
            scenario = s
            break
    
    if not scenario:
        return ("", "Invalid scenario", [], None)
    
    scenario_name, location_name, npcs, items = scenario
    
    # CRITICAL: Clear old session state before loading new scenario
    # This prevents Goblin/Wolf from previous scenario appearing in Shopping District
    gm.session.npcs_present = []  # Clear all NPCs
    gm.combat_manager.end_combat()  # End any active combat
    gm.message_history = []  # Clear chat history
    
    # Load character with specific location
    load_character_with_location(character_choice, location_name)
    
    # Add NPCs for this scenario (fresh list, not appending to old)
    gm.session.npcs_present = npcs.copy()  # Replace, don't append
    
    # Add items to location's persistent tracking
    if items:
        # Get or create Location object for current location
        current_loc = gm.session.get_current_location_obj()
        if current_loc:
            # Add items to location's available_items list
            for item in items:
                current_loc.add_item(item)
        else:
            # Fallback: use session-level tracking (deprecated but for compatibility)
            gm.session.location_items = items.copy()
    
    # Set GM context
    char = current_character
    mods = char.get_modifiers()
    char_state = gm.session.character_state
    
    context = f"""The player is {char.name}, a level {char.level} {char.race} {char.character_class}.

PLAYER CHARACTER STATS:
- HP: {char_state.current_hp}/{char_state.max_hp}  |  AC: {char.armor_class}  |  Prof Bonus: +{char.proficiency_bonus}
- STR: {char.strength} ({mods['strength']:+d})  |  DEX: {char.dexterity} ({mods['dexterity']:+d})  |  CON: {char.constitution} ({mods['constitution']:+d})
- INT: {char.intelligence} ({mods['intelligence']:+d})  |  WIS: {char.wisdom} ({mods['wisdom']:+d})  |  CHA: {char.charisma} ({mods['charisma']:+d})

EQUIPMENT: {', '.join(char.equipment[:5])}
INVENTORY: {', '.join([f"{item} ({qty})" for item, qty in char_state.inventory.items() if item not in char.equipment][:5]) or "Empty"}
"""
    
    if char.spells:
        context += f"\nSPELLS: {', '.join(char.spells[:5])}"
    
    gm.set_context(context)
    
    # Create welcome message
    location = gm.session.current_location
    desc = gm.session.scene_description
    
    npcs_text = f"\n⚠️  **You see:** {', '.join(npcs)}!" if npcs else ""
    # Better item display - describe what's available
    if items:
        if len(items) == 1:
            items_text = f"\n🎒 **You notice:** A {items[0]} is here."
        else:
            items_list = ', '.join(items[:-1]) + f" and {items[-1]}"
            items_text = f"\n🎒 **You notice:** {items_list} are here."
    else:
        items_text = ""
    
    welcome_message = f"""🧪 **DEBUG SCENARIO: {scenario_name}**

Welcome, {char.name}!
You find yourself in **{location}**.
{desc}
{npcs_text}{items_text}

You have **{char_state.gold} gold pieces** in your purse.

What would you like to do?
*Type `/help` to see available commands, or describe your action!*"""

    # Get character image if exists
    char_image = None
    if char.image_path and Path(char.image_path).exists():
        char_image = str(char.image_path)

    # Return character sheet, clear input, chat with welcome message, and image
    initial_chat = [{"role": "assistant", "content": welcome_message}]
    return format_character_sheet(), "", initial_chat, char_image


def load_party_mode() -> Tuple[str, gr.update, list]:
    """Load party mode and set GM context for party-based gameplay."""
    global gameplay_mode, conversation_history

    conversation_history = []
    gameplay_mode = "party"

    if not party_characters:
        return (
            "⚠️ No party members! Please add characters in the Party Management tab first.",
            gr.update(interactive=True),  # Keep msg_input interactive
            []
        )

    # Set random starting location for the party
    location_name, location_desc = random.choice(STARTING_LOCATIONS)
    gm.set_location(location_name, location_desc)

    # Build party context for GM
    party_info = []
    for char_name, char in party_characters.items():
        mods = char.get_modifiers()

        # Get dynamic HP from party state
        char_state = party.get_character(char_name)
        if char_state:
            hp_display = f"{char_state.current_hp}/{char_state.max_hp}"
        else:
            hp_display = f"{char.hit_points}/{char.hit_points}"

        party_info.append(f"""
**{char.name}** - {char.race} {char.character_class}, Level {char.level}
- HP: {hp_display}  |  AC: {char.armor_class}  |  Prof Bonus: +{char.proficiency_bonus}
- STR: {char.strength} ({mods['strength']:+d})  |  DEX: {char.dexterity} ({mods['dexterity']:+d})  |  CON: {char.constitution} ({mods['constitution']:+d})
- INT: {char.intelligence} ({mods['intelligence']:+d})  |  WIS: {char.wisdom} ({mods['wisdom']:+d})  |  CHA: {char.charisma} ({mods['charisma']:+d})
- Equipment: {', '.join(char.equipment[:3])}""")

    context = f"""The party consists of {len(party_characters)} adventurers:

{chr(10).join(party_info)}

Party Gold: {party.gold} GP"""

    gm.set_context(context)

    # Create welcome message for party mode
    party_names = ", ".join(party_characters.keys())
    welcome_message = f"""**🎭 Welcome, Adventurers!**

Your party of {len(party_characters)} finds themselves in **{location_name}**.

**Party Members:** {party_names}

{location_desc}

The party has **{party.gold} gold pieces** in the shared purse.

What would you like your party to do?

*Type `/help` to see available commands, or describe your party's action!*"""

    # Return party summary, interactive input, and welcome message
    initial_chat = [{"role": "assistant", "content": welcome_message}]
    return (
        format_party_sheet(),
        gr.update(interactive=True, value=""),  # Explicitly keep it interactive
        initial_chat  # Add welcome message to chat
    )


def format_party_sheet() -> str:
    """Format party sheet for display in character panel."""
    if not party_characters:
        return "**No Party Loaded**\n\nAdd characters in the Party Management tab."

    sheet = f"# 🎭 Party Mode\n\n"
    sheet += f"**{party.party_name}**\n"
    sheet += f"**Party Size:** {len(party_characters)} adventurer(s)\n"
    sheet += f"**Party Gold:** {party.gold} GP\n\n"
    sheet += "---\n\n"

    for char_name, char in party_characters.items():
        mods = char.get_modifiers()

        # Get dynamic HP from party state
        char_state = party.get_character(char_name)
        if char_state:
            hp_display = f"{char_state.current_hp}/{char_state.max_hp}"
        else:
            hp_display = str(char.hit_points)

        sheet += f"### {char.name}\n"
        sheet += f"*{char.race} {char.character_class}, Level {char.level}*\n"
        sheet += f"- HP: {hp_display} | AC: {char.armor_class}\n"
        sheet += f"- STR {char.strength} ({mods['strength']:+d}) | DEX {char.dexterity} ({mods['dexterity']:+d}) | CON {char.constitution} ({mods['constitution']:+d})\n"
        sheet += f"- INT {char.intelligence} ({mods['intelligence']:+d}) | WIS {char.wisdom} ({mods['wisdom']:+d}) | CHA {char.charisma} ({mods['charisma']:+d})\n\n"

    return sheet


def format_character_sheet() -> str:
    """Format character sheet for display."""
    if not current_character:
        return "No character selected"

    char = current_character
    mods = char.get_modifiers()

    # Get dynamic HP from game state if available
    char_state = gm.session.character_state
    current_hp = char_state.current_hp if char_state else char.hit_points
    max_hp = char_state.max_hp if char_state else char.hit_points
    gold = char_state.gold if char_state and hasattr(char_state, 'gold') else getattr(char, 'gold', 0)

    sheet = f"""# {char.name}
**{char.race} {char.character_class}, Level {char.level}**
*{char.background} | {char.alignment}*

---

### Combat Stats
- **HP**: {current_hp}/{max_hp}
- **AC**: {char.armor_class}
- **Proficiency Bonus**: +{char.proficiency_bonus}
- **Gold**: {gold} GP

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

### Inventory
{chr(10).join('- ' + f"{item} ({qty})" for item, qty in char_state.inventory.items() if item not in char.equipment) if char_state and char_state.inventory else '- Empty'}

"""

    if char.spells:
        sheet += f"""### Spells
{chr(10).join('- ' + spell for spell in char.spells)}
"""

    return sheet


def create_character(name: str, race: str, char_class: str, level: int,
                     alignment: str, background: str, str_val: int, dex_val: int,
                     con_val: int, int_val: int, wis_val: int, cha_val: int) -> Tuple[str, str]:
    """Create a new character with given parameters."""
    global current_character

    if not name:
        return "❌ Please enter a character name", gr.update()

    # Load racial traits and apply bonuses
    racial_traits = load_racial_traits(None, race)  # Use fallback data
    racial_bonuses_applied = ""

    if racial_traits:
        # Apply racial ability score bonuses
        for ability, bonus in racial_traits.ability_increases.items():
            if ability == "strength":
                str_val += bonus
            elif ability == "dexterity":
                dex_val += bonus
            elif ability == "constitution":
                con_val += bonus
            elif ability == "intelligence":
                int_val += bonus
            elif ability == "wisdom":
                wis_val += bonus
            elif ability == "charisma":
                cha_val += bonus

        racial_bonuses_applied = get_racial_bonus_summary(racial_traits)

    # Create character with bonuses applied
    character = Character(
        name=name,
        race=race,
        character_class=char_class,
        level=int(level),
        strength=str_val,
        dexterity=dex_val,
        constitution=con_val,
        intelligence=int_val,
        wisdom=wis_val,
        charisma=cha_val,
        background=background,
        alignment=alignment,
        gold=100  # Starting gold for new characters
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

    # Format success message with racial bonuses
    success_msg = f"✅ Character '{name}' created successfully!\n\nSaved to: {save_result}\n\n"
    if racial_bonuses_applied:
        success_msg += f"{racial_bonuses_applied}"

    return (
        success_msg,
        gr.update(choices=new_choices, value=f"{name} ({race} {char_class})")
    )


def get_initiative_tracker() -> Tuple[str, gr.update]:
    """
    Get initiative tracker display and combat status.

    Returns:
        Tuple of (initiative_display_text, accordion_update)
    """
    if gm.combat_manager.is_in_combat():
        # Get initiative tracker with party info if in party mode
        if gameplay_mode == "party" and party_characters:
            tracker = gm.combat_manager.get_initiative_tracker(gm.session.party)
        else:
            tracker = gm.combat_manager.get_initiative_tracker()

        return tracker, gr.update(visible=True, open=True)
    else:
        return "⚔️ Not currently in combat\n\nUse `/start_combat Goblin, Orc` to begin combat", gr.update(visible=False)


def handle_next_turn(history: list) -> Tuple[list, str, gr.update, str]:
    """
    Handle Next Turn button click.

    Returns:
        Tuple of (updated_history, initiative_display, accordion_update, character_sheet)
    """
    if not gm.combat_manager.is_in_combat():
        return (
            history + [
                {"role": "assistant", "content": "⚠️ Not in combat! Use `/start_combat` to begin."}
            ],
            *get_initiative_tracker(),
                get_current_sheet()
        )

    # Advance turn
    response = gm.generate_response("/next_turn", use_rag=False)

    new_history = history + [
        {"role": "assistant", "content": response}
    ]

    return (new_history, *get_initiative_tracker(),
                get_current_sheet())


def handle_end_combat(history: list) -> Tuple[list, str, gr.update, str]:
    """
    Handle End Combat button click.

    Returns:
        Tuple of (updated_history, initiative_display, accordion_update, character_sheet)
    """
    if not gm.combat_manager.is_in_combat():
        return (
            history + [
                {"role": "assistant", "content": "⚠️ Not in combat!"}
            ],
            *get_initiative_tracker(),
                get_current_sheet()
        )

    # End combat
    response = gm.generate_response("/end_combat", use_rag=False)

    new_history = history + [
        {"role": "assistant", "content": response}
    ]

    return (new_history, *get_initiative_tracker(),
                get_current_sheet())


def get_current_sheet() -> str:
    """Helper to get current character/party sheet based on mode."""
    if gameplay_mode == "party":
        return format_party_sheet()
    else:
        return format_character_sheet()


def chat(message: str, history: list) -> Tuple[list, str, gr.update, str]:
    """
    Handle chat messages.

    Returns:
        Tuple of (updated_history, initiative_display, accordion_update, character_sheet)
    """
    global conversation_history, gameplay_mode

    # Check if in party mode or character mode
    if gameplay_mode == "party":
        if not party_characters:
            return (
                history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "⚠️ Please load party mode first (add characters in Party Management tab)"}
                ],
                *get_initiative_tracker(),
                get_current_sheet()
            )
    else:
        if not current_character:
            return (
                history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "⚠️ Please load a character first"}
                ],
                *get_initiative_tracker(),
                get_current_sheet()
            )

    if not message.strip():
        return (history, *get_initiative_tracker(), get_current_sheet())

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
- `/level_up` - Level up your character (requires enough XP)

**Combat:**
- `/start_combat <enemies>` - Start combat with initiative rolls
- `/next_turn` or `/next` - Advance to next turn in combat
- `/initiative` - Show initiative tracker
- `/end_combat` - End combat

Otherwise, just type your action and press Enter!"""
            return (
                history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": help_text}
                ],
                *get_initiative_tracker(),
                get_current_sheet()
            )

        elif cmd == "/context":
            # Generate fresh context from current character state
            if current_character and gm.session.character_state:
                char = current_character
                char_state = gm.session.character_state
                mods = char.get_modifiers()
                
                fresh_context = f"""The player is {char.name}, a level {char.level} {char.race} {char.character_class}.

PLAYER CHARACTER STATS:
- HP: {char_state.current_hp}/{char_state.max_hp}  |  AC: {char.armor_class}  |  Prof Bonus: +{char.proficiency_bonus}
- STR: {char.strength} ({mods['strength']:+d})  |  DEX: {char.dexterity} ({mods['dexterity']:+d})  |  CON: {char.constitution} ({mods['constitution']:+d})
- INT: {char.intelligence} ({mods['intelligence']:+d})  |  WIS: {char.wisdom} ({mods['wisdom']:+d})  |  CHA: {char.charisma} ({mods['charisma']:+d})

EQUIPMENT: {', '.join(char.equipment[:5])}
INVENTORY: {', '.join([f"{item} ({qty})" for item, qty in char_state.inventory.items() if item not in char.equipment][:5]) or "Empty"}
"""
                if char.spells:
                    fresh_context += f"\nSPELLS: {', '.join(char.spells[:5])}"
            else:
                fresh_context = gm.session.scene_description
            
            return (
                history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": f"**Current Context:**\n\n{fresh_context}"}
                ],
                *get_initiative_tracker(),
                get_current_sheet()
            )

        elif cmd == "/stats":
            if gameplay_mode == "party":
                stats = format_party_sheet()
            else:
                stats = format_character_sheet()
            return (
                history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": stats}
                ],
                *get_initiative_tracker(),
                get_current_sheet()
            )

        elif cmd.startswith("/rag "):
            query = cmd[5:].strip()
            if query:
                results = gm.search_rag(query, n_results=2)
                formatted = gm.format_rag_context(results)
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": f"**RAG Search Results:**\n\n{formatted}"}
                    ],
                    *get_initiative_tracker(),
                get_current_sheet()
                )
            else:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "Usage: `/rag <query>` (e.g., `/rag magic missile`)"}
                    ],
                    *get_initiative_tracker(),
                get_current_sheet()
                )

        # Let other commands (like /buy, /sell, /start_combat, etc.) pass through to GM

    # Generate GM response (handles /buy, /sell, combat commands, and regular actions)
    try:
        response = gm.generate_response(message, use_rag=True)
        conversation_history.append((message, response))
        return (
            history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ],
            *get_initiative_tracker(),
                get_current_sheet()
        )
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        # Only add Ollama instructions if running locally
        if not (os.getenv("SPACE_ID") or os.getenv("SPACE_AUTHOR_NAME") or os.getenv("HF_SPACE")):
            error_msg += "\n\nMake sure Ollama is running and the model is installed:\n`ollama pull hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M`"
        return (
            history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": error_msg}
            ],
            *get_initiative_tracker(),
                get_current_sheet()
        )


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


def add_to_party(character_choices: List[str]) -> str:
    """Add selected characters to the party."""
    global party, party_characters

    if not character_choices:
        return "⚠️ No characters selected"

    added_count = 0
    for choice in character_choices:
        # Map character choice to file
        if "Thorin" in choice:
            filepath = CHARACTERS_DIR / "thorin_stormshield.json"
        elif "Elara" in choice:
            filepath = CHARACTERS_DIR / "elara_moonwhisper.json"
        else:
            name = choice.split("(")[0].strip()
            filepath = CHARACTERS_DIR / f"{name.lower().replace(' ', '_')}.json"

        char = load_character_from_json(filepath)
        if char and char.name not in party_characters:
            # Store Character for display
            party_characters[char.name] = char

            # Create CharacterState for game mechanics
            char_state = CharacterState(
                character_name=char.name,
                max_hp=char.hit_points,
                level=char.level
            )
            party.add_character(char_state)
            added_count += 1

    party_summary = get_party_summary()
    return f"✅ Added {added_count} character(s) to party!\n\n{party_summary}"


def remove_from_party(character_name: str) -> str:
    """Remove a character from the party."""
    global party, party_characters

    if character_name in party_characters:
        del party_characters[character_name]
        party.remove_character(character_name)
        return f"✅ Removed {character_name} from party\n\n{get_party_summary()}"
    else:
        return f"⚠️ {character_name} is not in the party"


def get_party_summary() -> str:
    """Get formatted party summary."""
    if not party_characters:
        return "**No characters in party**\n\nAdd characters from the dropdown above."

    summary = f"# 🎭 {party.party_name}\n\n"
    summary += f"**Party Size:** {len(party_characters)} adventurer(s)\n"
    summary += f"**Party Gold:** {party.gold} GP\n\n"
    summary += "---\n\n"

    for char_name, char in party_characters.items():
        char_state = party.get_character(char_name)
        status = "✅ Ready" if char_state and char_state.is_alive() else "❌ Dead"

        # Get dynamic HP
        if char_state:
            hp_display = f"{char_state.current_hp}/{char_state.max_hp}"
        else:
            hp_display = str(char.hit_points)

        summary += f"### {char.name} ({status})\n"
        summary += f"**{char.race} {char.character_class}, Level {char.level}**\n"
        summary += f"- HP: {hp_display} | AC: {char.armor_class}\n"
        summary += f"- Background: {char.background}\n\n"

    if party.shared_inventory:
        summary += "### 🎒 Shared Inventory\n"
        for item, qty in party.shared_inventory.items():
            summary += f"- {item} x{qty}\n"

    return summary


def get_all_character_sheets() -> str:
    """Get all character sheets formatted."""
    if not party_characters:
        return "No characters in party"

    sheets = []
    for char_name, char in party_characters.items():
        sheet = format_character_sheet_for_char(char)
        sheets.append(sheet)
        sheets.append("\n---\n\n")

    return "\n".join(sheets)


def format_character_sheet_for_char(char: Character) -> str:
    """Format character sheet for a specific character."""
    mods = char.get_modifiers()

    # Get dynamic HP from party state
    char_state = party.get_character(char.name)
    if char_state:
        hp_display = f"{char_state.current_hp}/{char_state.max_hp}"
    else:
        hp_display = str(char.hit_points)

    sheet = f"""# {char.name}
**{char.race} {char.character_class}, Level {char.level}**
*{char.background} | {char.alignment}*

### Combat Stats
- **HP**: {hp_display}
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

### Inventory
{chr(10).join('- ' + f"{item} ({qty})" for item, qty in char_state.inventory.items() if item not in char.equipment) if char_state and char_state.inventory else '- Empty'}
"""

    if char.spells:
        sheet += f"""\n### Spells
{chr(10).join('- ' + spell for spell in char.spells)}
"""

    return sheet


# Create Gradio interface
try:
    demo = gr.Blocks(title="D&D RAG Game Master", theme=gr.themes.Soft())
except TypeError:
    # Fallback for older Gradio versions that don't support theme parameter
    demo = gr.Blocks(title="D&D RAG Game Master")

with demo:
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
                    gr.Markdown("## Gameplay Mode")

                    mode_toggle = gr.Radio(
                        choices=["🎭 Single Character", "🎲 Party Mode"],
                        value="🎭 Single Character",
                        label="Play Mode",
                        info="Single Character: Traditional one-player mode | Party Mode: Multi-character adventure"
                    )

                    gr.Markdown("---")

                    # Character mode UI
                    character_dropdown = gr.Dropdown(
                        choices=get_available_characters(),
                        value=get_available_characters()[0] if get_available_characters() else None,
                        label="Choose Your Character",
                        visible=True
                    )

                    # Debug scenario dropdown (only visible in debug mode)
                    debug_scenario_dropdown = gr.Dropdown(
                        choices=[s[0] for s in DEBUG_SCENARIOS],
                        value=None,
                        label="🧪 Debug Scenario (Optional)",
                        info="Load character in specific test scenario for combat testing",
                        visible=settings.DEBUG_MODE
                    )

                    with gr.Row():
                        load_btn = gr.Button("Load Character", variant="primary", scale=2)
                        delete_btn = gr.Button("🗑️ Delete", variant="stop", scale=1)

                    load_party_btn = gr.Button("Load Party", variant="primary", visible=False)

                    delete_status = gr.Textbox(label="Delete Status", interactive=False, visible=False)

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

                    # Initiative Tracker (visible when in combat)
                    with gr.Accordion("⚔️ Initiative Tracker", open=False, visible=False) as combat_accordion:
                        initiative_display = gr.Markdown("Not in combat")

                        with gr.Row():
                            next_turn_btn = gr.Button("⏭️ Next Turn", variant="secondary", scale=1)
                            end_combat_btn = gr.Button("🛑 End Combat", variant="stop", scale=1)

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
            - "I cast Magic Missile at the goblin"
            - "I attack with my longsword"

            ### 🎭 Party Mode Tips
            - First add characters in the Party Management tab
            - Switch to "Party Mode" above and click "Load Party"
            - In party mode, the GM manages the entire group
            - Type actions like "We investigate the cave" or "The party attacks"
            - Use `/stats` to see all party members

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
                        char_level = gr.Slider(
                            minimum=1,
                            maximum=20,
                            value=1,
                            step=1,
                            label="Level",
                            info="Character level (1-20)"
                        )
                        char_alignment = gr.Dropdown(
                            choices=[
                                "Lawful Good", "Neutral Good", "Chaotic Good",
                                "Lawful Neutral", "True Neutral", "Chaotic Neutral",
                                "Lawful Evil", "Neutral Evil", "Chaotic Evil"
                            ],
                            value="True Neutral",
                            label="Alignment"
                        )

                    char_background = gr.Textbox(label="Background", placeholder="e.g., Soldier, Sage, Folk Hero")

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

        # Tab 3: Party Management
        with gr.Tab("🎭 Party Management"):
            gr.Markdown("""
            ## Manage Your Adventuring Party

            Create a band of adventurers! Add multiple characters to your party and view their stats.
            Each character can be viewed individually, and the party shares gold and inventory.
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Add Characters to Party")

                    party_char_selector = gr.Dropdown(
                        choices=get_available_characters(),
                        multiselect=True,
                        label="Select Characters",
                        info="Choose one or more characters to add to your party"
                    )

                    add_party_btn = gr.Button("➕ Add to Party", variant="primary", size="lg")

                    gr.Markdown("---")

                    gr.Markdown("### Remove from Party")

                    remove_char_selector = gr.Dropdown(
                        choices=[],
                        label="Select Character to Remove",
                        info="Choose a character to remove from the party"
                    )

                    remove_party_btn = gr.Button("➖ Remove from Party", variant="secondary")

                    party_status = gr.Textbox(label="Status", interactive=False, lines=3)

                with gr.Column(scale=2):
                    gr.Markdown("### Party Overview")

                    party_summary_display = gr.Markdown(get_party_summary())

                    gr.Markdown("---")

                    gr.Markdown("### Party Member Sheets")

                    with gr.Accordion("View All Character Sheets", open=False):
                        party_sheets_display = gr.Markdown("No characters in party")

            gr.Markdown("""
            ---

            **Party Features:**
            - Add multiple characters to form a party
            - Shared gold and inventory pool
            - View individual character stats
            - Track party health and status
            """)

    # Event handlers - Play Game Tab

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

    mode_toggle.change(
        toggle_mode,
        inputs=[mode_toggle],
        outputs=[character_dropdown, load_btn, delete_btn, load_party_btn]
    )

    load_btn.click(
        load_character_with_debug,
        inputs=[character_dropdown, debug_scenario_dropdown],
        outputs=[character_sheet, msg_input, chatbot, char_image]
    )

    load_party_btn.click(
        load_party_mode,
        inputs=[],
        outputs=[character_sheet, msg_input, chatbot]
    )

    delete_btn.click(
        delete_character,
        inputs=[character_dropdown],
        outputs=[delete_status, character_dropdown]
    ).then(
        lambda: gr.update(visible=True),
        outputs=[delete_status]
    )

    # Chat submit handlers - update both chat and initiative tracker
    submit_btn.click(
        chat,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, initiative_display, combat_accordion, character_sheet]
    ).then(
        lambda: "",
        outputs=[msg_input]
    )

    msg_input.submit(
        chat,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, initiative_display, combat_accordion, character_sheet]
    ).then(
        lambda: "",
        outputs=[msg_input]
    )

    # Combat control button handlers
    next_turn_btn.click(
        handle_next_turn,
        inputs=[chatbot],
        outputs=[chatbot, initiative_display, combat_accordion, character_sheet]
    )

    end_combat_btn.click(
        handle_end_combat,
        inputs=[chatbot],
        outputs=[chatbot, initiative_display, combat_accordion, character_sheet]
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
            char_name, char_race, char_class, char_level, char_alignment, char_background,
            str_slider, dex_slider, con_slider, int_slider, wis_slider, cha_slider
        ],
        outputs=[create_output, character_dropdown]
    )

    # Event handlers - Party Management Tab
    def add_and_update(character_choices):
        """Add characters to party and update all displays."""
        result = add_to_party(character_choices)
        summary = get_party_summary()
        sheets = get_all_character_sheets()

        # Update remove dropdown with current party members
        party_member_names = list(party_characters.keys())

        return (
            result,  # party_status
            summary,  # party_summary_display
            sheets,  # party_sheets_display
            gr.update(choices=party_member_names)  # remove_char_selector
        )

    def remove_and_update(character_name):
        """Remove character from party and update all displays."""
        if not character_name:
            return (
                "⚠️ Please select a character to remove",
                get_party_summary(),
                get_all_character_sheets(),
                gr.update()
            )

        result = remove_from_party(character_name)
        summary = get_party_summary()
        sheets = get_all_character_sheets()

        # Update remove dropdown with current party members
        party_member_names = list(party_characters.keys())

        return (
            result,  # party_status
            summary,  # party_summary_display
            sheets,  # party_sheets_display
            gr.update(choices=party_member_names, value=None)  # remove_char_selector
        )

    add_party_btn.click(
        add_and_update,
        inputs=[party_char_selector],
        outputs=[party_status, party_summary_display, party_sheets_display, remove_char_selector]
    )

    remove_party_btn.click(
        remove_and_update,
        inputs=[remove_char_selector],
        outputs=[party_status, party_summary_display, party_sheets_display, remove_char_selector]
    )


if __name__ == "__main__":
    # Launch
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
