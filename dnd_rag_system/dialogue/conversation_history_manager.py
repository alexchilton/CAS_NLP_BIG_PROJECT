"""
Conversation History Management

Handles message history, pruning, and summarization for GM dialogue system.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Conversation message for GM dialogue history."""
    role: str  # 'player', 'gm', 'system'
    content: str
    rag_context: Optional[str] = None
    timestamp: Optional[str] = None  # For tracking when message occurred


class ConversationHistoryManager:
    """
    Manages conversation history and summarization for the GM system.

    Responsibilities:
    - Store and retrieve message history
    - Prune old messages when context window is full
    - Generate summaries of pruned messages
    - Format history for LLM prompts

    Extracted from GameMaster class to follow Single Responsibility Principle.
    """

    def __init__(self, max_history: int = 30):
        """
        Initialize conversation history manager.

        Args:
            max_history: Maximum number of messages to keep in active history
        """
        self.message_history: List[Message] = []
        self.conversation_summary: str = ""
        self.max_history = max_history

    def add_message(self, role: str, content: str, rag_context: Optional[str] = None):
        """
        Add a message to the conversation history.

        Args:
            role: Message role ('player', 'gm', 'system')
            content: Message content
            rag_context: Optional RAG context used for this message
        """
        self.message_history.append(Message(role, content, rag_context))

    def get_recent_messages(self, n: int = 10) -> List[Message]:
        """
        Get the N most recent messages.

        Args:
            n: Number of recent messages to retrieve

        Returns:
            List of recent messages
        """
        return self.message_history[-n:] if len(self.message_history) > n else self.message_history

    def format_for_prompt(self, n_recent: int = 10) -> str:
        """
        Format recent conversation history for LLM prompt.

        Args:
            n_recent: Number of recent messages to include

        Returns:
            Formatted history string
        """
        recent_messages = self.get_recent_messages(n_recent)

        history_text = "\n".join([
            f"{'Player' if msg.role == 'player' else 'GM'}: {msg.content}"
            for msg in recent_messages
        ])

        return history_text

    def prune_history(self, is_party_mode: bool = False) -> bool:
        """
        Prune message history to prevent context window overflow.
        Keeps recent messages and creates summary of older ones.
        Uses more aggressive pruning for party mode.

        Args:
            is_party_mode: Whether in party mode (larger prompts, need more aggressive pruning)

        Returns:
            True if pruning occurred, False otherwise
        """
        # More aggressive pruning for party mode (5 characters = larger prompts)
        max_history = self.max_history if not is_party_mode else max(12, self.max_history // 2)

        # If history is within limits, no action needed
        if len(self.message_history) <= max_history:
            return False

        # Calculate how many messages to summarize
        messages_to_summarize = len(self.message_history) - max_history

        # Extract messages to summarize
        old_messages = self.message_history[:messages_to_summarize]

        # Create summary of old messages
        summary_text = self._create_message_summary(old_messages)

        # Update conversation summary
        if self.conversation_summary:
            self.conversation_summary += f"\n\n--- Session Continued ---\n{summary_text}"
        else:
            self.conversation_summary = summary_text

        # Keep only recent messages
        self.message_history = self.message_history[messages_to_summarize:]

        # Log for debugging
        mode_indicator = "party mode" if is_party_mode else "solo mode"
        logger.info(f"📝 Pruned {messages_to_summarize} messages ({mode_indicator}). History now: {len(self.message_history)} messages")

        return True

    def _create_message_summary(self, messages: List[Message]) -> str:
        """
        Create a concise summary of message exchanges.
        Focuses on key events: combat, quests, important discoveries.

        Args:
            messages: List of messages to summarize

        Returns:
            Summary text
        """
        if not messages:
            return ""

        # Build summary from key events
        summary_lines = []

        for msg in messages:
            # Extract important events (combat, quests, travel, shopping)
            content_lower = msg.content.lower()

            # Combat events
            if any(word in content_lower for word in ['combat', 'attack', 'damage', 'hp', 'defeated', 'killed']):
                if msg.role == 'gm':
                    # Condensed combat outcome
                    if 'defeated' in content_lower or 'killed' in content_lower or 'fled' in content_lower:
                        summary_lines.append(f"⚔️ Combat: {msg.content[:100]}")

            # Quest events
            elif any(word in content_lower for word in ['quest', 'mission', 'task', 'objective']):
                summary_lines.append(f"📜 Quest: {msg.content[:100]}")

            # Travel/exploration
            elif any(word in content_lower for word in ['travel', 'arrive', 'enter', 'leave', 'journey']):
                summary_lines.append(f"🗺️ Travel: {msg.content[:100]}")

            # Shopping/transactions
            elif any(word in content_lower for word in ['buy', 'sell', 'purchase', 'gold', 'shop']):
                summary_lines.append(f"💰 Trade: {msg.content[:100]}")

            # Important discoveries
            elif any(word in content_lower for word in ['find', 'discover', 'treasure', 'loot', 'item']):
                summary_lines.append(f"🔍 Discovery: {msg.content[:100]}")

        # If no key events found, create generic summary
        if not summary_lines:
            return f"The party had {len(messages)//2} exchanges covering general exploration and conversation."

        return "\n".join(summary_lines)

    def get_summary(self, max_chars: int = 500) -> str:
        """
        Get the conversation summary (for including in prompts).

        Args:
            max_chars: Maximum number of characters to return

        Returns:
            Summary text (truncated if necessary)
        """
        if not self.conversation_summary:
            return ""

        return self.conversation_summary[-max_chars:]

    def clear(self):
        """Clear all message history and summary."""
        self.message_history = []
        self.conversation_summary = ""

    def __len__(self) -> int:
        """Return the number of messages in active history."""
        return len(self.message_history)
