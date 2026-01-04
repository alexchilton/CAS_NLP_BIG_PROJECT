"""
World Builder - Creates the initial game world with locations and connections.

Provides pre-built starting locations and utilities for world generation.
"""

from typing import Dict, List
from dnd_rag_system.systems.game_state import Location, LocationType, GameSession


def create_starting_world() -> Dict[str, Location]:
    """
    Create the starting world with interconnected locations.
    
    Returns a dictionary of Location objects representing a small town
    with surrounding areas.
    """
    locations = {}
    
    # Central town hub
    locations["Town Square"] = Location(
        name="Town Square",
        location_type=LocationType.TOWN,
        description="The heart of the town, bustling with activity. Streets branch out in all directions. A fountain sits in the center where townsfolk gather.",
        is_safe=True,
        connections=["The Prancing Pony Inn", "Market Square", "Town Gates", "Temple District", "Adventurer's Guild Hall"]
    )
    
    # Tavern/Inn
    locations["The Prancing Pony Inn"] = Location(
        name="The Prancing Pony Inn",
        location_type=LocationType.TAVERN,
        description="A cozy tavern bustling with travelers and merchants. The smell of roasted meat and ale fills the air. Rooms are available for rent upstairs.",
        has_inn=True,
        is_safe=True,
        resident_npcs=["Barliman the Innkeeper"],
        connections=["Town Square"]
    )
    
    # Market/Shop
    locations["Market Square"] = Location(
        name="Market Square",
        location_type=LocationType.SHOP,
        description="A busy marketplace with stalls selling adventuring gear, potions, and supplies. Merchants call out their wares. Perfect for shopping before an adventure!",
        has_shop=True,
        is_safe=True,
        resident_npcs=["Greta the Merchant", "Old Tom the Blacksmith"],
        connections=["Town Square", "Town Gates"]
    )
    
    # Temple
    locations["Temple District"] = Location(
        name="Temple District",
        location_type=LocationType.TEMPLE,
        description="A peaceful area with temples to various gods. Clerics offer healing and blessings. The scent of incense fills the air.",
        has_shop=False,  # Could sell holy items
        is_safe=True,
        resident_npcs=["Father Marcus", "Sister Helena"],
        connections=["Town Square"]
    )
    
    # Guild Hall
    locations["Adventurer's Guild Hall"] = Location(
        name="Adventurer's Guild Hall",
        location_type=LocationType.GUILD_HALL,
        description="A gathering place for heroes seeking quests and glory. Notice boards line the walls with job postings. A small shop in the corner sells equipment.",
        has_shop=True,
        is_safe=True,
        resident_npcs=["Guild Master Thornbrook"],
        connections=["Town Square"]
    )
    
    # Town Gates (transition to wilderness)
    locations["Town Gates"] = Location(
        name="Town Gates",
        location_type=LocationType.TOWN,
        description="The entrance to town, where the road stretches out toward adventure. Guards keep watch. Beyond lies wilderness and danger.",
        is_safe=True,
        resident_npcs=["Guard Captain Ironhelm"],
        connections=["Town Square", "Market Square", "Forest Path", "Mountain Road"]
    )
    
    # Wilderness areas (dangerous, not safe for resting)
    locations["Forest Path"] = Location(
        name="Forest Path",
        location_type=LocationType.FOREST,
        description="A winding path through dense woods. Sunlight filters through the canopy. You hear rustling in the undergrowth. Wolves are known to prowl these woods.",
        is_safe=False,
        connections=["Town Gates", "Dark Cave", "Old Ruins"]
    )
    
    locations["Mountain Road"] = Location(
        name="Mountain Road",
        location_type=LocationType.MOUNTAIN,
        description="A rocky path leading into the mountains. The air grows colder as you climb. Orcs have been spotted in these peaks.",
        is_safe=False,
        connections=["Town Gates", "Dragon's Lair"]
    )
    
    # Dungeons (dangerous)
    locations["Dark Cave"] = Location(
        name="Dark Cave",
        location_type=LocationType.CAVE,
        description="A dark, damp cave entrance. The smell of decay wafts out. Goblins are said to nest deep within. Treasure may await the brave.",
        is_safe=False,
        is_discovered=False,  # Must be found first
        connections=["Forest Path"]
    )
    
    locations["Old Ruins"] = Location(
        name="Old Ruins",
        location_type=LocationType.RUINS,
        description="Crumbling stone structures covered in vines. Ancient magic lingers here. Undead guardians protect forgotten treasures.",
        is_safe=False,
        is_discovered=False,
        connections=["Forest Path"]
    )
    
    locations["Dragon's Lair"] = Location(
        name="Dragon's Lair",
        location_type=LocationType.CAVE,
        description="A massive cavern deep in the mountains. Treasure glitters in piles. The air is thick with the smell of sulfur. A dragon's roar echoes from within.",
        is_safe=False,
        is_discovered=False,
        connections=["Mountain Road"]
    )
    
    # Mürren - Dangerous mountain village
    locations["Mürren"] = Location(
        name="Mürren",
        location_type=LocationType.MOUNTAIN,
        description="A remote mountain village perched high in the Alps. The air is thin and cold. Despite its beauty, danger lurks - giants roam the peaks, and deadly ice elementals guard ancient treasures in the glaciers above. Only the brave venture here.",
        is_safe=False,  # Dangerous!
        has_shop=True,  # Small trading post for mountaineers
        has_inn=True,  # Shelter from the cold
        resident_npcs=["Erik the Mountain Guide", "Heidi the Herbalist"],
        connections=["Mountain Road"]
    )
    
    # Add Mürren to Mountain Road connections
    locations["Mountain Road"].add_connection("Mürren")
    
    return locations


