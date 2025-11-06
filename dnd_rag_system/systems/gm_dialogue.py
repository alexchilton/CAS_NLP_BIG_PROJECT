"""
D&D Game Master Dialogue System

RAG-enhanced AI Dungeon Master powered by Ollama LLM.
Uses ChromaDB to retrieve D&D rules, spells, monsters, and classes in real-time.
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

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


class GameMaster:
    """
    RAG-Enhanced AI Game Master.

    Uses ChromaDB to retrieve D&D rules and Ollama for dialogue generation.
    """

    def __init__(self, db_manager: ChromaDBManager, model_name: str = None):
        """
        Initialize Game Master.

        Args:
            db_manager: ChromaDBManager instance
            model_name: Ollama model name (defaults to settings)
        """
        self.db = db_manager
        self.model_name = model_name or settings.OLLAMA_MODEL_NAME
        self.session = GameSession()

        # Verify Ollama is available
        self._verify_ollama()

    def _verify_ollama(self):
        """Check if Ollama is installed and model is available."""
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
        Generate GM response using RAG and Ollama.

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
3. Be concise and engaging
4. Maintain narrative flow while being mechanically precise
5. If rules are unclear, use standard D&D 5e mechanics

GM RESPONSE:"""

        return prompt

    def _query_ollama(self, prompt: str, timeout: int = 30) -> str:
        """
        Send prompt to Ollama and get response.

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

    def set_context(self, context: str):
        """Update current scene/context."""
        self.session.context = context
        self.session.add_message('system', f"Scene: {context}")

    def show_conversation_history(self, n: int = 10):
        """Display recent conversation history."""
        recent = self.session.get_recent_history(n)

        print("\n" + "="*70)
        print("CONVERSATION HISTORY")
        print("="*70)

        for msg in recent:
            if msg.role == 'system':
                print(f"\n📍 {msg.content}")
            elif msg.role == 'player':
                print(f"\n🎲 Player: {msg.content}")
                if msg.rag_context:
                    print(f"   [RAG: {len(msg.rag_context)} chars retrieved]")
            elif msg.role == 'gm':
                print(f"🎭 GM: {msg.content}")

        print("\n" + "="*70)

    def save_session(self, filepath: str):
        """Save session to JSON file."""
        session_data = {
            'session_name': self.session.session_name,
            'context': self.session.context,
            'messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'rag_context': msg.rag_context
                }
                for msg in self.session.messages
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"✓ Session saved to {filepath}")


class InteractiveGM:
    """
    Interactive Game Master CLI.

    Provides command-line interface for playing D&D with the AI GM.
    """

    def __init__(self, gm: GameMaster):
        """Initialize interactive GM."""
        self.gm = gm
        self.running = False

    def print_help(self):
        """Print available commands."""
        print("\n" + "="*70)
        print("COMMANDS")
        print("="*70)
        print("  /help          - Show this help")
        print("  /context <text> - Set scene/context")
        print("  /history       - Show conversation history")
        print("  /rag <query>   - Test RAG search")
        print("  /norag         - Next response without RAG")
        print("  /save <file>   - Save session")
        print("  /quit          - Exit")
        print("\nOtherwise, just type your action and press Enter!")
        print("="*70)

    def run(self):
        """Run interactive game loop."""
        print("\n" + "="*70)
        print("🎲 D&D GAME MASTER - RAG-Enhanced AI Dungeon Master")
        print("="*70)
        print(f"Model: {self.gm.model_name}")
        print(f"Database: {self.gm.db.persist_dir}")
        print("\nType /help for commands or just start playing!")
        print("="*70)

        self.running = True
        use_rag_next = True

        while self.running:
            try:
                # Get player input
                player_input = input("\n🎲 You: ").strip()

                if not player_input:
                    continue

                # Handle commands
                if player_input.startswith('/'):
                    self._handle_command(player_input)
                    continue

                # Generate GM response
                print("\n🎭 GM: ", end="", flush=True)
                response = self.gm.generate_response(player_input, use_rag=use_rag_next)
                print(response)

                # Reset RAG flag
                use_rag_next = True

            except KeyboardInterrupt:
                print("\n\n👋 Game interrupted. Type /quit to exit or continue playing.")
            except Exception as e:
                print(f"\n❌ Error: {e}")

    def _handle_command(self, command: str):
        """Handle slash commands."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == '/quit' or cmd == '/exit':
            print("\n👋 Thanks for playing! Farewell, adventurer!")
            self.running = False

        elif cmd == '/help':
            self.print_help()

        elif cmd == '/context':
            if args:
                self.gm.set_context(args)
                print(f"📍 Scene set: {args}")
            else:
                print(f"Current context: {self.gm.session.context}")

        elif cmd == '/history':
            self.gm.show_conversation_history()

        elif cmd == '/rag':
            if args:
                print(f"\n🔍 Searching RAG for: {args}")
                results = self.gm.search_rag(args)
                formatted = self.gm.format_rag_context(results)
                print("\n" + "─"*70)
                print(formatted)
                print("─"*70)
            else:
                print("Usage: /rag <query>")

        elif cmd == '/save':
            filename = args if args else "session.json"
            if not filename.endswith('.json'):
                filename += '.json'
            self.gm.save_session(filename)

        else:
            print(f"Unknown command: {cmd}")
            print("Type /help for available commands")


def main():
    """Main entry point for GM dialogue system."""
    print("\n🎲 Initializing D&D Game Master...")

    try:
        # Initialize ChromaDB
        print("📚 Connecting to D&D knowledge base...")
        db = ChromaDBManager()

        # Initialize Game Master
        print("🎭 Loading AI Dungeon Master...")
        gm = GameMaster(db)

        print("✅ Game Master ready!")

        # Start interactive session
        interactive = InteractiveGM(gm)
        interactive.run()

    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}")
        print("\nTroubleshooting:")
        print("  1. Run: python initialize_rag.py")
        print("  2. Install Ollama: https://ollama.ai")
        print(f"  3. Download model: ollama pull {settings.OLLAMA_MODEL_NAME}")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
