"""
Validation Message Generator

Generates context-aware validation messages using LLM instead of hardcoded text.
Makes invalid action feedback narrative and immersive.
"""

from typing import Optional
from dnd_rag_system.core.llm_client import LLMClient


class ValidationMessageGenerator:
    """
    Generates narrative validation messages for invalid actions.
    
    Pipeline: Context → LLM → Narrative feedback
    
    Responsibilities:
    - Generate contextual error messages
    - Suggest alternatives based on scene
    - Make validation atmospheric, not mechanical
    - Provide fallback to standard messages
    """
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize validation message generator.
        
        Args:
            llm_client: LLM client for message generation
        """
        self.llm = llm_client
    
    def generate_invalid_target_message(
        self,
        attempted_target: str,
        available_targets: list[str],
        location: str = "unknown location",
        action_type: str = "action",
        fallback_message: str = None
    ) -> str:
        """
        Generate narrative message for invalid target.
        
        Args:
            attempted_target: What the player tried to target
            available_targets: List of valid targets
            location: Current location
            action_type: Type of action (attack, talk, examine)
            fallback_message: Fallback if LLM fails
            
        Returns:
            Narrative validation message
        """
        try:
            targets_str = ", ".join(available_targets) if available_targets else "nothing"
            
            prompt = f"""You are a Dungeon Master narrating why a player's action failed.

LOCATION: {location}
ATTEMPTED TARGET: {attempted_target}
AVAILABLE TARGETS: {targets_str}
ACTION: {action_type}

Write a brief 1-2 sentence narrative explanation of why the player can't target "{attempted_target}".
Then suggest they try one of the available targets.
Make it atmospheric and immersive. Keep it under 60 words.

NARRATIVE:"""

            response = self.llm.query(
                prompt=prompt,
                system_message="You are a D&D Dungeon Master narrating game events.",
                temperature=0.7,
                max_tokens=100
            )
            
            if response:
                cleaned = response.strip().replace("NARRATIVE:", "").strip()
                return cleaned
            
        except Exception as e:
            print(f"Warning: Validation message generation failed: {e}")
        
        # Fallback
        return fallback_message or f"You don't see '{attempted_target}' here. Available: {targets_str}"
    
    def generate_invalid_spell_message(
        self,
        spell_name: str,
        reason: str,
        fallback_message: str = None
    ) -> str:
        """
        Generate narrative message for invalid spell cast.
        
        Args:
            spell_name: Spell the player tried to cast
            reason: Why it's invalid (no slots, don't know it, wrong level, etc.)
            fallback_message: Fallback if LLM fails
            
        Returns:
            Narrative validation message
        """
        try:
            prompt = f"""You are a Dungeon Master narrating why a spell cannot be cast.

SPELL: {spell_name}
REASON: {reason}

Write a brief 1 sentence narrative explanation of why the spell fails.
Make it atmospheric (e.g., "magical energy fizzles", "words of power fail").
Keep it under 40 words.

NARRATIVE:"""

            response = self.llm.query(
                prompt=prompt,
                system_message="You are a D&D Dungeon Master.",
                temperature=0.7,
                max_tokens=80
            )
            
            if response:
                cleaned = response.strip().replace("NARRATIVE:", "").strip()
                return cleaned
            
        except Exception as e:
            print(f"Warning: Spell validation message generation failed: {e}")
        
        # Fallback
        return fallback_message or f"Cannot cast {spell_name}: {reason}"
    
    def generate_invalid_action_message(
        self,
        action_description: str,
        reason: str,
        location: str = "unknown location",
        fallback_message: str = None
    ) -> str:
        """
        Generate narrative message for any invalid action.
        
        Args:
            action_description: What the player tried to do
            reason: Why it's invalid
            location: Current location
            fallback_message: Fallback if LLM fails
            
        Returns:
            Narrative validation message
        """
        try:
            prompt = f"""You are a Dungeon Master narrating why a player's action isn't possible.

LOCATION: {location}
ATTEMPTED ACTION: {action_description}
REASON: {reason}

Write a brief 1 sentence narrative explanation of why this action can't be done.
Make it immersive and helpful. Keep it under 40 words.

NARRATIVE:"""

            response = self.llm.query(
                prompt=prompt,
                system_message="You are a D&D Dungeon Master.",
                temperature=0.7,
                max_tokens=80
            )
            
            if response:
                cleaned = response.strip().replace("NARRATIVE:", "").strip()
                return cleaned
            
        except Exception as e:
            print(f"Warning: Action validation message generation failed: {e}")
        
        # Fallback
        return fallback_message or f"You can't {action_description}: {reason}"
