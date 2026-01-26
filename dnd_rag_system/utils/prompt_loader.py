"""
Prompt Template Loader

Centralized utility for loading prompt templates from files.
Eliminates embedded 50+ line prompts from code.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PromptLoader:
    """
    Load and format prompt templates from template files.
    
    All long prompts are stored in dnd_rag_system/prompts/ directory.
    Templates use Python f-string style placeholders: {variable_name}
    """
    
    def __init__(self):
        # Find prompts directory relative to this file
        utils_dir = Path(__file__).parent
        rag_system_dir = utils_dir.parent
        self.prompts_dir = rag_system_dir / "prompts"
        
        if not self.prompts_dir.exists():
            raise FileNotFoundError(
                f"Prompts directory not found: {self.prompts_dir}. "
                "Run: mkdir -p dnd_rag_system/prompts"
            )
        
        # Cache loaded templates
        self._template_cache: Dict[str, str] = {}
        
        logger.debug(f"PromptLoader initialized: {self.prompts_dir}")
    
    def load(self, template_name: str, **kwargs) -> str:
        """
        Load and format a prompt template.
        
        Args:
            template_name: Name of template file (without .txt extension)
            **kwargs: Variables to substitute into template
            
        Returns:
            Formatted prompt string
            
        Examples:
            >>> loader = PromptLoader()
            >>> prompt = loader.load("mechanics_extraction", 
            ...                      narrative="The goblin attacks!",
            ...                      char_context="",
            ...                      npc_context="")
        """
        # Load template (with caching)
        if template_name not in self._template_cache:
            template_path = self.prompts_dir / f"{template_name}.txt"
            
            if not template_path.exists():
                raise FileNotFoundError(
                    f"Prompt template not found: {template_path}\n"
                    f"Available templates: {self.list_templates()}"
                )
            
            with open(template_path, 'r', encoding='utf-8') as f:
                self._template_cache[template_name] = f.read()
            
            logger.debug(f"Loaded template: {template_name}")
        
        # Format with provided variables
        template = self._template_cache[template_name]
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(
                f"Missing required variable {e} for template '{template_name}'. "
                f"Provided: {list(kwargs.keys())}"
            )
    
    def list_templates(self) -> list:
        """List all available prompt templates."""
        return sorted([
            f.stem for f in self.prompts_dir.glob("*.txt")
        ])
    
    def reload(self, template_name: Optional[str] = None):
        """
        Clear template cache to force reload.
        
        Args:
            template_name: Specific template to reload, or None for all
        """
        if template_name:
            self._template_cache.pop(template_name, None)
            logger.debug(f"Cleared cache for: {template_name}")
        else:
            self._template_cache.clear()
            logger.debug("Cleared all template cache")


# Singleton instance for easy importing
_default_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """Get the singleton PromptLoader instance."""
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader()
    return _default_loader


def load_prompt(template_name: str, **kwargs) -> str:
    """
    Convenience function to load a prompt template.
    
    Args:
        template_name: Name of template file (without .txt)
        **kwargs: Variables to substitute
        
    Returns:
        Formatted prompt
        
    Example:
        >>> from dnd_rag_system.utils.prompt_loader import load_prompt
        >>> prompt = load_prompt("mechanics_extraction", narrative="...", char_context="", npc_context="")
    """
    return get_prompt_loader().load(template_name, **kwargs)
