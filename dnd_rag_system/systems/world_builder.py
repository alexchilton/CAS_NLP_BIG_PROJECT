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
