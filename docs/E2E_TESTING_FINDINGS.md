# E2E Testing Findings and Issues

## Summary

Attempted to create E2E tests for combat mechanics to verify:
- NPCs taking damage from player attacks
- NPCs dying when HP reaches 0
- Combat turn order correctness
- Debug scenario switching functionality
- Shop system integration

## Tests Created

### 1. `test_simple_goblin_combat.py` - Selenium E2E Test
**Status**: ❌ BLOCKED - Gradio UI compatibility issues
**Approach**: Browser automation with Selenium

**Issues Found**:
- Modern Gradio (v4+) doesn't use native HTML `<select>` elements
- Custom dropdown components not compatible with standard Selenium selectors
- Found 0 `<select>` elements on page (expected at least 2: character dropdown, scenario dropdown)
- Previous tests may be using older Gradio version or different approach

**Evidence**:
```
🔍 Searching for character dropdown...
   Found 0 <select> elements
📸 Screenshot saved to: /tmp/dropdown_not_found.png
```

**Files**:
- Test script: `e2e_tests/test_simple_goblin_combat.py`
- Error log: `/tmp/simple_combat_test.log`
- Screenshot: `/tmp/dropdown_not_found.png`

### 2. `test_combat_mechanics_direct.py` - Direct Integration Test
**Status**: ❌ BLOCKED - Ollama not running
**Approach**: Direct API calls to game systems (bypasses UI)

**Issues Found**:
- Ollama LLM service not running on `http://localhost:11434`
- Test hangs waiting for LLM response
- Player attack calculation **IS WORKING**: "HITS! Attack roll: 10 + 5 = 15 vs AC 12. 💥 6 slashing damage"

**Evidence from logs**:
```
✅ Validation: valid - Player attacks goblin
⚔️ Player Attack: COMBAT INSTRUCTION: Thorin Stormshield attacks goblin with longsword and HITS!
   Attack roll: 10 + 5 = 15 vs AC 12. 💥 6 slashing damage
```

**This proves**:
- ✅ Attack calculation system IS functional
- ✅ Damage calculation IS working (6 slashing damage)
- ✅ Target validation works correctly (goblin found)
- ❓ Unknown: Does damage actually apply to NPC HP?
- ❓ Unknown: Do NPCs die when HP reaches 0?

**Files**:
- Test script: `e2e_tests/test_combat_mechanics_direct.py`
- Partial log: `/tmp/combat_direct_test.log`

## Key Observations from Code Review

### Player Attack System (`docs/PLAYER_ATTACK_CALCULATION.md`)

**According to documentation**, the player attack system was implemented:
1. Pre-calculates attack rolls (d20 + mods)
2. Calculates damage (weapon dice + STR mod)
3. Passes instruction to GM: "COMBAT INSTRUCTION: Thorin HITS Goblin for 8 damage"
4. Mechanics extractor should parse this and apply damage

**Code locations**:
- `gm_dialogue_unified.py:783-895` - `_calculate_player_attack()` method
- `gm_dialogue_unified.py:496-514` - Combat action detection
- `mechanics_applicator.py:275-335` - NPC damage application

### NPC Damage Tracking (`docs/FINAL_FIXES.md` - Fix #9)

**According to documentation**, NPC damage tracking was implemented:
1. Mechanics extractor extracts damage targeting NPCs
2. Applicator calls `combat_manager.apply_damage_to_npc()`
3. Displays: "💥 Goblin takes 8 damage! (HP: 4/12)"
4. Removes dead NPCs: "💥 Goblin takes 8 damage and dies! ☠️"

**Expected behavior**:
```
You attack the goblin!

⚙️ MECHANICS:
💥 Goblin takes 8 slashing damage! (HP: 4/12)

🎯 Goblin's turn!
```

## Critical Questions (Still Unanswered)

