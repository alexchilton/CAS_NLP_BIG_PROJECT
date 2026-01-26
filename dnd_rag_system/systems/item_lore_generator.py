"""
Item Lore Generator

Generates dynamic, context-aware item descriptions and backstories using RAG and LLM.
Showcases the RAG → LLM pipeline for immersive item flavor text.
"""

from typing import Optional, Dict, Any
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.core.llm_client import LLMClient
from dnd_rag_system.config import settings


class ItemLoreGenerator:
    """
    Generates rich, context-aware item lore and descriptions.
    
    Pipeline: ChromaDB (item/equipment data) → LLM (backstory generation)
    
    Responsibilities:
    - Query RAG for item mechanics and descriptions
    - Generate contextual backstories via LLM
    - Provide fallback to hardcoded descriptions
    - Vary descriptions based on context (character, location, quest)
    """
    
    def __init__(self, db_manager: ChromaDBManager, llm_client: LLMClient):
        """
        Initialize item lore generator.
        
        Args:
            db_manager: ChromaDB manager for RAG queries
            llm_client: LLM client for lore generation
        """
        self.db = db_manager
        self.llm = llm_client
    
    def generate_item_lore(
        self,
        item_name: str,
        item_type: str = "item",
        rarity: str = "common",
        character_context: Optional[str] = None,
        location: str = "unknown location",
        fallback_description: str = None
    ) -> str:
        """
        Generate rich item backstory using RAG and LLM.
        
        Args:
            item_name: Name of the item
            item_type: Type (weapon, armor, ring, potion, etc.)
            rarity: Rarity (common, uncommon, rare, very rare, legendary)
            character_context: Optional character info for personalization
            location: Current location for contextual flavor
            fallback_description: Fallback if LLM fails
            
        Returns:
            Rich item lore or fallback
        """
        try:
            # Step 1: Query RAG for item info
            rag_context = self._get_item_info(item_name, item_type)
            
            # Step 2: Generate LLM lore
            lore = self._generate_llm_lore(
                item_name=item_name,
                item_type=item_type,
                rarity=rarity,
                rag_info=rag_context,
                character_context=character_context,
                location=location
            )
            
            if lore and len(lore) > 20:
                return lore
            
        except Exception as e:
            print(f"Warning: Item lore generation failed: {e}")
        
        # Fallback
        return fallback_description or f"A {rarity} {item_type} known as {item_name}."
    
    def _get_item_info(self, item_name: str, item_type: str) -> str:
        """
        Query ChromaDB for item information.
        
        Args:
            item_name: Item name to search for
            item_type: Item type for filtering
            
        Returns:
            Formatted item info from RAG
        """
        try:
            # Build search query
            query = f"{item_name} {item_type} properties effects description"
            
            # Search equipment collection
            results = self.db.search(
                collection_name=settings.COLLECTION_NAMES['equipment'],
                query_text=query,
                n_results=2
            )
            
            if not results or not results.get('documents'):
                return f"A {item_type} called {item_name}."
            
            # Extract most relevant document
            documents = results['documents'][0] if isinstance(results['documents'][0], list) else results['documents']
            metadatas = results.get('metadatas', [[{}]])[0] if results.get('metadatas') else [{}]
            
            # Format info context
            info_parts = []
            for doc, meta in zip(documents[:1], metadatas[:1]):
                if isinstance(meta, dict):
                    name = meta.get('name', item_name)
                    info_parts.append(f"[{name}]: {doc[:300]}")
                else:
                    info_parts.append(doc[:300])
            
            return "\n".join(info_parts)
            
        except Exception as e:
            print(f"Warning: RAG query for {item_name} failed: {e}")
            return f"A {item_type} called {item_name}."
    
    def _generate_llm_lore(
        self,
        item_name: str,
        item_type: str,
        rarity: str,
        rag_info: str,
        character_context: Optional[str],
        location: str
    ) -> Optional[str]:
        """
        Generate item backstory using LLM.
        
        Args:
            item_name: Item name
            item_type: Item type
            rarity: Rarity level
            rag_info: Info from RAG database
            character_context: Character context
            location: Current location
            
        Returns:
            Generated backstory or None if failed
        """
        # Build context-aware prompt
        character_hint = f"\nThe item is being examined by: {character_context}" if character_context else ""
        
        prompt = f"""You are a Dungeon Master describing a magical item in D&D 5e.

ITEM: {item_name}
TYPE: {item_type}
RARITY: {rarity}
LOCATION: {location}{character_hint}

ITEM INFORMATION:
{rag_info}

Write a rich 2-3 sentence backstory for this item. Focus on:
- Its mysterious origin or legendary creator
- Historical significance or previous owners
- Why it's powerful or unique

Make it atmospheric and immersive. Keep it under 100 words.
DO NOT include game mechanics or stats.
DO NOT use the phrase "appears to be" or "seems like".

ITEM LORE:"""

        try:
            response = self.llm.query(
                prompt=prompt,
                system_message="You are a storytelling D&D Dungeon Master describing magical items.",
                temperature=0.85,
                max_tokens=200
            )
            
            if response:
                # Clean up response
                cleaned = response.strip()
                cleaned = cleaned.replace("ITEM LORE:", "").strip()
                cleaned = cleaned.replace("Lore:", "").strip()
                return cleaned
            
        except Exception as e:
            print(f"Warning: LLM generation failed for {item_name}: {e}")
        
        return None
    
    def generate_enhanced_description(
        self,
        item_name: str,
        base_description: str,
        item_type: str = "item",
        rarity: str = "common"
    ) -> str:
        """
        Enhance an existing item description with LLM flavor.
        
        Args:
            item_name: Item name
            base_description: Existing mechanical description
            item_type: Item type
            rarity: Rarity level
            
        Returns:
            Enhanced description combining mechanics and lore
        """
        try:
            lore = self.generate_item_lore(
                item_name=item_name,
                item_type=item_type,
                rarity=rarity,
                fallback_description=base_description
            )
            
            if lore and lore != base_description:
                # Combine lore + mechanics
                return f"{lore}\n\n*{base_description}*"
            
        except Exception as e:
            print(f"Warning: Enhanced description failed: {e}")
        
        return base_description
