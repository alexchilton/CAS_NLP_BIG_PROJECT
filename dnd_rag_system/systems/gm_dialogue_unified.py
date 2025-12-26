"""
D&D Game Master Dialogue System - Unified Version

RAG-enhanced AI Dungeon Master that automatically detects environment:
- Hugging Face Inference API (when running on HF Spaces)
- Local Ollama (for local development)

Auto-detection based on SPACE_ID, SPACE_AUTHOR_NAME, or HF_SPACE environment variables.
"""

import sys
import subprocess
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings
from dnd_rag_system.systems.game_state import GameSession, CombatState, PartyState
from dnd_rag_system.systems.action_validator import (
    ActionValidator, ValidationResult, ActionType, create_context_aware_prompt
)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG if (settings.DEBUG_MODE or os.getenv("GM_DEBUG", "").lower() == "true") else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Check if debug mode is enabled
DEBUG_PROMPTS = settings.DEBUG_MODE or os.getenv("GM_DEBUG", "").lower() == "true"
if DEBUG_PROMPTS:
    logger.info("🔍 GM Debug mode enabled - will log all prompts sent to LLM")
    logger.info("   Set GM_DEBUG=false or update settings.DEBUG_MODE to disable")


def is_huggingface_space() -> bool:
    """Check if running on Hugging Face Spaces."""
    return (
        os.getenv("SPACE_ID") is not None or
        os.getenv("SPACE_AUTHOR_NAME") is not None or
        os.getenv("HF_SPACE") is not None or
        os.getenv("USE_HF_API", "false").lower() == "true"  # Manual override
    )


@dataclass
class Message:
    """Conversation message for GM dialogue history."""
    role: str  # 'player', 'gm', 'system'
    content: str
    rag_context: Optional[str] = None