def initialize_world(game_session: GameSession, starting_location: str = "Town Square"):
    """
    Initialize the game world with starting locations.
    
    Args:
        game_session: GameSession to initialize
        starting_location: Where to start the player (default: Town Square)
    """
    # Create all locations
    locations = create_starting_world()
    
    # Add to game session
    for loc_name, location in locations.items():
        game_session.add_location(location)
    
    # Set starting location
    if starting_location in locations:
        game_session.set_location(starting_location, locations[starting_location].description)
    else:
        # Default to Town Square if invalid starting location
        game_session.set_location("Town Square", locations["Town Square"].description)


def get_random_starting_location() -> str:
    """
    Get a random safe starting location from the world.
    
    Returns the location name (not the full Location object).
    """
    import random
    safe_starts = [
        "Town Square",
        "The Prancing Pony Inn",
        "Market Square",
        "Temple District",
        "Adventurer's Guild Hall",
        "Town Gates"
    ]
    return random.choice(safe_starts)


def create_custom_location(
    name: str,
    location_type: LocationType,
    description: str,
    **kwargs
) -> Location:
    """
    Create a custom location with specified parameters.
    
    Args:
        name: Location name
        location_type: Type of location
        description: Description text
        **kwargs: Additional Location parameters (has_shop, is_safe, etc.)
    
    Returns:
        New Location object
    """
    return Location(
        name=name,
        location_type=location_type,
        description=description,
        **kwargs
    )


