"""
D&D Game Master Dialogue System - Unified Version

RAG-enhanced AI Dungeon Master that automatically detects environment:
- Hugging Face Inference API (when running on HF Spaces)
- Local Ollama (for local development)

Auto-detection based on SPACE_ID, SPACE_AUTHOR_NAME, or HF_SPACE environment variables.
"""

import sys
import subprocess
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings


def is_huggingface_space() -> bool:
    """Check if running on Hugging Face Spaces."""
    return (
        os.getenv("SPACE_ID") is not None or
        os.getenv("SPACE_AUTHOR_NAME") is not None or
        os.getenv("HF_SPACE") is not None or
        os.getenv("USE_HF_API", "false").lower() == "true"  # Manual override
    )


@dataclass
class Message:
    """Conversation message."""
    role: str  # 'player', 'gm', 'system'
    content: str
    rag_context: Optional[str] = None


@dataclass
class GameSession:
    """D&D game session state."""
    session_name: str = "D&D Adventure"
    messages: List[Message] = field(default_factory=list)
    context: str = "You are adventuring in a fantasy world"
    active_characters: List[str] = field(default_factory=list)

    def add_message(self, role: str, content: str, rag_context: Optional[str] = None):
        """Add message to conversation history."""
        self.messages.append(Message(role, content, rag_context))

    def get_recent_history(self, n: int = 5) -> List[Message]:
        """Get recent conversation history."""
        return self.messages[-n:] if len(self.messages) > n else self.messages


