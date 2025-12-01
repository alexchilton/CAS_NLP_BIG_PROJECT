"""
D&D Game Master Dialogue System - Hugging Face Spaces Version

RAG-enhanced AI Dungeon Master using Hugging Face Inference API.
Uses ChromaDB to retrieve D&D rules, spells, monsters, and classes in real-time.
"""

import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from huggingface_hub import InferenceClient

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings


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


class GameMasterHF:
    """
    RAG-Enhanced AI Game Master for Hugging Face Spaces.

    Uses ChromaDB to retrieve D&D rules and HF Inference API for dialogue generation.
    """

    def __init__(self, db_manager: ChromaDBManager, hf_token: str = None, model_name: str = None):
        """
        Initialize Game Master.

        Args:
            db_manager: ChromaDBManager instance
            hf_token: Hugging Face API token (or from environment)
            model_name: Model to use (defaults to Qwen2.5-14B-Instruct for good RPG performance)
        """
        self.db = db_manager
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.model_name = model_name or "Qwen/Qwen2.5-14B-Instruct"  # Good for RPG
        self.session = GameSession()

        # Initialize HF Inference Client
        self.client = InferenceClient(token=self.hf_token)

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
        Generate GM response using RAG and HF Inference API.

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

        # Step 3: Get LLM response
        try:
            response = self._query_hf(prompt)

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

    def _query_hf(self, prompt: str, timeout: int = 30) -> str:
        """
        Send prompt to Hugging Face Inference API and get response.

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
