"""
End-to-end test showing racial + class bonuses working together.
"""

import pytest
from dnd_rag_system.systems.character_creator import Character, CharacterCreator
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.rag_character_enhancer import enhance_character_with_rag
import chromadb


def test_complete_elf_wizard_creation():
    """Test complete character creation with racial AND class bonuses."""
    
    # Create base Elf Wizard
    char = Character(
        name="Elara",
        race="Elf",
        character_class="Wizard",
        level=1,
        strength=8,
        dexterity=12,  # Will get +2 from Elf racial
        constitution=14,
        intelligence=15,
        wisdom=10,
        charisma=10
    )
    
    # Apply racial bonuses from RAG
    client = chromadb.PersistentClient(path='chromadb')
    collection = client.get_collection('dnd5e_srd')
    results = collection.query(
        query_texts=["Elf race ability score"],
        n_results=1,
        where={"$and": [{"type": {"$eq": "race"}}, {"name": {"$eq": "Elf"}}]}
    )
    
    assert results and results['metadatas'][0], "Should find Elf in RAG"
    
    metadata = results['metadatas'][0][0]
    for key, val in metadata.items():
        if key.startswith('bonus_'):
            ability = key.replace('bonus_', '')
            current = getattr(char, ability)
            setattr(char, ability, current + val)
    
    # Verify racial bonus applied
    assert char.dexterity == 14, "Elf should get +2 DEX (12 + 2 = 14)"
    
    # Apply class features from RAG
    enhance_character_with_rag(char)
    
    # Verify class features
    assert char.hit_points == 8, "Wizard d6 + CON(+2) = 8 HP"
    assert len(char.class_features) > 0, "Should have class features"
    assert len(char.proficiencies) > 0, "Should have proficiencies"
    assert len(char.spells) > 0, "Wizard should have spells"
    
    # Verify spell slots mentioned
    features_str = ' '.join(char.class_features).lower()
    assert 'spell' in features_str, "Should mention spells"
    
    print(f"\n✅ COMPLETE CHARACTER:")
    print(f"  {char.name} - {char.race} {char.character_class} {char.level}")
    print(f"  STR: {char.strength}, DEX: {char.dexterity}, CON: {char.constitution}")
    print(f"  INT: {char.intelligence}, WIS: {char.wisdom}, CHA: {char.charisma}")
    print(f"  HP: {char.hit_points}")
    print(f"  Features: {len(char.class_features)}")
    print(f"  Spells: {len(char.spells)}")


def test_complete_half_orc_barbarian_creation():
    """Test Half-Orc Barbarian gets correct racial AND class bonuses."""
    
    char = Character(
        name="Grok",
        race="Half-Orc",
        character_class="Barbarian",
        level=1,
        strength=15,  # Will get +2 from Half-Orc
        dexterity=12,
        constitution=14,  # Will get +1 from Half-Orc
        intelligence=8,
        wisdom=10,
        charisma=10
    )
    
    # Apply racial bonuses
    client = chromadb.PersistentClient(path='chromadb')
    collection = client.get_collection('dnd5e_srd')
    results = collection.query(
        query_texts=["Half-Orc race ability score"],
        n_results=1,
        where={"$and": [{"type": {"$eq": "race"}}, {"name": {"$eq": "Half-Orc"}}]}
    )
    
    assert results and results['metadatas'][0], "Should find Half-Orc in RAG"
    
    metadata = results['metadatas'][0][0]
    for key, val in metadata.items():
        if key.startswith('bonus_'):
            ability = key.replace('bonus_', '')
            current = getattr(char, ability)
            setattr(char, ability, current + val)
    
    # Verify racial bonuses
    assert char.strength == 17, "Half-Orc should get +2 STR (15 + 2 = 17)"
    assert char.constitution == 15, "Half-Orc should get +1 CON (14 + 1 = 15)"
    
    # Apply class features
    enhance_character_with_rag(char)
    
    # Verify class features
    assert char.hit_points == 14, "Barbarian d12 + CON(+2) = 14 HP"
    assert any('Rage' in f for f in char.class_features), "Barbarian should have Rage"
    
    # Barbarian is not a caster
    assert len(char.spells) == 0, "Barbarian should have no spells"
    
    print(f"\n✅ COMPLETE CHARACTER:")
    print(f"  {char.name} - {char.race} {char.character_class} {char.level}")
    print(f"  STR: {char.strength}, DEX: {char.dexterity}, CON: {char.constitution}")
    print(f"  INT: {char.intelligence}, WIS: {char.wisdom}, CHA: {char.charisma}")
    print(f"  HP: {char.hit_points}")


if __name__ == '__main__':
    test_complete_elf_wizard_creation()
    test_complete_half_orc_barbarian_creation()
    print("\n🎉 ALL E2E TESTS PASSED!")
