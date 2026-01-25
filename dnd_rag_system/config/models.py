"""
Model configuration for D&D RAG System.

Contains settings for LLM models used across the system.
"""


class HuggingFaceConfig:
    """Configuration for HuggingFace Inference API"""

    # Model to use on HuggingFace Spaces
    # Used by: GameMaster, ActionValidator, MechanicsExtractor
    INFERENCE_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

    # Endpoint
    ROUTER_ENDPOINT = "https://router.huggingface.co"
