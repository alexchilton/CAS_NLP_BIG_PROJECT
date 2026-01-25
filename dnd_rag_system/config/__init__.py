"""
Configuration package for D&D RAG System.
"""

from .settings import *

# Import configuration classes from config.py
import sys
from pathlib import Path

# Add parent directory to path to import config.py
config_module_path = Path(__file__).parent.parent / "config.py"
if config_module_path.exists():
    # Import classes from config.py sibling module
    import importlib.util
    spec = importlib.util.spec_from_file_location("config_classes", config_module_path)
    config_classes = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_classes)

    # Export the configuration classes
    HuggingFaceConfig = config_classes.HuggingFaceConfig
    IntentClassifierConfig = config_classes.IntentClassifierConfig
    MechanicsExtractorConfig = config_classes.MechanicsExtractorConfig
    GameConfig = config_classes.GameConfig
