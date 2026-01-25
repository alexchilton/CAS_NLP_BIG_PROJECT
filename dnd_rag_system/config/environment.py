"""
Environment detection utilities for D&D RAG System.

Centralizes environment detection logic to avoid duplication across multiple files.
"""

import os


def is_huggingface_space() -> bool:
    """
    Detect if running on HuggingFace Spaces.

    Checks for HuggingFace-specific environment variables:
    - SPACE_ID: Automatically set by HF Spaces
    - SPACE_AUTHOR_NAME: Automatically set by HF Spaces
    - HF_SPACE: Legacy variable
    - USE_HF_API: Manual override for testing

    Returns:
        True if running on HuggingFace Spaces, False if running locally
    """
    return (
        os.getenv("SPACE_ID") is not None or
        os.getenv("SPACE_AUTHOR_NAME") is not None or
        os.getenv("HF_SPACE") is not None or
        os.getenv("USE_HF_API", "false").lower() == "true"
    )


def get_environment_name() -> str:
    """
    Get a human-readable name for the current environment.

    Returns:
        "huggingface" if on HF Spaces, "local" otherwise
    """
    return "huggingface" if is_huggingface_space() else "local"
