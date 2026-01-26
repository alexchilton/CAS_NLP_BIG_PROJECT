"""
Unit tests for ConversationHistoryManager.

Tests the extracted conversation history and summarization logic.
"""

import pytest
from dnd_rag_system.dialogue.conversation_history_manager import (
    ConversationHistoryManager,
    Message
)


@pytest.fixture
def history_manager():
    """Create a ConversationHistoryManager instance."""
    return ConversationHistoryManager(max_history=30)


class TestInitialization:
    """Test suite for initialization."""

    def test_initialization_default(self):
        """Test that ConversationHistoryManager initializes with defaults."""
        manager = ConversationHistoryManager()
        assert manager.message_history == []
        assert manager.conversation_summary == ""
        assert manager.max_history == 30

    def test_initialization_custom_max(self):
        """Test initialization with custom max history."""
        manager = ConversationHistoryManager(max_history=20)
        assert manager.max_history == 20


class TestAddMessage:
    """Test suite for adding messages."""

    def test_add_player_message(self, history_manager):
        """Test adding a player message."""
        history_manager.add_message('player', 'I attack the goblin')

        assert len(history_manager.message_history) == 1
        assert history_manager.message_history[0].role == 'player'
        assert history_manager.message_history[0].content == 'I attack the goblin'

    def test_add_gm_message(self, history_manager):
        """Test adding a GM message."""
        history_manager.add_message('gm', 'The goblin dodges your attack')

        assert len(history_manager.message_history) == 1
        assert history_manager.message_history[0].role == 'gm'

    def test_add_message_with_rag_context(self, history_manager):
        """Test adding a message with RAG context."""
        history_manager.add_message(
            'player',
            'I cast fireball',
            rag_context='Fireball spell details...'
        )

        assert history_manager.message_history[0].rag_context == 'Fireball spell details...'

    def test_add_multiple_messages(self, history_manager):
        """Test adding multiple messages."""
        history_manager.add_message('player', 'Hello')
        history_manager.add_message('gm', 'Greetings, adventurer')
        history_manager.add_message('player', 'I explore the dungeon')

        assert len(history_manager.message_history) == 3


class TestGetRecentMessages:
    """Test suite for retrieving recent messages."""

    def test_get_recent_messages_less_than_n(self, history_manager):
        """Test getting recent messages when total < n."""
        history_manager.add_message('player', 'Message 1')
        history_manager.add_message('gm', 'Message 2')

        recent = history_manager.get_recent_messages(10)
        assert len(recent) == 2

    def test_get_recent_messages_more_than_n(self, history_manager):
        """Test getting recent messages when total > n."""
        for i in range(20):
            history_manager.add_message('player', f'Message {i}')

        recent = history_manager.get_recent_messages(5)
        assert len(recent) == 5
        assert recent[0].content == 'Message 15'  # Last 5 messages
        assert recent[-1].content == 'Message 19'

    def test_get_recent_messages_empty_history(self, history_manager):
        """Test getting recent messages from empty history."""
        recent = history_manager.get_recent_messages(10)
        assert len(recent) == 0


class TestFormatForPrompt:
    """Test suite for formatting history for prompts."""

    def test_format_for_prompt_basic(self, history_manager):
        """Test basic prompt formatting."""
        history_manager.add_message('player', 'I attack')
        history_manager.add_message('gm', 'You hit!')

        formatted = history_manager.format_for_prompt(10)

        assert 'Player: I attack' in formatted
        assert 'GM: You hit!' in formatted

    def test_format_for_prompt_respects_n_recent(self, history_manager):
        """Test that formatting respects n_recent parameter."""
        for i in range(10):
            history_manager.add_message('player', f'Message {i}')

        formatted = history_manager.format_for_prompt(3)

        # Should only contain last 3 messages
        assert 'Message 7' in formatted
        assert 'Message 8' in formatted
        assert 'Message 9' in formatted
        assert 'Message 0' not in formatted

    def test_format_for_prompt_system_messages(self, history_manager):
        """Test formatting with system messages."""
        history_manager.add_message('system', 'Combat started')

        formatted = history_manager.format_for_prompt(10)

        # System messages should be formatted as GM
        assert 'GM: Combat started' in formatted


class TestPruneHistory:
    """Test suite for history pruning."""

    def test_prune_history_not_needed(self, history_manager):
        """Test that pruning doesn't occur when below limit."""
        for i in range(10):
            history_manager.add_message('player', f'Message {i}')

        pruned = history_manager.prune_history()

        assert pruned is False
        assert len(history_manager.message_history) == 10

    def test_prune_history_solo_mode(self, history_manager):
        """Test pruning in solo mode."""
        # Add more messages than max_history (30)
        for i in range(40):
            history_manager.add_message('player', f'Message {i}')

        pruned = history_manager.prune_history(is_party_mode=False)

        assert pruned is True
        assert len(history_manager.message_history) == 30  # Kept max_history
        assert history_manager.conversation_summary != ""  # Summary created

    def test_prune_history_party_mode(self, history_manager):
        """Test more aggressive pruning in party mode."""
        # Add 25 messages
        for i in range(25):
            history_manager.add_message('player', f'Message {i}')

        pruned = history_manager.prune_history(is_party_mode=True)

        assert pruned is True
        # Party mode uses max(12, max_history // 2) = max(12, 15) = 15
        assert len(history_manager.message_history) == 15

    def test_prune_history_preserves_recent(self, history_manager):
        """Test that pruning keeps the most recent messages."""
        for i in range(40):
            history_manager.add_message('player', f'Message {i}')

        history_manager.prune_history()

        # Should keep last 30 messages
        assert history_manager.message_history[0].content == 'Message 10'
        assert history_manager.message_history[-1].content == 'Message 39'

    def test_prune_history_accumulates_summary(self, history_manager):
        """Test that multiple prunes accumulate summary."""
        # First prune
        for i in range(40):
            history_manager.add_message('player', f'Message {i}')
        history_manager.prune_history()

        first_summary = history_manager.conversation_summary

        # Second prune
        for i in range(40, 50):
            history_manager.add_message('player', f'Message {i}')
        history_manager.prune_history()

        # Summary should have grown
        assert len(history_manager.conversation_summary) > len(first_summary)
        assert '--- Session Continued ---' in history_manager.conversation_summary


