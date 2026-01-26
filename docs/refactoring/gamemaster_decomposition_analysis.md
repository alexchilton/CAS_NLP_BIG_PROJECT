# GameMaster God Class Decomposition Analysis

**Date**: 2026-01-26
**Status**: Analysis Complete
**File**: `dnd_rag_system/systems/gm_dialogue_unified.py`
**Size**: 1707 lines, 22 methods

---

## Problem Statement

The `GameMaster` class exhibits the **God Class anti-pattern**:

- ✗ Too many responsibilities (violates Single Responsibility Principle)
- ✗ 1707 lines in a single file
- ✗ 22 methods doing unrelated tasks
- ✗ Difficult to test individual components
- ✗ Hard to understand and maintain
- ✗ Changes to one feature can break unrelated features

**Impact on Development**:
- Adding new dialogue features requires editing a 1707-line file
- Testing prompt building requires instantiating the entire GM system
- LLM client changes affect combat mechanics
- RAG improvements risk breaking message history

---

## Current Class Structure

### Methods Inventory

| Method | Lines | Responsibility |
|--------|-------|----------------|
| `__init__` | 38 | Initialize all subsystems |
| `search_rag` | 33 | RAG database search |
| `format_rag_context` | 27 | Format RAG results for prompt |
| `_prune_message_history` | 38 | Message history management |
| `_create_message_summary` | 48 | Summarize old messages |
| `generate_response` | **638** | **MAIN GOD METHOD** - Does everything |
| `_calculate_player_attack` | 116 | Combat attack calculation |
| `_build_prompt` | 179 | LLM prompt construction |
| `_generate_invalid_action_response` | 182 | Generate rejection messages |
| `_extract_and_update_location` | 65 | Parse location from narrative |
| `_remove_prompt_leakage` | 33 | Clean LLM response |
| `_post_process_response` | 30 | Update game state from response |
| `_query_ollama` | 92 | Send prompt to Ollama |
| `_query_hf` | 64 | Send prompt to HF API |
| `set_context` | 9 | Update scene description |
| `set_location` | 4 | Set location |
| `add_npc` | 6 | Add NPC to scene |
| `remove_npc` | 6 | Remove NPC from scene |
| `start_combat` | 5 | Start combat |
| `end_combat` | 4 | End combat |
| `add_quest` | 4 | Add quest |
| `get_session_summary` | 3 | Get session summary |

### Dependencies (Injected in `__init__`)

```python
# Database
self.db: ChromaDBManager

# Game State
self.session: GameSession
self.message_history: List[Message]
self.conversation_summary: str

# Subsystems (good - already separated!)
self.action_validator: ActionValidator
self.shop: ShopSystem
self.spell_manager: SpellManager
self.combat_manager: CombatManager
self.mechanics_extractor: MechanicsExtractor
self.mechanics_applicator: MechanicsApplicator
self.encounter_system: EncounterSystem
self.command_dispatcher: CommandDispatcher

# LLM Client
self.client: InferenceClient | subprocess
self.model_name: str
self.use_hf_api: bool
```

---

## Identified Responsibilities (Separate Concerns)

### 1️⃣ **RAG Retrieval & Formatting**
**Lines**: ~100 (methods: `search_rag`, `format_rag_context`)

- Search ChromaDB collections for D&D rules
- Format results into LLM-friendly context
- Filter by relevance (distance < 1.0)

**Proposed Class**: `RAGRetriever`

---

### 2️⃣ **Message History Management**
**Lines**: ~120 (methods: `_prune_message_history`, `_create_message_summary`)

- Maintain conversation history
- Prune old messages to prevent context overflow
- Create summaries of archived messages
- Different strategies for solo vs party mode

**Proposed Class**: `ConversationHistoryManager`

---

### 3️⃣ **LLM Prompt Building**
**Lines**: ~180 (method: `_build_prompt`)

- Assemble prompt from game state
- Add RAG context
- Add validation guidance
- Add combat instructions
- Add encounter instructions
- Format with proper structure

**Proposed Class**: `PromptBuilder`

