# GameMaster Decomposition Implementation Plan

**Status**: Ready to implement
**Branch**: `feature/decompose-gamemaster`
**Priority**: 4 (High - God class anti-pattern)

---

## Implementation Strategy

We'll use **incremental extraction** with parallel classes:

1. Create new classes alongside existing `GameMaster`
2. Update `GameMaster` to delegate to new classes
3. Keep all existing tests passing
4. Remove old code once migration is complete

This ensures we can **revert at any time** if issues arise.

---

## Phase 1: Extract RAG Retriever

### Step 1.1: Create `RAGRetriever` Class

**File**: `dnd_rag_system/dialogue/rag_retriever.py` (new)

```python
"""
RAG Retrieval and Formatting

Handles searching ChromaDB for D&D rules and formatting results for LLM prompts.
"""

from typing import Dict, Any
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings


class RAGRetriever:
    """
    Retrieves and formats D&D rules from RAG database.

    Responsibilities:
    - Search ChromaDB collections for relevant rules
    - Filter results by relevance
    - Format results for LLM context
    """

    def __init__(self, db_manager: ChromaDBManager):
        """
        Initialize RAG retriever.

        Args:
            db_manager: ChromaDB manager instance
        """
        self.db = db_manager

    def search_rag(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """
        Search RAG database for relevant D&D content.

        Args:
            query: Search query
            n_results: Number of results per collection

        Returns:
            Dictionary with results from all collections
        """
        results = {}

        # Search each collection
        for collection_type, collection_name in settings.COLLECTION_NAMES.items():
            try:
                search_results = self.db.search(
                    collection_name,
                    query,
                    n_results=n_results
                )

                if search_results['documents'] and search_results['documents'][0]:
                    results[collection_type] = {
                        'documents': search_results['documents'][0],
                        'metadatas': search_results['metadatas'][0],
                        'distances': search_results['distances'][0]
                    }
            except Exception as e:
                print(f"Warning: Could not search {collection_type}: {e}")
                continue

        return results

    def format_rag_context(self, rag_results: Dict[str, Any]) -> str:
        """
        Format RAG search results into context for LLM prompt.

        Args:
            rag_results: Results from search_rag()

        Returns:
            Formatted context string
        """
        if not rag_results:
            return "No specific rules retrieved."

        context_parts = []

        for collection_type, results in rag_results.items():
            docs = results['documents']
            metas = results['metadatas']
            distances = results['distances']

            for doc, meta, dist in zip(docs, metas, distances):
                # Only include very relevant results (distance < 1.0)
                if dist < 1.0:
                    name = meta.get('name', 'Unknown')
                    context_parts.append(f"[{collection_type.upper()}] {name}:\n{doc[:400]}")

        return "\n\n".join(context_parts) if context_parts else "No highly relevant rules found."
```

**Lines**: ~100

### Step 1.2: Create Unit Tests

**File**: `tests/test_rag_retriever.py` (new)

```python
"""Unit tests for RAGRetriever."""

import pytest
from dnd_rag_system.dialogue.rag_retriever import RAGRetriever


def test_search_rag_returns_results(mock_chromadb):
    """Test that search_rag returns formatted results."""
    retriever = RAGRetriever(mock_chromadb)
    results = retriever.search_rag("fireball spell")

    assert isinstance(results, dict)
    # Add more assertions based on mock data


def test_format_rag_context_filters_by_distance(mock_chromadb):
    """Test that only results with distance < 1.0 are included."""
    retriever = RAGRetriever(mock_chromadb)

    # Mock results with varying distances
    rag_results = {
        'spells': {
            'documents': ['Fireball spell...'],
            'metadatas': [{'name': 'Fireball'}],
            'distances': [0.5]  # Should be included
        },
        'monsters': {
            'documents': ['Goblin...'],
            'metadatas': [{'name': 'Goblin'}],
            'distances': [1.5]  # Should be excluded
        }
    }

    context = retriever.format_rag_context(rag_results)

    assert 'Fireball' in context
    assert 'Goblin' not in context
```

### Step 1.3: Update `GameMaster` to Use `RAGRetriever`

**File**: `dnd_rag_system/systems/gm_dialogue_unified.py`

