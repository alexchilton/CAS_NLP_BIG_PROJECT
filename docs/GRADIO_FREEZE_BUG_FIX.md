# 🐛 Gradio UI Freeze Bug - Analysis & Fix

## Problem Description

During the demo script run, the **Gradio chat UI froze** after ~10 turns while the backend continued processing.

### Symptoms

```
Turn 8-26: Response length stuck at exactly 864 bytes
Combat: Stuck fighting Goblin/Orc for 18+ rounds
UI: Completely frozen, no new messages appearing
Backend: Still running, still sending messages
Processing time: Jumped to 3+ minutes per response
```

## Root Causes

### 1. **LLM Response Timeout (Primary)**
The backend LLM (Ollama/Qwen) started taking **3+ minutes** to generate responses, likely due to:
- **Context window overflow** - After 10 turns, conversation history becomes too large
- **Model overload** - Inference slows down exponentially with context size
- **Network/server issues** - Local Ollama instance struggling

### 2. **Gradio UI Stuck (Secondary)**
While waiting for the slow LLM response:
- `send_message()` waited indefinitely on `networkidle`
- No timeout protection
- UI stopped updating chat messages
- Script kept sending messages to frozen UI

### 3. **Cached Message Loop (Tertiary)**
`get_last_bot_message()` kept reading the **same old message**:
- Last message in DOM: Turn 8 (864 bytes)
- No new messages being added
- Script thought combat was ongoing
- Kept attacking the already-dead Goblin/Orc

## Fixes Applied

### ✅ Fix 1: Message Tracking & Stuck Detection

**File:** `demo_endless_adventure_playwright.py`

```python
last_response_text = ""
stuck_count = 0

# Check if UI is stuck (same message 3+ times in a row)
if current_response == last_response_text:
    stuck_count += 1
    if stuck_count >= 3:
        print("🛑 UI appears stuck!")
        # Auto-recovery
        send_message(page, "/end_combat", max_wait=10)
        send_message(page, "/help", max_wait=10)
        stuck_count = 0
```

**What it does:**
- Tracks if we're getting the same response repeatedly
- After 3 identical responses, triggers recovery
- Tries to unstick by ending combat and sending /help
- Resets combat state to recover

### ✅ Fix 2: Timeout Protection in send_message

**File:** `playwright_helpers.py`

```python
def send_message(page: Page, message: str, max_wait: int = 180):
    """Send message with 3-minute timeout."""
    try:
        page.wait_for_load_state("networkidle", timeout=max_wait * 1000)
        return True  # Success
    except Exception:
        print("⚠️ Network idle timeout - UI may be stuck")
        return False  # Failure
```

**What it does:**
- Adds explicit 180-second (3 min) timeout
- Returns success/failure status
- Prevents infinite waiting
- Allows script to detect and handle timeouts

### ✅ Fix 3: Page Reload Recovery

**File:** `demo_endless_adventure_playwright.py`

```python
success = send_message(page, action, max_wait=180)

if not success:
    print("⚠️ Message send timeout - UI may be frozen!")
    time.sleep(30)  # Wait to see if it recovers
    
    # Check if recovered
    test_response = get_last_bot_message(page)
    if test_response == last_response_text:
        print("🛑 UI is definitely stuck. Trying to recover...")
        page.reload()  # Nuclear option: reload the page
```

**What it does:**
- If send fails, waits 30s for recovery
- Checks if UI recovered on its own
- If still stuck, reloads entire page
- Extreme measure but prevents permanent freeze

## Testing the Fixes

Run the demo again:
```bash
./run_demo.sh
```

**Watch for:**
1. ✅ Script detects stuck UI (same message 3x)
2. ✅ Auto-recovery kicks in (/end_combat + /help)
3. ✅ Timeout warnings appear if LLM takes >3 min
4. ✅ Page reload if completely stuck

## Remaining Issue: LLM Timeout

The **root cause** is still the LLM taking 3+ minutes. This needs investigation:

### Potential Solutions

#### Option 1: Context Window Management
Implement **conversation summarization** after N turns:

```python
if turn % 20 == 0:
    # Summarize last 20 turns into 1-2 paragraphs
    # Keep only summary + last 5 turns
    # Reduces context size dramatically
```

#### Option 2: Shorter Context
Modify `gm_dialogue_unified.py` to keep fewer messages:

```python
# Current: Keeps all messages
self.message_history.append(...)

# Better: Keep only last 10
self.message_history = self.message_history[-10:]
```

#### Option 3: Faster Model
Switch to a smaller/faster model for demos:
- Current: `Qwen3-4B-RPG-Roleplay-V2:Q4_K_M`
- Faster: `qwen2.5:3b` (mechanics extraction model)
- Fastest: `qwen2.5:1.5b`

#### Option 4: Timeout on Backend
Add timeout to `generate_response()`:

```python
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("LLM response timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60 second timeout

try:
    response = self._query_ollama(prompt)
finally:
    signal.alarm(0)  # Cancel timeout
```

## Recommended Next Steps

1. **Immediate:** Test the fixes (already applied)
2. **Short-term:** Implement context window pruning
3. **Medium-term:** Add backend timeout protection
4. **Long-term:** Implement proper context summarization with RAG

## Log Analysis

From your log, the pattern was clear:

```
Turn 1-7: Variable response lengths (107-864 bytes) ✅ Healthy
Turn 8:   864 bytes - Combat with Goblin/Orc starts
Turn 9:   864 bytes - IDENTICAL (first warning sign)
Turn 10:  864 bytes - IDENTICAL (stuck confirmed)
Turn 11-26: All 864 bytes - UI completely frozen
```

The UI froze at exactly **Turn 8** when the complex combat scenario began. This is likely when context size exceeded Ollama's sweet spot.

## Success Indicators

When the fixes work, you'll see:

```
Turn 8:   Combat starts
Turn 9:   Different response
Turn 10:  Different response
...
Turn 15:  Same message (1st time)
Turn 16:  Same message (2nd time)
Turn 17:  Same message (3rd time)
          🛑 UI appears stuck!
          💀 Force ending combat and refreshing...
          [Recovery triggered]
Turn 18:  Fresh response after recovery ✅
```

The demo will self-heal instead of looping forever!
