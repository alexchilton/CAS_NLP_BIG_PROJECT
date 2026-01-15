"""
Test for mechanics extractor zero-damage hallucination fix.

Tests that the mechanics extractor filters out LLM hallucinations
where it returns damage entries with amount: 0.
"""

import pytest
from dnd_rag_system.systems.mechanics_extractor import MechanicsExtractor


def test_filter_zero_damage_hallucinations():
    """Test that zero-damage entries are filtered out."""
    extractor = MechanicsExtractor(debug=False)
    
    # Simulate a narrative where no actual damage occurs
    # (e.g., NPC introduction, description, etc.)
    narrative = """
    An Ancient Red Dragon appears before you, its massive form coiled atop
    a mountain of gold. Its eyes glow with ancient malice as it regards you.
    Thorin readies his sword nervously.
    """
    
    mechanics = extractor.extract(
        narrative,
        character_names=["Thorin"],
        existing_npcs=[]
    )
    
    # Should have the NPC introduced
    assert len(mechanics.npcs_introduced) == 1
    assert mechanics.npcs_introduced[0]['name'] == "Ancient Red Dragon"
    
    # Should NOT have any damage entries (especially not zero-damage)
    assert len(mechanics.damage) == 0, \
        f"Expected no damage, got: {mechanics.damage}"
    
    # Verify no zero-amount entries
    for dmg in mechanics.damage:
        assert dmg.get('amount', 0) > 0, \
            f"Found zero-damage entry: {dmg}"


def test_real_damage_preserved():
    """Test that real damage entries are preserved."""
    extractor = MechanicsExtractor(debug=False)
    
    narrative = """
    Thorin swings his longsword at the goblin, striking it squarely!
    The blade cuts deep, dealing 12 slashing damage. The goblin staggers back,
    wounded but still standing.
    """
    
    mechanics = extractor.extract(
        narrative,
        character_names=["Thorin"],
        existing_npcs=["Goblin"]
    )
    
    # Should have damage
    assert len(mechanics.damage) > 0, "Real damage should be extracted"
    
    # Should have positive amount
    for dmg in mechanics.damage:
        assert dmg['amount'] > 0, f"Damage amount should be positive: {dmg}"
        
    # Should target the goblin
    goblin_damage = [d for d in mechanics.damage if 'goblin' in d['target'].lower()]
    assert len(goblin_damage) > 0, "Should have damage to goblin"


def test_no_acid_hallucination_on_dragon_intro():
    """
    Regression test for specific bug: When Ancient Red Dragon is introduced,
    LLM was hallucinating acid damage with amount: 0 for both dragon and player.
    """
    extractor = MechanicsExtractor(debug=False)
    
    narrative = """
    You enter the dragon's lair. Before you stands an Ancient Red Dragon,
    its scales gleaming crimson in the firelight. It has not attacked yet,
    merely watching you with ancient, intelligent eyes.
    """
    
    mechanics = extractor.extract(
        narrative,
        character_names=["Thorin Stormshield"],
        existing_npcs=[]
    )
    
    # Should extract the dragon as new NPC
    assert any('dragon' in npc['name'].lower() for npc in mechanics.npcs_introduced)
    
    # Should NOT have any damage (no combat yet)
    assert len(mechanics.damage) == 0, \
        f"No combat occurred, should have no damage. Got: {mechanics.damage}"
    
    # Specifically check for the "acid" hallucination bug
    for dmg in mechanics.damage:
        assert dmg.get('type') != 'acid' or dmg.get('amount', 0) > 0, \
            f"Found hallucinated acid damage: {dmg}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
