"""
Session State Management for Gradio Web UI

Replaces global variables with per-session state to enable multi-user support.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Literal
from pathlib import Path

# Avoid circular imports by importing at usage time
# from dnd_rag_system.systems.character_creator import Character
# from dnd_rag_system.systems.game_state import PartyState
# from dnd_rag_system.systems.gm_dialogue_unified import GameMaster


@dataclass
class SessionState:
    """
    Per-user session state for Gradio app.

    This class encapsulates all state that was previously stored in global variables,
    enabling multiple users to use the app simultaneously without interference.

    Each Gradio session gets its own instance of this class via gr.State.
    """

    # Character/Party state
    current_character: Optional['Character'] = None  # Type hint with string to avoid import
    party_characters: Dict[str, 'Character'] = field(default_factory=dict)
    party: Optional['PartyState'] = None
    gameplay_mode: Literal["character", "party"] = "character"

    # Conversation history
    conversation_history: List[Dict] = field(default_factory=list)

    # GameMaster instance (one per session for isolation)
    gm: Optional['GameMaster'] = None

    def __post_init__(self):
        """Initialize session-specific resources."""
        # Import here to avoid circular dependencies
        from dnd_rag_system.systems.game_state import PartyState

        # Initialize party if not provided
        if self.party is None:
            self.party = PartyState(party_name="Adventuring Party")

        # GameMaster will be initialized lazily in get_gm() to avoid pickling issues

    def reset(self):
        """Reset session state (for testing or manual reset)."""
        self.current_character = None
        self.party_characters.clear()
        self.conversation_history.clear()
        self.gameplay_mode = "character"

        # Reset party
        from dnd_rag_system.systems.game_state import PartyState
        self.party = PartyState(party_name="Adventuring Party")

        # Reset GM session (but keep same GM instance)
        if self.gm:
            from dnd_rag_system.systems.game_state import GameSession
            self.gm.session = GameSession()

    def to_dict(self) -> Dict:
        """
        Serialize session state to dictionary.

        Useful for debugging and session persistence (future feature).
        """
        return {
            "gameplay_mode": self.gameplay_mode,
            "has_character": self.current_character is not None,
            "party_size": len(self.party_characters),
            "conversation_length": len(self.conversation_history),
            "gm_initialized": self.gm is not None
        }

    def __repr__(self) -> str:
        """Readable representation for debugging."""
        return (
            f"SessionState("
            f"mode={self.gameplay_mode}, "
            f"char={self.current_character.name if self.current_character else None}, "
            f"party_size={len(self.party_characters)}, "
            f"history_len={len(self.conversation_history)})"
        )

    def __getstate__(self):
        """Custom pickling to exclude unpicklable objects."""
        state = self.__dict__.copy()
        # Don't pickle GM (will be recreated on unpickle)
        state['gm'] = None
        return state

    def __setstate__(self, state):
        """Custom unpickling to recreate GM."""
        self.__dict__.update(state)
        # Recreate GM on unpickle
        from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
        from dnd_rag_system.core.chroma_manager import ChromaDBManager
        db = ChromaDBManager()
        self.gm = GameMaster(db)


def create_session_state() -> SessionState:
    """
    Factory function to create a new SessionState.

    Use this in Gradio: session = gr.State(create_session_state())
    """
    from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
    from dnd_rag_system.core.chroma_manager import ChromaDBManager

    state = SessionState()
    # Initialize GameMaster for this session
    # Note: ChromaDB is shared (read-only), but GameSession is per-user
    db = ChromaDBManager()
    state.gm = GameMaster(db)
    return state


# Backward compatibility helper (for gradual migration)
def extract_session_globals(
    current_character,
    party_characters,
    party,
    gameplay_mode,
    conversation_history,
    gm
) -> SessionState:
    """
    Convert existing global variables to SessionState.

    This helper function is for gradual migration - allows converting
    existing code one piece at a time.

    Args:
        current_character: Current character object
        party_characters: Dict of party characters
        party: PartyState object
        gameplay_mode: "character" or "party"
        conversation_history: List of conversation messages
        gm: GameMaster instance

    Returns:
        SessionState with provided values
    """
    state = SessionState()
    state.current_character = current_character
    state.party_characters = party_characters
    state.party = party
    state.gameplay_mode = gameplay_mode
    state.conversation_history = conversation_history
    state.gm = gm
    return state