```python
# In __init__:
from dnd_rag_system.dialogue.rag_retriever import RAGRetriever

def __init__(self, db_manager: ChromaDBManager, hf_token: str = None, model_name: str = None):
    self.db = db_manager
    self.rag_retriever = RAGRetriever(db_manager)  # NEW
    # ... rest of init

# Update generate_response to use retriever:
# Step 2: Search RAG if enabled
if use_rag:
    rag_results = self.rag_retriever.search_rag(player_input)  # CHANGED
    rag_context = self.rag_retriever.format_rag_context(rag_results)  # CHANGED
```

**Remove old methods** (after testing):
- `search_rag` (line 114-146)
- `format_rag_context` (line 148-174)

**Lines Removed**: ~60

### Step 1.4: Test

```bash
# Run existing tests to ensure nothing broke
pytest tests/ -v

# Run new RAGRetriever tests
pytest tests/test_rag_retriever.py -v
```

**Exit Criteria**:
- ✅ All existing tests pass
- ✅ New unit tests pass
- ✅ `GameMaster` reduced by ~60 lines

---

## Phase 2: Extract Conversation History Manager

### Step 2.1: Create `ConversationHistoryManager` Class

**File**: `dnd_rag_system/dialogue/conversation_history_manager.py` (new)

```python
"""
Conversation History Management

Handles message history pruning and summarization to prevent context overflow.
"""

import logging
from typing import List
from dataclasses import dataclass
from dnd_rag_system.config.settings import MAX_MESSAGE_HISTORY, SUMMARIZE_EVERY_N_MESSAGES

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Conversation message for GM dialogue history."""
    role: str  # 'player', 'gm', 'system'
    content: str
    rag_context: str = None
    timestamp: str = None


class ConversationHistoryManager:
    """
    Manages conversation history with automatic pruning and summarization.

    Responsibilities:
    - Maintain message history
    - Prune old messages to prevent context overflow
    - Create summaries of archived messages
    - Adapt strategy for solo vs party mode
    """

    def __init__(self, session):
        """
        Initialize conversation history manager.

        Args:
            session: GameSession instance (for party mode detection)
        """
        self.session = session
        self.message_history: List[Message] = []
        self.conversation_summary: str = ""

    def add_message(self, role: str, content: str, rag_context: str = None):
        """Add a message to history and prune if needed."""
        self.message_history.append(Message(role, content, rag_context))
        self._prune_if_needed()

    def get_recent_messages(self, n: int = None) -> List[Message]:
        """Get recent N messages (or all if N not specified)."""
        if n is None:
            return self.message_history
        return self.message_history[-n:] if len(self.message_history) > n else self.message_history

    def _prune_if_needed(self):
        """Prune message history to prevent context window overflow."""
        # More aggressive pruning for party mode (5 characters = larger prompts)
        is_party_mode = self.session.party and len(self.session.party.characters) > 0
        max_history = MAX_MESSAGE_HISTORY if not is_party_mode else max(12, MAX_MESSAGE_HISTORY // 2)

        # If history is within limits, no action needed
        if len(self.message_history) <= max_history:
            return

        # Calculate how many messages to summarize
        messages_to_summarize = len(self.message_history) - max_history

        # Extract messages to summarize
        old_messages = self.message_history[:messages_to_summarize]

        # Create summary of old messages
        summary_text = self._create_summary(old_messages)

        # Update conversation summary
        if self.conversation_summary:
            self.conversation_summary += f"\n\n--- Session Continued ---\n{summary_text}"
        else:
            self.conversation_summary = summary_text

        # Keep only recent messages
        self.message_history = self.message_history[messages_to_summarize:]

        # Log for debugging
        mode_indicator = "party mode" if is_party_mode else "solo mode"
        logger.info(f"📝 Pruned {messages_to_summarize} messages ({mode_indicator}). History now: {len(self.message_history)} messages")
        self.session.add_note(f"Conversation history summarized ({messages_to_summarize} messages archived, {mode_indicator})")

    def _create_summary(self, messages: List[Message]) -> str:
        """
        Create a concise summary of message exchanges.
        Focuses on key events: combat, quests, important discoveries.
        """
        if not messages:
            return ""

        # Build summary from key events
        summary_lines = []

        for msg in messages:
            # Extract important events (combat, quests, travel, shopping)
            content_lower = msg.content.lower()

            # Combat events
            if any(word in content_lower for word in ['combat', 'attack', 'damage', 'hp', 'defeated', 'killed']):
                if msg.role == 'gm':
                    if 'defeated' in content_lower or 'killed' in content_lower or 'fled' in content_lower:
                        summary_lines.append(f"⚔️ Combat: {msg.content[:100]}")

            # Quest events
            elif any(word in content_lower for word in ['quest', 'mission', 'task', 'objective']):
                summary_lines.append(f"📜 Quest: {msg.content[:100]}")

            # Travel/exploration
            elif any(word in content_lower for word in ['travel', 'arrive', 'enter', 'leave', 'journey']):
                summary_lines.append(f"🗺️ Travel: {msg.content[:100]}")

            # Shopping/transactions
            elif any(word in content_lower for word in ['buy', 'sell', 'purchase', 'gold', 'shop']):
                summary_lines.append(f"💰 Trade: {msg.content[:100]}")

            # Important discoveries
            elif any(word in content_lower for word in ['find', 'discover', 'treasure', 'loot', 'item']):
                summary_lines.append(f"🔍 Discovery: {msg.content[:100]}")

        # If no key events found, create generic summary
        if not summary_lines:
            return f"The party had {len(messages)//2} exchanges covering general exploration and conversation."

        return "\n".join(summary_lines)
```

