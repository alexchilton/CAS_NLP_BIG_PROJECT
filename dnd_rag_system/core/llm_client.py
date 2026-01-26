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


class LLMClient:
    """
    Unified LLM client that works with both Ollama and HuggingFace Inference API.
    
    Centralizes all LLM query logic with consistent interface, error handling,
    debug logging, and response cleaning.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        hf_token: Optional[str] = None,
        debug: bool = False
    ):
        """
        Initialize unified LLM client.

        Args:
            model_name: Override model name (optional)
            hf_token: HuggingFace API token (optional)
            debug: Enable debug logging
        """
        self.debug = debug
        self.client, self.model_name, self.use_hf_api = LLMClientFactory.create_client(
            model_name=model_name,
            hf_token=hf_token,
            debug=debug
        )

    def query(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.7,
        timeout: int = 120,
        clean_response: bool = True
    ) -> str:
        """
        Query the LLM with a prompt.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            timeout: Response timeout in seconds
            clean_response: Whether to clean/sanitize the response

        Returns:
            Model response

        Raises:
            Exception: If query fails
        """
        if self.use_hf_api:
            return self._query_hf(prompt, max_tokens, temperature, timeout, clean_response)
        else:
            return self._query_ollama(prompt, timeout, clean_response)

    def _query_ollama(
        self,
        prompt: str,
        timeout: int = 120,
        clean_response: bool = True
    ) -> str:
        """Query Ollama (local mode)."""
        import re
        import logging
        logger = logging.getLogger(__name__)

        # Log prompt if debug mode
        if self.debug:
            logger.debug("=" * 80)
            logger.debug("PROMPT SENT TO OLLAMA:")
            logger.debug("-" * 80)
            logger.debug(prompt)
            logger.debug("=" * 80)

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

            if clean_response:
                response = self._clean_ollama_response(response)

            # Log response if debug mode
            if self.debug:
                logger.debug("-" * 80)
                logger.debug("RESPONSE FROM OLLAMA:")
                logger.debug(response)
                logger.debug("=" * 80)

            return response if response else "..."

        except subprocess.TimeoutExpired:
            raise Exception("Response timed out (LLM took too long)")
        except Exception as e:
            raise Exception(f"Ollama query failed: {e}")

    def _query_hf(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.7,
        timeout: int = 60,
        clean_response: bool = True
    ) -> str:
        """Query HuggingFace Inference API."""
        import logging
        logger = logging.getLogger(__name__)

        # Log prompt if debug mode
        if self.debug:
            logger.debug("=" * 80)
            logger.debug("PROMPT SENT TO HUGGING FACE API:")
            logger.debug("-" * 80)
            logger.debug(prompt)
            logger.debug("=" * 80)

        try:
            # Try chat_completion first (huggingface-hub >= 0.22)
            # Fall back to text_generation for older versions
            if hasattr(self.client, 'chat_completion'):
                # Newer API (v0.22+)
                messages = [{"role": "user", "content": prompt}]

                response = self.client.chat_completion(
                    messages=messages,
                    model=self.model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9,
                )

                response_text = response.choices[0].message.content.strip()
            else:
                # Older API (v0.20.3)
                logger.info("Using text_generation API (huggingface-hub < 0.22)")
                response_text = self.client.text_generation(
                    prompt=prompt,
                    model=self.model_name,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9,
                    return_full_text=False,
                )

            if clean_response:
                # Remove prompt echo if present
                if "GM RESPONSE:" in response_text:
                    response_text = response_text.split("GM RESPONSE:")[-1].strip()

            # Log response if debug mode
            if self.debug:
                logger.debug("-" * 80)
                logger.debug("RESPONSE FROM HUGGING FACE API:")
                logger.debug(response_text)
                logger.debug("=" * 80)

            return response_text if response_text else "..."

        except Exception as e:
            raise Exception(f"HF Inference API query failed: {e}")

    def _clean_ollama_response(self, response: str) -> str:
        """
        Clean up Ollama responses to remove hallucinated system prompts.

        Ollama models sometimes leak training data and system prompts.
        This removes common hallucination patterns.
        """
        import re

        # Remove prompt echo if present
        if "GM RESPONSE:" in response:
            response = response.split("GM RESPONSE:")[-1].strip()

        # Remove {{user}} template markers
        if "{{user}}" in response:
            response = response.split("{{user}}")[0].strip()

        # Remove "Take the role of" instruction blocks
        if "Take the role of" in response:
            response = response.split("Take the role of")[0].strip()

        # Remove "You must engage in roleplay" blocks
        if "you must roleplay" in response.lower():
            parts = re.split(r'you must (?:engage in )?roleplay', response, flags=re.IGNORECASE)
            response = parts[0].strip()

        # Remove "Never write for" instruction blocks
        if "Never write for" in response:
            response = response.split("Never write for")[0].strip()

        # Remove "Scenario:" metadata blocks
        if "Scenario:" in response:
            response = response.split("Scenario:")[0].strip()

        # Remove markdown code fences
        response = re.sub(r'```[\w]*\n.*?```', '', response, flags=re.DOTALL)

        # Remove duplicate paragraphs (hallucination symptom)
        paragraphs = response.split('\n\n')
        seen = set()
        cleaned_paragraphs = []
        for para in paragraphs:
            para_clean = para.strip()
            if para_clean and para_clean not in seen:
                seen.add(para_clean)
                cleaned_paragraphs.append(para)
        response = '\n\n'.join(cleaned_paragraphs)

        return response.strip()
