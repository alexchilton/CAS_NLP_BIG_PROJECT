# Demo Script Comparison: Solo vs Party Mode

## Two Demo Scripts for Performance Testing

### 🧙 Solo Mode: `run_demo_solo.sh`
Tests single character (Zephyr the Wizard)

**Expected Performance:**
- Context: ~800 tokens
- Response time: 3-5 seconds
- Pruning: Every 20 messages

**Character:**
- Zephyr (Elf Wizard, Level 5)
- INT 18, DEX 16, CON 14
- Focuses on arcane exploration and spell casting

**Use this to:**
- Establish baseline performance
- Test if context window pruning works
- Verify the system is fundamentally healthy

### 🎭 Party Mode: `run_demo.sh`
Tests 5-character party

**Expected Performance:**
- Context: ~1,350 tokens (1.7x larger!)
- Response time: 8-15 seconds
- Pruning: Every 10 messages (more aggressive)

**Party:**
- Sir Gideon (Paladin, Lvl 5) - Tank/healer
- Lyra (Wizard, Lvl 3) - Arcane caster
- Garret (Rogue, Lvl 4) - Sneak attacks
- Thonk (Barbarian, Lvl 2) - Melee DPS
- Seraphina (Cleric, Lvl 1) - Healer/support

**Use this to:**
- Test party mode specific issues
- Stress test context window
- Verify adaptive pruning (party = 10 msgs, solo = 20 msgs)

## What to Watch For

### ✅ Healthy System Signs:
```
✅ Response received in 4.2s
📝 Response: 387 chars
📊 Turn 10 stats: Solo mode, class=Wizard
```

### ⚠️ Warning Signs:
```
⚠️  Response was slow (>30s) - possible context window issue
⏱️  Response took 18.7s
```

### 🔥 Critical Issues:
```
🚨 TIMEOUT DETECTED!
├─ Total time: 182.3s
└─ Attempting recovery...
```

## Logging Comparison

### Solo Mode Logs:
```bash
./run_demo_solo.sh

# Expected output:
🔹 Turn 1
   📊 Turn 1 stats: Solo mode, class=Wizard
   ⏳ Waiting for response (max 180s)...
   ✅ Response received in 3.8s
   📝 Response: 412 chars

🔹 Turn 10
   ⏸️  Extended pause (turn 10) - checking system health...
      ├─ Average response time: ~4.1s
      ├─ Checking for context window issues...
      └─ Pausing 12s for observation...
```

### Party Mode Logs:
```bash
./run_demo.sh

# Expected output:
🔹 Turn 1
   📊 Turn 1 stats: 5 chars, mode=exploration
   ⏳ Waiting for response (max 180s)...
   ✅ Response received in 9.2s
   📝 Response: 684 chars

🔹 Turn 10
   ⏸️  Extended pause (turn 10) - checking system health...
      ├─ Average response time: ~9.5s
      ├─ Checking for context window issues...
      └─ Pausing 12s for observation...

# Backend logs should show:
📝 Pruned 2 messages (party mode). History now: 10 messages
```

## Performance Comparison Table

| Metric | Solo Mode | Party Mode | Difference |
|--------|-----------|------------|------------|
| **Context Size** | ~800 tokens | ~1,350 tokens | +69% |
| **Response Time** | 3-5s | 8-15s | ~2-3x slower |
| **Message Pruning** | Every 20 msgs | Every 10 msgs | 2x more often |
| **Max History** | 20 messages | 10 messages | 50% of solo |
| **Timeout Risk** | Low | Medium | Party = riskier |

## Testing Strategy

### 1. Baseline Test (Solo First):
```bash
# Clear old sessions
./stop_gradio.sh
rm -f characters/*.json

# Run solo demo
./run_demo_solo.sh
```

**Watch for:**
- Consistent 3-5s responses ✅
- No timeouts after 20+ turns ✅
- Pruning logs at turn 20 ✅

**If this fails:** Basic system issue (not party-specific)

### 2. Stress Test (Party Mode):
```bash
# Clear sessions
./stop_gradio.sh
rm -f characters/*.json

# Run party demo
./run_demo.sh
```

**Watch for:**
- Slower but stable 8-15s responses ✅
- More frequent pruning (every 10 msgs) ✅
- "party mode" in prune logs ✅
- No timeouts after 30+ turns ✅

**If this fails:** Party-specific issue confirmed

### 3. Side-by-Side Comparison:
Run both demos back-to-back and compare:
- Average response time (should be ~2x slower for party)
- Pruning frequency (should be 2x more often for party)
- Stuck/timeout frequency (party may timeout more)

## Interpreting Results

### Scenario A: Solo works, Party times out
**Diagnosis:** Party mode context too large  
**Solution:** Already implemented adaptive pruning (10 msgs for party)  
**Next step:** Try reducing party to 3 characters

### Scenario B: Both timeout after 20 turns
**Diagnosis:** Basic context window issue (pruning not working)  
**Solution:** Check logs for "Pruned X messages"  
**Next step:** Restart Gradio, verify pruning is active

### Scenario C: Both work perfectly
**Diagnosis:** System is healthy! Old sessions were the problem  
**Solution:** None needed  
**Next step:** Enjoy your working game! 🎉

### Scenario D: Both timeout immediately
**Diagnosis:** Hardware/model issue (not context)  
**Solution:** Try smaller model (qwen2.5:3b)  
**Next step:** Run `python3 scripts/diagnose_performance.py`

## Quick Commands

```bash
# Solo demo
./run_demo_solo.sh

# Party demo
./run_demo.sh

# Stop any running Gradio
./stop_gradio.sh

# Clear all sessions
rm -f characters/*.json

# Check performance
python3 scripts/diagnose_performance.py

# Monitor pruning in real-time
tail -f logs/gradio.log | grep "Pruned"
```

## Expected Timeline

**Solo mode:** Should run indefinitely (100+ turns tested)  
**Party mode:** Should run indefinitely with adaptive pruning  

**If either times out after 20 turns:** Something is wrong, check logs!
