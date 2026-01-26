"""
Model Registry - Centralized Model Configuration

Single source of truth for all LLM model names used across the system.
Update once here instead of in multiple files.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    description: str
    use_case: str
    size: str
    speed: str  # fast, medium, slow
    quality: str  # high, medium, low


class ModelRegistry:
    """
    Centralized registry of all LLM models used in the system.
    
    Benefits:
    - Single source of truth for model names
    - Easy to swap models across the entire system
    - Documents what each model is used for
    - Prevents typos in model names
    """
    
    # ============================================================================
    # PRIMARY MODELS (Most frequently used)
    # ============================================================================
    
    # Roleplay-optimized model for narrative generation
    ROLEPLAY = ModelConfig(
        name="hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M",
        description="4B param model fine-tuned on RPG/roleplay data",
        use_case="Main GM dialogue, narrative generation, monster descriptions, item lore",
        size="3.2GB",
        speed="medium",
        quality="high"
    )
    
    # Fast model for structured extraction
    MECHANICS = ModelConfig(
        name="qwen2.5:3b",
        description="Fast 3B param model optimized for JSON extraction",
        use_case="Intent classification, mechanics extraction, validation",
        size="1.9GB", 
        speed="fast",
        quality="medium"
    )
    
    # HuggingFace Inference API model (used on HF Spaces)
    HUGGINGFACE_INFERENCE = ModelConfig(
        name="meta-llama/Llama-3.1-8B-Instruct",
        description="Llama 3.1 8B via HF Inference API",
        use_case="All tasks when running on HuggingFace Spaces",
        size="8B params",
        speed="medium",
        quality="high"
    )
    
    # ============================================================================
    # MODEL USAGE MAP
    # ============================================================================
    
    @classmethod
    def get_model_for_task(cls, task: str, use_hf_api: bool = False) -> str:
        """
        Get the appropriate model name for a specific task.
        
        Args:
            task: Task identifier (dialogue, mechanics, intent, monsters, items, etc.)
            use_hf_api: Whether running on HuggingFace Spaces (uses Inference API)
            
        Returns:
            Model name string
        """
        # On HuggingFace Spaces, everything uses the Inference API model
        if use_hf_api:
            return cls.HUGGINGFACE_INFERENCE.name
        
        # Task-specific model selection for local Ollama
        task_map = {
            # Narrative generation tasks (use roleplay model)
            "dialogue": cls.ROLEPLAY.name,
            "narrative": cls.ROLEPLAY.name,
            "monsters": cls.ROLEPLAY.name,
            "items": cls.ROLEPLAY.name,
            "exploration": cls.ROLEPLAY.name,
            "locations": cls.ROLEPLAY.name,
            
            # Structured extraction tasks (use fast mechanics model)
            "mechanics": cls.MECHANICS.name,
            "intent": cls.MECHANICS.name,
            "validation": cls.MECHANICS.name,
            "extraction": cls.MECHANICS.name,
        }
        
        return task_map.get(task, cls.ROLEPLAY.name)
    
    @classmethod
    def get_all_models(cls) -> Dict[str, ModelConfig]:
        """Get dictionary of all available models."""
        return {
            "roleplay": cls.ROLEPLAY,
            "mechanics": cls.MECHANICS,
            "huggingface": cls.HUGGINGFACE_INFERENCE,
        }
    
    @classmethod
    def print_model_info(cls):
        """Print information about all registered models."""
        print("=" * 80)
        print("MODEL REGISTRY")
        print("=" * 80)
        
        for name, config in cls.get_all_models().items():
            print(f"\n{name.upper()}:")
            print(f"  Name: {config.name}")
            print(f"  Description: {config.description}")
            print(f"  Use Case: {config.use_case}")
            print(f"  Size: {config.size}")
            print(f"  Speed: {config.speed} | Quality: {config.quality}")
        
        print("\n" + "=" * 80)


# ============================================================================
# CONVENIENCE CONSTANTS (for backward compatibility)
# ============================================================================

# Legacy constant names that existing code might use
OLLAMA_MODEL_NAME = ModelRegistry.ROLEPLAY.name
DEFAULT_MECHANICS_MODEL = ModelRegistry.MECHANICS.name
HUGGINGFACE_INFERENCE_MODEL = ModelRegistry.HUGGINGFACE_INFERENCE.name


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Print all model info
    ModelRegistry.print_model_info()
    
    # Get model for specific tasks
    print("\nTask-based model selection (local):")
    print(f"  Dialogue: {ModelRegistry.get_model_for_task('dialogue')}")
    print(f"  Mechanics: {ModelRegistry.get_model_for_task('mechanics')}")
    print(f"  Intent: {ModelRegistry.get_model_for_task('intent')}")
    
    print("\nTask-based model selection (HuggingFace):")
    print(f"  All tasks: {ModelRegistry.get_model_for_task('dialogue', use_hf_api=True)}")