---

### 4️⃣ **LLM Communication**
**Lines**: ~200 (methods: `_query_ollama`, `_query_hf`, `_remove_prompt_leakage`)

- Route to Ollama or HF API
- Handle API calls
- Clean up response (remove prompt echo, leaked instructions)
- Timeout handling

**Proposed Class**: `LLMCommunicator` (or merge into existing `LLMClientFactory`)

---

### 5️⃣ **Response Post-Processing**
**Lines**: ~130 (methods: `_post_process_response`, `_extract_and_update_location`)

- Extract location changes from narrative
- Auto-add introduced NPCs
- Update game state based on narrative

**Proposed Class**: `ResponsePostProcessor`

---

### 6️⃣ **Combat Mechanics Calculation**
**Lines**: ~120 (method: `_calculate_player_attack`)

- Calculate attack rolls
- Determine hit/miss/crit
- Calculate damage
- Format instructions for GM

**Proposed Class**: Could be merged into existing `CombatManager`

---

### 7️⃣ **Invalid Action Response Generation**
**Lines**: ~180 (method: `_generate_invalid_action_response`)

- Generate character-appropriate rejection messages
- Race-specific dialogue (dwarf vs elf)
- Class-specific messages (fighter vs wizard)
- Deterministic (no LLM call)

**Proposed Class**: `InvalidActionResponder` or merge into `ActionValidator`

---

### 8️⃣ **Orchestration & Game Flow**
**Lines**: ~650 (main `generate_response` method)

This is the **orchestrator** that coordinates all the above:

1. Check player status (unconscious?)
2. Dispatch commands
3. Handle shop transactions
4. Parse party mode actions
5. Validate actions
6. Auto-start combat
7. Calculate attacks
8. Search RAG
9. Generate random encounters
10. Build prompt
11. Query LLM
12. Post-process response
13. Extract mechanics
14. Advance combat turns
15. Process NPC actions

**Proposed Class**: `GameOrchestrator` or streamlined `GameMaster`

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      GameMaster (Facade)                    │
│  - Simplified public API                                    │
│  - Delegates to specialized components                      │
│  - Thin orchestration layer                                 │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ RAGRetriever  │    │ PromptBuilder │    │LLMCommunicator│
│               │    │               │    │               │
│ - search_rag  │    │ - build_prompt│    │ - query_llm   │
│ - format      │    │ - add_context │    │ - clean_resp  │
└───────────────┘    └───────────────┘    └───────────────┘

┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ConversationMgr│    │ResponsePostPro│    │ActionResponder│
│               │    │               │    │               │
│ - add_message │    │ - extract_loc │    │ - generate    │
│ - prune       │    │ - add_npcs    │    │   invalid_msg │
│ - summarize   │    │ - update_state│    │               │
└───────────────┘    └───────────────┘    └───────────────┘

        Existing Subsystems (already separated):
