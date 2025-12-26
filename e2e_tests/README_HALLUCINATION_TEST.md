# Hallucination Bug Selenium Test

## Purpose

This test reproduces and validates the fix for the "large bug" documented in TODO.md, where the Reality Check system failed to prevent entity hallucination.

## The Bug (from TODO.md)

**Scenario:**
- Load Elara Moonwhisper (wizard character)
- Starting location: Adventurer's Guild Hall (no enemies)
- User action: "I cast Magic Missile at the goblin"

**Expected Behavior:**
- Action should be rejected (no goblin exists)
- Response: "There's no goblin here" or similar

**Actual Buggy Behavior:**
- ❌ GM hallucinated goblin appearing and dying
- ❌ Dragon appeared from nowhere
- ❌ Combat started unexpectedly
- ❌ Thorin appeared (wasn't even loaded!)
- ❌ Complete cascade of hallucinations

## The Test: `test_hallucination_bug.py`

### What It Tests

The test validates that the Reality Check system correctly:
1. ✅ Detects invalid spell target (goblin doesn't exist)
2. ✅ Rejects the action with appropriate message
3. ✅ Prevents entity hallucination (no goblin, dragon, Thorin)
4. ✅ Prevents unexpected combat start
5. ✅ Maintains game state consistency

### How to Run

**Step 1: Start the Gradio App**
```bash
cd /Users/alexchilton/DataspellProjects/CAS_NLP_BIG_PROJECT
python web/app_gradio.py
```

Wait for: `Running on local URL: http://localhost:7860`

**Step 2: Run the Test (in another terminal)**
```bash
cd /Users/alexchilton/DataspellProjects/CAS_NLP_BIG_PROJECT
python e2e_tests/test_hallucination_bug.py
```

**Step 3: Watch the Browser**
- Chrome will open automatically
- You'll see the test interact with the UI
- Watch the chat messages appear
- Test results printed to terminal

### Success Criteria

**Test PASSES if:**
- ✅ Action is rejected (validation fails)
- ✅ Response mentions "no goblin" or similar rejection
- ✅ NO goblin death narrated
- ✅ NO dragon appears
- ✅ NO combat UI appears
- ✅ NO Thorin appears

**Test FAILS if:**
- ❌ Goblin death is narrated (hallucination!)
- ❌ Dragon appears (hallucination!)
- ❌ Combat starts unexpectedly
- ❌ Thorin appears (wrong character!)
- ❌ Action is accepted (validation failed!)

### Test Output

```
================================================================================
HALLUCINATION BUG TEST (from TODO.md)
================================================================================

This test reproduces the bug where:
1. Player attacks non-existent goblin
2. GM hallucinates goblin death
3. Dragon appears from nowhere
4. Combat starts unexpectedly
5. Other characters appear (Thorin)

🌐 Navigating to http://localhost:7860
⏳ Waiting for Gradio to load...
✅ Gradio loaded

📝 Loading character: Elara
✅ Character loaded

📜 Initial messages count: 1

🏛️ Starting location check:
   ✅ Started in Guild Hall

⚔️ Pre-action combat state:
   ✅ No combat active (expected)

================================================================================
🔴 TESTING THE BUG: Cast spell at non-existent goblin
================================================================================

📤 Player: I cast Magic Missile at the goblin

📩 GM Response:
   [Response text here...]

🔍 Checking for hallucination bugs:
   ✅ PASS: No goblin death hallucination
   ✅ PASS: No dragon hallucination
   ✅ PASS: No unexpected combat
   ✅ PASS: No Thorin hallucination
   ✅ PASS: Action was properly rejected

================================================================================
✅ TEST PASSED: No hallucinations detected!
================================================================================

The Reality Check system correctly:
  - Rejected invalid action (no goblin present)
  - Prevented entity hallucination
  - Prevented unexpected combat
```

## Technical Details

### What the Test Checks

1. **Page text analysis**: Searches for keywords indicating hallucinations
2. **Combat UI detection**: Looks for "Initiative Tracker", "Combat Round", etc.
3. **Entity appearance**: Checks for goblin, dragon, Thorin in page text
4. **Rejection validation**: Looks for phrases like "no goblin", "not present"

### Related Code

- **Action Validator**: `dnd_rag_system/systems/action_validator.py`
  - `analyze_intent()` - Detects spell cast
  - `validate_action()` - Checks target exists
  - `_validate_spell()` - Spell-specific validation
  
- **GM Dialogue**: `dnd_rag_system/systems/gm_dialogue_unified.py`
  - Uses validation results to guide LLM response
  - Sends deterministic rejection for invalid actions

## Related Fixes

This test validates the fixes made to `action_validator.py`:

1. **Target Detection** (Line 676-693)
   - Enhanced fuzzy matching to handle articles
   - "the dragon" now matches "Ancient Red Dragon"

2. **Combat State** (Line 285-287)
   - Fixed `combat_state` → `combat` attribute bug
   - Prevents crashes during validation

3. **Item Extraction** (Line 587-593)
   - Filters out non-items like "for battle"
   - Prevents false positive item detection

## Troubleshooting

**Test fails with "Could not find chat input":**
- Wait longer for Gradio to load (increase timeout)
- Check if app is running on port 7860

**Test fails with "chromedriver not found":**
```bash
# macOS
brew install chromedriver

# Or download from:
https://chromedriver.chromium.org/
```

**Browser closes too quickly:**
- Adjust sleep time at end of test
- Set `HEADLESS = False` to watch the test

**Hallucinations still occur (test fails):**
- This indicates validation logic needs more work
- Check terminal output for which check failed
- Review action_validator.py logic

## Next Steps

After running this test:

1. **If PASS**: Move hallucination bug to DONE.md ✅
2. **If FAIL**: Investigate remaining validation gaps
3. Document which specific checks failed
4. Review and enhance validation logic

## Files

- **Test**: `e2e_tests/test_hallucination_bug.py`
- **Validator**: `dnd_rag_system/systems/action_validator.py`
- **GM System**: `dnd_rag_system/systems/gm_dialogue_unified.py`
- **Documentation**: `TODO.md` (bug description), `DONE.md` (fixes)
