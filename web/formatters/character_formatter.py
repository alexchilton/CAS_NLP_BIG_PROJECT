"""
Character sheet formatting functions.
"""

from pathlib import Path


def format_character_sheet(char, char_state, db) -> tuple:
    """
    Format character sheet for 3-column display.

    Args:
        char: Character object with base stats
        char_state: CharacterState object with dynamic game state
        db: ChromaDBManager for RAG lookups

    Returns:
        Tuple of (col1, col2, col3) markdown strings
        - col1: Name, portrait, combat stats, ability scores
        - col2: Equipment, inventory, RAG lookup
        - col3: Spells and class-specific info
    """
    if not char:
        return ("No character selected", "", "")

    mods = char.get_modifiers()

    # Get dynamic HP from game state if available
    current_hp = char_state.current_hp if char_state else char.hit_points
    max_hp = char_state.max_hp if char_state else char.hit_points
    gold = char_state.gold if char_state and hasattr(char_state, 'gold') else getattr(char, 'gold', 0)

    # ========== COLUMN 1: NAME, COMBAT STATS, ABILITY SCORES ==========
    temp_hp_str = f" (+{char_state.temp_hp} temp)" if char_state and char_state.temp_hp > 0 else ""
    col1 = f"""# {char.name}
**{char.race} {char.character_class}**
*Level {char.level}*
*{char.background}*
*{char.alignment}*

---

### ⚔️ Combat Stats
**HP:** {current_hp}/{max_hp}{temp_hp_str}
**AC:** {char.armor_class}
**Prof Bonus:** +{char.proficiency_bonus}
**Gold:** {gold} GP

"""

    # Ability Scores
    col1 += f"""### 📊 Ability Scores
| STR | DEX | CON | INT | WIS | CHA |
|:---:|:---:|:---:|:---:|:---:|:---:|
| {char.strength}<br>({mods['strength']:+d}) | {char.dexterity}<br>({mods['dexterity']:+d}) | {char.constitution}<br>({mods['constitution']:+d}) | {char.intelligence}<br>({mods['intelligence']:+d}) | {char.wisdom}<br>({mods['wisdom']:+d}) | {char.charisma}<br>({mods['charisma']:+d}) |

"""

    # Death Saves (if unconscious)
    if char_state and not char_state.is_conscious():
        col1 += f"""### ⚠️ Death Saves
**Successes:** {"✅" * char_state.death_saves.successes}{"⬜" * (3 - char_state.death_saves.successes)}
**Failures:** {"❌" * char_state.death_saves.failures}{"⬜" * (3 - char_state.death_saves.failures)}

*Make a death saving throw each turn with `/death_save`*

"""

    # ========== COLUMN 2: EQUIPMENT, INVENTORY, RAG LOOKUP ==========
    col2 = f"""### 🗡️ Equipment
{chr(10).join('- ' + item for item in char.equipment)}

"""

    col2 += """### 🎒 Inventory\n"""
    if char_state and char_state.inventory:
        inv_items = [f"- {item} ({qty})" for item, qty in char_state.inventory.items() if item not in char.equipment]
        if inv_items:
            col2 += chr(10).join(inv_items) + "\n"
        else:
            col2 += "*Empty*\n"
    else:
        col2 += "*Empty*\n"

    col2 += "\n"

    # ========== COLUMN 3: SPELLS & CLASS INFO ==========
    col3 = ""

    # Check if character is a spellcaster
    is_spellcaster = (char_state and char_state.spellcasting_class) or (char.spells and len(char.spells) > 0)

    if is_spellcaster:
        col3 += """### ✨ Spell Slots
"""

        if char_state and hasattr(char_state, 'spell_slots'):
            available_slots = char_state.spell_slots.get_available()
            if available_slots:
                for level, (current, max_slots) in sorted(available_slots.items()):
                    filled = "🔵" * current
                    empty = "⚪" * (max_slots - current)
                    col3 += f"**Lvl {level}:** {filled}{empty} `{current}/{max_slots}`\n"
            else:
                col3 += "*No spell slots*\n"
        else:
            col3 += f"*Use `/long_rest` to restore*\n"

        col3 += "\n"

        # Spells List (Organized by Level)
        if char.spells:
            from dnd_rag_system.systems.spell_manager import SpellManager
            spell_mgr = SpellManager(db)

            spell_count = len(char.spells)
            col3 += f"""### 📖 Spells ({spell_count})
"""

            # Add guidance
            if char_state and char_state.spellcasting_class:
                if char_state.is_prepared_caster():
                    col3 += f"*Auto-prepared {len(char_state.prepared_spells)} best spells*\n\n"
                else:
                    col3 += f"*All spells always prepared*\n\n"

            col3 += f"*💡 Use `/rag <spell>` for details*\n\n"

            # Organize spells by level
            spells_by_level = {}
            for spell in char.spells:
                level = spell_mgr.lookup_spell_level(spell)
                if level is None:
                    level = 999
                if level not in spells_by_level:
                    spells_by_level[level] = []
                spells_by_level[level].append(spell)

            # Display spells
            for level in sorted(spells_by_level.keys()):
                spells = sorted(spells_by_level[level])

                if level == 0:
                    level_label = "**Cantrips**"
                elif level == 999:
                    level_label = "**Unknown**"
                else:
                    level_label = f"**Level {level}**"

                col3 += f"{level_label}\n"

                for spell in spells:
                    is_prepared = (char_state and
                                 hasattr(char_state, 'prepared_spells') and
                                 spell in char_state.prepared_spells)
                    mark = "✓ " if is_prepared else ""
                    col3 += f"- {mark}{spell}\n"

                col3 += "\n"
    else:
        # Non-spellcaster: show class features
        if char.class_features:
            col3 += f"""### 🎯 Class Features
{chr(10).join('- ' + feature for feature in char.class_features[:5])}
"""

    return (col1, col2, col3)


def format_character_sheet_for_char(char, party_state) -> str:
    """
    Format character sheet for a specific character (party mode).

    Args:
        char: Character object
        party_state: PartyState to get dynamic character state

    Returns:
        Markdown string with character sheet
    """
    mods = char.get_modifiers()

    # Get dynamic HP from party state
    char_state = party_state.get_character(char.name)
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
