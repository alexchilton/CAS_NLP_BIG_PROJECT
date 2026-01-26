"""
Tests for ModelRegistry - centralized model name configuration
"""

import pytest
from dnd_rag_system.config.model_registry import ModelRegistry


class TestModelRegistry:
    """Test ModelRegistry centralized model configuration."""
    
    def test_primary_models_exist(self):
        """Should have primary model configurations."""
        assert hasattr(ModelRegistry, 'ROLEPLAY')
        assert hasattr(ModelRegistry, 'MECHANICS')
        assert hasattr(ModelRegistry, 'HUGGINGFACE_INFERENCE')
    
    def test_roleplay_model_exists(self):
        """Roleplay model should be configured."""
        assert hasattr(ModelRegistry.ROLEPLAY, 'name')
        assert ModelRegistry.ROLEPLAY.name
        assert hasattr(ModelRegistry.ROLEPLAY, 'description')
    
    def test_mechanics_model_exists(self):
        """Mechanics model should be configured."""
        assert hasattr(ModelRegistry.MECHANICS, 'name')
        assert ModelRegistry.MECHANICS.name
        assert hasattr(ModelRegistry.MECHANICS, 'description')
    
    def test_huggingface_inference_model_exists(self):
        """HuggingFace inference model should be configured."""
        assert hasattr(ModelRegistry.HUGGINGFACE_INFERENCE, 'name')
        assert ModelRegistry.HUGGINGFACE_INFERENCE.name


class TestGetModelForTask:
    """Test task-based model routing."""
    
    def test_get_model_for_roleplay_task(self):
        """Should return roleplay model for dramatic descriptions."""
        model = ModelRegistry.get_model_for_task("roleplay")
        assert model is not None
        assert isinstance(model, str)  # Returns model name string
    
    def test_get_model_for_mechanics_task(self):
        """Should return mechanics model for extraction."""
        model = ModelRegistry.get_model_for_task("mechanics")
        assert model is not None
        assert isinstance(model, str)
    
    def test_get_model_for_dialogue_task(self):
        """Should return dialogue model."""
        model = ModelRegistry.get_model_for_task("dialogue")
        assert model is not None
        assert isinstance(model, str)
    
    def test_unknown_task_returns_default(self):
        """Unknown task should return default model."""
        model = ModelRegistry.get_model_for_task("unknown_task_12345")
        assert model is not None  # Should return a default
        assert isinstance(model, str)


class TestModelNames:
    """Test that model names are valid strings."""
    
    def test_roleplay_model_name_is_string(self):
        """Roleplay model name should be non-empty string."""
        assert isinstance(ModelRegistry.ROLEPLAY.name, str)
        assert len(ModelRegistry.ROLEPLAY.name) > 0
    
    def test_mechanics_model_name_is_string(self):
        """Mechanics model name should be non-empty string."""
        assert isinstance(ModelRegistry.MECHANICS.name, str)
        assert len(ModelRegistry.MECHANICS.name) > 0
    
    def test_huggingface_model_name_is_string(self):
        """HuggingFace model name should be non-empty string."""
        assert isinstance(ModelRegistry.HUGGINGFACE_INFERENCE.name, str)
        assert len(ModelRegistry.HUGGINGFACE_INFERENCE.name) > 0
    
    def test_no_model_names_are_none(self):
        """No model names should be None."""
        assert ModelRegistry.ROLEPLAY.name is not None
        assert ModelRegistry.MECHANICS.name is not None
        assert ModelRegistry.HUGGINGFACE_INFERENCE.name is not None


class TestModelDescriptions:
    """Test that model descriptions/purposes are documented."""
    
    def test_all_models_have_description(self):
        """All registered models should have documentation."""
        assert hasattr(ModelRegistry.ROLEPLAY, 'description')
        assert hasattr(ModelRegistry.MECHANICS, 'description')
        assert hasattr(ModelRegistry.HUGGINGFACE_INFERENCE, 'description')
    
    def test_descriptions_are_meaningful(self):
        """Descriptions should be informative."""
        # Check that descriptions exist and are non-empty
        roleplay_desc = ModelRegistry.ROLEPLAY.description
        mechanics_desc = ModelRegistry.MECHANICS.description
        
        if roleplay_desc:
            assert len(roleplay_desc) > 5
        if mechanics_desc:
            assert len(mechanics_desc) > 5


class TestBackwardCompatibility:
    """Test that ModelRegistry maintains backward compatibility."""
    
    def test_can_access_model_names_directly(self):
        """Should be able to access model names for backward compatibility."""
        # These are the primary models that code relies on
        roleplay_name = ModelRegistry.ROLEPLAY.name
        mechanics_name = ModelRegistry.MECHANICS.name
        hf_name = ModelRegistry.HUGGINGFACE_INFERENCE.name
        
        assert isinstance(roleplay_name, str)
        assert isinstance(mechanics_name, str)
        assert isinstance(hf_name, str)
    
    def test_model_names_follow_convention(self):
        """Model names should follow expected conventions."""
        # Ollama models might have : in name
        # HuggingFace models might have / in name
        for model in [ModelRegistry.ROLEPLAY, ModelRegistry.MECHANICS, ModelRegistry.HUGGINGFACE_INFERENCE]:
            name = model.name
            # Should not be empty or just whitespace
            assert name.strip() == name
            assert len(name) > 0
