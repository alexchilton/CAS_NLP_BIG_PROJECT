"""
Chat and command handling.
"""

import os
from pathlib import Path
from typing import Tuple

from dnd_rag_system.systems.game_state import GameSession


def handle_rag_lookup(query: str, gm, db) -> str:
    """
    Look up spell or item details from RAG database.

    Args:
        query: Spell or item name
        gm: GameMaster instance
        db: ChromaDBManager instance

    Returns:
        Formatted markdown with spell/item details
    """
    if not query or not query.strip():
        return "*Enter a spell or item name to see details*"

    query = query.strip()

    # Try multiple collections: spells first, then items, then general rules
    from dnd_rag_system.systems.spell_manager import SpellManager
    spell_mgr = SpellManager(db)

    # Check if it's a spell
    spell_details = spell_mgr.lookup_spell_details(query)

    if spell_details:
        # Format spell details nicely
        level_str = "Cantrip" if spell_details['level'] == 0 else f"Level {spell_details['level']}"
        conc_str = "⚠️ Requires Concentration" if spell_details['concentration'] else ""

        result = f"""## 🪄 {spell_details['name']}
*{level_str} {spell_details['school']}*  {conc_str}

**Description:**
{spell_details['description']}

---
*Source: D&D 5e SRD via RAG*
"""
        return result

    # Fallback to general RAG search (items, rules, etc.)
    results = gm.search_rag(query, n_results=2)
    if results and results.get('documents') and results['documents'][0]:
        formatted = gm.format_rag_context(results)
        return f"## 📖 {query}\n\n{formatted}\n\n---\n*Source: D&D 5e SRD via RAG*"

    return f"❌ **'{query}' not found in D&D 5e SRD**\n\nTry searching for:\n- Spell names (e.g., 'Magic Missile', 'Fireball')\n- Item names (e.g., 'Longsword', 'Plate Armor')\n- Monster names (e.g., 'Goblin', 'Dragon')\n- Class features (e.g., 'Action Surge', 'Sneak Attack')"


def chat(
    message: str,
    history: list,
    gameplay_mode: str,
    current_character,
    party_characters: dict,
    conversation_history: list,
    gm,
    get_initiative_tracker_func,
    get_current_sheet_func
) -> Tuple[list, str, str, str, str, str]:
    """
    Handle chat messages and commands.

    Args:
        message: User input message
        history: Chat history
        gameplay_mode: "character" or "party"
        current_character: Current Character object
        party_characters: Dict of party characters
        conversation_history: Global conversation history
        gm: GameMaster instance
        get_initiative_tracker_func: Function to get initiative tracker
        get_current_sheet_func: Function to get current sheet

    Returns:
        Tuple of (updated_history, initiative_display, accordion_update, char_col1, char_col2, char_col3)
    """
    # Check if in party mode or character mode
    if gameplay_mode == "party":
        if not party_characters:
            return (
                history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "⚠️ Please load party mode first (add characters in Party Management tab)"}
                ],
                *get_initiative_tracker_func(),
                *get_current_sheet_func()
            )
    else:
        if not current_character:
            return (
                history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": "⚠️ Please load a character first"}
                ],
                *get_initiative_tracker_func(),
                *get_current_sheet_func()
            )

    if not message.strip():
        return (history, *get_initiative_tracker_func(), *get_current_sheet_func())

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

**Equipment:**
- `/equip <item>` - Equip a magic item from your inventory
- `/unequip <slot>` - Unequip an item from a slot (e.g., ring_left, neck, armor)
- `/equipment` - Show all equipped items and bonuses

**Save/Load:**
- `/save_game <name>` - Save current game session (e.g., `/save_game campaign1`)
- `/load_game <name>` - Load a saved game session (e.g., `/load_game campaign1`)

**Items & Potions:**
- `/use <item>` - Use a potion or item (e.g., `/use healing potion`)