class GameMaster:
    """
    RAG-Enhanced AI Game Master - Unified Version.

    Automatically uses:
    - HF Inference API on Hugging Face Spaces
    - Ollama for local development
    """

    def __init__(self, db_manager: ChromaDBManager, hf_token: str = None, model_name: str = None):
        """
        Initialize Game Master.

        Args:
            db_manager: ChromaDBManager instance
            hf_token: Hugging Face API token (optional, will use env var)
            model_name: Model name override (optional)
        """
        self.db = db_manager
        self.session = GameSession(session_name="D&D Adventure")
        self.message_history: List[Message] = []  # Separate conversation history
        self.action_validator = ActionValidator(debug=DEBUG_PROMPTS)  # Reality check system

        # Auto-detect environment
        self.use_hf_api = is_huggingface_space()

        if self.use_hf_api:
            print("🤗 Using Hugging Face Inference API mode")
            try:
                from huggingface_hub import InferenceClient
            except ImportError:
                raise ImportError("huggingface_hub is required for HF Spaces. Install with: pip install huggingface_hub")

            self.hf_token = hf_token or os.getenv("HF_TOKEN")
            # Use a model that's available via Inference API
            # Qwen2.5-7B-Instruct is excellent for roleplay and available on HF Inference API
            self.model_name = model_name or "Qwen/Qwen2.5-7B-Instruct"
            self.client = InferenceClient(token=self.hf_token)
            print(f"   Model: {self.model_name}")
            print(f"   Note: Using Inference API compatible model (local uses RPG-specific model)")
        else:
            print("🦙 Using local Ollama mode")
            # Local Ollama model
            self.model_name = model_name or settings.OLLAMA_MODEL_NAME
            self.client = None
            self._verify_ollama()
            print(f"   Model: {self.model_name}")

    def _verify_ollama(self):
        """Check if Ollama is installed and model is available (local mode only)."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise Exception("Ollama not responding")

            # Check if model exists
            if self.model_name not in result.stdout:
                print(f"⚠️  Model '{self.model_name}' not found in Ollama")
                print(f"   Available models:\n{result.stdout}")
                print(f"\n   To download: ollama pull {self.model_name}")
                raise Exception(f"Model {self.model_name} not available")

        except FileNotFoundError:
            raise Exception("Ollama not found. Please install from https://ollama.ai")
        except subprocess.TimeoutExpired:
            raise Exception("Ollama not responding (timeout)")

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

    def generate_response(self, player_input: str, use_rag: bool = True) -> str:
        """
        Generate GM response using RAG and LLM (Ollama or HF API).

        Args:
            player_input: Player's action or question
            use_rag: Whether to use RAG retrieval

        Returns:
            GM response
        """
        rag_context = ""

        # Step 1: Reality Check - Validate action against game state
        action_intent = self.action_validator.analyze_intent(player_input)
        validation = self.action_validator.validate_action(action_intent, self.session)

        if DEBUG_PROMPTS:
            logger.debug(f"🎯 Action Intent: {action_intent}")
            logger.debug(f"✅ Validation: {validation.result.value} - {validation.message}")

        # Step 1.5: For INVALID actions, return deterministic response without calling LLM
        # Small LLMs are bad at following "do not" instructions, so we handle this ourselves
        if validation.result == ValidationResult.INVALID:
            response = self._generate_invalid_action_response(validation)

            # Save to history
            self.message_history.append(Message('player', player_input))
            self.message_history.append(Message('gm', response))
            self.session.add_note(f"Invalid action rejected: {validation.action.action_type.value}")

            return response

        # Step 2: Search RAG if enabled
        if use_rag:
            rag_results = self.search_rag(player_input)
            rag_context = self.format_rag_context(rag_results)

        # Step 3: Build prompt with history, RAG context, and validation guidance
        prompt = self._build_prompt(player_input, rag_context, validation)

        # Step 4: Get LLM response (route based on mode)
        try:
            if self.use_hf_api:
                response = self._query_hf(prompt)
            else:
                response = self._query_ollama(prompt)

            # Step 5: Post-process response (e.g., auto-add NPCs introduced in conversation)
            self._post_process_response(response, validation)

            # Save to history
            self.message_history.append(Message('player', player_input, rag_context if use_rag else None))
            self.message_history.append(Message('gm', response))
            self.session.add_note(f"Player: {player_input[:50]}... | GM: {response[:50]}...")

            return response

        except Exception as e:
            return f"Error generating response: {e}"

    def _build_prompt(self, player_input: str, rag_context: str, validation=None) -> str:
        """
        Build complete prompt for LLM with full game state context.

        Args:
            player_input: Player's action
            rag_context: Retrieved RAG information
            validation: ValidationReport from action validator (optional)
        """

        # Get recent conversation history
        recent_messages = self.message_history[-4:] if len(self.message_history) > 4 else self.message_history
        history_text = "\n".join([
            f"{'Player' if msg.role == 'player' else 'GM'}: {msg.content}"
            for msg in recent_messages
        ])

        # Build game state context
        prompt = f"""You are an experienced Dungeon Master running a D&D 5e game.

CURRENT LOCATION: {self.session.current_location}
SCENE: {self.session.scene_description if self.session.scene_description else "The adventure continues..."}
TIME: Day {self.session.day}, {self.session.time_of_day}
"""

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
                quest_names = [q['name'] for q in active[:2]]  # Show up to 2 active quests
                prompt += f"\nACTIVE QUESTS: {', '.join(quest_names)}\n"

        prompt += "\n"

        if rag_context and rag_context != "No specific rules retrieved." and rag_context != "No highly relevant rules found.":
            prompt += f"""RETRIEVED D&D RULES (Apply these rules accurately):
{rag_context}

"""

        if history_text:
            prompt += f"""RECENT CONVERSATION:
{history_text}

"""

        prompt += f"""PLAYER ACTION: {player_input}

"""

        prompt += """INSTRUCTIONS:
