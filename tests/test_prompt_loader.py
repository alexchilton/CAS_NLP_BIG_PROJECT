"""
Tests for PromptLoader utility - centralized prompt template loading
"""

import pytest
from pathlib import Path
from dnd_rag_system.utils.prompt_loader import PromptLoader, load_prompt, get_prompt_loader


class TestPromptLoaderInitialization:
    """Test PromptLoader initialization and setup."""
    
    def test_loader_initializes_successfully(self):
        """PromptLoader should initialize and find prompts directory."""
        loader = PromptLoader()
        assert loader.prompts_dir.exists()
        assert loader.prompts_dir.name == "prompts"
    
    def test_prompts_directory_exists(self):
        """Prompts directory should exist and contain template files."""
        loader = PromptLoader()
        templates = list(loader.prompts_dir.glob("*.txt"))
        assert len(templates) > 0, "No .txt template files found"
    
    def test_list_templates(self):
        """Should list all available templates."""
        loader = PromptLoader()
        templates = loader.list_templates()
        
        # Check for known templates
        assert 'mechanics_extraction' in templates
        assert 'intent_classification' in templates
        assert 'explore_location' in templates
        assert isinstance(templates, list)
        assert len(templates) >= 9


class TestTemplateLoading:
    """Test loading and formatting templates."""
    
    def test_load_mechanics_extraction_template(self):
        """Should load mechanics extraction template."""
        loader = PromptLoader()
        prompt = loader.load(
            "mechanics_extraction",
            narrative="The goblin attacks!",
            char_context="",
            npc_context=""
        )
        
        assert "Extract D&D game mechanics" in prompt
        assert "The goblin attacks!" in prompt
        assert "NARRATIVE:" in prompt
        assert len(prompt) > 100
    
    def test_load_intent_classification_template(self):
        """Should load intent classification template."""
        loader = PromptLoader()
        prompt = loader.load(
            "intent_classification",
            user_input="I attack the goblin",
            party_context=""
        )
        
        assert "Analyze this D&D player action" in prompt
        assert "I attack the goblin" in prompt
        assert "action_type" in prompt
    
    def test_load_explore_location_template(self):
        """Should load explore location template."""
        loader = PromptLoader()
        prompt = loader.load(
            "explore_location",
            from_location_name="Dark Cave",
            from_location_type="dungeon",
            context_str="You've been exploring",
            current_theme="underground",
            new_location_type="cave",
            new_theme="underground",
            safety_level="DANGEROUS"
        )
        
        assert "Dark Cave" in prompt
        assert "Generate a NEW location" in prompt
    
    def test_template_not_found_error(self):
        """Should raise error for non-existent template."""
        loader = PromptLoader()
        
        with pytest.raises(FileNotFoundError) as exc_info:
            loader.load("nonexistent_template", some_var="value")
        
        assert "Prompt template not found" in str(exc_info.value)
        assert "Available templates:" in str(exc_info.value)
    
    def test_missing_variable_error(self):
        """Should raise error when required variable is missing."""
        loader = PromptLoader()
        
        with pytest.raises(ValueError) as exc_info:
            # Load template without required variables
            loader.load("mechanics_extraction")
        
        assert "Missing required variable" in str(exc_info.value)


class TestTemplateCaching:
    """Test template caching functionality."""
    
    def test_templates_are_cached(self):
        """Should cache loaded templates."""
        loader = PromptLoader()
        
        # Load template twice
        prompt1 = loader.load("mechanics_extraction", narrative="Test", char_context="", npc_context="")
        prompt2 = loader.load("mechanics_extraction", narrative="Test", char_context="", npc_context="")
        
        # Should be using cached template (same content)
        assert prompt1 == prompt2
        assert "mechanics_extraction" in loader._template_cache
    
    def test_reload_clears_cache(self):
        """Should clear cache when reload() is called."""
        loader = PromptLoader()
        
        # Load template to populate cache
        loader.load("mechanics_extraction", narrative="Test", char_context="", npc_context="")
        assert "mechanics_extraction" in loader._template_cache
        
        # Reload specific template
        loader.reload("mechanics_extraction")
        assert "mechanics_extraction" not in loader._template_cache
    
    def test_reload_all_clears_all_caches(self):
        """Should clear all caches when reload() is called without argument."""
        loader = PromptLoader()
        
        # Load multiple templates
        loader.load("mechanics_extraction", narrative="Test", char_context="", npc_context="")
        loader.load("intent_classification", user_input="Test", party_context="")
        
        assert len(loader._template_cache) == 2
        
        # Reload all
        loader.reload()
        assert len(loader._template_cache) == 0