**Spellcasting:**
- `/spells` - Show your known and prepared spells
- `/learn_spell <spell>` - Learn a new spell (e.g., `/learn_spell Fireball`)
- `/prepare_spell <spell>` - Prepare a spell for casting (Wizard/Cleric/Druid/Paladin)
- `/unprepare_spell <spell>` - Unprepare a spell (frees up a preparation slot)
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
                *get_initiative_tracker_func(),
                *get_current_sheet_func()
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
                *get_initiative_tracker_func(),
                *get_current_sheet_func()
            )

        elif cmd == "/stats":
            # This will be handled by get_current_sheet_func
            col1, col2, col3 = get_current_sheet_func()
            stats = f"{col1}\n\n{col2}\n\n{col3}"
            return (
                history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": stats}
                ],
                *get_initiative_tracker_func(),
                *get_current_sheet_func()
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
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )
            else:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "Usage: `/rag <query>` (e.g., `/rag magic missile`)"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

        elif cmd == "/equipment":
            # Show equipped items and bonuses
            if gm.session.character_state:
                from dnd_rag_system.systems.character_equipment import CharacterEquipment
                equipment_manager = CharacterEquipment(gm.session.character_state)
                equipment_summary = equipment_manager.get_equipment_summary()
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": equipment_summary}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )
            else:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "⚠️ No character loaded"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

        elif cmd.startswith("/equip "):
            # Equip an item
            item_name = message[7:].strip()
            if not item_name:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "Usage: `/equip <item>` (e.g., `/equip Ring of Protection`)"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

            if gm.session.character_state:
                from dnd_rag_system.systems.character_equipment import CharacterEquipment
                equipment_manager = CharacterEquipment(gm.session.character_state)
                success, response_msg = equipment_manager.equip_item(item_name)
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": response_msg}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )
            else:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "⚠️ No character loaded"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

        elif cmd.startswith("/unequip "):
            # Unequip an item from a slot
            slot = message[9:].strip()
            if not slot:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "Usage: `/unequip <slot>` (e.g., `/unequip ring_left`, `/unequip neck`)\n\nValid slots: ring_left, ring_right, neck, armor, main_hand, off_hand, head, hands, feet, back, waist"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

            if gm.session.character_state:
                from dnd_rag_system.systems.character_equipment import CharacterEquipment
                equipment_manager = CharacterEquipment(gm.session.character_state)
                success, response_msg = equipment_manager.unequip_item(slot)
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": response_msg}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )
            else:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "⚠️ No character loaded"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

        elif cmd.startswith("/learn_spell "):
            # Learn a new spell
            spell_name = message[13:].strip()
            if not spell_name:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "Usage: `/learn_spell <spell>` (e.g., `/learn_spell Fireball`)"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

            if gm.session.character_state:
                result = gm.session.character_state.learn_spell(spell_name)
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": result["message"]}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )
            else:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "⚠️ No character loaded"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

        elif cmd.startswith("/prepare_spell "):
            # Prepare a spell (prepared casters only)
            spell_name = message[15:].strip()
            if not spell_name:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "Usage: `/prepare_spell <spell>` (e.g., `/prepare_spell Magic Missile`)"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

            if gm.session.character_state:
                # Need ability modifier - get from character
                if current_character:
                    ability_mod = current_character.get_ability_modifier(
                        getattr(current_character, gm.session.character_state.spellcasting_ability.lower(), 10)
                    )
                else:
                    ability_mod = 0

                result = gm.session.character_state.prepare_spell(spell_name, ability_mod)
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": result["message"]}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )
            else:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "⚠️ No character loaded"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

        elif cmd.startswith("/unprepare_spell "):
            # Unprepare a spell
            spell_name = message[17:].strip()
            if not spell_name:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "Usage: `/unprepare_spell <spell>` (e.g., `/unprepare_spell Fireball`)"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

            if gm.session.character_state:
                result = gm.session.character_state.unprepare_spell(spell_name)
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": result["message"]}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )
            else:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "⚠️ No character loaded"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

        elif cmd == "/spells":
            # Show known and prepared spells
            if gm.session.character_state:
                char_state = gm.session.character_state

                if not char_state.spellcasting_class:
                    spell_msg = "❌ You are not a spellcaster"
                else:
                    spell_msg = f"# 📖 Spells for {char_state.character_name}\n\n"
                    spell_msg += f"**Class**: {char_state.spellcasting_class} ({char_state.spellcasting_ability}-based)\n\n"

                    if char_state.is_prepared_caster():
                        # Prepared caster
                        spell_msg += f"**Type**: Prepared Caster\n"

                        if current_character:
                            ability_score = getattr(current_character, char_state.spellcasting_ability.lower(), 10)
                            ability_mod = current_character.get_ability_modifier(ability_score)
                            max_prepared = char_state.get_max_prepared_spells(ability_mod)
                            spell_msg += f"**Max Prepared**: {max_prepared} ({ability_mod} modifier + {char_state.level} level)\n\n"
                        else:
                            spell_msg += "\n"

                        spell_msg += f"### Known Spells ({len(char_state.known_spells)})\n"
                        if char_state.known_spells:
                            spell_msg += "\n".join([f"- {spell}" for spell in char_state.known_spells])
                        else:
                            spell_msg += "*None*"

                        spell_msg += f"\n\n### Prepared Spells ({len(char_state.prepared_spells)})\n"
                        if char_state.prepared_spells:
                            spell_msg += "\n".join([f"- ✓ {spell}" for spell in char_state.prepared_spells])
                        else:
                            spell_msg += "*None - use `/prepare_spell <spell>` to prepare spells*"
                    else:
                        # Known caster
                        spell_msg += f"**Type**: Known Caster (all known spells are prepared)\n\n"

                        spell_msg += f"### Known Spells ({len(char_state.known_spells)})\n"
                        if char_state.known_spells:
                            spell_msg += "\n".join([f"- {spell}" for spell in char_state.known_spells])
                        else:
                            spell_msg += "*None - use `/learn_spell <spell>` to learn spells*"

                    # Show spell slots
                    spell_msg += "\n\n### Spell Slots\n"
                    available_slots = char_state.spell_slots.get_available()
                    if available_slots:
                        for level, (current, max_slots) in available_slots.items():
                            spell_msg += f"- **Level {level}**: {current}/{max_slots}\n"
                    else:
                        spell_msg += "*No spell slots*"

                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": spell_msg}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )
            else:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "⚠️ No character loaded"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

        elif cmd.startswith("/save_game "):
            # Save game session
            save_name = message[11:].strip()
            if not save_name:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "Usage: `/save_game <name>` (e.g., `/save_game campaign1`)"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

            try:
                saves_dir = Path(__file__).parent.parent / "saves"
                saves_dir.mkdir(exist_ok=True)

                save_path = saves_dir / f"{save_name}.json"
                gm.session.save_to_json(save_path)

                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": f"✅ Game saved successfully!\n\nSaved to: `{save_path}`\n\nYou can load this save with: `/load_game {save_name}`"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )
            except Exception as e:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": f"❌ Error saving game: {str(e)}"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

        elif cmd.startswith("/load_game "):
            # Load game session
            save_name = message[11:].strip()
            if not save_name:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": "Usage: `/load_game <name>` (e.g., `/load_game campaign1`)"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

            try:
                saves_dir = Path(__file__).parent.parent / "saves"
                save_path = saves_dir / f"{save_name}.json"

                if not save_path.exists():
                    # List available saves
                    available_saves = [f.stem for f in saves_dir.glob("*.json")] if saves_dir.exists() else []
                    saves_list = ", ".join(available_saves) if available_saves else "none"

                    return (
                        history + [
                            {"role": "user", "content": message},
                            {"role": "assistant", "content": f"❌ Save file '{save_name}' not found.\n\nAvailable saves: {saves_list}"}
                        ],
                        *get_initiative_tracker_func(),
                        *get_current_sheet_func()
                    )

                # Load the session
                gm.session = GameSession.load_from_json(save_path)

                # Restore character state
                if gm.session.character_state:
                    char_name = gm.session.character_state.character_name
                    if char_name in gm.session.base_character_stats:
                        # This would need to update the global current_character
                        # We'll need to pass this back somehow
                        pass

                location = gm.session.current_location
                char_state = gm.session.character_state

                load_message = f"✅ Game loaded successfully!\n\n**Location**: {location}\n"
                if char_state:
                    load_message += f"**Character**: {char_state.character_name}\n"
                    load_message += f"**HP**: {char_state.current_hp}/{char_state.max_hp}\n"
                    load_message += f"**Gold**: {char_state.gold} GP\n"

                if gm.combat_manager.is_in_combat():
                    load_message += f"\n⚔️ **In Combat** - Round {gm.session.combat.round_number}"

                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": load_message}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )
            except Exception as e:
                return (
                    history + [
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": f"❌ Error loading game: {str(e)}"}
                    ],
                    *get_initiative_tracker_func(),
                    *get_current_sheet_func()
                )

        # Let other commands pass through to GM

    # Generate GM response (handles /buy, /sell, combat commands, and regular actions)
    try:
        response = gm.generate_response(message, use_rag=True)
        conversation_history.append((message, response))
        return (
            history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ],
            *get_initiative_tracker_func(),
            *get_current_sheet_func()
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
            *get_initiative_tracker_func(),
            *get_current_sheet_func()
        )


def clear_history(conversation_history_ref: list) -> list:
    """
    Clear conversation history.

    Args:
        conversation_history_ref: Reference to conversation history list

    Returns:
        Empty list
    """
    conversation_history_ref.clear()
    return []


def roll_random_stats() -> tuple:
    """
    Roll random ability scores using 3d6 method.

    Returns:
        Tuple of (STR, DEX, CON, INT, WIS, CHA)
    """
    import random

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
