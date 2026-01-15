"""Tests for RAG-powered character enhancement."""

import pytest
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dnd_rag_system.systems.rag_character_enhancer import RAGCharacterEnhancer


@dataclass
class MockCharacter:
    """Mock character for testing."""
    name: str = "Test Character"
    character_class: str = "Fighter"
    level: int = 1
    constitution: int = 10
    hit_points: int = 0
    proficiencies: List[str] = field(default_factory=list)
    class_features: List[str] = field(default_factory=list)
    spells: List[str] = field(default_factory=list)
    
    def get_ability_modifier(self, score: int) -> int:
        return (score - 10) // 2
    
    def calculate_hit_points(self, hit_die: int) -> int:
        con_mod = self.get_ability_modifier(self.constitution)
        return hit_die + con_mod


class TestRAGCharacterEnhancer:
    """Test RAG character enhancement."""
    
    @pytest.fixture
    def enhancer(self):
        """Create enhancer instance."""
        return RAGCharacterEnhancer()
    
    def test_get_hit_die_barbarian(self, enhancer):
        """Barbarian should have d12 hit die."""
        assert enhancer.get_hit_die('Barbarian') == 12
    
    def test_get_hit_die_fighter(self, enhancer):
        """Fighter should have d10 hit die."""
        assert enhancer.get_hit_die('Fighter') == 10
    
    def test_get_hit_die_wizard(self, enhancer):
        """Wizard should have d6 hit die."""
        assert enhancer.get_hit_die('Wizard') == 6
    
    def test_get_hit_die_unknown(self, enhancer):
        """Unknown class should default to d8."""
        assert enhancer.get_hit_die('UnknownClass') == 8
    
    def test_spell_slots_full_caster_level_1(self, enhancer):
        """Wizard at level 1 should have 2 first-level slots."""
        slots = enhancer.get_spell_slots('Wizard', 1)
        assert slots[0] == 2  # 2x 1st-level slots
        assert sum(slots[1:]) == 0  # No higher-level slots
    
    def test_spell_slots_half_caster_level_1(self, enhancer):
        """Paladin at level 1 should have no spell slots."""
        slots = enhancer.get_spell_slots('Paladin', 1)
        assert sum(slots) == 0  # No slots at level 1
    
    def test_spell_slots_half_caster_level_2(self, enhancer):
        """Paladin at level 2 should have 2 first-level slots."""
        slots = enhancer.get_spell_slots('Paladin', 2)
        assert slots[0] == 2
    
    def test_spell_slots_non_caster(self, enhancer):
        """Fighter should have no spell slots."""
        slots = enhancer.get_spell_slots('Fighter', 1)
        assert sum(slots) == 0
    
    def test_enhance_fighter(self, enhancer):
        """Test enhancing a Fighter character."""
        char = MockCharacter(
            name="Conan",
            character_class="Fighter",
            level=1,
            constitution=14
        )
        
        enhancer.enhance_character(char)
        
        # Should have correct HP (d10 + CON mod)
        assert char.hit_points == 12  # 10 + 2
        
        # Should have class features
        assert len(char.class_features) >= 2
        assert any('Fighting Style' in f for f in char.class_features)
        assert any('Second Wind' in f for f in char.class_features)
        
        # Fighter is not a caster
        assert len(char.spells) == 0
    
    def test_enhance_wizard(self, enhancer):
        """Test enhancing a Wizard character."""
        char = MockCharacter(
            name="Gandalf",
            character_class="Wizard",
            level=1,
            constitution=12
        )
        
        enhancer.enhance_character(char)
        
        # Should have correct HP (d6 + CON mod)
        assert char.hit_points == 7  # 6 + 1
        
        # Should have class features including spellcasting
        assert any('Spellcasting' in f for f in char.class_features)
        assert any('Arcane Recovery' in f for f in char.class_features)
        assert any('Spell Slots' in f for f in char.class_features)
        
        # Should have spells suggested
        assert len(char.spells) > 0
    
    def test_enhance_paladin(self, enhancer):
        """Test enhancing a Paladin (half-caster)."""
        char = MockCharacter(
            name="Sir Galahad",
            character_class="Paladin",
            level=1,
            constitution=14
        )
        
        enhancer.enhance_character(char)
        
        # Should have correct HP (d10 + CON mod)
        assert char.hit_points == 12
        
        # Should have level 1 features
        assert any('Divine Sense' in f for f in char.class_features)
        
        # No spells at level 1
        assert len(char.spells) == 0
    
    def test_basic_class_features_rogue(self, enhancer):
        """Test that Rogue gets correct level 1 features."""
        features = enhancer._get_basic_class_features('Rogue', 1)
        
        assert 'Expertise' in features
        assert any('Sneak Attack' in f for f in features)
        assert any('Thieves' in f for f in features)
    
    def test_basic_class_features_unknown_class(self, enhancer):
        """Unknown class should return empty features."""
        features = enhancer._get_basic_class_features('UnknownClass', 1)
        assert len(features) == 0
    
    def test_extract_proficiencies(self, enhancer):
        """Test proficiency extraction from class text."""
        sample_text = """
        Class: Wizard
        Hit Die: d6
        Armor Proficiency: None
        Weapon Proficiency: Daggers, quarterstaffs, light crossbows
        Saving Throws: Intelligence, Wisdom
        """
        
        profs = enhancer.extract_proficiencies(sample_text)
        
        # Armor "None" is filtered out
        assert profs['armor'] == []
        assert len(profs['weapons']) > 0
        assert 'Daggers' in profs['weapons']
        assert len(profs['saving_throws']) == 2
        assert 'Intelligence' in profs['saving_throws']


class TestRAGIntegration:
    """Integration tests with actual ChromaDB."""
    
    @pytest.fixture
    def enhancer(self):
        """Create enhancer with real ChromaDB."""
        return RAGCharacterEnhancer('chromadb')
    
    def test_query_wizard_class(self, enhancer):
        """Test querying Wizard class info from ChromaDB."""
        if not enhancer.srd_collection:
            pytest.skip("SRD collection not available")
        
        info = enhancer.query_class_info('Wizard')
        
        assert info is not None
        assert 'document' in info
        assert 'Wizard' in info['document']
        assert info['metadata']['type'] == 'class'
        assert info['metadata']['hit_die'] == 'd6'
    
    def test_query_spells(self, enhancer):
        """Test querying spells for Wizard."""
        if not enhancer.srd_collection:
            pytest.skip("SRD collection not available")
        
        spells = enhancer.query_spells_for_class('Wizard', max_level=1, limit=5)
        
        # Should find some spells
        assert len(spells) > 0
        
        # All should be level 0 or 1
        for spell in spells:
            assert spell['level'] <= 1
            assert 'name' in spell
            assert 'school' in spell