**Lines**: ~140

### Step 2.2: Update `GameMaster` to Use `ConversationHistoryManager`

```python
# In __init__:
from dnd_rag_system.dialogue.conversation_history_manager import ConversationHistoryManager

def __init__(self, db_manager: ChromaDBManager, hf_token: str = None, model_name: str = None):
    self.db = db_manager
    self.session = GameSession(session_name="D&D Adventure")
    self.history_manager = ConversationHistoryManager(self.session)  # NEW
    # Remove: self.message_history and self.conversation_summary
```

**Remove old methods** (after testing):
- `_prune_message_history` (line 176-213)
- `_create_message_summary` (line 215-263)

**Update all references**:
- `self.message_history` → `self.history_manager.message_history`
- `self._prune_message_history()` → (handled automatically by `add_message`)
- `self.conversation_summary` → `self.history_manager.conversation_summary`

**Lines Removed**: ~90

---

## Phase 3: Extract Prompt Builder

### Step 3.1: Create `PromptBuilder` Class

**File**: `dnd_rag_system/dialogue/prompt_builder.py` (new)

```python
"""
LLM Prompt Builder

Constructs formatted prompts for the LLM based on game state and context.
"""

from typing import Optional, List
from dnd_rag_system.systems.action_validator import ValidationResult
from dnd_rag_system.config.settings import RECENT_MESSAGES_FOR_PROMPT


class PromptBuilder:
    """
    Builds formatted prompts for LLM queries.

    Responsibilities:
    - Assemble prompt from game state
    - Add RAG context
    - Add validation guidance
    - Add combat/encounter instructions
    - Format with proper structure
    """

    def __init__(self, session):
        """
        Initialize prompt builder.

        Args:
            session: GameSession instance
        """
        self.session = session

    def build_prompt(
        self,
        player_input: str,
        recent_messages: List,
        conversation_summary: str,
        rag_context: str = "",
        validation = None,
        encounter_instruction: str = "",
        player_attack_instruction: str = "",
        steal_instruction: str = ""
    ) -> str:
        """
        Build complete prompt for LLM with full game state context.

        Args:
            player_input: Player's action
            recent_messages: Recent conversation messages
            conversation_summary: Summary of older messages
            rag_context: Retrieved RAG information
            validation: ValidationReport from action validator
            encounter_instruction: Hidden instruction for random encounter
            player_attack_instruction: Pre-calculated attack instruction
            steal_instruction: Steal attempt instructions

        Returns:
            Formatted prompt string
        """
        # Build conversation history
        history_text = "\n".join([
            f"{'Player' if msg.role == 'player' else 'GM'}: {msg.content}"
            for msg in recent_messages
        ])

        # Build base prompt with game state
        prompt = f"""You are an experienced Dungeon Master running a D&D 5e game.

CURRENT LOCATION: {self.session.current_location}
SCENE: {self.session.scene_description if self.session.scene_description else "The adventure continues..."}
TIME: Day {self.session.day}, {self.session.time_of_day}
"""

        # Add conversation summary if exists
        if conversation_summary:
            prompt += f"\nPREVIOUS SESSION SUMMARY:\n{conversation_summary[-500:]}\n"

        # Add location context
        current_loc = self.session.get_current_location_obj()
        if current_loc:
            if current_loc.visit_count > 1:
                prompt += f"NOTE: The party has been here before. Describe naturally without explicitly counting visits.\n"

            if current_loc.defeated_enemies:
                enemies = ", ".join(list(current_loc.defeated_enemies)[:3])
                prompt += f"AFTERMATH: These enemies were defeated here previously: {enemies}. You may mention remains/corpses if appropriate.\n"

        # Add NPCs/Monsters if present
        if self.session.npcs_present:
            prompt += f"\nNPCs/CREATURES PRESENT: {', '.join(self.session.npcs_present)}\n"

        # Add combat state if in combat
        if self.session.combat.in_combat:
            prompt += f"\nCOMBAT STATUS: Round {self.session.combat.round_number}, {self.session.combat.get_current_turn()}'s turn\n"
            prompt += f"Initiative Order: {', '.join([f'{name} ({init})' for name, init in self.session.combat.initiative_order])}\n"

        # Add active quests
        if self.session.active_quests:
            active = [q for q in self.session.active_quests if q.get('status') == 'active']
            if active:
                quest_names = [q['name'] for q in active[:2]]
                prompt += f"\nACTIVE QUESTS: {', '.join(quest_names)}\n"

        prompt += "\n"

        # Add RAG context if provided
        if rag_context and rag_context not in ["No specific rules retrieved.", "No highly relevant rules found."]:
            prompt += f"""RETRIEVED D&D RULES (Apply these rules accurately):
{rag_context}

"""

        # Add conversation history
        if history_text:
            prompt += f"""RECENT CONVERSATION:
{history_text}

"""

        # Add player action
        prompt += f"""PLAYER ACTION: {player_input}

"""

        # Add special instructions
        if encounter_instruction:
            prompt += f"""{encounter_instruction}

"""

        if player_attack_instruction:
            prompt += f"""{player_attack_instruction}

"""

        # Add base instructions
        prompt += """INSTRUCTIONS:
1. Apply D&D 5e rules accurately using the retrieved information
2. Consider the current location, NPCs present, and combat state
3. Ask for appropriate dice rolls (d20 for attacks/checks, damage dice, saves, etc.)
4. Be concise and engaging (2-4 sentences max)
5. Maintain narrative flow while being mechanically precise
6. If rules are unclear, use standard D&D 5e mechanics
7. Be concise, respond in 3-5 sentences unless more detail is explicitly required.

"""

        # Add steal instruction prominently
        if steal_instruction:
            prompt += f"""
═══════════════════════════════════════════════════════════════════
🎯 STEAL ATTEMPT MECHANICS 🎯
═══════════════════════════════════════════════════════════════════

{steal_instruction}

DO NOT create random monsters or encounters. ONLY the NPCs listed above should react.
═══════════════════════════════════════════════════════════════════

GM RESPONSE:"""
            return prompt

        # Add validation guidance
        if validation:
            if validation.result == ValidationResult.INVALID:
                prompt += f"""
═══════════════════════════════════════════════════════════════════
🚫 CRITICAL RULE - THIS ACTION IS IMPOSSIBLE 🚫
═══════════════════════════════════════════════════════════════════

{validation.message}

YOU MUST NARRATE FAILURE. DO NOT create the target/item/NPC.

Examples of CORRECT responses:
- "You swing your sword, but there's nothing there - the cavern is empty."
- "You reach for your bow, but you're only carrying your longsword and shield."
- "You try to recall the spell, but as a fighter, you have no magical training."

DO NOT write: "The goblin appears" or "You pull out your bow"
The target DOES NOT EXIST. Narrate the impossibility.
═══════════════════════════════════════════════════════════════════

GM RESPONSE:"""
            elif validation.result == ValidationResult.NPC_INTRODUCTION:
                prompt += f"""
═══════════════════════════════════════════════════════════════════
💬 NPC INTRODUCTION OPPORTUNITY 💬
═══════════════════════════════════════════════════════════════════

{validation.message}

Player wants to interact with: "{validation.action.target}"

If this makes sense in current location, introduce them naturally.
If NOT logical, narrate that no such person is present.
═══════════════════════════════════════════════════════════════════

GM RESPONSE:"""
            elif validation.matched_entity and validation.matched_entity != validation.action.target:
                prompt += f"""
═══════════════════════════════════════════════════════════════════
ℹ️ TARGET CLARIFICATION ℹ️
═══════════════════════════════════════════════════════════════════

{validation.message}

Player said: "{validation.action.target}"
Likely means: "{validation.matched_entity}"

Use "{validation.matched_entity}" in your response.
═══════════════════════════════════════════════════════════════════

GM RESPONSE:"""
            else:
                prompt += f"""{validation.message}

GM RESPONSE:"""
        else:
            prompt += """
GM RESPONSE:"""

        return prompt
```

