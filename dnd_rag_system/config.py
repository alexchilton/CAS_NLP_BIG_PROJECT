"""
D&D RAG System Configuration

Configuration settings for the D&D RAG system, including intent classification,
model settings, and feature toggles.
"""


class HuggingFaceConfig:
    """Configuration for HuggingFace Inference API"""

    # Model to use on HuggingFace Spaces
    # Used by: GameMaster, ActionValidator, MechanicsExtractor
    INFERENCE_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

    # Endpoint
    ROUTER_ENDPOINT = "https://router.huggingface.co"


class IntentClassifierConfig:
    """Configuration for action intent classification"""

    # Classifier types
    KEYWORD_BASED = "keyword"
    LLM_BASED = "llm"

    # Default classifier - LLM-based for better natural language understanding
    # Falls back to keyword-based automatically if LLM fails
    DEFAULT_CLASSIFIER = LLM_BASED

    # LLM settings (reuses same model as mechanics extractor)
    LLM_MODEL = "qwen2.5:3b"  # Fast, reliable for structured extraction
    LLM_TIMEOUT = 10  # seconds - intent classification should be quick

    # Debug mode (enables verbose logging)
    DEBUG_INTENT_CLASSIFICATION = False

    # Parallel comparison mode (for testing/validation)
    # When True, runs both classifiers and logs differences
    COMPARE_CLASSIFIERS = False


class MechanicsExtractorConfig:
    """Configuration for mechanics extraction from GM narrative"""

    # Model for extracting game mechanics from narrative
    MODEL = "qwen2.5:3b"  # Same model as intent classification
    TIMEOUT = 30  # seconds - narrative extraction can be more complex
    DEBUG = False


class GameConfig:
    """General game configuration"""

    # RAG settings
    RAG_ENABLED = True
    RAG_TOP_K = 3  # Number of similar documents to retrieve

    # Auto-save settings
    AUTO_SAVE_ENABLED = True
    AUTO_SAVE_INTERVAL = 300  # seconds (5 minutes)

    # Combat settings
    AUTO_ROLL_NPC_INITIATIVE = True

    # Shop settings
    REQUIRE_SHOP_LOCATION = True  # Enforce shop location validation