def generate_random_location(from_location: Location, direction: str = None) -> Location:
    """
    Lazily generate a new location based on the current location and context.
    
    This creates procedurally generated areas for exploration without
    pre-defining the entire world.
    
    Args:
        from_location: The location we're exploring from
        direction: Optional direction/hint for generation (e.g., "north", "deeper")
    
    Returns:
        Newly generated Location
    """
    import random
    
    # Determine what type of location to generate based on current type
    if from_location.location_type in [LocationType.TOWN, LocationType.TAVERN, LocationType.SHOP]:
        # From safe areas, generate wilderness or roads
        possible_types = [LocationType.FOREST, LocationType.WILDERNESS, LocationType.MOUNTAIN]
        weights = [0.4, 0.4, 0.2]
    elif from_location.location_type in [LocationType.FOREST, LocationType.WILDERNESS]:
        # From wilderness, can find dungeons or more wilderness
        possible_types = [LocationType.CAVE, LocationType.RUINS, LocationType.FOREST, LocationType.WILDERNESS]
        weights = [0.3, 0.2, 0.25, 0.25]
    elif from_location.location_type == LocationType.MOUNTAIN:
        # Mountains can have caves or castles
        possible_types = [LocationType.CAVE, LocationType.CASTLE, LocationType.RUINS]
        weights = [0.5, 0.2, 0.3]
    else:
        # Dungeons lead to more dungeons or back to wilderness
        possible_types = [LocationType.CAVE, LocationType.RUINS, LocationType.DUNGEON]
        weights = [0.4, 0.3, 0.3]
    
    location_type = random.choices(possible_types, weights=weights)[0]
    
    # Generate name based on type
    name_prefixes = {
        LocationType.FOREST: ["Dark", "Whispering", "Ancient", "Misty", "Shadowed"],
        LocationType.CAVE: ["Deep", "Hidden", "Crystal", "Forgotten", "Echoing"],
        LocationType.RUINS: ["Ancient", "Cursed", "Forgotten", "Overgrown", "Crumbling"],
        LocationType.MOUNTAIN: ["Lonely", "Frozen", "Thunder", "Giant's", "Eagle's"],
        LocationType.WILDERNESS: ["Barren", "Wild", "Trackless", "Lost", "Windswept"],
        LocationType.CASTLE: ["Ruined", "Abandoned", "Haunted", "Broken", "Old"],
        LocationType.DUNGEON: ["Deep", "Dark", "Abandoned", "Ancient", "Cursed"]
    }
    
    name_suffixes = {
        LocationType.FOREST: ["Woods", "Grove", "Forest", "Thicket"],
        LocationType.CAVE: ["Cavern", "Grotto", "Cave", "Hollow"],
        LocationType.RUINS: ["Ruins", "Temple", "Keep", "Monastery"],
        LocationType.MOUNTAIN: ["Peak", "Summit", "Crag", "Ridge"],
        LocationType.WILDERNESS: ["Plains", "Moors", "Barrens", "Wastes"],
        LocationType.CASTLE: ["Castle", "Fortress", "Stronghold", "Citadel"],
        LocationType.DUNGEON: ["Depths", "Dungeon", "Catacombs", "Labyrinth"]
    }
    
    prefix = random.choice(name_prefixes[location_type])
    suffix = random.choice(name_suffixes[location_type])
    name = f"{prefix} {suffix}"
    
    # Generate description
    descriptions = {
        LocationType.FOREST: [
            f"A dense forest where sunlight barely penetrates the canopy. Strange sounds echo through the trees.",
            f"Towering trees surround you, their branches forming a natural cathedral overhead.",
            f"The forest path winds between ancient oaks. You sense eyes watching from the shadows."
        ],
        LocationType.CAVE: [
            f"A dark cave entrance yawns before you. The air is cold and damp, carrying strange echoes.",
            f"Natural stone formations create an otherworldly landscape. Water drips somewhere in the darkness.",
            f"The cave walls glitter with mineral deposits. Deep passages lead into the unknown."
        ],
        LocationType.RUINS: [
            f"Crumbling stone structures speak of a forgotten civilization. Vines reclaim what was once grand.",
            f"Ancient architecture lies in ruins, yet hints of former glory remain visible.",
            f"Weathered statues guard empty halls. What secrets lie buried here?"
        ],
        LocationType.MOUNTAIN: [
            f"Rocky crags tower above. The air is thin and cold. Snow clings to the highest peaks.",
            f"A treacherous mountain path winds upward. One wrong step could be fatal.",
            f"The mountain looms, stark and imposing. Ancient caves dot its flanks."
        ],
        LocationType.WILDERNESS: [
            f"Empty land stretches endlessly. No roads, no shelter, just raw nature.",
            f"A desolate expanse where few dare to tread. Wind howls across open ground.",
            f"Trackless wilderness extends in all directions. Navigation will be difficult."
        ],
        LocationType.CASTLE: [
            f"A ruined castle emerges from the landscape. Its walls are broken but still imposing.",
            f"Once-mighty fortifications now stand empty. What drove its inhabitants away?",
            f"The castle's towers lean at dangerous angles. Its halls echo with memory of battles long past."
        ],
        LocationType.DUNGEON: [
            f"Stone stairs descend into darkness. The air smells of decay and ancient evil.",
            f"Passages extend deeper underground. Torchlight flickers on damp walls.",
            f"This place was built as a prison, or perhaps a tomb. Either way, it's not welcoming."
        ]
    }
    
    description = random.choice(descriptions[location_type])
    
    # Determine if it's safe (most generated locations are dangerous)
    is_safe = location_type in [LocationType.TOWN, LocationType.TAVERN, LocationType.SHOP, LocationType.TEMPLE]
    
    # Create the location
    # Initially undiscovered - will be marked discovered when added to world_map
    return Location(
        name=name,
        location_type=location_type,
        description=description,
        is_safe=is_safe,
        is_discovered=False,  # Will be marked discovered when /explore adds to world_map
        connections=[from_location.name]  # Connected back to where we came from
    )