┌───────────────┬───────────────┬───────────────┬───────────────┐
│ActionValidator│ ShopSystem    │ CombatManager │ SpellManager  │
├───────────────┼───────────────┼───────────────┼───────────────┤
│MechanicsExtrac│MechanicsApplic│EncounterSystem│CommandDispatch│
└───────────────┴───────────────┴───────────────┴───────────────┘
```

---

## Benefits of Decomposition

### 🎯 Single Responsibility Principle
Each class has ONE reason to change:
- RAG changes? → Only `RAGRetriever` changes
- Prompt format changes? → Only `PromptBuilder` changes
- LLM API changes? → Only `LLMCommunicator` changes

### 🧪 Testability
- Test prompt building WITHOUT initializing entire GM
- Test RAG formatting WITHOUT LLM
- Test message summarization in isolation
- Mock LLM responses easily

### 📖 Readability
- Each class ~150-200 lines (manageable)
- Clear separation of concerns
- Easier to onboard new developers

### 🔧 Maintainability
- Changes localized to relevant class
- Less risk of breaking unrelated features
- Easier to debug issues

### 🚀 Extensibility
- Add new prompt formats? Extend `PromptBuilder`
- Support new LLM providers? Extend `LLMCommunicator`
- Different RAG strategies? Swap `RAGRetriever`

---

## Migration Risks & Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**:
- Create new classes alongside old `GameMaster`
- Gradually migrate functionality
- Keep existing tests passing
- Use feature flags for new implementation

### Risk 2: Performance Overhead
**Mitigation**:
- Minimal - just delegating method calls
- No additional serialization
- Same objects passed by reference

### Risk 3: Session State Management
**Mitigation**:
- All components share same `GameSession` instance
- Pass session as constructor parameter
- No state duplication

---

## Implementation Plan

### Phase 1: Extract Simple Components (Low Risk)
**Effort**: 2-3 hours

1. **Create `RAGRetriever` class**
   - Extract `search_rag` and `format_rag_context`
   - Takes `ChromaDBManager` in constructor
   - 2 methods, ~100 lines

2. **Create `ConversationHistoryManager` class**
   - Extract `_prune_message_history` and `_create_message_summary`
   - Manages `message_history` and `conversation_summary`
   - 2 methods, ~120 lines

3. **Test in isolation**
   - Unit tests for RAG retrieval
   - Unit tests for message pruning

### Phase 2: Extract LLM Components (Medium Risk)
**Effort**: 3-4 hours

4. **Create `PromptBuilder` class**
   - Extract `_build_prompt`
   - Takes game state as input, returns formatted prompt
   - ~180 lines

5. **Create `LLMCommunicator` class**
   - Extract `_query_ollama`, `_query_hf`, `_remove_prompt_leakage`
   - Wraps LLM API calls
   - ~200 lines

6. **Test with mocked LLM**
   - Test prompt format
   - Test response cleaning

### Phase 3: Extract Response Processing (Medium Risk)
**Effort**: 2-3 hours

7. **Create `ResponsePostProcessor` class**
   - Extract `_post_process_response`, `_extract_and_update_location`
   - Updates game state from narrative
   - ~130 lines

8. **Create `InvalidActionResponder` class**
   - Extract `_generate_invalid_action_response`
   - Character-specific rejection messages
   - ~180 lines

### Phase 4: Refactor Core `generate_response` (Highest Risk)
**Effort**: 4-5 hours

9. **Slim down `GameMaster.generate_response`**
   - Delegate to new components
   - Keep only orchestration logic
   - Reduce from 638 lines to ~150 lines

10. **Update `GameMaster.__init__`**
    - Initialize new components
    - Pass dependencies

### Phase 5: Integration Testing
**Effort**: 2-3 hours

11. **Run full test suite**
    - All unit tests
    - Integration tests
    - E2E tests (shop, combat, steal)

12. **Manual testing**
    - Load character
    - Test combat
    - Test shop
    - Test party mode

---

## Success Criteria

✅ All existing tests pass
✅ `GameMaster` class reduced to < 400 lines
✅ Each new class < 250 lines
✅ New classes have unit tests
✅ No performance regression
✅ E2E tests pass (shop, combat, steal, inventory)

---

## Estimated Total Effort

**16-20 hours** (2-3 days)

Breakdown:
- Phase 1 (Simple): 2-3 hours
- Phase 2 (LLM): 3-4 hours
- Phase 3 (Response): 2-3 hours
- Phase 4 (Orchestration): 4-5 hours
- Phase 5 (Testing): 2-3 hours
- Buffer for issues: 3-5 hours

---

## Alternative: Minimal Refactoring (Quick Win)

If time is limited, focus on **Phase 1 only**:

- Extract `RAGRetriever` (1 hour)
- Extract `ConversationHistoryManager` (1 hour)
- Test (1 hour)

**Total**: 3 hours, reduces `GameMaster` by ~200 lines

---

## Next Steps

1. **Decision**: Full decomposition or minimal refactoring?
2. **Create feature branch**: `feature/decompose-gamemaster` ✅ (already created)
3. **Start with Phase 1**: Low-risk extractions
4. **Validate with tests**: Ensure no breakage
5. **Continue or stop**: Based on results of Phase 1

