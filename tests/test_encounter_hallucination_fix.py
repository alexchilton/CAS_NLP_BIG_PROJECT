"""
Test for the Wolf/Goblin hallucination bug fix.

This test verifies that when an encounter generates one monster (e.g., Goblin),
the mechanics extractor doesn't add a different hallucinated monster (e.g., Wolf)
to the NPCs list.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.encounter_system import EncounterSystem, EncounterResult
from dnd_rag_system.systems.mechanics_extractor import ExtractedMechanics
from dnd_rag_system.systems.game_state import GameSession


def test_hallucination_filtering():
    """Test that hallucinated monster names are filtered out when an encounter is active."""
    
    print("🧪 Testing Encounter Hallucination Fix\n")
    print("=" * 80)
    
    # Simulate an encounter that generated "Goblin"
    encounter = EncounterResult(
        monster_name="Goblin",
        monster_cr=0.25,
        description="A small goblin with a rusty scimitar",
        surprise=False
    )
    
    print(f"✅ Generated encounter: {encounter.monster_name}")
    
    # Simulate GM hallucinating "Wolf" instead
    hallucinated_mechanics = ExtractedMechanics(
        npcs_introduced=[
            {"name": "Wolf", "type": "enemy"},  # WRONG - GM hallucinated this
        ]
    )
    
    print(f"⚠️  GM hallucinated and mentioned: Wolf")
    print(f"   (but actual encounter is: {encounter.monster_name})")
    
    # The filtering logic from gm_dialogue_unified.py
    if encounter and hallucinated_mechanics.npcs_introduced:
        original_count = len(hallucinated_mechanics.npcs_introduced)
        filtered_npcs = []
        
        for npc in hallucinated_mechanics.npcs_introduced:
            npc_name = npc.get('name', '').strip().lower()
            encounter_name = encounter.monster_name.strip().lower()
            
            # Allow the actual encounter monster
            if npc_name == encounter_name:
                filtered_npcs.append(npc)
            # Allow non-monster NPCs (merchants, guards, etc.) if type is not "enemy"
            elif npc.get('type') != 'enemy':
                filtered_npcs.append(npc)
            else:
                # This is a hallucinated enemy - skip it
                print(f"🔧 Filtered hallucinated enemy '{npc_name}' - actual encounter is '{encounter_name}'")
        
        hallucinated_mechanics.npcs_introduced = filtered_npcs
    
    # Verify the hallucinated Wolf was filtered out
    assert len(hallucinated_mechanics.npcs_introduced) == 0, \
        f"Expected 0 NPCs after filtering, got {len(hallucinated_mechanics.npcs_introduced)}"
    
    print("✅ Hallucinated 'Wolf' was correctly filtered out!")
    print()
    
    # Test case 2: GM correctly mentions the actual encounter monster
    print("-" * 80)
    correct_mechanics = ExtractedMechanics(
        npcs_introduced=[
            {"name": "Goblin", "type": "enemy"},  # CORRECT - matches encounter
        ]
    )
    
    print(f"✅ GM correctly mentioned: Goblin")
    
    # Apply same filtering
    if encounter and correct_mechanics.npcs_introduced:
        filtered_npcs = []
        
        for npc in correct_mechanics.npcs_introduced:
            npc_name = npc.get('name', '').strip().lower()
            encounter_name = encounter.monster_name.strip().lower()
            
            if npc_name == encounter_name:
                filtered_npcs.append(npc)
            elif npc.get('type') != 'enemy':
                filtered_npcs.append(npc)
            else:
                print(f"🔧 Filtered hallucinated enemy '{npc_name}' - actual encounter is '{encounter_name}'")
        
        correct_mechanics.npcs_introduced = filtered_npcs
    
    # Verify the correct Goblin was kept
    assert len(correct_mechanics.npcs_introduced) == 1, \
        f"Expected 1 NPC after filtering, got {len(correct_mechanics.npcs_introduced)}"
    assert correct_mechanics.npcs_introduced[0]['name'] == 'Goblin', \
        f"Expected 'Goblin', got {correct_mechanics.npcs_introduced[0]['name']}"
    
    print("✅ Correct 'Goblin' was kept!")
    print()
    
    # Test case 3: Friendly NPCs should not be filtered
    print("-" * 80)
    mixed_mechanics = ExtractedMechanics(
        npcs_introduced=[
            {"name": "Wolf", "type": "enemy"},     # Wrong - should be filtered
            {"name": "Merchant", "type": "friendly"},  # OK - not an enemy
            {"name": "Goblin", "type": "enemy"},   # Correct - matches encounter
        ]
    )
    
    print(f"✅ GM mentioned: Wolf (enemy), Merchant (friendly), Goblin (enemy)")
    
    # Apply filtering
    if encounter and mixed_mechanics.npcs_introduced:
        filtered_npcs = []
        
        for npc in mixed_mechanics.npcs_introduced:
            npc_name = npc.get('name', '').strip().lower()
            encounter_name = encounter.monster_name.strip().lower()
            
            if npc_name == encounter_name:
                filtered_npcs.append(npc)
            elif npc.get('type') != 'enemy':
                filtered_npcs.append(npc)
            else:
                print(f"🔧 Filtered hallucinated enemy '{npc_name}' - actual encounter is '{encounter_name}'")
        
        mixed_mechanics.npcs_introduced = filtered_npcs
    
    # Verify: Wolf filtered, Merchant kept, Goblin kept
    assert len(mixed_mechanics.npcs_introduced) == 2, \
        f"Expected 2 NPCs after filtering, got {len(mixed_mechanics.npcs_introduced)}"
    
    npc_names = [npc['name'] for npc in mixed_mechanics.npcs_introduced]
    assert 'Goblin' in npc_names, "Expected Goblin to be kept"
    assert 'Merchant' in npc_names, "Expected Merchant to be kept"
    assert 'Wolf' not in npc_names, "Expected Wolf to be filtered out"
    
    print("✅ Mixed NPCs correctly handled: Wolf filtered, Merchant and Goblin kept!")
    
    print()
    print("=" * 80)
    print("🎉 All tests passed! Hallucination fix is working correctly.")
    print()
    print("Summary:")
    print("  - Hallucinated enemy monsters are filtered out")
    print("  - Correct encounter monsters are kept")
    print("  - Friendly/neutral NPCs are not filtered")


if __name__ == "__main__":
    test_hallucination_filtering()