1. **Do NPCs actually take damage?**
   - Attack calculation: ✅ Works
   - Damage extraction: ❓ Unknown (needs LLM response)
   - Damage application: ❓ Unknown (needs test completion)

2. **Do NPCs die?**
   - User report: "i have yet to see a dead goblin and wolf"
   - Documentation claims it's implemented
   - No test verification yet

3. **Are there still double NPC turn bugs?**
   - User example showed: "🎯 Goblin's turn!" twice in a row
   - Documentation claims this was fixed
   - No test verification yet

4. **Does HP math work correctly?**
   - User example: "HP: 18/28" → "takes 8 damage" → "HP: 17/28" ❌ (should be 10)
   - This suggests phantom damage or caching issues
   - Needs investigation

## User's Original Bugs (From Previous Session)

From user's combat example:
```
⚠️ You see: Wolf!
> attack the wolf
As the Goblin raises...  ← Bug #1: Wrong NPC (Wolf → Goblin)

🎯 Goblin's turn!
💥 3 damage
🎯 Goblin's turn!  ← Bug #2: Double NPC turn
💥 8 damage

HP: 18/28
💥 You take 8 slashing damage
HP: 17/28  ← Bug #3: Math error (18-8=17 instead of 10)
```

**Status of fixes**:
- Bug #1 (Wrong NPC): ❓ Unknown - needs test
- Bug #2 (Double turns): ❓ Unknown - needs test
- Bug #3 (HP math): ❓ Unknown - needs test

## Testing Blockers

### Immediate Blockers

1. **Ollama Not Running**
   - All tests require LLM responses
   - Need to start: `ollama serve`
   - Need to verify model is pulled: `ollama list | grep Qwen`

2. **Gradio UI Changes**
   - Modern Gradio uses custom components
   - Standard Selenium selectors don't work
   - Need to update selectors or use alternative approach

### Solutions for Blockers

**Option A: Fix Ollama (Fastest)**
```bash
# Start Ollama service
ollama serve

# In another terminal, run direct test
python3 e2e_tests/test_combat_mechanics_direct.py
```

**Option B: Fix Selenium Selectors**
- Research Gradio 4+ dropdown selectors
- Use `data-testid` or ARIA attributes
- May need to inspect live Gradio DOM

**Option C: Manual Testing** (User can do this now)
1. Start Ollama: `ollama serve`
2. Start Gradio: `python3 web/app_gradio.py`
3. Load "Goblin Fight" debug scenario
4. Attack goblin 10+ times
5. Watch for:
   - "💥 Goblin takes X damage! (HP: Y/Z)"
   - HP decreasing each attack
   - "💥 Goblin... dies!" message
   - Goblin removed from combat

## Docker & HuggingFace Compatibility

> User concern: "it would also be nice to know that this is still also working with docker and even hugging face - i suspect its not"

### Potential Issues

**Docker:**
- Ollama runs as separate service
- Need `docker-compose.yml` with Ollama container
- Volume mounts for ChromaDB persistence
- Network configuration for Ollama API

**HuggingFace Spaces:**
- ❌ **Ollama won't work** - HF Spaces can't run Ollama server
- ❌ **Local model dependencies** - Qwen model requires download
- ✅ **ChromaDB should work** - In-memory or persistent volume
- ✅ **Gradio UI should work** - HF Spaces designed for Gradio

### Required Changes for HuggingFace

1. **Replace Ollama with HuggingFace Inference API**
   ```python
   # Instead of Ollama local:
   from transformers import pipeline
   generator = pipeline("text-generation", model="Qwen/Qwen-4B")
   ```

2. **Or use HuggingFace Inference Endpoints**
   ```python
   import requests
   API_URL = "https://api-inference.huggingface.co/models/..."
   headers = {"Authorization": f"Bearer {HF_TOKEN}"}
   ```

3. **Environment Detection**
   ```python
   if os.getenv("SPACE_ID") or os.getenv("HF_SPACE"):
       # Use HuggingFace API
   else:
       # Use local Ollama
   ```

