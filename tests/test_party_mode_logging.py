
#!/usr/bin/env python3
"""
Test Party Mode with Debug Logging

This script creates a party with multiple characters and sends a command to the GM,
showing exactly what prompt gets sent to the LLM.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.systems.character_creator import Character

print("=" * 80)
print("🧪 PARTY MODE LOGGING TEST")
print("=" * 80)
print("\nThis test creates a 3-character party and sends a command to the GM.")
print("With GM_DEBUG=true, you'll see the FULL prompt sent to the LLM.\n")
print("=" * 80)

# Initialize GM
print("\n📋 Initializing GM...")
db = ChromaDBManager()
gm = GameMaster(db)

# Create a diverse party of 3 characters
print("\n👥 Creating party of 3 adventurers...")

warrior = Character(
    name='Thorin Ironforge',
    race='Dwarf',
    character_class='Fighter',
    level=5,
    strength=18,
    dexterity=12,
    constitution=16,
    intelligence=10,
    wisdom=11,
    charisma=8,
    hit_points=52,
    armor_class=18,
    proficiency_bonus=3,
    background='Soldier',
    alignment='Lawful Good',
    equipment=['Battleaxe', 'Shield', 'Plate Armor', 'Healing Potion (x2)', '100 GP'],
    spells=[]
)

wizard = Character(
    name='Elara Starweaver',
    race='Elf',
    character_class='Wizard',
    level=5,
    strength=8,
    dexterity=14,
    constitution=12,
    intelligence=18,
    wisdom=13,
    charisma=11,
    hit_points=28,
    armor_class=12,
    proficiency_bonus=3,
    background='Sage',
    alignment='Neutral Good',
    equipment=['Quarterstaff', 'Spellbook', 'Robes', 'Component Pouch', '75 GP'],
    spells=['Fireball', 'Magic Missile', 'Shield', 'Detect Magic', 'Identify']
)

rogue = Character(
    name='Shadow Swift',
    race='Halfling',
    character_class='Rogue',
    level=5,
    strength=10,
    dexterity=18,
    constitution=13,
    intelligence=12,
    wisdom=14,
    charisma=15,
    hit_points=35,
    armor_class=15,
    proficiency_bonus=3,
    background='Criminal',
    alignment='Chaotic Neutral',
    equipment=['Shortsword (x2)', 'Leather Armor', 'Thieves Tools', 'Lockpicks', '150 GP'],
    spells=[]
)

party = {
    'Thorin Ironforge': warrior,
    'Elara Starweaver': wizard,
    'Shadow Swift': rogue
}

print(f"   ✅ {warrior.name} - {warrior.race} {warrior.character_class}, Level {warrior.level}")
print(f"   ✅ {wizard.name} - {wizard.race} {wizard.character_class}, Level {wizard.level}")
print(f"   ✅ {rogue.name} - {rogue.race} {rogue.character_class}, Level {rogue.level}")

# Set the scene first
print("\n🏰 Setting up the scene...")
gm.set_location("Ancient Dungeon Entrance", "")
gm.add_npc("Stone Guardian (Hostile)")
gm.add_npc("Mysterious Hooded Figure (Unknown)")

# Build party context WITH scene description (similar to what load_party_mode() does)
print("\n🎭 Building party context for GM...")
party_info = []
for char_name, char in party.items():
    mods = char.get_modifiers()
    party_info.append(f"""
**{char.name}** - {char.race} {char.character_class}, Level {char.level}
- HP: {char.hit_points}  |  AC: {char.armor_class}  |  Prof Bonus: +{char.proficiency_bonus}
- STR: {char.strength} ({mods['strength']:+d})  |  DEX: {char.dexterity} ({mods['dexterity']:+d})  |  CON: {char.constitution} ({mods['constitution']:+d})
- INT: {char.intelligence} ({mods['intelligence']:+d})  |  WIS: {char.wisdom} ({mods['wisdom']:+d})  |  CHA: {char.charisma} ({mods['charisma']:+d})
- Equipment: {', '.join(char.equipment[:3])}""")

scene_with_party = f"""The party stands before a massive stone doorway carved with dwarven runes. A faint blue light emanates from within.

THE ADVENTURING PARTY consists of {len(party)} members:
{chr(10).join(party_info)}

Party Gold: 325 GP (pooled)"""

gm.set_context(scene_with_party)
print("   ✅ Party context set with scene description")

print("   ✅ Location: Ancient Dungeon Entrance")
print("   ✅ NPCs: Stone Guardian, Mysterious Hooded Figure")

# Send a party command
print("\n" + "=" * 80)
print("📤 SENDING PARTY COMMAND TO GM")
print("=" * 80)
print("\n🎬 Party Action: 'The party cautiously approaches the entrance. Thorin examines")
print("   the runes, Elara detects for magic, and Shadow checks for traps.'\n")
print("-" * 80)
print("⚠️  WITH GM_DEBUG=true, YOU WILL SEE:")
print("   1. The FULL prompt sent to the LLM (including all party member stats)")
print("   2. The location and NPC information")
print("   3. The complete game state context")
print("-" * 80)

player_action = """The party cautiously approaches the entrance. Thorin examines the runes,
Elara casts Detect Magic, and Shadow checks for traps."""

# This will trigger debug logging if GM_DEBUG=true
response = gm.generate_response(player_action, use_rag=False)

print("\n" + "=" * 80)
print("📥 GM RESPONSE:")
print("=" * 80)
print(response)
print("\n" + "=" * 80)
print("\n✅ Test completed!")
print("\nTo see the FULL prompt, run this script with: GM_DEBUG=true python3 test_party_mode_logging.py")
print("=" * 80)
