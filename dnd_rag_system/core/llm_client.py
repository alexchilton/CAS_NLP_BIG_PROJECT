"""
LLM Client Factory for D&D RAG System.

Provides unified client creation for both HuggingFace Inference API and local Ollama,
with automatic environment detection.
"""

import os
import subprocess
from typing import Optional, Tuple, Any

from dnd_rag_system.config import is_huggingface_space, HuggingFaceConfig, settings


class LLMClientFactory:
    """
    Factory for creating LLM clients with automatic environment detection.

    Handles both HuggingFace Inference API (for HF Spaces) and local Ollama.
    """

    @staticmethod
    def create_client(
        model_name: Optional[str] = None,
        hf_token: Optional[str] = None,
        debug: bool = False
    ) -> Tuple[Any, str, bool]:
        """
        Create an LLM client with automatic environment detection.

        Args:
            model_name: Override model name (optional)
            hf_token: HuggingFace API token (optional, uses HF_TOKEN env var)
            debug: Enable debug logging

        Returns:
            Tuple of (client, model_name, use_hf_api):
            - client: InferenceClient (HF) or None (Ollama uses subprocess)
            - model_name: Model name being used
            - use_hf_api: True if using HF API, False if using Ollama

        Raises:
            ImportError: If HuggingFace dependencies missing on HF Spaces
            Exception: If Ollama not available in local mode
        """
        use_hf_api = is_huggingface_space()

        if use_hf_api:
            return LLMClientFactory._create_hf_client(model_name, hf_token, debug)
        else:
            return LLMClientFactory._create_ollama_client(model_name, debug)

    @staticmethod
    def _create_hf_client(
        model_name: Optional[str],
        hf_token: Optional[str],
        debug: bool
    ) -> Tuple[Any, str, bool]:
        """Create HuggingFace Inference API client."""
        if debug:
            print("🤗 Using Hugging Face Inference API mode")

        try:
            from huggingface_hub import InferenceClient
        except ImportError:
            raise ImportError(
                "huggingface_hub is required for HF Spaces. "
                "Install with: pip install huggingface_hub"
            )

        token = hf_token or os.getenv("HF_TOKEN")
        # Always use HuggingFaceConfig model on HF Spaces
        # Ignore Ollama-format models like "qwen2.5:3b"
        model = HuggingFaceConfig.INFERENCE_MODEL

        client = InferenceClient(
            token=token,
            base_url=HuggingFaceConfig.ROUTER_ENDPOINT
        )

        if debug:
            print(f"   Model: {model}")
            print(f"   Endpoint: {HuggingFaceConfig.ROUTER_ENDPOINT}")
            print(f"   Note: Using Inference API compatible model")

        return client, model, True

    @staticmethod
    def _create_ollama_client(
        model_name: Optional[str],
        debug: bool
    ) -> Tuple[None, str, bool]:
        """Create Ollama client (returns None - Ollama uses subprocess)."""
        if debug:
            print("🦙 Using local Ollama mode")

        model = model_name or settings.OLLAMA_MODEL_NAME

        # Verify Ollama is available
        LLMClientFactory._verify_ollama(model)

        if debug:
            print(f"   Model: {model}")

        return None, model, False

    @staticmethod
    def _verify_ollama(model_name: str) -> None:
        """
        Verify Ollama is installed and model is available.

        Args:
            model_name: Model to check for

        Raises:
            Exception: If Ollama not found, not responding, or model not available
        """
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise Exception("Ollama not responding")

            # Check if model exists
            if model_name not in result.stdout:
                print(f"⚠️  Model '{model_name}' not found in Ollama")
                print(f"   Available models:\n{result.stdout}")
                print(f"\n   To download: ollama pull {model_name}")
                raise Exception(f"Model {model_name} not available")

        except FileNotFoundError:
            raise Exception(
                "Ollama not found. Please install from https://ollama.ai"
            )
        except subprocess.TimeoutExpired:
            raise Exception("Ollama not responding (timeout)")


class OllamaClient:
    """
    Wrapper for Ollama subprocess calls to provide a consistent interface.

    This mirrors the InferenceClient API for easier code reuse.
    """

    def __init__(self, model_name: str):
        """
        Initialize Ollama client wrapper.

        Args:
            model_name: Ollama model name
        """
        self.model_name = model_name
        LLMClientFactory._verify_ollama(model_name)

    def text_generation(
        self,
        prompt: str,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: int = 120
    ) -> str:
        """
        Generate text using Ollama.

        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate (unused for Ollama)
            temperature: Sampling temperature (unused for Ollama)
            timeout: Response timeout in seconds

        Returns:
            Generated text

        Raises:
            Exception: If Ollama query fails
        """
        try:
            result = subprocess.run(
                ['ollama', 'run', self.model_name, prompt],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                raise Exception(f"Ollama error: {result.stderr}")

            response = result.stdout.strip()
            return response if response else "..."

        except subprocess.TimeoutExpired:
            raise Exception("Response timed out (LLM took too long)")
        except Exception as e:
            raise Exception(f"Ollama query failed: {e}")
