"""
Test context window management - message pruning and summarization.
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.gm_dialogue_unified import GameMaster, Message
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings


def test_message_pruning_basic():
    """Test that message history is pruned when it exceeds MAX_MESSAGE_HISTORY."""
    db = ChromaDBManager()
    gm = GameMaster(db)
    
    # Add messages up to the limit
    for i in range(settings.MAX_MESSAGE_HISTORY // 2):
        gm.message_history.append(Message('player', f'Action {i}'))
        gm.message_history.append(Message('gm', f'Response {i}'))
    
    # Verify we're at the limit
    assert len(gm.message_history) == settings.MAX_MESSAGE_HISTORY
    assert gm.conversation_summary == ""  # No summary yet
    
    # Add more messages to trigger pruning
    gm.message_history.append(Message('player', 'I attack the goblin'))
    gm.message_history.append(Message('gm', 'You defeat the goblin!'))
    gm._prune_message_history()
    
    # Should be back at the limit
    assert len(gm.message_history) == settings.MAX_MESSAGE_HISTORY
    # Should have created a summary
    assert gm.conversation_summary != ""
    
    print(f"✅ Message history pruned successfully")
    print(f"   Messages: {len(gm.message_history)}")
    print(f"   Summary length: {len(gm.conversation_summary)} chars")


def test_message_summarization_combat():
    """Test that combat messages are properly summarized."""
    db = ChromaDBManager()
    gm = GameMaster(db)
    
    # Add combat-related messages
    messages = [
        Message('player', 'I attack the goblin with my sword'),
        Message('gm', 'You hit! The goblin takes 8 damage and is defeated.'),
        Message('player', 'I loot the corpse'),
        Message('gm', 'You find 10 gold pieces'),
    ]
    
    summary = gm._create_message_summary(messages)
    
    # Should detect combat
    assert 'Combat' in summary or 'defeat' in summary.lower()
    print(f"✅ Combat summary created:")
    print(f"   {summary}")


def test_message_summarization_travel():
    """Test that travel messages are properly summarized."""
    db = ChromaDBManager()
    gm = GameMaster(db)
    
    messages = [
        Message('player', 'I travel to the nearby tavern'),
        Message('gm', 'You arrive at the Rusty Dragon Inn. The smell of ale fills the air.'),
        Message('player', 'I enter the tavern'),
        Message('gm', 'Inside, you see several patrons drinking.'),
    ]
    
    summary = gm._create_message_summary(messages)
    
    # Should detect travel
    assert 'Travel' in summary or 'arrive' in summary.lower()
    print(f"✅ Travel summary created:")
    print(f"   {summary}")


def test_long_session_performance():
    """Test that a long session maintains stable performance."""
    db = ChromaDBManager()
    gm = GameMaster(db)
    
    # Simulate 50 turns (100 messages)
    for turn in range(50):
        gm.message_history.append(Message('player', f'Turn {turn}: I explore'))
        gm.message_history.append(Message('gm', f'Turn {turn}: You find something interesting'))
        gm._prune_message_history()
    
    # Should never exceed the limit
    assert len(gm.message_history) <= settings.MAX_MESSAGE_HISTORY
    # Should have accumulated summary
    assert gm.conversation_summary != ""
    assert len(gm.conversation_summary) > 100  # Should have substantial summary
    
    print(f"✅ Long session handled successfully")
    print(f"   After 50 turns:")
    print(f"   - Message history: {len(gm.message_history)} messages")
    print(f"   - Summary: {len(gm.conversation_summary)} chars")
    print(f"   - Last summary preview: {gm.conversation_summary[-200:]}")


def test_summary_continuity():
    """Test that summaries accumulate properly across multiple pruning cycles."""
    db = ChromaDBManager()
    gm = GameMaster(db)
    
    # First batch - combat
    for i in range(settings.MAX_MESSAGE_HISTORY // 2 + 5):
        gm.message_history.append(Message('player', 'I attack the goblin'))
        gm.message_history.append(Message('gm', 'The goblin is defeated!'))
        gm._prune_message_history()
    
    first_summary = gm.conversation_summary
    assert first_summary != ""
    
    # Second batch - travel
    for i in range(settings.MAX_MESSAGE_HISTORY // 2 + 5):
        gm.message_history.append(Message('player', 'I travel to the town'))
        gm.message_history.append(Message('gm', 'You arrive at the town'))
        gm._prune_message_history()
    
    second_summary = gm.conversation_summary
    
    # Summary should have grown
    assert len(second_summary) > len(first_summary)
    # Should contain "Session Continued" marker
    assert "Session Continued" in second_summary
    
    print(f"✅ Summary continuity maintained")
    print(f"   First summary: {len(first_summary)} chars")
    print(f"   Second summary: {len(second_summary)} chars")


if __name__ == "__main__":
    print("Testing Context Window Management\n" + "="*50)
    
    test_message_pruning_basic()
    print()
    test_message_summarization_combat()
    print()
    test_message_summarization_travel()
    print()
    test_long_session_performance()
    print()
    test_summary_continuity()
    
    print("\n" + "="*50)
    print("🎉 All context window tests passed!")
