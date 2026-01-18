#!/usr/bin/env python3
"""
Quick diagnostic to check why your demo is timing out.
Run this to see if it's context size, Ollama issues, or something else.
"""

import subprocess
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

print("🔍 D&D RAG System - Performance Diagnostic\n")
print("="*70)

# 1. Check Ollama is running
print("\n1️⃣  Checking Ollama...")
try:
    result = subprocess.run(['ollama', 'ps'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print("   ✅ Ollama is running")
        if result.stdout.strip():
            print(f"   📊 Loaded models:\n{result.stdout}")
        else:
            print("   ⚠️  No models loaded in memory!")
            print("      Model will be loaded on first request (adds 5-10s delay)")
    else:
        print(f"   ❌ Ollama error: {result.stderr}")
except FileNotFoundError:
    print("   ❌ Ollama not found! Install from https://ollama.ai")
    sys.exit(1)
except subprocess.TimeoutExpired:
    print("   ❌ Ollama not responding")
    sys.exit(1)

# 2. Test inference speed
print("\n2️⃣  Testing inference speed...")
model = "hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M"
test_prompt = "You are a DM. The player attacks. Respond in 1 sentence."

print(f"   Testing with: {model}")
print(f"   Prompt: '{test_prompt}'")

start = time.time()
try:
    result = subprocess.run(
        ['ollama', 'run', model, test_prompt],
        capture_output=True,
        text=True,
        timeout=30
    )
    elapsed = time.time() - start
    
    if result.returncode == 0:
        print(f"   ✅ Response in {elapsed:.1f}s")
        if elapsed < 5:
            print("      🚀 Fast! System is healthy.")
        elif elapsed < 15:
            print("      ⚠️  Acceptable but could be faster.")
        else:
            print("      🔥 Slow! This will cause timeouts in long sessions.")
        print(f"   📝 Response: {result.stdout[:100]}...")
    else:
        print(f"   ❌ Error: {result.stderr}")
except subprocess.TimeoutExpired:
    print(f"   ❌ TIMEOUT after 30s! Your system is too slow.")
    print("      Possible causes:")
    print("      - CPU too slow")
    print("      - RAM/swap thrashing")
    print("      - Model too large for available RAM")

# 3. Check context window settings
print("\n3️⃣  Checking context window settings...")
from dnd_rag_system.config import settings

print(f"   MAX_MESSAGE_HISTORY: {settings.MAX_MESSAGE_HISTORY}")
print(f"   RECENT_MESSAGES_FOR_PROMPT: {settings.RECENT_MESSAGES_FOR_PROMPT}")
print(f"   OLLAMA_TIMEOUT: {settings.OLLAMA_TIMEOUT}s")

if settings.MAX_MESSAGE_HISTORY <= 20:
    print("   ✅ Pruning is configured correctly")
else:
    print(f"   ⚠️  MAX_MESSAGE_HISTORY is {settings.MAX_MESSAGE_HISTORY} (high!)")
    print("      Consider lowering to 15-20")

# 4. Test GameMaster initialization
print("\n4️⃣  Testing GameMaster initialization...")
try:
    from dnd_rag_system.core.chroma_manager import ChromaDBManager
    from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
    
    db = ChromaDBManager()
    gm = GameMaster(db)
    
    print("   ✅ GameMaster initialized")
    print(f"   Message history: {len(gm.message_history)}")
    print(f"   Has _prune_message_history: {hasattr(gm, '_prune_message_history')}")
    print(f"   Has conversation_summary: {hasattr(gm, 'conversation_summary')}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

# 5. Estimate typical context size
print("\n5️⃣  Estimating context size...")
estimated_tokens = (
    100 +  # System prompt
    50 +   # Location/time
    75 +   # Party status
    200 +  # Recent 8 messages
    100    # Instructions
)
print(f"   Estimated: ~{estimated_tokens} tokens per request")
if estimated_tokens < 1000:
    print("   ✅ Context is small - should be fast!")
else:
    print(f"   ⚠️  Context is {estimated_tokens} tokens - may be slow")

# 6. Final verdict
print("\n" + "="*70)
print("📊 DIAGNOSTIC SUMMARY")
print("="*70)
print()
print("If inference test was < 5s: ✅ System is healthy")
print("If inference test was 5-15s: ⚠️  Borderline - may timeout after 20+ turns")
print("If inference test was > 15s: 🔥 Will definitely timeout - need faster hardware")
print()
print("Next steps:")
print("  1. If Ollama test was slow, try a smaller model:")
print("     ollama pull qwen2.5:3b")
print("     (Then update OLLAMA_MODEL_NAME in settings.py)")
print()
print("  2. Restart Gradio to clear old sessions:")
print("     ./stop_gradio.sh && ./start_gradio.sh")
print()
print("  3. Run demo again and watch for 'Pruned' messages in logs")
print()

print("="*70)