1. Apply D&D 5e rules accurately using the retrieved information
2. Consider the current location, NPCs present, and combat state
3. Ask for appropriate dice rolls (d20 for attacks/checks, damage dice, saves, etc.)
4. Be concise and engaging (2-4 sentences max)
5. Maintain narrative flow while being mechanically precise
6. If rules are unclear, use standard D&D 5e mechanics

"""

        # Add validation guidance RIGHT BEFORE response - most prominent position
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
                # Valid action
                prompt += f"""{validation.message}

GM RESPONSE:"""
        else:
            prompt += """
GM RESPONSE:"""

        return prompt

    def _generate_invalid_action_response(self, validation) -> str:
        """
        Generate a deterministic, character-appropriate response for invalid actions.
        Doesn't call LLM since small models are bad at following "do not" instructions.

        Makes responses colorful and personality-driven - we can be blunt/insulting
        since this is pre-written and not AI-generated!

        Args:
            validation: ValidationReport with invalid result

        Returns:
            GM response narrating the impossibility with personality
        """
        action = validation.action

        # Get character info for personality
        char_name = "You"
        char_race = ""
        char_class = ""
        if hasattr(self.session, 'character_state') and self.session.character_state:
            char_name = getattr(self.session.character_state, 'character_name', 'You')
            char_race = getattr(self.session.character_state, 'race', '').lower()
            char_class = getattr(self.session.character_state, 'character_class', '')

        # Combat-specific responses
        if action.action_type == ActionType.COMBAT:
            # NEW: Check if trying to use a weapon they don't have
            if action.resource:
                # Get what they actually have
                inventory_hint = ""
                if hasattr(self.session, 'character_state') and self.session.character_state:
                    inv = list(self.session.character_state.inventory.keys())[:3]
                    if inv:
                        inventory_hint = f" Ye're carryin': {', '.join(inv)}."

                if char_race == 'dwarf':
                    return (
                        f"Ye reach fer yer {action.resource} to attack, but it's not there! "
                        f"Ye pat down yer belt and check yer pack - nothin'! "
                        f"Can't attack with a weapon ye don't have, ye daft fool!{inventory_hint}"
                    )
                else:
                    return (
                        f"You reach for your {action.resource} to attack, but it's not there. "
                        f"You search your belt and pack, but can't find it.{inventory_hint}"
                    )

            elif action.target:
                # No weapon specified, just invalid target
                if char_race == 'dwarf':
                    return (
                        f"Ye swing yer weapon with all the fury of the mountain halls, but there's nothin' there! "
                        f"No {action.target}, no enemy - just empty air and yer own embarrassment. "
                        f"Bah! Ye're seein' things that aren't there, ye daft fool!"
                    )
                elif char_race == 'elf':
                    return (
                        f"With graceful precision, you strike at... nothing. The {action.target} you imagined "
                        f"exists only in your mind. Perhaps you should meditate more before battle?"
                    )
                else:
                    return (
                        f"You swing your weapon at where you think the {action.target} should be, "
                        f"but there's nothing there. Looking around, you see no enemies - only empty space. "
                        f"Perhaps you heard something that wasn't there?"
                    )
            else:
                if char_race == 'dwarf':
                    return "Ye ready yer weapon and look fer a fight, but there's nothin' to bash! The cavern's quiet as a tomb."
                else:
                    return "You ready your weapon and look for something to fight, but you don't see any enemies nearby."

        # Item use responses
        elif action.action_type == ActionType.ITEM_USE:
            if action.resource:
                # Get what they actually have
                inventory_hint = ""
                if hasattr(self.session, 'character_state') and self.session.character_state:
                    inv = list(self.session.character_state.inventory.keys())[:3]
                    if inv:
                        inventory_hint = f" You're carrying: {', '.join(inv)}."

                if char_race == 'dwarf':
                    return (
                        f"Ye reach fer yer {action.resource}... but it's not in yer pack, ye forgetful oaf! "
                        f"Ye search through yer belongings but come up empty.{inventory_hint} "
                        f"Should've checked before leavin' the tavern!"
                    )
                else:
                    return (
                        f"You reach for your {action.resource}, but it's not there. "
                        f"You search your pack but don't find it.{inventory_hint}"
                    )
            else:
                return "You search through your belongings, trying to find what you need."

        # Spell casting responses - THIS IS WHERE WE CAN BE BLUNT!
        elif action.action_type == ActionType.SPELL_CAST:
            if action.resource:
                if char_class in ['Fighter', 'Barbarian', 'Rogue', 'Monk']:
                    # Be colorfully insulting for non-casters trying to cast spells
                    if char_race == 'dwarf' and char_class == 'Fighter':
                        return (
                            f"Ye try to cast {action.resource}? Are ye daft?! Ye're a FIGHTER, not some fancy-robed wizard! "
                            f"The only magic ye know is the magic of a good axe to the skull! "
                            f"Stop wavin' yer hands around like an idiot and stick to what ye know - FIGHTING!"
                        )
                    elif char_class == 'Barbarian':
                        return (
                            f"You try to cast {action.resource}... *narrator laughs* You're a BARBARIAN, you fool! "
                            f"Your idea of magic is hitting things REALLY hard. The mystical words escape you because "
                            f"you literally don't know any. Stick to raging and smashing!"
                        )
                    elif char_class == 'Rogue':
                        return (
                            f"You attempt to cast {action.resource} with all the magical aptitude of a wet sock. "
                            f"You're a ROGUE - your talents lie in sneaking and stabbing, not spellcasting! "
                            f"The arcane words feel foreign and stupid in your mouth. Maybe stick to your daggers?"
                        )
                    else:
                        return (
                            f"You try to recall the words to cast {action.resource}, "
                            f"but as a {char_class}, you have no magical training. "
                            f"The arcane words escape you. You're not a mage, you idiot!"
                        )
                else:
                    # For actual spellcasters who just don't know the spell
                    return (
                        f"You try to cast {action.resource}, but you don't know that spell. "
                        f"You can't recall the proper incantation or gestures. "
                        f"Maybe study your spellbook next time?"
                    )
            else:
                return "You attempt to channel magical energy, but nothing happens."

        # Generic invalid action
        else:
            if char_race == 'dwarf':
                return "Ye try to do... something, but it ain't workin'. Ye're missin' somethin', or the timin's all wrong!"
            else:
                return (
                    "You attempt the action, but something prevents you from completing it. "
                    "Perhaps you're missing something, or the timing isn't right."
                )

    def _post_process_response(self, response: str, validation) -> None:
        """
        Post-process GM response to update game state.
        Handles NPC auto-introduction and other state updates.

        Args:
            response: GM's response
            validation: ValidationReport from action validation
        """
        # Auto-add NPCs introduced during conversation
        if validation.result == ValidationResult.NPC_INTRODUCTION and validation.action.target:
            npc_name = validation.action.target.title()

            # Check if GM actually introduced the NPC (response isn't a rejection)
            rejection_phrases = [
                "no such", "nobody", "no one", "isn't here", "not present",
                "don't see", "can't find", "nowhere to be found"
            ]

            response_lower = response.lower()
            is_rejection = any(phrase in response_lower for phrase in rejection_phrases)

            if not is_rejection and npc_name not in self.session.npcs_present:
                # GM introduced the NPC, add to game state
                self.session.npcs_present.append(npc_name)
                self.session.add_note(f"NPC introduced in conversation: {npc_name}")

                if DEBUG_PROMPTS:
                    logger.debug(f"🎭 Auto-added NPC to scene: {npc_name}")

    def _query_ollama(self, prompt: str, timeout: int = 120) -> str:
        """
        Send prompt to Ollama and get response (local mode).

        Args:
            prompt: Complete prompt
            timeout: Response timeout in seconds

        Returns:
            Model response
        """
        # Log prompt if debug mode is enabled
        if DEBUG_PROMPTS:
            logger.debug("=" * 80)
            logger.debug("PROMPT SENT TO OLLAMA:")
            logger.debug("-" * 80)
            logger.debug(prompt)
            logger.debug("=" * 80)

        try:
            result = subprocess.run(
                ['ollama', 'run', self.model_name, prompt],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode != 0:
                raise Exception(f"Ollama error: {result.stderr}")

            response = result.stdout.strip()

            # Clean up response (remove prompt echo if present)
            if "GM RESPONSE:" in response:
                response = response.split("GM RESPONSE:")[-1].strip()

            # Log response if debug mode is enabled
            if DEBUG_PROMPTS:
                logger.debug("-" * 80)
                logger.debug("RESPONSE FROM OLLAMA:")
                logger.debug(response)
                logger.debug("=" * 80)

            return response if response else "..."

        except subprocess.TimeoutExpired:
            raise Exception("Response timed out (LLM took too long)")
        except Exception as e:
            raise Exception(f"Ollama query failed: {e}")

    def _query_hf(self, prompt: str, timeout: int = 60) -> str:
        """
        Send prompt to Hugging Face Inference API and get response (HF mode).

        Args:
            prompt: Complete prompt
            timeout: Response timeout in seconds

        Returns:
            Model response
        """
        # Log prompt if debug mode is enabled
        if DEBUG_PROMPTS:
            logger.debug("=" * 80)
            logger.debug("PROMPT SENT TO HUGGING FACE API:")
            logger.debug("-" * 80)
            logger.debug(prompt)
            logger.debug("=" * 80)

        try:
            # Use chat completion API for conversational models
            messages = [{"role": "user", "content": prompt}]

            response = self.client.chat_completion(
                messages=messages,
                model=self.model_name,
                max_tokens=300,
                temperature=0.7,
                top_p=0.9,
            )

            # Extract the response text
            response_text = response.choices[0].message.content.strip()

            # Remove prompt echo if present
            if "GM RESPONSE:" in response_text:
                response_text = response_text.split("GM RESPONSE:")[-1].strip()

            # Log response if debug mode is enabled
            if DEBUG_PROMPTS:
                logger.debug("-" * 80)
                logger.debug("RESPONSE FROM HUGGING FACE API:")
                logger.debug(response_text)
                logger.debug("=" * 80)

            return response_text if response_text else "..."

        except Exception as e:
            raise Exception(f"HF Inference API query failed: {e}")

    def set_context(self, context: str):
        """
        Update current scene/context.

        For backwards compatibility, sets scene_description.
        Use set_location() for more detailed location tracking.
        """
        self.session.scene_description = context
        self.session.add_note(f"Scene updated: {context}")

    def set_location(self, location: str, description: str = ""):
        """Set current location and scene description."""
        self.session.set_location(location, description)

    def add_npc(self, npc_name: str):
        """Add an NPC or monster to the current scene."""
        if npc_name not in self.session.npcs_present:
            self.session.npcs_present.append(npc_name)
            self.session.add_note(f"{npc_name} appeared")

    def remove_npc(self, npc_name: str):
        """Remove an NPC or monster from the current scene."""
        if npc_name in self.session.npcs_present:
            self.session.npcs_present.remove(npc_name)
            self.session.add_note(f"{npc_name} left or was defeated")

    def start_combat(self, initiatives: Dict[str, int]):
        """Start combat with initiative rolls."""
        self.session.combat.start_combat(initiatives)
        self.session.add_note(f"Combat started! Initiative order: {', '.join([f'{n} ({i})' for n, i in self.session.combat.initiative_order])}")

    def end_combat(self):
        """End combat."""
        self.session.combat.end_combat()
        self.session.add_note("Combat ended")

    def add_quest(self, name: str, description: str):
        """Add a quest to the session."""
        self.session.add_quest(name, description)
        self.session.add_note(f"New quest: {name}")

    def get_session_summary(self) -> str:
        """Get comprehensive session summary."""
        return self.session.get_session_summary()
