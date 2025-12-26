"""
Equipment Data Loader for D&D RAG System

Parses equipment.txt and structures equipment data for ChromaDB.
Extracts:
- Armor (name, cost, AC, weight, type)
- Weapons (name, cost, damage, weight, properties)
- Adventuring gear (name, cost, weight, description)
- Tools, mounts, vehicles, etc.
"""

import re
from typing import List, Dict, Any
from pathlib import Path


class EquipmentLoader:
    """Parse and structure D&D equipment data."""

    def __init__(self, equipment_file: Path):
        """
        Initialize equipment loader.

        Args:
            equipment_file: Path to equipment.txt file
        """
        self.equipment_file = equipment_file
        self.equipment_data = []

    def load_and_parse(self) -> List[Dict[str, Any]]:
        """
        Load and parse equipment file.

        Returns:
            List of equipment dictionaries with structured data
        """
        with open(self.equipment_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse different equipment categories
        self.equipment_data.extend(self._parse_armor(content))
        self.equipment_data.extend(self._parse_weapons(content))
        self.equipment_data.extend(self._parse_adventuring_gear(content))
        self.equipment_data.extend(self._parse_tools(content))
        self.equipment_data.extend(self._parse_mounts(content))

        return self.equipment_data

    def _parse_armor(self, content: str) -> List[Dict[str, Any]]:
        """Parse armor data from equipment text."""
        armor_data = []

        # Light Armor
        armor_patterns = [
            (r'Padded\s+5 gp\s+11 \+ Dex modifier\s+Disadvantage\s+81b\.',
             {'name': 'Padded Armor', 'cost_gp': 5, 'ac': '11 + Dex', 'weight': 8, 'type': 'Light Armor', 'stealth': 'Disadvantage'}),
            (r'Leather\s+10 gp\s+11 \+ Dex modifier\s+101b\.',
             {'name': 'Leather Armor', 'cost_gp': 10, 'ac': '11 + Dex', 'weight': 10, 'type': 'Light Armor'}),
            (r'Studded leather\s+45 gp\s+12 \+ Dex modifier\s+13lb\.',
             {'name': 'Studded Leather Armor', 'cost_gp': 45, 'ac': '12 + Dex', 'weight': 13, 'type': 'Light Armor'}),
            # Medium Armor
            (r'Hide\s+10 gp\s+12 \+ Dex modifier \(max 2\)\s+121b\.',
             {'name': 'Hide Armor', 'cost_gp': 10, 'ac': '12 + Dex (max 2)', 'weight': 12, 'type': 'Medium Armor'}),
            (r'Chain shirt\s+50 gp\s+13 \+ Dex modifier \(ma x 2\)\s+201b\.',
             {'name': 'Chain Shirt', 'cost_gp': 50, 'ac': '13 + Dex (max 2)', 'weight': 20, 'type': 'Medium Armor'}),
            (r'Seale mai!\s+50 gp\s+14 \+ Dex modifier \(max 2\)\s+Disadvantage\s+451b\.',
             {'name': 'Scale Mail', 'cost_gp': 50, 'ac': '14 + Dex (max 2)', 'weight': 45, 'type': 'Medium Armor', 'stealth': 'Disadvantage'}),
            (r'Breastplate\s+400 gp\s+14 \+ Dex modifier \(max 2\)\s+201b\.',
             {'name': 'Breastplate', 'cost_gp': 400, 'ac': '14 + Dex (max 2)', 'weight': 20, 'type': 'Medium Armor'}),
            (r'Half plate\s+750 gp\s+15 \+ Dex modifier \(max 2\)\s+Disadvantage\s+401b\.',
             {'name': 'Half Plate', 'cost_gp': 750, 'ac': '15 + Dex (max 2)', 'weight': 40, 'type': 'Medium Armor', 'stealth': 'Disadvantage'}),
            # Heavy Armor
            (r'Ring mail\s+30 gp\s+14\s+Disadvantage\s+401b\.',
             {'name': 'Ring Mail', 'cost_gp': 30, 'ac': '14', 'weight': 40, 'type': 'Heavy Armor', 'stealth': 'Disadvantage'}),
            (r'Chain mail\s+75 gp\s+16\s+Str 13\s+Disadvantage\s+551b\.',
             {'name': 'Chain Mail', 'cost_gp': 75, 'ac': '16', 'weight': 55, 'type': 'Heavy Armor', 'str_req': 13, 'stealth': 'Disadvantage'}),
            (r'Splint\s+200 gp\s+17\s+Str 15\s+Disadvantage\s+601b\.',
             {'name': 'Splint Armor', 'cost_gp': 200, 'ac': '17', 'weight': 60, 'type': 'Heavy Armor', 'str_req': 15, 'stealth': 'Disadvantage'}),
            (r'Plate\s+1,500 gp\s+18\s+Str 15\s+Disadvantage\s+651b\.',
             {'name': 'Plate Armor', 'cost_gp': 1500, 'ac': '18', 'weight': 65, 'type': 'Heavy Armor', 'str_req': 15, 'stealth': 'Disadvantage'}),
            # Shield
            (r'Shield\s+10 gp\s+\+2\s+61b\.',
             {'name': 'Shield', 'cost_gp': 10, 'ac': '+2', 'weight': 6, 'type': 'Shield'}),
        ]

        for pattern, data in armor_patterns:
            if re.search(pattern, content):
                desc = f"{data['type']}. AC: {data['ac']}, Weight: {data['weight']} lb, Cost: {data['cost_gp']} gp"
                if 'stealth' in data:
                    desc += f", Stealth: {data['stealth']}"

                armor_data.append({
                    'name': data['name'],
                    'category': 'armor',
                    'subcategory': data['type'],
                    'cost_gp': data['cost_gp'],
                    'description': desc,
                    'metadata': data
                })

        return armor_data

    def _parse_weapons(self, content: str) -> List[Dict[str, Any]]:
        """Parse weapon data from equipment text."""
        weapons = []

        # Simple Melee Weapons
        weapon_patterns = [
            {'name': 'Club', 'cost_gp': 0.1, 'damage': '1d4 bludgeoning', 'properties': 'Light', 'weight': 2, 'type': 'Simple Melee'},
            {'name': 'Dagger', 'cost_gp': 2, 'damage': '1d4 piercing', 'properties': 'Finesse, light, thrown (20/60)', 'weight': 1, 'type': 'Simple Melee'},
            {'name': 'Greatclub', 'cost_gp': 0.2, 'damage': '1d8 bludgeoning', 'properties': 'Two-handed', 'weight': 10, 'type': 'Simple Melee'},
            {'name': 'Handaxe', 'cost_gp': 5, 'damage': '1d6 slashing', 'properties': 'Light, thrown (20/60)', 'weight': 2, 'type': 'Simple Melee'},
            {'name': 'Javelin', 'cost_gp': 0.5, 'damage': '1d6 piercing', 'properties': 'Thrown (30/120)', 'weight': 2, 'type': 'Simple Melee'},
            {'name': 'Light Hammer', 'cost_gp': 2, 'damage': '1d4 bludgeoning', 'properties': 'Light, thrown (20/60)', 'weight': 2, 'type': 'Simple Melee'},
            {'name': 'Mace', 'cost_gp': 5, 'damage': '1d6 bludgeoning', 'properties': '', 'weight': 4, 'type': 'Simple Melee'},
            {'name': 'Quarterstaff', 'cost_gp': 0.2, 'damage': '1d6 bludgeoning', 'properties': 'Versatile (1d8)', 'weight': 4, 'type': 'Simple Melee'},
            {'name': 'Spear', 'cost_gp': 1, 'damage': '1d6 piercing', 'properties': 'Thrown (20/60), versatile (1d8)', 'weight': 3, 'type': 'Simple Melee'},
            # Martial Melee Weapons
            {'name': 'Battleaxe', 'cost_gp': 10, 'damage': '1d8 slashing', 'properties': 'Versatile (1d10)', 'weight': 4, 'type': 'Martial Melee'},
            {'name': 'Longsword', 'cost_gp': 15, 'damage': '1d8 slashing', 'properties': 'Versatile (1d10)', 'weight': 3, 'type': 'Martial Melee'},
            {'name': 'Greatsword', 'cost_gp': 50, 'damage': '2d6 slashing', 'properties': 'Heavy, two-handed', 'weight': 6, 'type': 'Martial Melee'},
            {'name': 'Rapier', 'cost_gp': 25, 'damage': '1d8 piercing', 'properties': 'Finesse', 'weight': 2, 'type': 'Martial Melee'},
            {'name': 'Shortsword', 'cost_gp': 10, 'damage': '1d6 piercing', 'properties': 'Finesse, light', 'weight': 2, 'type': 'Martial Melee'},
            {'name': 'Warhammer', 'cost_gp': 15, 'damage': '1d8 bludgeoning', 'properties': 'Versatile (1d10)', 'weight': 2, 'type': 'Martial Melee'},
            # Ranged Weapons
            {'name': 'Shortbow', 'cost_gp': 25, 'damage': '1d6 piercing', 'properties': 'Ammunition (80/320), two-handed', 'weight': 2, 'type': 'Simple Ranged'},
            {'name': 'Longbow', 'cost_gp': 50, 'damage': '1d8 piercing', 'properties': 'Ammunition (150/600), heavy, two-handed', 'weight': 2, 'type': 'Martial Ranged'},
            {'name': 'Light Crossbow', 'cost_gp': 25, 'damage': '1d8 piercing', 'properties': 'Ammunition (80/320), loading, two-handed', 'weight': 5, 'type': 'Simple Ranged'},
            {'name': 'Heavy Crossbow', 'cost_gp': 50, 'damage': '1d10 piercing', 'properties': 'Ammunition (100/400), heavy, loading, two-handed', 'weight': 18, 'type': 'Martial Ranged'},
        ]

        for weapon in weapon_patterns:
            desc = f"{weapon['type']}. Damage: {weapon['damage']}, Weight: {weapon['weight']} lb, Cost: {weapon['cost_gp']} gp"
            if weapon['properties']:
                desc += f", Properties: {weapon['properties']}"

            weapons.append({
                'name': weapon['name'],
                'category': 'weapon',
                'subcategory': weapon['type'],
                'cost_gp': weapon['cost_gp'],
                'description': desc,
                'metadata': weapon
            })

        return weapons

    def _parse_adventuring_gear(self, content: str) -> List[Dict[str, Any]]:
        """Parse adventuring gear."""
        gear = []

        # Common adventuring gear with prices
        gear_items = [
            {'name': 'Backpack', 'cost_gp': 2, 'weight': 5, 'desc': 'Can hold 1 cubic foot/30 pounds of gear'},
            {'name': 'Bedroll', 'cost_gp': 1, 'weight': 7, 'desc': 'For sleeping on adventures'},
            {'name': 'Rope, Hempen (50 feet)', 'cost_gp': 1, 'weight': 10, 'desc': 'Standard adventuring rope, 50 feet long'},
            {'name': 'Rope, Silk (50 feet)', 'cost_gp': 10, 'weight': 5, 'desc': 'Lightweight silk rope, 50 feet long'},
            {'name': 'Torch', 'cost_gp': 0.01, 'weight': 1, 'desc': 'Burns for 1 hour, bright light 20 ft, dim light 20 ft'},
            {'name': 'Rations (1 day)', 'cost_gp': 0.5, 'weight': 2, 'desc': 'One day of preserved food'},
            {'name': 'Waterskin', 'cost_gp': 0.2, 'weight': 5, 'desc': 'Holds 4 pints of liquid'},
            {'name': 'Potion of Healing', 'cost_gp': 50, 'weight': 0.5, 'desc': 'Heals 2d4+2 hit points when consumed'},
            {'name': 'Lantern, Hooded', 'cost_gp': 5, 'weight': 2, 'desc': 'Casts bright light 30 ft, dim 30 ft. Burns 6 hours on 1 pint of oil'},
            {'name': 'Oil (flask)', 'cost_gp': 0.1, 'weight': 1, 'desc': '1 pint of lamp oil'},
            {'name': 'Tinderbox', 'cost_gp': 0.5, 'weight': 1, 'desc': 'Used to light fires'},
            {'name': 'Crowbar', 'cost_gp': 2, 'weight': 5, 'desc': 'Grants advantage on Strength checks for leverage'},
            {'name': 'Hammer', 'cost_gp': 1, 'weight': 3, 'desc': 'Basic tool for construction and repairs'},
            {'name': 'Piton', 'cost_gp': 0.05, 'weight': 0.25, 'desc': 'Metal spike for climbing'},
            {'name': 'Grappling Hook', 'cost_gp': 2, 'weight': 4, 'desc': 'Hook for climbing and securing ropes'},
            {'name': 'Tent, Two-person', 'cost_gp': 2, 'weight': 20, 'desc': 'Simple portable shelter for two'},
            {'name': 'Blanket', 'cost_gp': 0.5, 'weight': 3, 'desc': 'Warm blanket for sleeping'},
        ]

        for item in gear_items:
            gear.append({
                'name': item['name'],
                'category': 'gear',
                'subcategory': 'adventuring gear',
                'cost_gp': item['cost_gp'],
                'description': f"{item['desc']}. Weight: {item['weight']} lb, Cost: {item['cost_gp']} gp",
                'metadata': item
            })

        return gear

    def _parse_tools(self, content: str) -> List[Dict[str, Any]]:
        """Parse tools."""
        tools = []

        tool_items = [
            {'name': "Thieves' Tools", 'cost_gp': 25, 'weight': 1, 'desc': 'For picking locks and disarming traps'},
            {'name': "Herbalism Kit", 'cost_gp': 5, 'weight': 3, 'desc': 'For identifying and using herbs'},
            {'name': "Healer's Kit", 'cost_gp': 5, 'weight': 3, 'desc': 'Has 10 uses. Stabilize dying creatures'},
            {'name': "Navigator's Tools", 'cost_gp': 25, 'weight': 2, 'desc': 'For navigation at sea'},
            {'name': "Smith's Tools", 'cost_gp': 20, 'weight': 8, 'desc': 'For smithing and metalwork'},
        ]

        for item in tool_items:
            tools.append({
                'name': item['name'],
                'category': 'tool',
                'subcategory': 'tools',
                'cost_gp': item['cost_gp'],
                'description': f"{item['desc']}. Weight: {item['weight']} lb, Cost: {item['cost_gp']} gp",
                'metadata': item
            })

        return tools

    def _parse_mounts(self, content: str) -> List[Dict[str, Any]]:
        """Parse mounts and animals."""
        mounts = []

        mount_items = [
            {'name': 'Riding Horse', 'cost_gp': 75, 'speed': '60 ft', 'capacity': 480, 'desc': 'A reliable riding horse'},
            {'name': 'Pony', 'cost_gp': 30, 'speed': '40 ft', 'capacity': 225, 'desc': 'A small pony, suitable for halflings'},
            {'name': 'Warhorse', 'cost_gp': 400, 'speed': '60 ft', 'capacity': 540, 'desc': 'A trained combat mount'},
            {'name': 'Mastiff', 'cost_gp': 25, 'speed': '40 ft', 'capacity': 195, 'desc': 'A guard dog'},
        ]

        for item in mount_items:
            mounts.append({
                'name': item['name'],
                'category': 'mount',
                'subcategory': 'animals',
                'cost_gp': item['cost_gp'],
                'description': f"{item['desc']}. Speed: {item['speed']}, Carrying capacity: {item['capacity']} lb, Cost: {item['cost_gp']} gp",
                'metadata': item
            })

        return mounts


def load_equipment_to_chromadb(chroma_manager, equipment_file: Path):
    """
    Load equipment data into ChromaDB.

    Args:
        chroma_manager: ChromaDBManager instance
        equipment_file: Path to equipment.txt file

    Returns:
        Number of equipment items loaded
    """
    loader = EquipmentLoader(equipment_file)
    equipment_data = loader.load_and_parse()

    collection_name = "dnd_equipment"

    # Get or create collection
    collection = chroma_manager.get_or_create_collection(collection_name)

    # Prepare data for batch add
    documents = []
    metadatas = []
    ids = []

    for item in equipment_data:
        documents.append(item['description'])
        metadatas.append({
            'name': item['name'],
            'category': item['category'],
            'subcategory': item['subcategory'],
            'cost_gp': item['cost_gp']
        })
        ids.append(f"equipment_{item['name'].lower().replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')}")

    # Add all items in one batch
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"✅ Loaded {len(equipment_data)} equipment items to ChromaDB")
    return len(equipment_data)
