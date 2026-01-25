"""
Configuration package for D&D RAG System.

Centralizes all configuration settings:
- settings: General settings, Ollama models, collection names
- environment: Environment detection (HF Spaces vs local)
- models: LLM model configurations (HuggingFace, Ollama)
- game: Game system configurations (intent classifier, mechanics, etc.)
"""

# Core settings
from .settings import *

# Environment detection
from .environment import is_huggingface_space, get_environment_name

# Model configurations
from .models import HuggingFaceConfig

# Game system configurations
from .game import (
    IntentClassifierConfig,
    MechanicsExtractorConfig,
    GameConfig
)

# Export all for convenience
__all__ = [
    # From settings
    'settings',

    # Environment
    'is_huggingface_space',
    'get_environment_name',

    # Models
    'HuggingFaceConfig',

    # Game
    'IntentClassifierConfig',
    'MechanicsExtractorConfig',
    'GameConfig',
]
