"""
Test location-aware encounter generation.

Verifies that encounters match location types appropriately.
"""

import pytest
from dnd_rag_system.systems.encounter_system import EncounterSystem


class TestLocationAwareEncounters:
    """Test that monster encounters match their environments."""
    
    def test_cave_monsters_appropriate(self):
        """Test that caves spawn underground creatures."""
        encounter_sys = EncounterSystem(chromadb_manager=None)  # No RAG, use fallback
        
        # Generate 20 encounters in caves
        cave_monsters = []
        for _ in range(20):
            monster = encounter_sys._get_fallback_monster_by_location("cave", min_cr=0, max_cr=3)
            cave_monsters.append(monster['name'])
        
        print(f"\n🕳️ Cave encounters: {set(cave_monsters)}")
        
        # Should be underground creatures
        underground_creatures = {"Goblin", "Kobold", "Bugbear", "Ogre", "Hobgoblin", "Orc Scout", 
                                "Giant Bat", "Giant Spider", "Duergar", "Quaggoth"}
        
        # At least some should be underground-appropriate
        matches = [m for m in cave_monsters if m in underground_creatures]
        assert len(matches) > 0, f"Cave should spawn underground creatures, got: {cave_monsters}"
        
        # Should NOT spawn forest creatures like Wolves or Bears (unless fallback triggered)
        forest_only = {"Brown Bear", "Dryad", "Treant"}
        forest_spawns = [m for m in cave_monsters if m in forest_only]
        assert len(forest_spawns) == 0, f"Cave shouldn't spawn forest creatures: {forest_spawns}"
    
    def test_forest_monsters_appropriate(self):
        """Test that forests spawn woodland creatures."""
        encounter_sys = EncounterSystem()
        
        forest_monsters = []
        for _ in range(20):
            monster = encounter_sys._get_fallback_monster_by_location("forest", min_cr=0, max_cr=3)
            forest_monsters.append(monster['name'])
        
        print(f"\n🌲 Forest encounters: {set(forest_monsters)}")
        
        # Should include forest/woodland creatures
        woodland_creatures = {"Wolf", "Boar", "Dire Wolf", "Goblin", "Orc", "Gnoll", 
                             "Owlbear", "Brown Bear", "Bugbear", "Bandit"}
        
        matches = [m for m in forest_monsters if m in woodland_creatures]
        assert len(matches) > 0, "Forest should spawn woodland creatures"
    
    def test_mountain_monsters_appropriate(self):
        """Test that mountains spawn alpine creatures."""
        encounter_sys = EncounterSystem()
        
        mountain_monsters = []
        for _ in range(20):
            monster = encounter_sys._get_fallback_monster_by_location("mountain", min_cr=0, max_cr=5)
            mountain_monsters.append(monster['name'])
        
        print(f"\n⛰️ Mountain encounters: {set(mountain_monsters)}")
        
        # Should include mountain creatures
        alpine_creatures = {"Kobold", "Harpy", "Hippogriff", "Hill Giant", "Stone Giant",
                           "Ogre", "Manticore", "Griffon", "Eagle"}
        
        matches = [m for m in mountain_monsters if m in alpine_creatures]
        assert len(matches) > 0, "Mountains should spawn alpine creatures"
    
    def test_ruins_monsters_appropriate(self):
        """Test that ruins spawn undead and constructs."""
        encounter_sys = EncounterSystem()
        
        ruins_monsters = []
        for _ in range(20):
            monster = encounter_sys._get_fallback_monster_by_location("ruins", min_cr=0, max_cr=3)
            ruins_monsters.append(monster['name'])
        
        print(f"\n🏛️ Ruins encounters: {set(ruins_monsters)}")
        
        # Should include undead/constructs
        ruin_creatures = {"Skeleton", "Zombie", "Shadow", "Ghoul", "Specter", "Wight",
                         "Gargoyle", "Mimic", "Animated Armor", "Mummy"}
        
        matches = [m for m in ruins_monsters if m in ruin_creatures]
        assert len(matches) > 0, "Ruins should spawn undead/constructs"
        
        # Should NOT spawn living beasts
        living_beasts = {"Wolf", "Bear", "Boar"}
        beast_spawns = [m for m in ruins_monsters if m in living_beasts]
        assert len(beast_spawns) == 0, f"Ruins shouldn't spawn living beasts: {beast_spawns}"
    
    def test_dungeon_variety(self):
        """Test that dungeons have mixed creature types."""
        encounter_sys = EncounterSystem()
        
        dungeon_monsters = []
        for _ in range(30):
            monster = encounter_sys._get_fallback_monster_by_location("dungeon", min_cr=0, max_cr=5)
            dungeon_monsters.append(monster['name'])
        
        unique_monsters = set(dungeon_monsters)
        print(f"\n🏰 Dungeon encounters ({len(unique_monsters)} unique): {unique_monsters}")
        
        # Dungeons should have variety (humanoids, undead, aberrations)
        assert len(unique_monsters) >= 5, "Dungeons should have variety of creatures"
    
    def test_cr_range_respected(self):
        """Test that CR ranges are respected in location-aware queries."""
        encounter_sys = EncounterSystem()
        
        # Low level characters in cave (CR 0-1)
        for _ in range(10):
            monster = encounter_sys._get_fallback_monster_by_location("cave", min_cr=0, max_cr=1)
            assert monster['cr'] <= 1, f"Monster CR {monster['cr']} exceeds max of 1"
        
        # High level characters in cave (CR 5-8)
        for _ in range(10):
            monster = encounter_sys._get_fallback_monster_by_location("cave", min_cr=5, max_cr=8)
            assert monster['cr'] >= 5, f"Monster CR {monster['cr']} below min of 5"
            assert monster['cr'] <= 8, f"Monster CR {monster['cr']} exceeds max of 8"
        
        print("✅ CR ranges properly enforced")
    
    def test_unknown_location_fallback(self):
        """Test that unknown locations use generic fallback."""
        encounter_sys = EncounterSystem()
        
        # Query for location type we haven't defined
        monster = encounter_sys._get_fallback_monster_by_location("spaceship", min_cr=1, max_cr=3)
        
        # Should still return a monster (generic fallback)
        assert monster is not None
        assert 'name' in monster
        assert 'cr' in monster
        assert 1 <= monster['cr'] <= 3
        
        print(f"✅ Unknown location fallback: {monster['name']} (CR {monster['cr']})")
    
    def test_environment_keywords_defined(self):
        """Test that environment keywords are defined for all location types."""
        encounter_sys = EncounterSystem()
        
        common_locations = ["cave", "forest", "mountain", "ruins", "dungeon", "wilderness"]
        
        for loc in common_locations:
            assert loc in encounter_sys.LOCATION_TO_ENVIRONMENT, \
                f"Missing environment keywords for {loc}"
            keywords = encounter_sys.LOCATION_TO_ENVIRONMENT[loc]
            assert len(keywords) > 0, f"No keywords for {loc}"
            print(f"  {loc}: {keywords}")
        
        print("✅ All location types have environment keywords")
    
    def test_full_encounter_generation_cave(self):
        """Test full encounter generation for cave."""
        encounter_sys = EncounterSystem()
        
        # Simulate 10 encounter checks in a cave
        encounters_generated = 0
        monster_names = []
        
        for _ in range(30):  # Try 30 times, should get some encounters
            encounter = encounter_sys.generate_encounter("cave", character_level=3)
            if encounter:
                encounters_generated += 1
                monster_names.append(encounter.monster_name)
        
        print(f"\n🎲 Cave encounter rate: {encounters_generated}/30")
        print(f"   Monsters spawned: {set(monster_names)}")
        
        # Should have triggered some encounters (45% rate in caves)
        assert encounters_generated > 0, "Should generate at least some encounters"
        
        # All monsters should be cave-appropriate (when using fallback)
        # Note: If RAG is working, this might vary
    
    def test_safe_location_low_encounter_rate(self):
        """Test that safe locations have very low encounter rates."""
        encounter_sys = EncounterSystem()
        
        # Try 100 encounter checks in a shop (0% rate)
        shop_encounters = 0
        for _ in range(100):
            encounter = encounter_sys.generate_encounter("shop", character_level=5)
            if encounter:
                shop_encounters += 1
        
        assert shop_encounters == 0, "Shops should never have encounters"
        
        # Try in town (3% rate) - might get a few
        town_encounters = 0
        for _ in range(100):
            encounter = encounter_sys.generate_encounter("town", character_level=5)
            if encounter:
                town_encounters += 1
        
        # Should be rare
        assert town_encounters < 15, f"Towns should have low encounter rate, got {town_encounters}/100"
        print(f"✅ Safe locations: Shop=0/100, Town={town_encounters}/100")


if __name__ == "__main__":
    print("🧪 Location-Aware Encounter Tests")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s"])
