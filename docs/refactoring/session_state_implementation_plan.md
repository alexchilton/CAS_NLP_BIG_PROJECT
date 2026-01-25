# SessionState Implementation Plan

## Status: 🟡 IN PROGRESS (Design Complete, Implementation Pending)

Branch: `feature/remove-global-state`

## Completed ✅

1. **Analysis** - Identified all global variable usage (20+ functions affected)
2. **Design** - Created `SessionState` class with all required fields
3. **Documentation** - Wrote comprehensive analysis and risk assessment

## Next Steps (Implementation)

### Phase 1: Refactor Core Wrapper Functions (2-3 hours)

**Functions to Update (in order):**

1. `get_current_sheet(session: SessionState)` ← reads 4 globals
2. `load_character_wrapper(char_choice, session)` ← writes 3 globals
3. `load_character_with_debug_wrapper(char_choice, scenario, session)` ← writes 3 globals
4. `chat_wrapper(message, history, session)` ← reads 4 globals
5. `clear_history_wrapper(session)` ← writes 1 global
6. `load_party_mode_wrapper(session)` ← writes 4 globals
7. `add_to_party_wrapper(choices, session)` ← writes 2 globals
8. `remove_from_party_wrapper(name, session)` ← writes 2 globals

**Pattern for Each Function:**

```python
# BEFORE
def function_wrapper(arg1, arg2):
    global var1, var2
    # ... logic ...
    var1 = new_value
    return result

# AFTER
def function_wrapper(arg1, arg2, session: SessionState):
    # ... logic ...
    session.var1 = new_value
    return result, session  # CRITICAL: Return session!
```

**Testing After Each Function:**
- Add type hints to catch missing parameters
- Test manually with single user
- Verify state flows correctly

### Phase 2: Update Gradio Event Handlers (1-2 hours)

**Event Handlers to Update:**

1. Load character button (play tab)
2. Load party button (play tab)
3. Delete character button (play tab)
4. Chat submit button + Enter key (play tab)
5. Combat control buttons (next turn, end combat) (play tab)
6. Clear history button (play tab)
7. Quick action buttons (attack, cast, use item, help) (play tab)
8. Create character button (create tab)
9. Add/remove party buttons (party tab)

**Pattern for Event Handlers:**

```python
# BEFORE
component.click(
    wrapper_function,
    inputs=[arg1, arg2],
    outputs=[output1, output2]
)

# AFTER
component.click(
    wrapper_function,
    inputs=[arg1, arg2, session_state],  # Add session
    outputs=[output1, output2, session_state]  # Return session
)
```

**Special Cases:**
- `.then()` chains need session passed through
- Lambda functions need session parameter
- Multiple outputs need session appended

### Phase 3: Create gr.State Component (30 min)

**In app_gradio.py, after demo creation:**

```python
with demo:
    # Create session state component (ONE per user session)
    session_state = gr.State(create_session_state())

    # ... rest of UI setup ...
```

**Key Points:**
- Only ONE `gr.State` component created
- Passed to ALL event handlers
- Gradio automatically manages per-session instances

### Phase 4: Remove Global Variables (15 min)

**Delete from app_gradio.py (lines 75-80):**
```python
# DELETE THESE:
current_character = None
conversation_history = []
party = PartyState(...)
party_characters = {}
gameplay_mode = "character"
```

**Delete global gm (line 69):**
```python
# DELETE THIS:
gm = GameMaster(db)
```

**Search for remaining global statements:**
```bash
grep "global " web/app_gradio.py
# Should return NO results
```

### Phase 5: Integration Testing (1 hour)

**Test Scenarios:**

1. **Single User Flow:**
   - Load character ✓
   - Chat with GM ✓
   - Start combat ✓
   - Use spells/items ✓
   - Clear history ✓

2. **Party Mode Flow:**
   - Create party ✓
   - Add characters ✓
   - Start combat ✓
   - Remove characters ✓

3. **Multi-User Test (CRITICAL):**
   - Open app in 2 browser windows (different sessions)
   - Window 1: Load Character A
   - Window 2: Load Character B
   - Window 1: Chat "Hello"
   - Window 2: Chat "Goodbye"
   - Verify: Each window shows only its own character/chat
   - Verify: No state leakage between sessions

4. **Edge Cases:**
   - Reload page (state should reset)
   - Switch between character/party mode
   - Rapid clicking (race conditions)

**Automated Test (Create Later):**
```python
# tests/test_session_state.py
def test_session_isolation():
    """Test that two SessionState instances are independent."""
    session1 = create_session_state()
    session2 = create_session_state()

    session1.gameplay_mode = "party"
    assert session2.gameplay_mode == "character"

    session1.conversation_history.append({"role": "user", "content": "test"})
    assert len(session2.conversation_history) == 0
```

## Success Criteria

- [ ] No `global` statements in app_gradio.py
- [ ] All event handlers pass/return `session_state`
- [ ] App works with single user (smoke test)
- [ ] App works with multiple users simultaneously (isolation test)
- [ ] No race conditions or state leakage
- [ ] All existing tests still pass

## Rollback Plan

If issues arise:
1. Discard changes: `git checkout main`
2. Delete feature branch: `git branch -D feature/remove-global-state`
3. Start over with smaller scope (e.g., only character mode first)

## Estimated Time

- Phase 1: 2-3 hours (function refactoring)
- Phase 2: 1-2 hours (event handler updates)
- Phase 3: 30 minutes (gr.State setup)
- Phase 4: 15 minutes (cleanup)
- Phase 5: 1 hour (testing)

**Total: 5-7 hours of focused work**

## Current Status

**Completed:**
- ✅ Analysis (30 min)
- ✅ Design (30 min)
- ✅ Documentation (30 min)

**Remaining:**
- ⏳ Implementation (5-7 hours)

**Branch:** `feature/remove-global-state`
**Ready to merge:** NO (implementation not started)
**Blocking issues:** None
**Next action:** Begin Phase 1 (refactor wrapper functions)
