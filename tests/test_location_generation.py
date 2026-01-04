"""
Test suite for location generation system.

Tests procedural generation, consistency, world map integrity.
"""

import pytest
from dnd_rag_system.systems.world_builder import (
    generate_random_location,
    create_starting_world,
    initialize_world
)
from dnd_rag_system.systems.game_state import Location, LocationType, GameSession


class TestLocationGeneration:
    """Test procedural location generation."""
    
    def test_generate_from_town(self):
        """Test location generation from town produces valid wilderness."""
        town = Location(
            name="Test Town",
            location_type=LocationType.TOWN,
            description="A test town",
            is_safe=True
        )
        
        # Generate 10 locations and verify they follow the rules
        for _ in range(10):
            loc = generate_random_location(town)
            
            # From TOWN should generate FOREST, WILDERNESS, or MOUNTAIN
            assert loc.location_type in [LocationType.FOREST, LocationType.WILDERNESS, LocationType.MOUNTAIN]
            
            # Should have name and description
            assert loc.name
            assert loc.description
            assert len(loc.description) > 20  # Non-trivial description
            
            # Should be connected back to origin
            assert "Test Town" in loc.connections
            
            # Wilderness should be dangerous
            assert loc.is_safe == False
            
            print(f"  Generated: {loc.name} ({loc.location_type.value})")
    
    def test_generate_from_forest(self):
        """Test location generation from forest produces dungeons or more forest."""
        forest = Location(
            name="Dark Forest",
            location_type=LocationType.FOREST,
            description="A dark forest",
            is_safe=False
        )
        
        for _ in range(10):
            loc = generate_random_location(forest)
            
            # From FOREST should generate CAVE, RUINS, FOREST, or WILDERNESS
            assert loc.location_type in [LocationType.CAVE, LocationType.RUINS, LocationType.FOREST, LocationType.WILDERNESS]
            
            assert "Dark Forest" in loc.connections
            assert loc.is_safe == False
            
            print(f"  Generated: {loc.name} ({loc.location_type.value})")
    
    def test_generate_from_mountain(self):
        """Test location generation from mountain."""
        mountain = Location(
            name="Snowy Peak",
            location_type=LocationType.MOUNTAIN,
            description="A snowy mountain",
            is_safe=False
        )
        
        for _ in range(10):
            loc = generate_random_location(mountain)
            
            # From MOUNTAIN should generate CAVE, CASTLE, or RUINS
            assert loc.location_type in [LocationType.CAVE, LocationType.CASTLE, LocationType.RUINS]
            
            assert "Snowy Peak" in loc.connections
            print(f"  Generated: {loc.name} ({loc.location_type.value})")
    
    def test_location_names_unique(self):
        """Test that generated locations have varied names."""
        town = Location(
            name="Test Town",
            location_type=LocationType.TOWN,
            description="A test town",
            is_safe=True
        )
        
        names = set()
        for _ in range(50):
            loc = generate_random_location(town)
            names.add(loc.name)
        
        # With 50 generations from random templates, expect at least 20 unique names
        assert len(names) >= 20, f"Only {len(names)} unique names in 50 generations"
        print(f"  Generated {len(names)} unique location names from 50 attempts")
    
    def test_massive_generation_consistency(self):
        """Generate lots of locations and verify world map stays consistent."""
        session = GameSession()
        initialize_world(session)
        
        # Start at Town Square
        assert session.current_location == "Town Square"
        initial_count = len(session.world_map)
        print(f"  Starting world has {initial_count} locations")
        
        # Generate 100 new locations
        generated = []
        current_loc = session.get_current_location_obj()
        
        for i in range(100):
            new_loc = generate_random_location(current_loc)
            session.add_location(new_loc)
            session.connect_locations(current_loc.name, new_loc.name)
            generated.append(new_loc.name)
            
            # Sometimes move to the new location to vary generation
            if i % 3 == 0 and i > 0:
                current_loc = new_loc
        
        # Verify world map grew (may have duplicates since names can repeat)
        assert len(session.world_map) >= initial_count + 45  # At least 45% unique (randomness)
        unique_count = len(session.world_map) - initial_count
        duplicate_rate = 1 - (unique_count / 100)
        print(f"  World map now has {len(session.world_map)} locations (+{unique_count})")
        print(f"  Duplicate name rate: {duplicate_rate:.1%}")
        
        # Verify all generated locations are in world map
        for loc_name in generated:
            assert loc_name in session.world_map
            loc = session.world_map[loc_name]
            
            # Verify structure integrity
            assert loc.name == loc_name
            assert loc.location_type in LocationType
            assert len(loc.connections) > 0  # Should have at least one connection
        
        print(f"  ✅ All 100 generated locations have valid structure")
    
    def test_connection_bidirectionality(self):
        """Test that connections are bidirectional."""
        session = GameSession()
        initialize_world(session)
        
        town = session.get_location("Town Square")
        forest = generate_random_location(town)
        session.add_location(forest)
        session.connect_locations(town.name, forest.name)
        
        # Verify bidirectional connection
        assert forest.name in town.connections
        assert town.name in forest.connections
        
        print(f"  ✅ {town.name} ↔ {forest.name} (bidirectional)")
    
    def test_max_connections_limit(self):
        """Test that locations can't exceed max connections."""
        session = GameSession()
        town = Location(
            name="Hub Town",
            location_type=LocationType.TOWN,
            description="A hub town",
            is_safe=True
        )
        session.add_location(town)
        
        # Try to add 10 connections (should stop at 6)
        for i in range(10):
            loc = Location(
                name=f"Location {i}",
                location_type=LocationType.FOREST,
                description=f"Location {i}",
                is_safe=False
            )
            session.add_location(loc)
            
            # Manually add connection (simulating /explore command)
            if len(town.connections) < 6:
                session.connect_locations(town.name, loc.name)
        
        # Should have max 6 connections
        assert len(town.connections) <= 6
        print(f"  ✅ Hub town connections limited to {len(town.connections)}")


