"""
Monster Description Generator

Generates dynamic, context-aware monster encounter descriptions using RAG and LLM.
Showcases the RAG → LLM pipeline for immersive combat encounters.
"""

from typing import Optional, Dict, Any
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.core.llm_client import LLMClient
from dnd_rag_system.config import settings


class MonsterDescriptionGenerator:
    """
    Generates rich, context-aware monster encounter descriptions.
    
    Pipeline: ChromaDB (monster lore) → LLM (dramatic narration)
    
    Responsibilities:
    - Query RAG for monster lore and statistics
    - Generate contextual encounter descriptions via LLM
    - Provide fallback to hardcoded descriptions
    - Vary descriptions based on context (location, encounter count, party level)
    """
    
    def __init__(self, db_manager: ChromaDBManager, llm_client: LLMClient):
        """
        Initialize monster description generator.
        
        Args:
            db_manager: ChromaDB manager for RAG queries
            llm_client: LLM client for description generation
        """
        self.db = db_manager
        self.llm = llm_client
    
    def generate_encounter_description(
        self,
        monster_name: str,
        monster_cr: float,
        location: str = "unknown location",
        is_repeat_encounter: bool = False,
        party_level: int = 1,
        fallback_description: str = None
    ) -> str:
        """
        Generate dramatic monster encounter description using RAG and LLM.
        
        Args:
            monster_name: Name of the monster
            monster_cr: Challenge rating
            location: Current location/environment
            is_repeat_encounter: Whether player has fought this before
            party_level: Average party level for context
            fallback_description: Fallback if LLM fails
            
        Returns:
            Rich encounter description or fallback
        """
        try:
            # Step 1: Query RAG for monster lore
            rag_context = self._get_monster_lore(monster_name, monster_cr)
            
            # Step 2: Generate LLM description
            description = self._generate_llm_description(
                monster_name=monster_name,
                monster_cr=monster_cr,
                location=location,
                rag_lore=rag_context,
                is_repeat=is_repeat_encounter,
                party_level=party_level
            )
            
            if description and len(description) > 20:
                return description
            
        except Exception as e:
            print(f"Warning: Monster description generation failed: {e}")
        
        # Fallback
        return fallback_description or f"A {monster_name} appears!"
    
    def _get_monster_lore(self, monster_name: str, cr: float) -> str:
        """
        Query ChromaDB for monster lore and statistics.
        
        Args:
            monster_name: Monster name to search for
            cr: Challenge rating for filtering
            
        Returns:
            Formatted lore text from RAG
        """
        try:
            # Build search query
            query = f"{monster_name} challenge rating {cr} abilities attacks description"
            
            # Search monster collection
            results = self.db.search(
                collection_name=settings.COLLECTION_NAMES['monsters'],
                query_text=query,
                n_results=3
            )
            
            if not results or not results.get('documents'):
                return f"A dangerous {monster_name} (CR {cr})."
            
            # Extract most relevant document
            documents = results['documents'][0] if isinstance(results['documents'][0], list) else results['documents']
            metadatas = results.get('metadatas', [[{}]])[0] if results.get('metadatas') else [{}]
            
            # Format lore context
            lore_parts = []
            for doc, meta in zip(documents[:2], metadatas[:2]):
                if isinstance(meta, dict):
                    name = meta.get('name', monster_name)
                    lore_parts.append(f"[{name}]: {doc[:300]}")
                else:
                    lore_parts.append(doc[:300])
            
            return "\n\n".join(lore_parts)
            
        except Exception as e:
            print(f"Warning: RAG query for {monster_name} failed: {e}")
            return f"A {monster_name} (CR {cr})."
    
    def _generate_llm_description(
        self,
        monster_name: str,
        monster_cr: float,
        location: str,
        rag_lore: str,
        is_repeat: bool,
        party_level: int
    ) -> Optional[str]:
        """
        Generate dramatic encounter description using LLM.
        
        Args:
            monster_name: Monster name
            monster_cr: Challenge rating
            location: Current location
            rag_lore: Lore from RAG database
            is_repeat: Whether this is a repeat encounter
            party_level: Party level for context
            
        Returns:
            Generated description or None if failed
        """
        # Build context-aware prompt
        repeat_hint = "The party has encountered this creature before." if is_repeat else "This is the party's first encounter with this creature."
        threat_level = self._get_threat_level(monster_cr, party_level)
        
        prompt = f"""You are a Dungeon Master describing a monster encounter in D&D 5e.

MONSTER: {monster_name} (CR {monster_cr})
LOCATION: {location}
PARTY LEVEL: {party_level}
THREAT LEVEL: {threat_level}
{repeat_hint}

MONSTER LORE:
{rag_lore}

Write a dramatic 2-3 sentence encounter description. Focus on:
- Visual appearance and threatening demeanor
- How it emerges/appears in this location
- One distinctive feature or action

Make it atmospheric and immersive. Keep it concise (under 100 words).
DO NOT include game mechanics or stats.
DO NOT repeat the monster's name more than once.

ENCOUNTER DESCRIPTION:"""

        try:
            response = self.llm.query(
                prompt=prompt,
                system_message="You are a dramatic D&D Dungeon Master narrating monster encounters.",
                temperature=0.8,
                max_tokens=200
            )
            
            if response:
                # Clean up response
                cleaned = response.strip()
                # Remove common LLM artifacts
                cleaned = cleaned.replace("ENCOUNTER DESCRIPTION:", "").strip()
                cleaned = cleaned.replace("Description:", "").strip()
                return cleaned
            
        except Exception as e:
            print(f"Warning: LLM generation failed for {monster_name}: {e}")
        
        return None
    
    def _get_threat_level(self, monster_cr: float, party_level: int) -> str:
        """
        Determine threat level relative to party.
        
        Args:
            monster_cr: Monster challenge rating
            party_level: Average party level
            
        Returns:
            Threat description (Deadly, Dangerous, Moderate, Easy)
        """
        diff = monster_cr - party_level
        
        if diff >= 3:
            return "Deadly (far above party level)"
        elif diff >= 1:
            return "Dangerous (above party level)"
        elif diff >= -1:
            return "Moderate (appropriate challenge)"
        else:
            return "Easy (below party level)"
    
    def generate_multi_monster_description(
        self,
        monster_names: list[str],
        location: str = "unknown location",
        party_level: int = 1
    ) -> str:
        """
        Generate description for multiple monsters appearing together.
        
        Args:
            monster_names: List of monster names
            location: Current location
            party_level: Average party level
            
        Returns:
            Multi-monster encounter description
        """
        if not monster_names:
            return "Enemies appear!"
        
        if len(monster_names) == 1:
            return self.generate_encounter_description(
                monster_names[0],
                monster_cr=1,  # Default CR
                location=location,
                party_level=party_level
            )
        
        # For multiple monsters, create group description
        try:
            monster_list = ", ".join(monster_names[:-1]) + f" and {monster_names[-1]}"
            
            prompt = f"""You are a Dungeon Master describing a combat encounter in D&D 5e.

MONSTERS: {monster_list}
LOCATION: {location}
PARTY LEVEL: {party_level}

Write a dramatic 2-3 sentence description of these monsters appearing together.
Focus on the threat they pose as a group and how they coordinate.
Keep it under 80 words.

ENCOUNTER DESCRIPTION:"""

            response = self.llm.query(
                prompt=prompt,
                system_message="You are a dramatic D&D Dungeon Master.",
                temperature=0.8,
                max_tokens=150
            )
            
            if response:
                return response.strip().replace("ENCOUNTER DESCRIPTION:", "").strip()
                
        except Exception as e:
            print(f"Warning: Multi-monster description failed: {e}")
        
        # Fallback
        return f"⚔️ **{monster_list} appear!**"