class GameMaster:
    """
    RAG-Enhanced AI Game Master - Unified Version.

    Automatically uses:
    - HF Inference API on Hugging Face Spaces
    - Ollama for local development
    """

    def __init__(self, db_manager: ChromaDBManager, hf_token: str = None, model_name: str = None):
        """
        Initialize Game Master.

        Args:
            db_manager: ChromaDBManager instance
            hf_token: Hugging Face API token (optional, will use env var)
            model_name: Model name override (optional)
        """
        self.db = db_manager
        self.session = GameSession()

        # Auto-detect environment
        self.use_hf_api = is_huggingface_space()

        if self.use_hf_api:
            print("🤗 Using Hugging Face Inference API mode")
            try:
                from huggingface_hub import InferenceClient
            except ImportError:
                raise ImportError("huggingface_hub is required for HF Spaces. Install with: pip install huggingface_hub")

            self.hf_token = hf_token or os.getenv("HF_TOKEN")
            # Use a model that's available via Inference API
            # Qwen2.5-7B-Instruct is excellent for roleplay and available on HF Inference API
            self.model_name = model_name or "Qwen/Qwen2.5-7B-Instruct"
            self.client = InferenceClient(token=self.hf_token)
            print(f"   Model: {self.model_name}")
            print(f"   Note: Using Inference API compatible model (local uses RPG-specific model)")
        else:
            print("🦙 Using local Ollama mode")
            # Local Ollama model
            self.model_name = model_name or settings.OLLAMA_MODEL_NAME
            self.client = None
            self._verify_ollama()
            print(f"   Model: {self.model_name}")

    def _verify_ollama(self):
        """Check if Ollama is installed and model is available (local mode only)."""
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
            if self.model_name not in result.stdout:
                print(f"⚠️  Model '{self.model_name}' not found in Ollama")
                print(f"   Available models:\n{result.stdout}")
                print(f"\n   To download: ollama pull {self.model_name}")
                raise Exception(f"Model {self.model_name} not available")

        except FileNotFoundError:
            raise Exception("Ollama not found. Please install from https://ollama.ai")
        except subprocess.TimeoutExpired:
            raise Exception("Ollama not responding (timeout)")

    def search_rag(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """
        Search RAG database for relevant D&D content.

        Args:
            query: Search query
            n_results: Number of results per collection

        Returns:
            Dictionary with results from all collections
        """
        results = {}

        # Search each collection
        for collection_type, collection_name in settings.COLLECTION_NAMES.items():
            try:
                search_results = self.db.search(
                    collection_name,
                    query,
                    n_results=n_results
                )

                if search_results['documents'] and search_results['documents'][0]:
                    results[collection_type] = {
                        'documents': search_results['documents'][0],
                        'metadatas': search_results['metadatas'][0],
                        'distances': search_results['distances'][0]
                    }
            except Exception as e:
                print(f"Warning: Could not search {collection_type}: {e}")
                continue

        return results

    def format_rag_context(self, rag_results: Dict[str, Any]) -> str:
        """
        Format RAG search results into context for LLM prompt.

        Args:
            rag_results: Results from search_rag()

        Returns:
            Formatted context string
        """
        if not rag_results:
            return "No specific rules retrieved."

        context_parts = []

        for collection_type, results in rag_results.items():
            docs = results['documents']
            metas = results['metadatas']
            distances = results['distances']

            for doc, meta, dist in zip(docs, metas, distances):
                # Only include very relevant results (distance < 1.0)
                if dist < 1.0:
                    name = meta.get('name', 'Unknown')
                    context_parts.append(f"[{collection_type.upper()}] {name}:\n{doc[:400]}")

        return "\n\n".join(context_parts) if context_parts else "No highly relevant rules found."

    def generate_response(self, player_input: str, use_rag: bool = True) -> str:
        """
        Generate GM response using RAG and LLM (Ollama or HF API).

        Args:
            player_input: Player's action or question
            use_rag: Whether to use RAG retrieval

        Returns:
            GM response
        """
        rag_context = ""

        # Step 1: Search RAG if enabled
        if use_rag:
            rag_results = self.search_rag(player_input)
            rag_context = self.format_rag_context(rag_results)

        # Step 2: Build prompt with history and RAG context
        prompt = self._build_prompt(player_input, rag_context)

        # Step 3: Get LLM response (route based on mode)
        try:
            if self.use_hf_api:
                response = self._query_hf(prompt)
            else:
                response = self._query_ollama(prompt)

            # Save to history
            self.session.add_message('player', player_input, rag_context if use_rag else None)
            self.session.add_message('gm', response)

            return response

        except Exception as e:
            return f"Error generating response: {e}"

    def _build_prompt(self, player_input: str, rag_context: str) -> str:
        """Build complete prompt for LLM."""

        # Get recent conversation history
        history = self.session.get_recent_history(n=4)
        history_text = "\n".join([
            f"{'Player' if msg.role == 'player' else 'GM'}: {msg.content}"
            for msg in history
        ])

        prompt = f"""You are an experienced Dungeon Master running a D&D 5e game.

CURRENT SCENE: {self.session.context}

"""

        if rag_context and rag_context != "No specific rules retrieved." and rag_context != "No highly relevant rules found.":
            prompt += f"""RETRIEVED D&D RULES (Apply these rules accurately):
{rag_context}

"""

        if history_text:
            prompt += f"""RECENT CONVERSATION:
{history_text}

"""

        prompt += f"""PLAYER ACTION: {player_input}

INSTRUCTIONS:
1. Apply D&D 5e rules accurately using the retrieved information
2. Ask for appropriate dice rolls (d20 for attacks/checks, damage dice, saves, etc.)
3. Be concise and engaging (2-4 sentences max)
4. Maintain narrative flow while being mechanically precise
5. If rules are unclear, use standard D&D 5e mechanics

GM RESPONSE:"""

        return prompt

    def _query_ollama(self, prompt: str, timeout: int = 120) -> str:
        """
        Send prompt to Ollama and get response (local mode).

        Args:
            prompt: Complete prompt
            timeout: Response timeout in seconds

        Returns:
            Model response
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

            # Clean up response (remove prompt echo if present)
            if "GM RESPONSE:" in response:
                response = response.split("GM RESPONSE:")[-1].strip()

            return response if response else "..."

        except subprocess.TimeoutExpired:
            raise Exception("Response timed out (LLM took too long)")
        except Exception as e:
            raise Exception(f"Ollama query failed: {e}")

    def _query_hf(self, prompt: str, timeout: int = 60) -> str:
        """
        Send prompt to Hugging Face Inference API and get response (HF mode).

        Args:
            prompt: Complete prompt
            timeout: Response timeout in seconds

        Returns:
            Model response
        """
        try:
            response = self.client.text_generation(
                prompt,
                model=self.model_name,
                max_new_tokens=300,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
                do_sample=True,
            )

            # Clean up response
            response = response.strip()

            # Remove prompt echo if present
            if "GM RESPONSE:" in response:
                response = response.split("GM RESPONSE:")[-1].strip()

            return response if response else "..."

        except Exception as e:
            raise Exception(f"HF Inference API query failed: {e}")

    def set_context(self, context: str):
        """Update current scene/context."""
        self.session.context = context
        self.session.add_message('system', f"Scene: {context}")