class TestConvenienceFunctions:
    """Test convenience functions for common usage."""
    
    def test_load_prompt_convenience_function(self):
        """load_prompt() should work as shortcut."""
        prompt = load_prompt(
            "mechanics_extraction",
            narrative="Test narrative",
            char_context="",
            npc_context=""
        )
        
        assert "Test narrative" in prompt
        assert "Extract D&D game mechanics" in prompt
    
    def test_get_prompt_loader_singleton(self):
        """get_prompt_loader() should return singleton instance."""
        loader1 = get_prompt_loader()
        loader2 = get_prompt_loader()
        
        # Should be same instance
        assert loader1 is loader2


class TestAllTemplates:
    """Test that all expected templates exist and are loadable."""
    
    @pytest.mark.parametrize("template_name,required_vars", [
        ("mechanics_extraction", {"narrative": "test", "char_context": "", "npc_context": ""}),
        ("intent_classification", {"user_input": "test", "party_context": ""}),
        ("explore_location", {
            "from_location_name": "test",
            "from_location_type": "dungeon",
            "context_str": "test",
            "current_theme": "dark",
            "new_location_type": "cave",
            "new_theme": "dark",
            "safety_level": "dangerous"
        }),
        ("monster_encounter", {
            "monster_name": "Goblin",
            "monster_cr": "1/4",
            "location": "Cave",
            "party_level": "3",
            "repeat_info": "",
            "lore": "",
            "repeat_guidance": ""
        }),
        ("multi_monster_encounter", {
            "monster_list": "2 Goblins",
            "location": "Cave",
            "party_level": "3"
        }),
        ("item_lore", {
            "item_name": "Sword",
            "item_type": "weapon",
            "rarity": "rare",
            "lore": "",
            "lore_guidance": ""
        }),
        ("validation_no_target", {
            "location": "Tavern",
            "attempted_target": "dragon"
        }),
        ("validation_no_spell_slots", {
            "spell_name": "Fireball",
            "reason": "No spell slots"
        }),
        ("validation_invalid_action", {
            "location": "Tavern",
            "action_description": "test",
            "reason": "test"
        }),
    ])
    def test_template_loads_successfully(self, template_name, required_vars):
        """Each template should load with its required variables."""
        loader = PromptLoader()
        prompt = loader.load(template_name, **required_vars)
        
        assert len(prompt) > 0
        assert isinstance(prompt, str)


class TestTemplateContent:
    """Test that templates contain expected content."""
    
    def test_mechanics_extraction_has_json_schema(self):
        """Mechanics extraction should include JSON schema."""
        prompt = load_prompt(
            "mechanics_extraction",
            narrative="test",
            char_context="",
            npc_context=""
        )
        
        assert '"damage":' in prompt
        assert '"healing":' in prompt
        assert '"conditions_added":' in prompt
        assert '"spell_slots_used":' in prompt
        assert '"npcs_introduced":' in prompt
    
    def test_intent_classification_has_action_types(self):
        """Intent classification should list action types."""
        prompt = load_prompt(
            "intent_classification",
            user_input="test",
            party_context=""
        )
        
        assert '"combat"' in prompt or 'combat' in prompt
        assert '"spell_cast"' in prompt or 'spell_cast' in prompt
        assert '"steal"' in prompt or 'steal' in prompt
        assert '"exploration"' in prompt or 'exploration' in prompt
    
    def test_templates_include_dm_roleplay_guidance(self):
        """Templates should include DM roleplay guidance."""
        monster_prompt = load_prompt(
            "monster_encounter",
            monster_name="Goblin",
            monster_cr="1/4",
            location="Cave",
            party_level="3",
            repeat_info="",
            lore="",
            repeat_guidance=""
        )
        
        assert "Dungeon Master" in monster_prompt or "dramatic" in monster_prompt
