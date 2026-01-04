# Steal Mechanics Fix - Item Extraction

## Problem
Tests were failing because `_extract_item()` method couldn't extract item names from steal commands:
- Input: `"steal the healing potion"`
- Expected resource: `"healing potion"`
- Actual resource: `None` (then `"Healing Potion"` after partial fix)

## Root Cause
The `_extract_item()` method in `action_validator.py` only had patterns for item use actions:
- `use`, `drink`, `eat`, `equip`, `wear`, `wield`, etc.
- Missing: `steal`, `swipe`, `pilfer`, `pocket`, `snatch`, `lift`

## Solution
**File**: `dnd_rag_system/systems/action_validator.py`

### Change 1: Add steal keywords to item patterns (line 675)
```python
item_patterns = [
    r'\b(?:steal|swipe|pilfer|pocket|snatch|lift)\b',  # Added steal keywords
    r'\b(?:use|uses|using)\b',
    r'\b(?:drink|drinks|drinking)\b',
    # ... rest of patterns
]
```

### Change 2: Return lowercase item names (line 704)
```python
# Before:
item_name = ' '.join(words).strip('.,!?')
return item_name.title()  # Returns "Healing Potion"

# After:
item_name = ' '.join(words).strip('.,!?').lower()
return item_name  # Returns "healing potion"
```

**Reason for lowercase**: Inventory and shop systems use lowercase item names for consistency.

## Test Results
All 13 tests in `test_recent_fixes.py` now passing:
- ✅ `test_steal_keyword_detected` - Extracts "healing potion" from "steal the healing potion"
- ✅ `test_swipe_keyword_detected` - Alternative keywords work (swipe, pocket, pickpocket)
- ✅ All other tests remain passing (no regressions)

## Integration Points
1. **Action Detection** (line 175): `if any(keyword in lower_input for keyword in self.STEAL_KEYWORDS)`
2. **Item Extraction** (line 176): `item = self._extract_item(lower_input)`
3. **Steal Handler** (lines 435-461 in `gm_dialogue_unified.py`): Receives extracted item name

## Next Steps
Manual testing in Gradio UI to verify:
1. Steal command extracts item correctly
2. Item appears in inventory after success
3. Stealth checks work with NPCs
4. No goblin hallucinations
