# Global State Analysis - app_gradio.py

## Current Global Variables (Lines 75-80)

```python
current_character = None           # Type: Character | None
conversation_history = []          # Type: List[Dict]
party = PartyState(...)           # Type: PartyState
party_characters = {}             # Type: Dict[str, Character]
gameplay_mode = "character"       # Type: Literal["character", "party"]
```

## Global State Usage By Function

### Functions That READ Global State:
1. `get_current_sheet()` - reads: `current_character`, `party_characters`, `party`, `gameplay_mode`
2. `get_initiative_tracker_wrapper()` - reads: `gameplay_mode`, `party_characters`, `party`
3. `get_party_summary_wrapper()` - reads: `party_characters`, `party`
4. `get_all_character_sheets_wrapper()` - reads: `party_characters`, `party`
5. `chat_wrapper()` - reads: `gameplay_mode`, `current_character`, `party_characters`, `conversation_history`

### Functions That WRITE Global State:
1. `load_character_wrapper()` - writes: `current_character`, `conversation_history`, `gameplay_mode`
2. `load_character_with_debug_wrapper()` - writes: `current_character`, `conversation_history`, `gameplay_mode`
3. `load_character_with_location()` - writes: `current_character`, `conversation_history`, `gameplay_mode`
4. `clear_history_wrapper()` - writes: `conversation_history`
5. `load_party_mode_wrapper()` - writes: `party_characters`, `party`, `gameplay_mode`, `conversation_history`
6. `add_to_party_wrapper()` - writes: `party_characters`, `party`
7. `remove_from_party_wrapper()` - writes: `party_characters`, `party`

## Dependencies

### GameMaster Dependencies:
- `gm` is created once at module level (line 69)
- `gm.session` is shared state that needs to stay coordinated
- Multiple users would share the same `gm` instance (BAD!)

### Solution: Each session needs its own GameMaster instance OR use session-scoped state

## Proposed SessionState Class

```python
@dataclass
class SessionState:
    """Per-user session state for Gradio app."""

    # Character/Party state
    current_character: Optional[Character] = None
    party_characters: Dict[str, Character] = field(default_factory=dict)
    party: PartyState = field(default_factory=lambda: PartyState(party_name="Adventuring Party"))
    gameplay_mode: Literal["character", "party"] = "character"

    # Conversation history
    conversation_history: List[Dict] = field(default_factory=list)

    # GameMaster instance (one per session!)
    gm: Optional[GameMaster] = None

    def __post_init__(self):
        """Initialize GameMaster for this session."""
        if self.gm is None:
            db = ChromaDBManager()  # Shared DB is OK
            self.gm = GameMaster(db)
```

## Gradio gr.State Integration

### Current Pattern (WRONG - uses globals):
```python
def load_character_wrapper(character_choice: str):
    global current_character
    current_character = load_character(...)
    return result
```

### New Pattern (RIGHT - uses gr.State):
```python
def load_character_wrapper(character_choice: str, session_state: SessionState):
    session_state.current_character = load_character(...)
    return result, session_state  # Return updated state!
```

### Gradio Event Handler Changes:
```python
# Before (implicit global state)
load_btn.click(load_character_wrapper, inputs=[character_dropdown], outputs=[...])

# After (explicit session state)
session = gr.State(SessionState())  # Create state component
load_btn.click(
    load_character_wrapper,
    inputs=[character_dropdown, session],  # Pass state as input
    outputs=[..., session]  # Return state as output
)
```

## Refactoring Strategy

### Phase 1: Create SessionState Class
- Define `SessionState` dataclass in new file `web/session_state.py`
- Include GameMaster instance creation

### Phase 2: Refactor Wrapper Functions
- Add `session_state: SessionState` parameter to all wrappers
- Replace `global` statements with `session_state.field` access
- Return `session_state` in outputs

### Phase 3: Update Gradio Event Handlers
- Create `gr.State(SessionState())` component
- Add `session` to inputs/outputs of all event handlers
- Test each handler individually

### Phase 4: Remove Global Variables
- Delete global variable declarations
- Verify no remaining `global` statements

### Phase 5: Test Multi-User Support
- Open app in multiple browser windows
- Verify each session maintains independent state
- Test race conditions (simultaneous actions)

## Risk Assessment

**HIGH RISK:**
- GameMaster contains ChromaDB (shared resource) - ensure thread-safe
- Session state passed through many layers - easy to miss a return value
- Gradio state serialization - ensure SessionState is picklable

**MITIGATION:**
- Test thoroughly after each phase
- Keep commits small and focused
- Use type hints to catch missing state parameters
- Add integration test for multi-user scenarios

## Files to Modify

1. `web/session_state.py` - NEW file for SessionState class
2. `web/app_gradio.py` - Remove globals, add gr.State
3. Potentially: handler functions if they access globals directly
