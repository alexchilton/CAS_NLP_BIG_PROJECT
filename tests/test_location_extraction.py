"""
Test Location Extraction and Consistency

Verifies that:
1. GM location mentions are parsed and update session state
2. Location does NOT change during combat
3. Location stays consistent across multiple actions
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.gm_dialogue_unified import GameMaster


def test_location_extraction():
    """Test that location mentions in GM narrative update session state."""
    
    print("\n" + "="*80)
    print("🧪 Testing Location Extraction")
    print("="*80)
    
    gm = GameMaster(db_manager=None)  # No RAG needed for this test
    
    # Test cases with different patterns
    test_cases = [
        ("You find yourself in The Market Square.", "The Market Square"),
        ("You are in Goblin Cave Entrance.", "Goblin Cave Entrance"),
        ("You travel to The Prancing Pony Inn.", "The Prancing Pony Inn"),
        ("You arrive at Dark Forest Clearing.", "Dark Forest Clearing"),
        ("You enter the Town Gates.", "Town Gates"),
    ]
    
    for i, (response, expected_location) in enumerate(test_cases, 1):
        gm._extract_and_update_location(response)
        
        if gm.session.current_location == expected_location:
            print(f"✅ Test {i}: Extracted '{expected_location}'")
        else:
            print(f"❌ Test {i}: Expected '{expected_location}', got '{gm.session.current_location}'")
    
    print("\n" + "="*80)
    print("🧪 Testing Location Lock During Combat")
    print("="*80)
    
    # Set initial location
    gm.session.current_location = "Goblin Cave"
    print(f"Initial location: {gm.session.current_location}")
    
    # Start combat
    gm.session.combat.in_combat = True
    print(f"Combat started: {gm.combat_manager.is_in_combat()}")
    
    # Try to change location during combat (should be blocked)
    gm._extract_and_update_location("You find yourself in The Market Square.")
    
    if gm.session.current_location == "Goblin Cave":
        print(f"✅ Location stayed locked: '{gm.session.current_location}' (combat active)")
    else:
        print(f"❌ Location changed during combat! Now: '{gm.session.current_location}'")
    
    # End combat
    gm.session.combat.in_combat = False
    
    # Now location change should work
    gm._extract_and_update_location("You travel to The Safe Haven.")
    
    if gm.session.current_location == "The Safe Haven":
        print(f"✅ Location changed after combat: '{gm.session.current_location}'")
    else:
        print(f"❌ Location didn't update after combat: '{gm.session.current_location}'")
    
    print("\n" + "="*80)
    print("✅ All location extraction tests complete!")
    print("="*80)


if __name__ == "__main__":
    test_location_extraction()