def generate_llm_enhanced_location(
    from_location: Location,
    llm_generate_func,
    game_context: dict = None
) -> Location:
    """
    Generate a new location with LLM-created name and description.
    
    Uses Python for structure (type, safety, connections) and LLM for flavor
    (unique name and rich description based on context).
    
    Args:
        from_location: The location we're exploring from
        llm_generate_func: Function that calls LLM and returns response string
        game_context: Optional dict with game state context (npcs, defeated_enemies, etc.)
    
    Returns:
        Newly generated Location with LLM-enhanced name and description
    """
    import random
    import re
    
    # Step 1: Python determines structure (same logic as generate_random_location)
    if from_location.location_type in [LocationType.TOWN, LocationType.TAVERN, LocationType.SHOP]:
        possible_types = [LocationType.FOREST, LocationType.WILDERNESS, LocationType.MOUNTAIN]
        weights = [0.4, 0.4, 0.2]
    elif from_location.location_type in [LocationType.FOREST, LocationType.WILDERNESS]:
        possible_types = [LocationType.CAVE, LocationType.RUINS, LocationType.FOREST, LocationType.WILDERNESS]
        weights = [0.3, 0.2, 0.25, 0.25]
    elif from_location.location_type == LocationType.MOUNTAIN:
        possible_types = [LocationType.CAVE, LocationType.CASTLE, LocationType.RUINS]
        weights = [0.5, 0.2, 0.3]
    else:
        possible_types = [LocationType.CAVE, LocationType.RUINS, LocationType.DUNGEON]
        weights = [0.4, 0.3, 0.3]
    
    location_type = random.choices(possible_types, weights=weights)[0]
    is_safe = location_type in [LocationType.TOWN, LocationType.TAVERN, LocationType.SHOP, LocationType.TEMPLE]
    
    # Step 2: Build context for LLM
    context_parts = []
    context_parts.append(f"Current location: {from_location.name} ({from_location.location_type.value})")
    
    if game_context:
        if game_context.get('npcs_present'):
            context_parts.append(f"NPCs nearby: {', '.join(game_context['npcs_present'])}")
        if game_context.get('defeated_enemies'):
            context_parts.append(f"Recent battles: Defeated {', '.join(list(game_context['defeated_enemies'])[:3])}")
        if game_context.get('time_of_day'):
            context_parts.append(f"Time: {game_context['time_of_day']}")
        if game_context.get('weather'):
            context_parts.append(f"Weather: {game_context['weather']}")
    
    context_str = "\n".join(context_parts)
    
    # Step 3: LLM prompt for name and description
    prompt = f"""You are exploring from {from_location.name}. Generate a NEW location discovery.

CONTEXT:
{context_str}

NEW LOCATION TYPE: {location_type.value}
SAFETY: {'SAFE area (town, temple, shop)' if is_safe else 'DANGEROUS wilderness/dungeon'}

Generate EXACTLY in this format:
NAME: [Unique, evocative name for this {location_type.value}]
DESCRIPTION: [2-3 vivid sentences describing what you see, hear, smell. Make it atmospheric and specific to the context.]

Requirements:
- Name should be unique and memorable (not generic like "Dark Cave")
- Description should reference the context (e.g., mention recent battles, weather, time of day)
- Keep it concise but evocative
- Make it feel like D&D exploration

Generate the location:"""
    
    # Step 4: Call LLM
    try:
        llm_response = llm_generate_func(prompt)
        
        # Step 5: Parse LLM response
        name_match = re.search(r'NAME:\s*(.+?)(?:\n|$)', llm_response, re.IGNORECASE)
        desc_match = re.search(r'DESCRIPTION:\s*(.+?)(?:\n\n|$)', llm_response, re.IGNORECASE | re.DOTALL)
        
        if name_match and desc_match:
            name = name_match.group(1).strip()
            description = desc_match.group(1).strip()
            
            # Clean up any quotes or extra whitespace
            name = name.strip('"\'')
            description = description.strip()
            
        else:
            # Fallback to template if parsing fails
            import logging
            logging.warning(f"Failed to parse LLM location response, using template fallback")
            fallback_loc = generate_random_location(from_location)
            name = fallback_loc.name
            description = fallback_loc.description
    
    except Exception as e:
        # If LLM fails, fallback to template
        import logging
        logging.error(f"LLM location generation failed: {e}, using template fallback")
        fallback_loc = generate_random_location(from_location)
        name = fallback_loc.name
        description = fallback_loc.description
    
    # Step 6: Create and return Location
    # Initially undiscovered - will be marked discovered when added to world_map
    return Location(
        name=name,
        location_type=location_type,
        description=description,
        is_safe=is_safe,
        is_discovered=False,  # Will be marked discovered when /explore adds to world_map
        connections=[from_location.name]
    )
