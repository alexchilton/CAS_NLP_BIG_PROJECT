"""
D&D Character Creator

Interactive character creation system with RAG-powered lookups for:
- Race selection and trait lookup (FROM ChromaDB)
- Class selection and feature lookup (FROM ChromaDB)
- Ability score generation
- Equipment selection
- Character sheet generation

Uses constants to avoid magic strings.
"""

import sys
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings
from dnd_rag_system.constants import CharacterClasses, CharacterRaces


@dataclass
class Character:
    """D&D Character data."""
    name: str = ""
    race: str = ""
    character_class: str = ""
    level: int = 1

    # Ability Scores
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    # Derived Stats
    hit_points: int = 0
    armor_class: int = 10
    proficiency_bonus: int = 2

    # Character Details
    background: str = ""
    alignment: str = ""
    race_traits: List[str] = field(default_factory=list)
    class_features: List[str] = field(default_factory=list)
    proficiencies: List[str] = field(default_factory=list)
    equipment: List[str] = field(default_factory=list)
    spells: List[str] = field(default_factory=list)
    gold: int = 50  # Starting gold

    # Character Image (for future GAN generation)
    image_path: Optional[str] = None

    def get_ability_modifier(self, score: int) -> int:
        """Calculate ability modifier from score."""
        return (score - 10) // 2

    def get_modifiers(self) -> Dict[str, int]:
        """Get all ability modifiers."""
        return {
            'strength': self.get_ability_modifier(self.strength),
            'dexterity': self.get_ability_modifier(self.dexterity),
            'constitution': self.get_ability_modifier(self.constitution),
            'intelligence': self.get_ability_modifier(self.intelligence),
            'wisdom': self.get_ability_modifier(self.wisdom),
            'charisma': self.get_ability_modifier(self.charisma)
        }

    def calculate_hit_points(self, hit_die: int) -> int:
        """
        Calculate HP for character's level.
        
        Formula:
        - Level 1: max hit die + CON modifier
        - Each additional level: average of hit die + CON modifier
        """
        con_mod = self.get_ability_modifier(self.constitution)
        
        # First level: full hit die + CON mod
        hp = hit_die + con_mod
        
        # Additional levels: average + CON mod per level
        if self.level > 1:
            avg_roll = (hit_die // 2) + 1  # e.g., d6 = 4, d8 = 5, d10 = 6, d12 = 7
            hp += (self.level - 1) * (avg_roll + con_mod)
        
        return max(1, hp)  # Minimum 1 HP

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return asdict(self)

    def to_json(self, filepath: str):
        """Save character to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"✓ Character saved to {filepath}")


class CharacterCreator:
    """
    Interactive D&D character creation with RAG integration.

    Uses ChromaDB to look up race traits, class features, etc.
    """

    def __init__(self, db_manager: ChromaDBManager):
        """
        Initialize character creator.

        Args:
            db_manager: ChromaDBManager instance
        """
        self.db = db_manager
        self.character = Character()

    def create_character_interactive(self) -> Character:
        """
        Interactive character creation workflow.

        Returns:
            Complete Character object
        """
        print("\n" + "="*70)
        print("🎲 D&D CHARACTER CREATOR")
        print("="*70)
        print("\nLet's create your D&D character!\n")

        # Step 1: Name
        self.character.name = self._get_character_name()

        # Step 2: Race
        self.character.race = self._select_race()
        self._apply_race_traits()

        # Step 3: Class
        self.character.character_class = self._select_class()
        self._apply_class_features()

        # Step 4: Ability Scores
        self._generate_ability_scores()

        # Step 5: Calculate derived stats
        self._calculate_derived_stats()

        # Step 6: Background & Alignment
        self._set_background_and_alignment()

        # Step 7: Equipment
        self._select_starting_equipment()

        # Step 8: Spells (if caster)
        if self._is_spellcaster():
            self._select_starting_spells()

        # Show final character sheet
        self._display_character_sheet()

        return self.character

    def _get_character_name(self) -> str:
        """Get character name from user."""
        while True:
            name = input("What is your character's name? ").strip()
            if name:
                print(f"\n👋 Hello, {name}!\n")
                return name
            print("Please enter a valid name.")

    def _select_race(self) -> str:
        """Select character race with RAG lookup."""
        print("="*70)
        print("STEP 1: Choose Your Race")
        print("="*70)

        print("\nAvailable races:")
        for i, race in enumerate(settings.DND_RACES, 1):
            print(f"  {i}. {race}")

        print(f"  {len(settings.DND_RACES) + 1}. Learn more about a race")

        while True:
            choice = input("\nSelect a race (number): ").strip()

            if not choice.isdigit():
                print("Please enter a number.")
                continue

            choice_num = int(choice)

            # Learn more option
            if choice_num == len(settings.DND_RACES) + 1:
                race_name = input("Which race do you want to learn about? ").strip()
                self._show_race_info(race_name)
                continue

            # Valid race selection
            if 1 <= choice_num <= len(settings.DND_RACES):
                selected_race = settings.DND_RACES[choice_num - 1]
                print(f"\n✓ You selected: {selected_race}")

                # Show race info
                self._show_race_info(selected_race)

                confirm = input("\nConfirm this choice? (y/n): ").strip().lower()
                if confirm == 'y':
                    return selected_race
            else:
                print(f"Please enter a number between 1 and {len(settings.DND_RACES) + 1}")

    def _show_race_info(self, race_name: str):
        """Show race information from RAG."""
        print(f"\n{'─'*70}")
        print(f"📖 About {race_name.title()}:")
        print(f"{'─'*70}")

        # Search for race info in RAG
        results = self.db.search(
            settings.COLLECTION_NAMES['races'],
            f"{race_name} traits abilities",
            n_results=2
        )

        if results['documents'] and results['documents'][0]:
            for doc in results['documents'][0]:
                print(doc[:400] + "..." if len(doc) > 400 else doc)
                print()
        else:
            print(f"(Race information for {race_name} not yet in database)")
            print(f"Placeholder: {race_name}s are playable characters in D&D 5e.")

    def _apply_race_traits(self):
        """Apply racial traits and ability bonuses using RAG."""
        race = self.character.race
        
        # Try to get racial bonuses from RAG/SRD
        try:
            import chromadb
            client = chromadb.PersistentClient(path='chromadb')
            collection = client.get_collection('dnd5e_srd')
            
            results = collection.query(
                query_texts=[f"{race} race ability score"],
                n_results=1,
                where={"$and": [{"type": {"$eq": "race"}}, {"name": {"$eq": race}}]}
            )
            
            if results and results.get('metadatas') and results['metadatas'][0]:
                metadata = results['metadatas'][0][0]
                
                # Extract bonus_* fields
                bonuses = {}
                for key, val in metadata.items():
                    if key.startswith('bonus_'):
                        ability = key.replace('bonus_', '')
                        bonuses[ability] = val
                
                if bonuses:
                    print(f"\n  ✓ Racial bonuses from SRD:")
                    
                    # Apply bonuses to character
                    for ability, bonus in bonuses.items():
                        current_val = getattr(self.character, ability)
                        setattr(self.character, ability, current_val + bonus)
                        print(f"    +{bonus} {ability.capitalize()} → {current_val + bonus}")
                    
                    self.character.race_traits.append(f"{race} racial traits")
                    return
        except Exception as e:
            print(f"  ⚠️  Could not get racial bonuses from RAG: {e}")
        
        # Fallback to hardcoded if RAG fails
        print(f"  ⚠️  Using fallback racial bonuses for {race}")
        race_bonuses = {
            CharacterRaces.HUMAN: {'strength': 1, 'dexterity': 1, 'constitution': 1,
                     'intelligence': 1, 'wisdom': 1, 'charisma': 1},
            CharacterRaces.ELF: {'dexterity': 2},
            CharacterRaces.DWARF: {'constitution': 2},
            CharacterRaces.HALFLING: {'dexterity': 2},
            CharacterRaces.DRAGONBORN: {'strength': 2, 'charisma': 1},
            CharacterRaces.GNOME: {'intelligence': 2},
            CharacterRaces.HALF_ELF: {'charisma': 2},
            CharacterRaces.HALF_ORC: {'strength': 2, 'constitution': 1},
            CharacterRaces.TIEFLING: {'intelligence': 1, 'charisma': 2}
        }

        if race in race_bonuses:
            for ability, bonus in race_bonuses[race].items():
                current_val = getattr(self.character, ability)
                setattr(self.character, ability, current_val + bonus)
                print(f"  +{bonus} {ability.title()}")

        self.character.race_traits.append(f"{race} racial traits")

    def _select_class(self) -> str:
        """Select character class with RAG lookup."""
        print("\n" + "="*70)
        print("STEP 2: Choose Your Class")
        print("="*70)

        print("\nAvailable classes:")
        for i, cls in enumerate(settings.DND_CLASSES, 1):
            print(f"  {i}. {cls}")

        print(f"  {len(settings.DND_CLASSES) + 1}. Learn more about a class")

        while True:
            choice = input("\nSelect a class (number): ").strip()

            if not choice.isdigit():
                print("Please enter a number.")
                continue

            choice_num = int(choice)

            # Learn more option
            if choice_num == len(settings.DND_CLASSES) + 1:
                class_name = input("Which class do you want to learn about? ").strip()
                self._show_class_info(class_name)
                continue

            # Valid class selection
            if 1 <= choice_num <= len(settings.DND_CLASSES):
                selected_class = settings.DND_CLASSES[choice_num - 1]
                print(f"\n✓ You selected: {selected_class}")

                # Show class info
                self._show_class_info(selected_class)

                confirm = input("\nConfirm this choice? (y/n): ").strip().lower()
                if confirm == 'y':
                    return selected_class
            else:
                print(f"Please enter a number between 1 and {len(settings.DND_CLASSES) + 1}")

    def _show_class_info(self, class_name: str):
        """Show class information from RAG."""
        print(f"\n{'─'*70}")
        print(f"⚔️  About {class_name}:")
        print(f"{'─'*70}")

        # Search for class info in RAG
        results = self.db.search(
            settings.COLLECTION_NAMES['classes'],
            f"{class_name} features abilities",
            n_results=2
        )

        if results['documents'] and results['documents'][0]:
            for doc in results['documents'][0]:
                print(doc[:500] + "..." if len(doc) > 500 else doc)
                print()
        else:
            print(f"Loading {class_name} information...")

    def _apply_class_features(self):
        """Apply starting class features using SRD RAG data."""
        cls = self.character.character_class
        
        # Try to use RAG-powered enhancement if available
        try:
            from dnd_rag_system.systems.rag_character_enhancer import enhance_character_with_rag
            
            print(f"\n🔮 Auto-applying {cls} features from SRD...")
            enhance_character_with_rag(self.character)
            print("✓ Class features applied from official SRD data\n")
            
        except Exception as e:
            # Fallback to basic features if RAG enhancement fails
            print(f"⚠️  Using basic class features (SRD unavailable: {e})\n")
            
            # Add starting features (basic fallback)
            self.character.class_features.append(f"{cls} starting features")
            
            # Add proficiencies (simplified)
            self.character.proficiencies.extend([
                f"{cls} weapon proficiencies",
                f"{cls} armor proficiencies",
                f"{cls} saving throws"
            ])

    def _generate_ability_scores(self):
        """Generate ability scores."""
        print("\n" + "="*70)
        print("STEP 3: Ability Scores")
        print("="*70)

        print("\nChoose method:")
        print("  1. Standard Array (15, 14, 13, 12, 10, 8)")
        print("  2. Roll 4d6, drop lowest (random)")
        print("  3. Point Buy (27 points)")

        method = input("\nSelect method (1-3): ").strip()

        if method == "1":
            self._assign_standard_array()
        elif method == "2":
            self._roll_ability_scores()
        elif method == "3":
            self._point_buy_ability_scores()
        else:
            print("Invalid choice, using Standard Array")
            self._assign_standard_array()

    def _assign_standard_array(self):
        """Assign standard array to abilities."""
        array = [15, 14, 13, 12, 10, 8]
        abilities = ['strength', 'dexterity', 'constitution',
                    'intelligence', 'wisdom', 'charisma']

        print("\nStandard Array: 15, 14, 13, 12, 10, 8")
        print("Assign these scores to your abilities:\n")

        for ability in abilities:
            while True:
                print(f"Available scores: {array}")
                choice = input(f"{ability.title()}: ").strip()

                if choice.isdigit() and int(choice) in array:
                    score = int(choice)
                    array.remove(score)
                    setattr(self.character, ability, score)
                    break
                print("Invalid choice. Pick from available scores.")

    def _roll_ability_scores(self):
        """Roll ability scores (4d6 drop lowest)."""
        print("\nRolling ability scores (4d6, drop lowest)...\n")

        abilities = ['strength', 'dexterity', 'constitution',
                    'intelligence', 'wisdom', 'charisma']

        for ability in abilities:
            rolls = sorted([random.randint(1, 6) for _ in range(4)])
            score = sum(rolls[1:])  # Drop lowest
            setattr(self.character, ability, score)
            print(f"{ability.title()}: {rolls} → {score} (dropped {rolls[0]})")

        input("\nPress Enter to continue...")

    def _point_buy_ability_scores(self):
        """Point buy ability scores."""
        print("\nPoint Buy: Start with 8 in each stat, spend 27 points")
        print("Cost: 9=1pt, 10=2pt, 11=3pt, 12=4pt, 13=5pt, 14=7pt, 15=9pt")
        print("\n(Simplified implementation - using Standard Array instead)\n")
        self._assign_standard_array()

    def _calculate_derived_stats(self):
        """Calculate HP, AC, etc."""
        # Hit points (simplified - using d8 as average)
        hit_die = 8
        self.character.hit_points = self.character.calculate_hit_points(hit_die)

        # AC (10 + Dex modifier, no armor)
        dex_mod = self.character.get_ability_modifier(self.character.dexterity)
        self.character.armor_class = 10 + dex_mod

    def _set_background_and_alignment(self):
        """Set background and alignment."""
        print("\n" + "="*70)
        print("STEP 4: Background & Alignment")
        print("="*70)

        self.character.background = input("\nBackground (e.g., Soldier, Noble, Folk Hero): ").strip()
        self.character.alignment = input("Alignment (e.g., Lawful Good, Chaotic Neutral): ").strip()

    def _select_starting_equipment(self):
        """Select starting equipment."""
        print("\n" + "="*70)
        print("STEP 5: Starting Equipment")
        print("="*70)

        # Simplified - add class-appropriate gear
        cls = self.character.character_class

        print(f"\n{cls} starting equipment:")
        if cls in [CharacterClasses.FIGHTER, CharacterClasses.PALADIN, CharacterClasses.RANGER]:
            self.character.equipment = ["Longsword", "Shield", "Chainmail", "Backpack", "50 GP"]
        elif cls in [CharacterClasses.WIZARD, CharacterClasses.SORCERER, CharacterClasses.WARLOCK]:
            self.character.equipment = ["Quarterstaff", "Spellbook", "Robes", "Component Pouch", "25 GP"]
        elif cls in [CharacterClasses.ROGUE, CharacterClasses.BARD]:
            self.character.equipment = ["Shortsword", "Leather Armor", "Thieves' Tools", "Backpack", "40 GP"]
        elif cls == CharacterClasses.CLERIC:
            self.character.equipment = ["Mace", "Shield", "Chainmail", "Holy Symbol", "30 GP"]
        else:
            self.character.equipment = ["Basic gear", "50 GP"]

        for item in self.character.equipment:
            print(f"  - {item}")

    def _is_spellcaster(self) -> bool:
        """Check if class is a spellcaster."""
        spellcasting_classes = [
            CharacterClasses.WIZARD, 
            CharacterClasses.SORCERER, 
            CharacterClasses.WARLOCK, 
            CharacterClasses.CLERIC,
            CharacterClasses.DRUID, 
            CharacterClasses.BARD, 
            CharacterClasses.PALADIN, 
            CharacterClasses.RANGER
        ]
        return self.character.character_class in spellcasting_classes

    def _select_starting_spells(self):
        """Select starting spells from RAG."""
        print("\n" + "="*70)
        print("STEP 6: Starting Spells")
        print("="*70)

        cls = self.character.character_class
        print(f"\n{cls} starting spells:")

        # Search for cantrips
        cantrip_results = self.db.search(
            settings.COLLECTION_NAMES['spells'],
            f"{cls} cantrip",
            n_results=5
        )

        if cantrip_results['documents'] and cantrip_results['documents'][0]:
            print("\nAvailable Cantrips:")
            for i, (doc, meta) in enumerate(zip(cantrip_results['documents'][0],
                                                cantrip_results['metadatas'][0]), 1):
                spell_name = meta.get('name', 'Unknown')
                print(f"  {i}. {spell_name}")

                if i <= 3:  # Auto-select first 3
                    self.character.spells.append(spell_name)

            print(f"\n✓ Selected cantrips: {', '.join(self.character.spells[:3])}")
        else:
            print("(Spell data not yet loaded)")
            self.character.spells = [f"{cls} cantrips (see PHB)"]

    def _display_character_sheet(self):
        """Display final character sheet."""
        char = self.character
        mods = char.get_modifiers()

        print("\n" + "="*70)
        print("🎉 CHARACTER CREATION COMPLETE!")
        print("="*70)
        print(f"\n{char.name}")
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

        print("\n" + "="*70)


def main():
    """Main character creation flow."""
    print("\n🎲 D&D 5e Character Creator with RAG")

    # Initialize database
    print("Connecting to D&D knowledge base...")
    db = ChromaDBManager()

    # Create character
    creator = CharacterCreator(db)
    character = creator.create_character_interactive()

    # Save option
    save = input("\nSave character to file? (y/n): ").strip().lower()
    if save == 'y':
        filename = input("Filename (e.g., gandalf.json): ").strip()
        if not filename.endswith('.json'):
            filename += '.json'
        character.to_json(filename)

    print("\n✨ Character creation complete! Ready to adventure!")


if __name__ == '__main__':
    main()
