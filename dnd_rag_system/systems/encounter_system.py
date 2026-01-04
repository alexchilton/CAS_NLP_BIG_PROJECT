"""
Random Encounter System for D&D RAG

Generates random monster encounters based on:
- Location type (forests more dangerous than towns)
- Character level (appropriate challenge rating)
- D&D 5e encounter rules

Integrates with:
- Monster RAG (ChromaDB) for creature selection
- Game state for location/level tracking
- GM dialogue for narrative integration
"""

import random
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class EncounterResult:
    """Result of an encounter check."""
    monster_name: str
    monster_cr: float
    description: str
    surprise: bool = False


class EncounterSystem:
    """Manages random encounters in the game world."""
    
    # Encounter chances by location type (0.0 - 1.0)
    ENCOUNTER_RATES = {
        "dungeon": 0.50,      # 50% - Very dangerous!
        "cave": 0.45,         # 45% - Dark and scary
        "ruins": 0.40,        # 40% - Ancient dangers
        "wilderness": 0.35,   # 35% - Wild animals/monsters
        "forest": 0.30,       # 30% - Beasts and bandits
        "mountain": 0.30,     # 30% - Dragons, giants
        "road": 0.20,         # 20% - Bandits, travelers
        "town_outskirts": 0.15,  # 15% - Edge of safety
        "tavern": 0.05,       # 5% - Bar fights rare
        "town": 0.03,         # 3% - Mostly safe
        "shop": 0.0,          # 0% - Never in shops!
        "temple": 0.02,       # 2% - Sacred ground
    }
    
    # CR ranges by character level for balanced encounters
    CR_BY_LEVEL = {
        1: (0, 1),      # Level 1: CR 0-1 (rats, goblins)
        2: (0, 2),      # Level 2: CR 0-2
        3: (1, 3),      # Level 3: CR 1-3
        4: (2, 4),      # Level 4: CR 2-4
        5: (3, 5),      # Level 5: CR 3-5
        6: (4, 6),
        7: (5, 7),
        8: (6, 8),
        9: (7, 10),
        10: (8, 12),
    }
    
    def __init__(self, chromadb_manager=None):
        """
        Initialize encounter system.
        
        Args:
            chromadb_manager: ChromaDB manager for querying monsters
        """
        self.chromadb = chromadb_manager
        
    def should_encounter(self, location_type: str) -> bool:
        """
        Roll for random encounter based on location.
        
        Args:
            location_type: Type of location (forest, dungeon, town, etc.)
            
        Returns:
            True if encounter should happen
        """
        # Normalize location type
        location_type = location_type.lower()
        
        # Get encounter rate (default 20% for unknown types)
        rate = self.ENCOUNTER_RATES.get(location_type, 0.20)
        
        # Roll the dice!
        return random.random() < rate
    
    def get_appropriate_cr_range(self, character_level: int) -> tuple:
        """
        Get appropriate CR range for character level.
        
        Args:
            character_level: Player character level (1-20)
            
        Returns:
            (min_cr, max_cr) tuple
        """
        if character_level <= 10:
            return self.CR_BY_LEVEL.get(character_level, (0, 2))
        else:
            # High level characters
            return (character_level - 3, character_level + 2)
    
    def query_random_monster(self, min_cr: float = 0, max_cr: float = 5) -> Optional[Dict]:
        """
        Query a random monster from ChromaDB within CR range.
        
        Args:
            min_cr: Minimum challenge rating
            max_cr: Maximum challenge rating
            
        Returns:
            Monster data dict or None
        """
        if not self.chromadb:
            # Fallback monsters if no RAG available
            return self._get_fallback_monster(min_cr, max_cr)
        
        try:
            # Query monsters collection
            results = self.chromadb.query_collection(
                collection_name="monsters",
                query_text=f"monster challenge rating {min_cr} to {max_cr}",
                n_results=20  # Get multiple to choose from
            )
            
            if results and len(results['documents']) > 0:
                # Filter by CR if metadata available
                valid_monsters = []
                for i, doc in enumerate(results['documents']):
                    # Try to extract CR from document
                    cr = self._extract_cr_from_doc(doc)
                    if cr is not None and min_cr <= cr <= max_cr:
                        valid_monsters.append({
                            'name': self._extract_name_from_doc(doc),
                            'description': doc,
                            'cr': cr
                        })
                
                if valid_monsters:
                    return random.choice(valid_monsters)
            
            # Fallback if RAG fails
            return self._get_fallback_monster(min_cr, max_cr)
            
        except Exception as e:
            print(f"⚠️  Encounter system: RAG query failed: {e}")
            return self._get_fallback_monster(min_cr, max_cr)
    
    def _extract_cr_from_doc(self, doc: str) -> Optional[float]:
        """Extract challenge rating from monster document."""
        # Look for patterns like "CR 1", "Challenge 2", etc.
        import re
        patterns = [
            r'CR[:\s]+(\d+(?:\.\d+)?)',
            r'Challenge[:\s]+(\d+(?:\.\d+)?)',
            r'challenge rating[:\s]+(\d+(?:\.\d+)?)',
        ]
        
        doc_lower = doc.lower()
        for pattern in patterns:
            match = re.search(pattern, doc_lower, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        
        return None
    
    def _extract_name_from_doc(self, doc: str) -> str:
        """Extract monster name from document."""
        # Try to get first line or first few words
        lines = doc.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            # Remove common prefixes
            first_line = first_line.replace('Monster:', '').replace('Name:', '').strip()
            # Take first 5 words max
            words = first_line.split()[:5]
            return ' '.join(words)
        return "Unknown Creature"
    
    def _get_fallback_monster(self, min_cr: float, max_cr: float) -> Dict:
        """Fallback monsters when RAG unavailable."""
        monsters_by_cr = {
            0: ["Giant Rat", "Commoner Bandit", "Swarm of Rats"],
            0.25: ["Goblin", "Wolf", "Skeleton"],
            0.5: ["Orc", "Hobgoblin", "Gnoll"],
            1: ["Dire Wolf", "Bugbear", "Animated Armor"],
            2: ["Ogre", "Gargoyle", "Werewolf"],
            3: ["Veteran Warrior", "Owlbear", "Manticore"],
            4: ["Ettin", "Black Pudding", "Ghost"],
            5: ["Hill Giant", "Troll", "Elemental"],
            6: ["Chimera", "Mage", "Young Dragon"],
            8: ["Frost Giant", "Hydra", "Mind Flayer"],
            10: ["Stone Golem", "Guardian Naga", "Young Red Dragon"],
            13: ["Vampire", "Storm Giant", "Adult Dragon"],
        }
        
        # Find monsters in CR range
        valid_monsters = []
        for cr, monster_list in monsters_by_cr.items():
            if min_cr <= cr <= max_cr:
                valid_monsters.extend([(name, cr) for name in monster_list])
        
        if not valid_monsters:
            # Default to goblin
            return {
                'name': 'Goblin',
                'cr': 0.25,
                'description': 'A small, cunning humanoid with green skin and sharp teeth.'
            }
        
        name, cr = random.choice(valid_monsters)
        return {
            'name': name,
            'cr': cr,
            'description': f'A dangerous {name.lower()} (CR {cr}).'
        }
    
    def generate_encounter(self, 
                          location_type: str, 
                          character_level: int = 3) -> Optional[EncounterResult]:
        """
        Main method: Check for encounter and generate if needed.
        
        Args:
            location_type: Current location type
            character_level: Player character level
            
        Returns:
            EncounterResult if encounter happens, None otherwise
        """
        # Step 1: Roll for encounter
        if not self.should_encounter(location_type):
            return None
        
        # Step 2: Determine appropriate CR
        min_cr, max_cr = self.get_appropriate_cr_range(character_level)
        
        # Step 3: Select monster
        monster = self.query_random_monster(min_cr, max_cr)
        if not monster:
            return None
        
        # Step 4: Check for surprise
        surprise = random.random() < 0.2  # 20% chance of surprise
        
        return EncounterResult(
            monster_name=monster['name'],
            monster_cr=monster.get('cr', 1),
            description=monster.get('description', f"A wild {monster['name']}!"),
            surprise=surprise
        )
    
    def format_encounter_for_gm(self, encounter: EncounterResult) -> str:
        """
        Format encounter for GM system message injection.
        
        Args:
            encounter: The encounter to format
            
        Returns:
            String to inject into GM context
        """
        if encounter.surprise:
            return (
                f"\n═══════════════════════════════════════════════════════════════════\n"
                f"🎲 MANDATORY ENCOUNTER - USE THIS EXACT MONSTER NAME 🎲\n"
                f"═══════════════════════════════════════════════════════════════════\n"
                f"A {encounter.monster_name} (CR {encounter.monster_cr}) suddenly appears!\n"
                f"CRITICAL: You MUST say '{encounter.monster_name}' (not any other creature).\n"
                f"Describe the {encounter.monster_name} appearing dramatically and attacking immediately.\n"
                f"═══════════════════════════════════════════════════════════════════\n"
            )
        else:
            return (
                f"\n═══════════════════════════════════════════════════════════════════\n"
                f"🎲 MANDATORY ENCOUNTER - USE THIS EXACT MONSTER NAME 🎲\n"
                f"═══════════════════════════════════════════════════════════════════\n"
                f"A {encounter.monster_name} (CR {encounter.monster_cr}) is nearby!\n"
                f"CRITICAL: You MUST say '{encounter.monster_name}' (not any other creature).\n"
                f"Describe it appearing, approaching, or being spotted by the player.\n"
                f"═══════════════════════════════════════════════════════════════════\n"
            )
    
    def format_encounter_fallback(self, encounter: EncounterResult) -> str:
        """
        Fallback encounter text if GM doesn't include it.
        
        Args:
            encounter: The encounter
            
        Returns:
            Narrative text to append to response
        """
        if encounter.surprise:
            return (
                f"\n\n⚠️  **Suddenly!** A {encounter.monster_name} leaps out from hiding! "
                f"You're caught by surprise!"
            )
        else:
            return (
                f"\n\nYou spot a {encounter.monster_name} ahead. "
                f"It notices you and moves to attack!"
            )


# Example usage
if __name__ == "__main__":
    # Test without RAG
    encounter_sys = EncounterSystem()
    
    print("🎲 Testing Encounter System\n")
    
    # Test different locations
    locations = ["dungeon", "forest", "town", "shop"]
    
    for loc in locations:
        print(f"📍 Location: {loc}")
        for i in range(5):
            encounter = encounter_sys.generate_encounter(loc, character_level=3)
            if encounter:
                print(f"  ⚔️  Encounter {i+1}: {encounter.monster_name} (CR {encounter.monster_cr})")
                if encounter.surprise:
                    print(f"      💥 SURPRISE ATTACK!")
            else:
                print(f"  ✅ No encounter")
        print()
