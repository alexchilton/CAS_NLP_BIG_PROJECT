"""
Mechanics Service - Facade for Mechanics Extraction and Application

Consolidates the pattern of:
1. Extract mechanics from GM narrative
2. Filter NPC hallucinations
3. Apply mechanics to game state
4. Return feedback

This simplifies GameMaster by providing a single method call instead of 80+ lines of code.
"""

import logging
from typing import List, Optional, TYPE_CHECKING

from dnd_rag_system.systems.mechanics_extractor import MechanicsExtractor
from dnd_rag_system.systems.mechanics_applicator import MechanicsApplicator

if TYPE_CHECKING:
    from dnd_rag_system.systems.game_state import GameSession
    from dnd_rag_system.systems.combat_manager import CombatManager

logger = logging.getLogger(__name__)


class MechanicsService:
    """
    Facade service for mechanics extraction and application.
    
    Combines MechanicsExtractor and MechanicsApplicator with filtering logic
    to provide a simplified interface for GameMaster.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize mechanics service.
        
        Args:
            debug: Enable debug logging
        """
        self.extractor = MechanicsExtractor(debug=debug)
        self.applicator = MechanicsApplicator(debug=debug)
        self.debug = debug
    
    def process_narrative(
        self,
        narrative: str,
        game_session: 'GameSession',
        combat_manager: Optional['CombatManager'] = None,
        encounter_monster_name: Optional[str] = None
    ) -> List[str]:
        """
        Extract mechanics from narrative and apply to game state.
        
        Handles the complete workflow:
        1. Extracts mechanics from GM narrative
        2. Filters NPC hallucinations (if encounter is active)
        3. Applies mechanics to characters/party
        4. Applies damage to NPCs
        5. Returns consolidated feedback
        
        Args:
            narrative: GM's narrative response
            game_session: Current game session
            combat_manager: Optional combat manager for NPC damage
            encounter_monster_name: Optional name of actual encounter monster (for filtering)
            
        Returns:
            List of feedback messages about applied mechanics
        """
        # Get character names for better extraction
        char_names = []
        if game_session.party and len(game_session.party.characters) > 0:
            char_names = list(game_session.party.characters.keys())
        elif game_session.character_state:
            char_names = [game_session.character_state.character_name]
        
        if not char_names:
            return []
        
        # Extract mechanics from GM response
        mechanics = self.extractor.extract(
            narrative,
            char_names,
            existing_npcs=game_session.npcs_present
        )
        
        # If no mechanics found, return early
        if not mechanics.has_mechanics():
            return []
        
        # Filter NPC hallucinations if we have an encounter
        if encounter_monster_name and mechanics.npcs_introduced:
            mechanics = self._filter_npc_hallucinations(
                mechanics,
                encounter_monster_name,
                game_session.npcs_present
            )
        
        # Apply mechanics to session NPCs
        npc_feedback = self.applicator.apply_npcs_to_session(mechanics, game_session)
        
        # Apply damage/healing/conditions to characters
        if game_session.party and len(game_session.party.characters) > 0:
            char_feedback = self.applicator.apply_to_party(mechanics, game_session.party)
        else:
            char_feedback = self.applicator.apply_to_character(
                mechanics,
                game_session.character_state,
                game_session=game_session
            )
        
        # Apply damage to NPCs (enemies) if combat manager provided
        npc_damage_feedback = []
        if combat_manager:
            npc_damage_feedback = self.applicator.apply_damage_to_npcs(
                mechanics,
                combat_manager,
                game_session
            )
        
        # Combine and deduplicate feedback
        all_feedback = npc_feedback + char_feedback + npc_damage_feedback
        return self._deduplicate_feedback(all_feedback)
    
    def _filter_npc_hallucinations(
        self,
        mechanics,
        encounter_monster_name: str,
        existing_npcs: List[str]
    ):
        """
        Filter hallucinated NPCs from mechanics extraction.
        
        When there's an encounter, only allow:
        - The actual encounter monster
        - Non-enemy NPCs (merchants, guards, etc.)
        - NPCs already present in the scene
        
        Args:
            mechanics: Extracted mechanics object
            encounter_monster_name: Name of the actual encounter monster
            existing_npcs: List of NPCs already present
            
        Returns:
            Modified mechanics object with filtered NPCs
        """
        if not mechanics.npcs_introduced:
            return mechanics
        
        original_count = len(mechanics.npcs_introduced)
        filtered_npcs = []
        existing_lower = [npc.lower() for npc in existing_npcs]
        encounter_name_lower = encounter_monster_name.strip().lower()
        
        for npc in mechanics.npcs_introduced:
            npc_name = npc.get('name', '').strip()
            npc_name_lower = npc_name.lower()
            
            # Skip if already present
            if npc_name_lower in existing_lower:
                if self.debug:
                    logger.debug(f"🔧 Filtered NPC '{npc_name}' - already present")
                continue
            
            # Allow the actual encounter monster
            if npc_name_lower == encounter_name_lower:
                filtered_npcs.append(npc)
            # Allow non-enemy NPCs (merchants, guards, etc.)
            elif npc.get('type') != 'enemy':
                filtered_npcs.append(npc)
            else:
                # This is a hallucinated enemy - skip it
                if self.debug:
                    logger.debug(f"🔧 Filtered hallucinated enemy '{npc_name}' - actual encounter is '{encounter_monster_name}'")
        
        mechanics.npcs_introduced = filtered_npcs
        
        if self.debug and original_count != len(filtered_npcs):
            logger.debug(f"🔧 Filtered {original_count - len(filtered_npcs)} NPC(s) from mechanics extraction")
        
        return mechanics
    
    def _deduplicate_feedback(self, feedback_list: List[str]) -> List[str]:
        """
        Remove duplicate feedback messages.
        
        Fixes LLM prompt leakage causing duplicate extractions.
        
        Args:
            feedback_list: List of feedback messages
            
        Returns:
            Deduplicated list of feedback messages
        """
        if not feedback_list:
            return []
        
        unique_feedback = []
        seen = set()
        
        for msg in feedback_list:
            msg_normalized = msg.strip().lower()
            if msg_normalized and msg_normalized not in seen:
                unique_feedback.append(msg)
                seen.add(msg_normalized)
        
        return unique_feedback
