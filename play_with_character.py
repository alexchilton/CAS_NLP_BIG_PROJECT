#!/usr/bin/env python3
"""
D&D Character-Aware Game Session

Integrated test script that:
1. Creates or loads a character
2. Starts a GM dialogue session with character context
3. Allows playing with character stats visible to GM
"""

import os
# Suppress tokenizer warning when forking subprocess
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import sys
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.character_creator import CharacterCreator, Character
from dnd_rag_system.systems.gm_dialogue import GameMaster, InteractiveGM


class CharacterAwareGM(InteractiveGM):
    """
    Enhanced GM that knows about the player's character.

    Extends InteractiveGM to include character information in prompts.
    """

    def __init__(self, gm: GameMaster, character: Character):
        """Initialize with character context."""
        super().__init__(gm)
        self.character = character

        # Set initial scene with character info
        self._initialize_character_context()

    def _initialize_character_context(self):
        """Add character to GM's context."""
        char = self.character
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

        self.gm.set_context(context)

    def print_help(self):
        """Override help to add character commands."""
        super().print_help()
        print("\nCHARACTER COMMANDS:")
        print("  /character     - Show character sheet")
        print("  /stats         - Quick stats view")
        print()

    def run(self):
        """Override run to handle character commands."""
        print("\n" + "="*70)
        print(f"🎲 D&D GAME SESSION - Playing as {self.character.name}")
        print("="*70)
        print(f"Character: {self.character.name} ({self.character.race} {self.character.character_class})")
        print(f"Model: {self.gm.model_name}")
        print(f"Database: {self.gm.db.persist_dir}")
        print("\nType /help for commands or start playing!")
        print("="*70)

        self.running = True
        use_rag_next = True

        while self.running:
            try:
                # Get player input
                player_input = input(f"\n🎲 {self.character.name}: ").strip()

                if not player_input:
                    continue

                # Handle commands
                if player_input.startswith('/'):
                    # Check for character-specific commands first
                    if player_input.lower() == '/character':
                        self._show_character_sheet()
                        continue
                    elif player_input.lower() == '/stats':
                        self._show_quick_stats()
                        continue
                    else:
                        # Use parent's command handler
                        self._handle_command(player_input)
                        continue

                # Generate GM response
                print("\n🎭 GM: ", end="", flush=True)
                response = self.gm.generate_response(player_input, use_rag=use_rag_next)
                print(response)

                # Reset RAG flag
                use_rag_next = True

            except KeyboardInterrupt:
                print("\n\n👋 Game interrupted. Type /quit to exit or continue playing.")
            except Exception as e:
                print(f"\n❌ Error: {e}")

    def _show_character_sheet(self):
        """Display full character sheet."""
        char = self.character
        mods = char.get_modifiers()

        print("\n" + "="*70)
        print(f"CHARACTER SHEET - {char.name}")
        print("="*70)
        print(f"{char.race} {char.character_class}, Level {char.level}")
        print(f"{char.background} | {char.alignment}")
        print("\n" + "─"*70)

        print("\nABILITY SCORES:")
        print(f"  STR: {char.strength:2d} ({mods['strength']:+d})  |  INT: {char.intelligence:2d} ({mods['intelligence']:+d})")
        print(f"  DEX: {char.dexterity:2d} ({mods['dexterity']:+d})  |  WIS: {char.wisdom:2d} ({mods['wisdom']:+d})")
        print(f"  CON: {char.constitution:2d} ({mods['constitution']:+d})  |  CHA: {char.charisma:2d} ({mods['charisma']:+d})")

        print(f"\nCOMBAT STATS:")
        print(f"  HP: {char.hit_points}  |  AC: {char.armor_class}  |  Proficiency: +{char.proficiency_bonus}")

        print(f"\nEQUIPMENT:")
        for item in char.equipment:
            print(f"  - {item}")

        if char.spells:
            print(f"\nSPELLS:")
            for spell in char.spells:
                print(f"  - {spell}")

        print("="*70)

    def _show_quick_stats(self):
        """Show condensed stats."""
        char = self.character
        mods = char.get_modifiers()

        print(f"\n📊 {char.name} | HP: {char.hit_points} | AC: {char.armor_class} | Prof: +{char.proficiency_bonus}")
        print(f"   STR {mods['strength']:+d} | DEX {mods['dexterity']:+d} | CON {mods['constitution']:+d} | INT {mods['intelligence']:+d} | WIS {mods['wisdom']:+d} | CHA {mods['charisma']:+d}")


def load_character_from_json(filepath: str) -> Character:
    """Load character from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Create Character object from dict
    char = Character()
    for key, value in data.items():
        if hasattr(char, key):
            setattr(char, key, value)

    return char


def main():
    """Main entry point for character-aware game session."""
    print("\n" + "="*70)
    print("🎲 D&D CHARACTER-AWARE GAME SESSION")
    print("="*70)

    try:
        # Initialize ChromaDB
        print("\n📚 Connecting to D&D knowledge base...")
        db = ChromaDBManager()

        # Character selection
        print("\n" + "─"*70)
        print("CHARACTER SELECTION")
        print("─"*70)
        print("\n1. Create new character")
        print("2. Load existing character")
        print("3. Use test character (quick start)")

        choice = input("\nSelect option (1-3): ").strip()

        if choice == "1":
            # Create new character
            print("\n🎭 Starting character creator...")
            creator = CharacterCreator(db)
            character = creator.create_character_interactive()

            # Save option
            save = input("\nSave character? (y/n): ").strip().lower()
            if save == 'y':
                filename = input("Filename (e.g., aragorn.json): ").strip()
                if not filename.endswith('.json'):
                    filename += '.json'
                character.to_json(filename)

        elif choice == "2":
            # Load existing character
            filename = input("\nCharacter filename: ").strip()
            if not filename.endswith('.json'):
                filename += '.json'

            character = load_character_from_json(filename)
            print(f"\n✅ Loaded: {character.name} ({character.race} {character.character_class})")

        else:
            # Quick test character
            print("\n⚡ Creating test character...")
            character = Character(
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
            print(f"✅ Created: {character.name} - a battle-ready dwarf fighter!")

        # Initialize Game Master with character
        print("\n🎭 Initializing AI Game Master...")
        gm = GameMaster(db)

        print("✅ Game Master ready!")

        # Start character-aware session
        interactive = CharacterAwareGM(gm, character)
        interactive.run()

    except FileNotFoundError as e:
        print(f"\n❌ Character file not found: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}")
        print("\nTroubleshooting:")
        print("  1. Run: python initialize_rag.py")
        print("  2. Install Ollama: https://ollama.ai")
        print("  3. Download model: ollama pull hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
