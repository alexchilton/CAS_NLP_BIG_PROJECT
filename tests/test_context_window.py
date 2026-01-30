"""
Test context window management - message pruning and summarization.
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.dialogue.conversation_history_manager import Message
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings


def test_message_pruning_basic(chromadb):
    """Test that message history is pruned when it exceeds MAX_MESSAGE_HISTORY."""
    gm = GameMaster(chromadb)
    
    # Add messages up to the limit
    for i in range(settings.MAX_MESSAGE_HISTORY // 2):
        gm.history_manager.add_message('player', f'Action {i}')
        gm.history_manager.add_message('gm', f'Response {i}')
    
    # Verify we're at the limit
    assert len(gm.history_manager.message_history) == settings.MAX_MESSAGE_HISTORY
    assert gm.history_manager.conversation_summary == ""  # No summary yet
    
    # Add more messages to trigger pruning
    gm.history_manager.add_message('player', 'I attack the goblin')
    gm.history_manager.add_message('gm', 'You defeat the goblin!')
    gm.history_manager.prune_history(is_party_mode=False)
    
    # Should be back at the limit
    assert len(gm.history_manager.message_history) == settings.MAX_MESSAGE_HISTORY
    # Should have created a summary
    assert gm.history_manager.conversation_summary != ""
    
    print(f"✅ Message history pruned successfully")
    print(f"   Messages: {len(gm.history_manager.message_history)}")
    print(f"   Summary length: {len(gm.history_manager.conversation_summary)} chars")


def test_message_summarization_combat(chromadb):
    """Test that combat messages are properly summarized."""
    gm = GameMaster(chromadb)
    
    # Add combat-related messages
    messages = [
        Message('player', 'I attack the goblin with my sword'),
        Message('gm', 'You hit! The goblin takes 8 damage and is defeated.'),
        Message('player', 'I loot the corpse'),
        Message('gm', 'You find 10 gold pieces'),
    ]
    
    summary = gm.history_manager._create_message_summary(messages)
    
    # Should detect combat
    assert 'Combat' in summary or 'defeat' in summary.lower()
    print(f"✅ Combat summary created:")
    print(f"   {summary}")


def test_message_summarization_travel(chromadb):
    """Test that travel messages are properly summarized."""
    gm = GameMaster(chromadb)
    
    messages = [
        Message('player', 'I travel to the nearby tavern'),
        Message('gm', 'You arrive at the Rusty Dragon Inn. The smell of ale fills the air.'),
        Message('player', 'I enter the tavern'),
        Message('gm', 'Inside, you see several patrons drinking.'),
    ]
    
    summary = gm.history_manager._create_message_summary(messages)
    
    # Should detect travel
    assert 'Travel' in summary or 'arrive' in summary.lower()
    print(f"✅ Travel summary created:")
    print(f"   {summary}")


def test_long_session_performance(chromadb):
    """Test that a long session maintains stable performance."""
    gm = GameMaster(chromadb)
    
    # Simulate 50 turns (100 messages)
    for turn in range(50):
        gm.history_manager.message_history.append(Message('player', f'Turn {turn}: I explore'))
        gm.history_manager.message_history.append(Message('gm', f'Turn {turn}: You find something interesting'))
        gm.history_manager.prune_history(is_party_mode=False)
    
    # Should never exceed the limit
    assert len(gm.history_manager.message_history) <= settings.MAX_MESSAGE_HISTORY
    # Should have accumulated summary
    assert gm.history_manager.conversation_summary != ""
    assert len(gm.history_manager.conversation_summary) > 100  # Should have substantial summary
    
    print(f"✅ Long session handled successfully")
    print(f"   After 50 turns:")
    print(f"   - Message history: {len(gm.history_manager.message_history)} messages")
    print(f"   - Summary: {len(gm.history_manager.conversation_summary)} chars")
    print(f"   - Last summary preview: {gm.history_manager.conversation_summary[-200:]}")


def test_summary_continuity(chromadb):
    """Test that summaries accumulate properly across multiple pruning cycles."""
    gm = GameMaster(chromadb)
    gm = GameMaster(db)
    
    # First batch - combat
    for i in range(settings.MAX_MESSAGE_HISTORY // 2 + 5):
        gm.history_manager.message_history.append(Message('player', 'I attack the goblin'))
        gm.history_manager.message_history.append(Message('gm', 'The goblin is defeated!'))
        gm.history_manager.prune_history(is_party_mode=False)
    
    first_summary = gm.history_manager.conversation_summary
    assert first_summary != ""
    
    # Second batch - travel
    for i in range(settings.MAX_MESSAGE_HISTORY // 2 + 5):
        gm.history_manager.message_history.append(Message('player', 'I travel to the town'))
        gm.history_manager.message_history.append(Message('gm', 'You arrive at the town'))
        gm.history_manager.prune_history(is_party_mode=False)
    
    second_summary = gm.history_manager.conversation_summary
    
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
