#!/usr/bin/env python3
"""
Test the backend API directly without GUI.
Tests if GameMaster, context pruning, and response cleaning work.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
from dnd_rag_system.systems.character_creator import Character
import time

def test_backend():
    print("=" * 60)
    print("BACKEND API TEST (No GUI)")
    print("=" * 60)
    
    # Initialize
    print("\n1️⃣  Initializing GameMaster...")
    db = ChromaDBManager()
    gm = GameMaster(db)
    print("   ✅ GameMaster initialized")
    
    # Load a character (simplified - just use the data for game session)
    print("\n2️⃣  Loading character...")
    char_dir = Path(__file__).parent / "characters"
    char_files = list(char_dir.glob("*.json"))
    
    if not char_files:
        print("   ❌ No characters found! Create one first.")
        return
    
    char_file = char_files[0]
    import json
    with open(char_file, 'r') as f:
        char_data = json.load(f)
    
    # Create simplified Character object
    char = Character(
        name=char_data['name'],
        race=char_data['race'],
        character_class=char_data.get('character_class', 'Fighter'),
        level=char_data['level']
    )
    # Manually set other attributes
    char.hp = char_data.get('hit_points', 10)
    char.max_hp = char.hp
    
    print(f"   ✅ Loaded: {char.name} (Level {char.level} {char.character_class})")
    
    # Start game
    print("\n3️⃣  Starting game session...")
    from dnd_rag_system.systems.game_state import CharacterState
    # Create character state from char data
    char_state = CharacterState(char, notes=[])
    gm.session.character_state = char_state
    gm.session.current_location = "Forest Path"
    gm.session.scene_description = "A winding forest path stretches before you."
    
    print(f"   ✅ Location: {gm.session.current_location}")
    print(f"   ✅ Message history: {len(gm.message_history)} messages")
    
    # Test adventure loop
    print("\n4️⃣  Running 10-turn adventure...")
    actions = [
        "I look around carefully",
        "I explore the area",
        "I search for treasure",
        "I move forward cautiously",
        "I check for danger",
        "/start_combat Goblin",
        "I attack the goblin!",
        "I strike again!",
        "/end_combat",
        "I rest briefly",
    ]
    
    for turn, action in enumerate(actions, 1):
        print(f"\n{'='*60}")
        print(f"Turn {turn}: {action}")
        print(f"{'='*60}")
        
        # Send action
        start = time.time()
        try:
            response = gm.generate_response(action, use_rag=True)
            elapsed = time.time() - start
            
            # Check response quality
            response_len = len(response)
            has_leak = any(x in response for x in ['{{user}}', 'Take the role', 'Scenario:'])
            
            print(f"✅ Response received in {elapsed:.1f}s")
            print(f"   Length: {response_len} chars")
            print(f"   History size: {len(gm.message_history)} messages")
            print(f"   Prompt leak: {'❌ YES!' if has_leak else '✅ No'}")
            
            if has_leak:
                print(f"   ⚠️  LEAKED TEXT DETECTED:")
                print(f"   {response[:200]}...")
            else:
                print(f"   Preview: {response[:100]}...")
            
            # Check for slowdown
            if elapsed > 10:
                print(f"   ⚠️  SLOW RESPONSE! ({elapsed:.1f}s)")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Final stats
    print("\n" + "=" * 60)
    print("FINAL STATS")
    print("=" * 60)
    print(f"Total messages in history: {len(gm.message_history)}")
    print(f"Has summary: {bool(gm.conversation_summary)}")
    if gm.conversation_summary:
        print(f"Summary length: {len(gm.conversation_summary)} chars")
        print(f"Summary preview: {gm.conversation_summary[:200]}...")
    print(f"Session notes: {len(gm.session.notes)}")
    print(f"Current location: {gm.session.current_location}")
    print(f"In combat: {gm.combat_manager.is_in_combat()}")
    
    print("\n✅ Backend API test complete!")

if __name__ == "__main__":
    test_backend()
