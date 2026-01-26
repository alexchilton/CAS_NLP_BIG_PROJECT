"""
Model configuration for D&D RAG System.

Contains settings for LLM models used across the system.
"""

from dnd_rag_system.config.model_registry import ModelRegistry


class HuggingFaceConfig:
    """Configuration for HuggingFace Inference API"""

    # Model to use on HuggingFace Spaces
    # Used by: GameMaster, ActionValidator, MechanicsExtractor
    INFERENCE_MODEL = ModelRegistry.HUGGINGFACE_INFERENCE.name

    # Endpoint
    ROUTER_ENDPOINT = "https://router.huggingface.co"