**Files to modify**:
- `dnd_rag_system/systems/gm_dialogue_unified.py` - LLM client
- `dnd_rag_system/config/settings.py` - Add HF config
- `requirements.txt` - Add `transformers` if using local inference
- `README.md` - Document HF deployment

### Docker Configuration Example

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  dnd_app:
    build: .
    ports:
      - "7860:7860"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - ./chromadb:/app/chromadb
    depends_on:
      - ollama

volumes:
  ollama_data:
```

## Next Steps

### Immediate (To unblock testing)

1. ✅ **Start Ollama**
   ```bash
   ollama serve
   ```

2. ✅ **Run direct test**
   ```bash
   python3 e2e_tests/test_combat_mechanics_direct.py
   ```

3. ✅ **Analyze results**
   - Check if NPCs take damage
   - Check if NPCs die
   - Check for bugs mentioned by user

### Short-term (Fix E2E tests)

1. **Fix Selenium selectors** for Gradio 4+
2. **Create party vs 2 monsters test** (after simple test passes)
3. **Test scenario switching** (combat → shop)
4. **Test shop system** (`/buy`, `/sell`)

### Medium-term (Deployment)

1. **Docker support**
   - Create `docker-compose.yml`
   - Test Ollama in container
   - Document deployment

2. **HuggingFace Spaces support**
   - Add HF Inference API integration
   - Environment detection
   - Update documentation

### Long-term (Robustness)

1. **Comprehensive test suite**
   - Unit tests for combat calculations
   - Integration tests for damage application
   - E2E tests for full combat scenarios

2. **CI/CD integration**
   - Automated testing on commits
   - Docker build validation
   - HF Space preview deployments

## Files Created This Session

1. `e2e_tests/test_simple_goblin_combat.py` - Selenium E2E test (blocked)
2. `e2e_tests/test_combat_mechanics_direct.py` - Direct integration test (needs Ollama)
3. `docs/E2E_TESTING_FINDINGS.md` - This document

## Log Files

- `/tmp/simple_combat_test.log` - Selenium test output
- `/tmp/combat_direct_test.log` - Direct test output (partial)
- `/tmp/dropdown_not_found.png` - Selenium screenshot

## Recommendations

### For User (Manual Testing Now)

1. Start Ollama: `ollama serve` (in separate terminal)
2. Start Gradio: `python3 web/app_gradio.py`
3. Load "Goblin Fight" scenario from debug dropdown
4. Attack goblin repeatedly and observe:
   - Does "💥 Goblin takes X damage! (HP: Y/Z)" appear?
   - Does HP decrease each attack?
   - Does goblin die after enough attacks?
   - Any double NPC turns?
   - HP math correct?

### For Automated Testing

1. **Fix Ollama first** (blocks all tests)
2. **Run direct test** to verify core mechanics
3. **Fix Selenium** if E2E UI testing is critical
4. **Add Docker/HF support** for deployment

### For Deployment

1. **Docker**: Should work with `docker-compose` and Ollama container
2. **HuggingFace**: Requires code changes to replace Ollama with HF API
3. **Document**: Both deployment methods in README

## Conclusion

**What We Know**:
- ✅ Attack calculation system works
- ✅ Damage calculation works
- ✅ Debug scenario system implemented
- ✅ Documentation claims NPC damage tracking is implemented

**What We Don't Know** (blocked by Ollama):
- ❓ Do NPCs actually take damage from player attacks?
- ❓ Do NPCs die when HP reaches 0?
- ❓ Are the reported bugs (wrong NPC, double turns, HP math) fixed?

**Immediate Action Required**:
1. Start Ollama service
2. Run direct integration test
3. Verify NPC damage and death mechanics

**User's Concern Valid**: Without running tests, we cannot confirm if "goblins and wolves" actually die in combat.