**Lines**: ~220

### Step 3.2: Update `GameMaster` to Use `PromptBuilder`

```python
# In __init__:
from dnd_rag_system.dialogue.prompt_builder import PromptBuilder

def __init__(self, ...):
    self.prompt_builder = PromptBuilder(self.session)  # NEW

# In generate_response, replace _build_prompt call:
prompt = self.prompt_builder.build_prompt(
    player_input=player_input,
    recent_messages=self.history_manager.get_recent_messages(RECENT_MESSAGES_FOR_PROMPT),
    conversation_summary=self.history_manager.conversation_summary,
    rag_context=rag_context,
    validation=validation,
    encounter_instruction=encounter_instruction,
    player_attack_instruction=player_attack_instruction,
    steal_instruction=steal_instruction
)
```

**Remove old method**: `_build_prompt` (line 1019-1196)

**Lines Removed**: ~180

---

## Testing Strategy

### After Each Phase

```bash
# 1. Run unit tests for new class
pytest tests/test_<new_class>.py -v

# 2. Run all existing tests
pytest tests/ -v

# 3. Run E2E tests
pytest e2e_tests/ -v -m e2e

# 4. Manual smoke test
python -c "
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.systems.gm_dialogue_unified import GameMaster

db = ChromaDBManager()
gm = GameMaster(db)
response = gm.generate_response('I attack the goblin')
print(response)
"
```

