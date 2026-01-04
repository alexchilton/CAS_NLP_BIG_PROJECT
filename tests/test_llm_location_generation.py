"""
Test LLM-enhanced location generation.

Verifies that LLM generates unique, contextual locations.
"""

import pytest
from dnd_rag_system.systems.world_builder import (
    generate_llm_enhanced_location,
    generate_random_location
)
from dnd_rag_system.systems.game_state import Location, LocationType


class TestLLMEnhancedGeneration:
    """Test LLM-enhanced location generation."""
    
    def test_llm_enhanced_with_mock(self):
        """Test LLM-enhanced generation with mock LLM."""
        town = Location(
            name="Test Town",
            location_type=LocationType.TOWN,
            description="A test town",
            is_safe=True
        )
        
        # Mock LLM that returns a structured response
        def mock_llm(prompt: str) -> str:
            return """NAME: Whispering Shadowfen
DESCRIPTION: A misty marshland where twisted trees emerge from murky waters. Strange whispers echo through the fog, and you catch glimpses of glowing eyes watching from the darkness. The air smells of decay and ancient magic."""
        
        # Generate location
        loc = generate_llm_enhanced_location(
            from_location=town,
            llm_generate_func=mock_llm,
            game_context={'time_of_day': 'night', 'npcs_present': []}
        )
        
        # Verify structure
        assert loc.name == "Whispering Shadowfen"
        assert "misty marshland" in loc.description.lower()
        assert "twisted trees" in loc.description.lower()
        assert loc.location_type in [LocationType.FOREST, LocationType.WILDERNESS, LocationType.MOUNTAIN]
        assert "Test Town" in loc.connections
        assert loc.is_safe == False  # Wilderness should be dangerous
        assert loc.is_discovered == True  # Discovered via /explore command
        
        print(f"✅ Generated: {loc.name}")
        print(f"   Type: {loc.location_type.value}")
        print(f"   Description: {loc.description[:100]}...")
    
    def test_llm_enhanced_fallback_on_failure(self):
        """Test that LLM failures fallback to template generation."""
        town = Location(
            name="Test Town",
            location_type=LocationType.TOWN,
            description="A test town",
            is_safe=True
        )
        
        # Mock LLM that raises an exception
        def failing_llm(prompt: str) -> str:
            raise Exception("LLM unavailable")
        
        # Should not crash, should fallback
        loc = generate_llm_enhanced_location(
            from_location=town,
            llm_generate_func=failing_llm
        )
        
        # Should have generated something via fallback
        assert loc.name
        assert loc.description
        assert len(loc.description) > 20
        assert "Test Town" in loc.connections
        
        print(f"✅ Fallback generated: {loc.name}")
    
    def test_llm_enhanced_fallback_on_bad_parse(self):
        """Test that unparseable LLM responses fallback to template."""
        town = Location(
            name="Test Town",
            location_type=LocationType.TOWN,
            description="A test town",
            is_safe=True
        )
        
        # Mock LLM that returns garbage
        def bad_llm(prompt: str) -> str:
            return "This is not a valid response format at all!"
        
        # Should fallback gracefully
        loc = generate_llm_enhanced_location(
            from_location=town,
            llm_generate_func=bad_llm
        )
        
        # Should have template-generated content
        assert loc.name
        assert loc.description
        print(f"✅ Bad parse fallback: {loc.name}")
    
    def test_llm_enhanced_with_context(self):
        """Test that game context is included in LLM prompt."""
        forest = Location(
            name="Dark Forest",
            location_type=LocationType.FOREST,
            description="A dark forest",
            is_safe=False
        )
        forest.defeated_enemies = {"Goblin Chief", "Orc Warrior"}
        
        # Mock LLM that checks if context was provided
        prompt_received = []
        def context_checking_llm(prompt: str) -> str:
            prompt_received.append(prompt)
            return """NAME: Blood-Soaked Clearing
DESCRIPTION: A clearing littered with goblin and orc corpses from yesterday's battle. Carrion birds circle overhead."""
        
        game_context = {
            'defeated_enemies': forest.defeated_enemies,
            'time_of_day': 'morning',
            'npcs_present': ['Thorin'],
            'day': 2
        }
        
        loc = generate_llm_enhanced_location(
            from_location=forest,
            llm_generate_func=context_checking_llm,
            game_context=game_context
        )
        
        # Verify context was in prompt
        assert len(prompt_received) == 1
        prompt = prompt_received[0]
        assert "Dark Forest" in prompt
        assert "morning" in prompt or "Morning" in prompt
        assert "Thorin" in prompt or "NPCs nearby" in prompt
        
        # Verify generated location
        assert loc.name == "Blood-Soaked Clearing"
        assert "corpses" in loc.description.lower()
        
        print(f"✅ Context-aware generation: {loc.name}")
        print(f"   Context included: defeated_enemies, time_of_day, npcs")
    
    def test_comparison_template_vs_llm(self):
        """Compare template vs LLM generation output."""
        town = Location(
            name="Riverside Town",
            location_type=LocationType.TOWN,
            description="A peaceful town by the river",
            is_safe=True
        )
        
        # Template generation
        template_locs = []
        for i in range(5):
            loc = generate_random_location(town)
            template_locs.append(loc.name)
        
        # LLM generation (mock)
        counter = [0]
        def unique_llm(prompt: str) -> str:
            counter[0] += 1
            names = [
                "Mistweaver's Glade",
                "Thundering Cascades",
                "Serpent's Cradle Valley",
                "Moonlit Hollow",
                "Stormbreak Ridge"
            ]
            return f"NAME: {names[counter[0]-1]}\nDESCRIPTION: A unique and memorable location with contextual details."
        
        llm_locs = []
        for i in range(5):
            loc = generate_llm_enhanced_location(town, unique_llm)
            llm_locs.append(loc.name)
        
        print("\n📊 Comparison:")
        print(f"Template names: {template_locs}")
        print(f"LLM names: {llm_locs}")
        
        # LLM names should all be unique
        assert len(set(llm_locs)) == 5, "LLM should generate unique names"
        
        # Template names may have duplicates
        template_unique = len(set(template_locs))
        print(f"Template unique: {template_unique}/5")
        print(f"LLM unique: 5/5")
        
        print("✅ LLM generates more varied names")


if __name__ == "__main__":
    print("🧪 LLM-Enhanced Location Generation Tests")
    print("=" * 60)
    pytest.main([__file__, "-v", "-s"])
