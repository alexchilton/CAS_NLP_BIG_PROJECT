# Context Window FAQ

## Q: What is the maximum context size?

**Model limit:** 32,768 tokens (Qwen 3 4B)

**Practical limit:** ~1,000 tokens for acceptable performance on CPU

## Q: Is it linear slowdown (4x context = 4x slower)?

**No! It's exponential (quadratic to be precise).**

| Context | Time | Slowdown |
|---------|------|----------|
| 500 tokens | 2s | 1x (baseline) |
| 1,000 tokens | 5s | 2.5x |
| 2,000 tokens | 15s | 7.5x |
| 4,000 tokens | 60s | 30x |
| 8,000 tokens | 240s | 120x |

**Why?** Transformer attention is O(n²) - every token attends to every other token.

## Q: My demo timed out after 100 seconds. Why?

**Your context was too large BEFORE pruning was implemented.**

Without pruning:
- Turn 20: ~40 messages = ~2,500 tokens = 30s response
- Turn 40: ~80 messages = ~4,500 tokens = 180s response ⚠️ **TIMEOUT!**

With pruning (now):
- Turn 20: ~20 messages = ~700 tokens = 4s response ✅
- Turn 100: ~20 messages = ~700 tokens = 4s response ✅

## Q: How large is the context now?

With your current pruning settings:

```
MAX_MESSAGE_HISTORY = 20
RECENT_MESSAGES_FOR_PROMPT = 8
```

Typical context breakdown:
- System prompt: ~100 tokens
- Game state: ~125 tokens  
- Recent 8 messages: ~200 tokens
- Instructions: ~100 tokens
- **TOTAL: ~525-850 tokens** ✅

This is **only 2.5% of the model's capacity** and should be fast!

## Q: Will pruning solve my timeout issues?

**Yes, but...**

1. **Pruning prevents FUTURE timeouts** by keeping context small
2. **Old sessions might still have huge context** - restart Gradio to clear
3. **Model loading delays** - first request takes 5-10s longer

## Q: How do I know if it's working?

Check logs for pruning messages:

```bash
tail -f logs/gradio.log | grep "Pruned"

# You should see:
# 📝 Pruned 10 messages. History now: 20 messages
```

## Q: What if it's still slow after pruning?

Run diagnostic:

```bash
python3 scripts/diagnose_performance.py
```

This will test:
1. Ollama is running
2. Inference speed (should be < 5s)
3. Context settings
4. GameMaster initialization

If inference test takes > 15s, your hardware is too slow.

## Q: Can I make it faster?

**Option 1: Use smaller model** (fastest)
```bash
ollama pull qwen2.5:3b
```
Then update `settings.py`:
```python
OLLAMA_MODEL_NAME = "qwen2.5:3b"
```

**Option 2: Aggressive pruning**
```python
MAX_MESSAGE_HISTORY = 12
RECENT_MESSAGES_FOR_PROMPT = 6
```

**Option 3: GPU acceleration** (requires CUDA/ROCm)
- RTX 3090: 10-30x faster
- Apple M-series: 5x faster with Metal

## Q: Will I lose game history with pruning?

**No!** Three-tier memory preserves everything:

1. **Short-term** (`message_history`): Last 20 messages for immediate context
2. **Medium-term** (`conversation_summary`): Compressed summaries of old messages
3. **Long-term** (`session.notes`): Key events permanently recorded

Example summary:
```
⚔️ Combat: Defeated 2 goblins and 1 orc
🗺️ Travel: Arrived at Riverside Tavern
💰 Trade: Bought 3 healing potions for 150 gold
```

## Q: How do I restart with clean slate?

```bash
# Stop Gradio
./stop_gradio.sh

# Clear old character sessions (optional)
rm -rf characters/*.json

# Restart
./start_gradio.sh
```

## Q: Can I check context size in real-time?

Add to your code:

```python
print(f"Context size: ~{len(gm.message_history) * 40} tokens")
```

Or check the debug logs when `DEBUG_MODE = True`.

## Q: What's the sweet spot for settings?

**For 4B model on CPU:**
```python
MAX_MESSAGE_HISTORY = 20
RECENT_MESSAGES_FOR_PROMPT = 8
OLLAMA_TIMEOUT = 120
```

**For 3B model (faster):**
```python
MAX_MESSAGE_HISTORY = 30
RECENT_MESSAGES_FOR_PROMPT = 12  
OLLAMA_TIMEOUT = 60
```

**For 7B+ model (slower):**
```python
MAX_MESSAGE_HISTORY = 12
RECENT_MESSAGES_FOR_PROMPT = 6
OLLAMA_TIMEOUT = 180
```

## Q: Is 32K context really usable?

**Technically yes, practically no.**

- 32K tokens would take **~20-30 minutes per response** on CPU
- Even on high-end GPU: **~30-60 seconds**
- Only useful for batch processing, not interactive games

Keep it under 1K tokens for interactive use!