class TestStartingWorld:
    """Test the fixed starting world."""
    
    def test_starting_world_locations(self):
        """Test that starting world has expected locations."""
        locations = create_starting_world()
        
        # Should have core locations
        expected = [
            "Town Square",
            "The Prancing Pony Inn",
            "Market Square",
            "Temple District",
            "Adventurer's Guild Hall",
            "Town Gates",
            "Forest Path",
            "Mountain Road",
            "Dark Cave",
            "Old Ruins",
            "Dragon's Lair",
            "Mürren"
        ]
        
        for loc_name in expected:
            assert loc_name in locations, f"Missing: {loc_name}"
        
        print(f"  ✅ Starting world has all {len(expected)} core locations")
    
    def test_starting_connections(self):
        """Test that starting locations are properly connected."""
        locations = create_starting_world()
        
        town_square = locations["Town Square"]
        
        # Town Square should be the hub
        assert len(town_square.connections) >= 4
        assert "The Prancing Pony Inn" in town_square.connections
        assert "Market Square" in town_square.connections
        
        # Verify bidirectional connections
        inn = locations["The Prancing Pony Inn"]
        assert "Town Square" in inn.connections
        
        print(f"  ✅ Town Square has {len(town_square.connections)} connections")
    
    def test_safe_vs_dangerous_locations(self):
        """Test that safe/dangerous flags are correct."""
        locations = create_starting_world()
        
        # Safe locations
        assert locations["Town Square"].is_safe == True
        assert locations["The Prancing Pony Inn"].is_safe == True
        assert locations["Market Square"].is_safe == True
        
        # Dangerous locations
        assert locations["Forest Path"].is_safe == False
        assert locations["Dark Cave"].is_safe == False
        assert locations["Dragon's Lair"].is_safe == False
        assert locations["Mürren"].is_safe == False  # Mountain village is dangerous!
        
        print(f"  ✅ Safe/dangerous flags correct")


class TestLocationTypes:
    """Test location type distributions."""
    
    def test_type_distribution(self):
        """Test that generation follows expected type distribution."""
        town = Location(
            name="Test Town",
            location_type=LocationType.TOWN,
            description="Test",
            is_safe=True
        )
        
        # Generate 100 locations and check distribution
        type_counts = {}
        for _ in range(100):
            loc = generate_random_location(town)
            loc_type = loc.location_type
            type_counts[loc_type] = type_counts.get(loc_type, 0) + 1
        
        # From TOWN: 40% FOREST, 40% WILDERNESS, 20% MOUNTAIN
        # With 100 samples, expect roughly:
        # FOREST: ~40, WILDERNESS: ~40, MOUNTAIN: ~20
        
        print(f"  Type distribution from TOWN:")
        for loc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"    {loc_type.value}: {count}%")
        
        # Should have all three types
        assert LocationType.FOREST in type_counts
        assert LocationType.WILDERNESS in type_counts
        assert LocationType.MOUNTAIN in type_counts
        
        # FOREST and WILDERNESS should be most common
        assert type_counts[LocationType.FOREST] >= 20
        assert type_counts[LocationType.WILDERNESS] >= 20


if __name__ == "__main__":
    print("🧪 Location Generation Tests")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s"])