### Exit Criteria for Each Phase

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ All E2E tests pass
- ✅ Code reduction achieved
- ✅ No performance regression

---

## Rollback Plan

If issues arise:

1. **Revert last commit**:
   ```bash
   git reset --hard HEAD~1
   ```

2. **Keep refactoring in separate branch**:
   ```bash
   git stash
   git checkout main
   # Fix urgent issue
   git checkout feature/decompose-gamemaster
   git stash pop
   ```

3. **Use feature flags** (if implementing partially):
   ```python
   USE_NEW_RAG_RETRIEVER = os.getenv("USE_NEW_RAG", "true").lower() == "true"

   if USE_NEW_RAG_RETRIEVER:
       self.rag_retriever = RAGRetriever(db_manager)
   else:
       # Old code path
   ```

---

## Success Metrics

### Code Quality
- ✅ `GameMaster` class reduced from 1707 to < 800 lines
- ✅ Each new class < 250 lines
- ✅ Cyclomatic complexity reduced

### Maintainability
- ✅ Each class has single, clear responsibility
- ✅ Unit tests for each component
- ✅ Code coverage maintained or improved

### Functionality
- ✅ All existing features work
- ✅ No new bugs introduced
- ✅ Performance maintained

---

## Timeline

**Phase 1**: 2-3 hours
**Phase 2**: 2-3 hours
**Phase 3**: 3-4 hours

**Total**: 7-10 hours (1-2 days)

---

## Next Action

**Start with Phase 1**: Extract `RAGRetriever`

This is the lowest-risk, highest-value first step.