class TestCreateMessageSummary:
    """Test suite for message summarization."""

    def test_summarize_combat_events(self, history_manager):
        """Test summarization of combat messages."""
        history_manager.add_message('player', 'I attack the goblin')
        history_manager.add_message('gm', 'You defeated the goblin!')

        summary = history_manager._create_message_summary(history_manager.message_history)

        assert '⚔️ Combat:' in summary
        assert 'defeated the goblin' in summary.lower()

    def test_summarize_quest_events(self, history_manager):
        """Test summarization of quest messages."""
        history_manager.add_message('gm', 'You received a new quest: Find the lost sword')

        summary = history_manager._create_message_summary(history_manager.message_history)

        assert '📜 Quest:' in summary
        assert 'quest' in summary.lower()

    def test_summarize_travel_events(self, history_manager):
        """Test summarization of travel messages."""
        history_manager.add_message('gm', 'You arrive at the tavern')

        summary = history_manager._create_message_summary(history_manager.message_history)

        assert '🗺️ Travel:' in summary
        assert 'arrive' in summary.lower()

    def test_summarize_shop_events(self, history_manager):
        """Test summarization of shopping messages."""
        history_manager.add_message('player', 'I buy a healing potion for 50 gold')

        summary = history_manager._create_message_summary(history_manager.message_history)

        assert '💰 Trade:' in summary
        assert 'buy' in summary.lower()

    def test_summarize_discovery_events(self, history_manager):
        """Test summarization of discovery messages."""
        history_manager.add_message('gm', 'You find a treasure chest!')

        summary = history_manager._create_message_summary(history_manager.message_history)

        assert '🔍 Discovery:' in summary
        assert 'find' in summary.lower()

    def test_summarize_generic_messages(self, history_manager):
        """Test summarization when no key events found."""
        history_manager.add_message('player', 'Hello')
        history_manager.add_message('gm', 'Hi there')

        summary = history_manager._create_message_summary(history_manager.message_history)

        # Should create generic summary
        assert 'exchanges' in summary.lower()

    def test_summarize_truncates_long_content(self, history_manager):
        """Test that summaries truncate long message content."""
        long_message = 'A' * 200  # 200 character message
        history_manager.add_message('gm', f'You defeated the enemy! {long_message}')

        summary = history_manager._create_message_summary(history_manager.message_history)

        # Should be truncated to 100 chars (plus emoji prefix)
        for line in summary.split('\n'):
            if 'Combat:' in line:
                assert len(line) <= 120  # 100 content + emoji/prefix

    def test_summarize_empty_messages(self, history_manager):
        """Test summarization of empty message list."""
        summary = history_manager._create_message_summary([])
        assert summary == ""


class TestGetSummary:
    """Test suite for getting summary."""

    def test_get_summary_empty(self, history_manager):
        """Test getting summary when none exists."""
        summary = history_manager.get_summary()
        assert summary == ""

    def test_get_summary_with_content(self, history_manager):
        """Test getting summary with content."""
        # Manually set summary (normally created by pruning)
        history_manager.conversation_summary = "Test summary content"

        summary = history_manager.get_summary()
        assert summary == "Test summary content"

    def test_get_summary_respects_max_chars(self, history_manager):
        """Test that get_summary respects max_chars parameter."""
        # Create a long summary
        history_manager.conversation_summary = "A" * 1000

        summary = history_manager.get_summary(max_chars=100)

        assert len(summary) == 100
        # Should get LAST 100 chars
        assert summary == "A" * 100

    def test_get_summary_returns_last_chars(self, history_manager):
        """Test that get_summary returns the LAST N characters."""
        history_manager.conversation_summary = "START" + "X" * 500 + "END"

        summary = history_manager.get_summary(max_chars=10)

        # Should get last 10 chars (containing "END")
        assert "END" in summary
        assert "START" not in summary


class TestClear:
    """Test suite for clearing history."""

    def test_clear_removes_all_messages(self, history_manager):
        """Test that clear removes all messages."""
        history_manager.add_message('player', 'Test')
        history_manager.add_message('gm', 'Response')

        history_manager.clear()

        assert len(history_manager.message_history) == 0

    def test_clear_removes_summary(self, history_manager):
        """Test that clear removes summary."""
        history_manager.conversation_summary = "Test summary"

        history_manager.clear()

        assert history_manager.conversation_summary == ""


class TestLen:
    """Test suite for __len__ method."""

    def test_len_empty(self, history_manager):
        """Test length of empty history."""
        assert len(history_manager) == 0

    def test_len_with_messages(self, history_manager):
        """Test length with messages."""
        history_manager.add_message('player', 'Test 1')
        history_manager.add_message('gm', 'Test 2')

        assert len(history_manager) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
