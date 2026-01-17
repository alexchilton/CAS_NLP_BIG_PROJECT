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
import random
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
from dnd_rag_system.systems.shop_system import ShopSystem
from dnd_rag_system.systems.combat_manager import CombatManager
from dnd_rag_system.systems.mechanics_extractor import MechanicsExtractor
from dnd_rag_system.systems.mechanics_applicator import MechanicsApplicator
from dnd_rag_system.systems.encounter_system import EncounterSystem
from dnd_rag_system.systems.spell_manager import SpellManager
from dnd_rag_system.constants import Commands, ActionKeywords

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
    timestamp: Optional[str] = None  # For tracking when message occurred


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
        self.message_history: List[Message] = []  # Active conversation history
        self.conversation_summary: str = ""  # Compressed summary of older messages
        self.action_validator = ActionValidator(debug=DEBUG_PROMPTS)  # Reality check system
        self.shop = ShopSystem(db_manager, debug=DEBUG_PROMPTS)  # Shop transaction system
        self.spell_manager = SpellManager(db_manager)  # Spell and resource management
        self.combat_manager = CombatManager(self.session.combat, spell_manager=self.spell_manager, debug=DEBUG_PROMPTS)  # Combat system with XP tracking

        # Narrative to Mechanics Translation System
        self.mechanics_extractor = MechanicsExtractor(debug=DEBUG_PROMPTS)
        self.mechanics_applicator = MechanicsApplicator(debug=DEBUG_PROMPTS)

        # Random Encounter System
        self.encounter_system = EncounterSystem(chromadb_manager=db_manager)

        # Initialize world map with starting locations
        from dnd_rag_system.systems.world_builder import initialize_world
        initialize_world(self.session)

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

    def _prune_message_history(self):
        """
        Prune message history to prevent context window overflow.
        Keeps recent messages and creates summary of older ones.
        Uses more aggressive pruning for party mode.
        """
        from dnd_rag_system.config.settings import MAX_MESSAGE_HISTORY, SUMMARIZE_EVERY_N_MESSAGES
        
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
        summary_text = self._create_message_summary(old_messages)
        
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

    def _create_message_summary(self, messages: List[Message]) -> str:
        """
        Create a concise summary of message exchanges.
        Focuses on key events: combat, quests, important discoveries.
        
        Args:
            messages: List of messages to summarize
            
        Returns:
            Summary text
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
                    # Condensed combat outcome
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
        transaction_feedback = ""
        combat_feedback = ""

        # Step 0: Check if player is unconscious and prevent actions
        if self.session.character_state:
            from dnd_rag_system.systems.game_state import Condition
            if Condition.UNCONSCIOUS.value in self.session.character_state.conditions:
                # Only allow certain commands while unconscious
                allowed_commands = Commands.unconscious_allowed_commands()
                if not any(player_input.lower().strip().startswith(cmd) for cmd in allowed_commands):
                    return """⚠️ **You are unconscious and cannot take actions!**

You have fallen unconscious (0 HP). According to D&D 5e rules:
- You cannot move, speak, or take any actions
- Enemies may continue attacking you
- You must make death saving throws

**What you can do:**
- Type `/death_save` to make a death saving throw (not yet implemented)
- Type `/stats` to see your character condition
- Wait for healing from allies or stabilization

*Note: Death saving throw system coming soon. For now, ask GM for healing or revival.*"""

        # Step -1: Combat Command Processing
        # Handle combat commands like /start_combat, /next_turn, /end_combat, /initiative
        combat_command_handled = False
        lower_input = player_input.lower().strip()

        if lower_input.startswith(Commands.START_COMBAT):
            # Parse NPCs from command: /start_combat Goblin, Orc, Dragon
            npc_list = []
            if ' ' in player_input:
                npc_text = player_input.split(' ', 1)[1]
                npc_list = [npc.strip() for npc in npc_text.split(',')]

            # Use existing NPCs if no list provided
            if not npc_list:
                npc_list = self.session.npcs_present

            if npc_list:
                # Start combat with party or single character
                if self.session.party and len(self.session.party.characters) > 0:
                    combat_feedback = self.combat_manager.start_combat_with_party(
                        self.session.party,
                        npc_list
                    )
                elif self.session.character_state:
                    combat_feedback = self.combat_manager.start_combat_with_character(
                        self.session.character_state,
                        npc_list
                    )
                else:
                    combat_feedback = "⚠️ No character or party loaded!"

                # Add NPCs to session so they can be targeted by action validator
                for npc in npc_list:
                    if npc not in self.session.npcs_present:
                        self.session.npcs_present.append(npc)
                        if DEBUG_PROMPTS:
                            logger.debug(f"🎭 Added {npc} to npcs_present for combat targeting")

                # IMPORTANT: If combat starts with an NPC's turn, process NPC turns immediately
                current_turn = self.combat_manager.get_current_turn_name()
                if current_turn and current_turn in self.combat_manager.npc_monsters:
                    # Get player AC for NPC targeting
                    target_ac = 15  # Default
                    if self.session.character_state and hasattr(self.session.character_state, 'armor_class'):
                        target_ac = self.session.character_state.armor_class
                    elif self.session.party and len(self.session.party.characters) > 0:
                        first_char = list(self.session.party.characters.values())[0]
                        if hasattr(first_char, 'armor_class'):
                            target_ac = first_char.armor_class

                    # Process all NPC turns (damage is applied inside process_npc_turns)
                    npc_actions = self.combat_manager.process_npc_turns(
                        target_ac,
                        target_character=self.session.character_state,
                        target_party=self.session.party
                    )

                    if npc_actions:
                        combat_feedback += "\n\n**🐉 NPC ACTIONS:**\n" + "\n\n".join(npc_actions)

            else:
                combat_feedback = "⚠️ No NPCs specified for combat! Use: `/start_combat Goblin, Orc` or add NPCs with add_npc() first."

            combat_command_handled = True

        elif lower_input in ['/next_turn', '/next']:
            combat_feedback = self.combat_manager.advance_turn()
            combat_command_handled = True

        elif lower_input in ['/flee', '/run', '/escape']:
            # Attempt to flee from combat
            if not self.combat_manager.is_in_combat():
                combat_feedback = "⚠️ Not in combat! Nothing to flee from."
            else:
                # Get character's DEX modifier for flee check
                dex_mod = 0
                if self.session.character_state:
                    # Single character mode - get DEX from base stats
                    char_name = self.session.character_state.character_name
                    if char_name in self.session.base_character_stats:
                        base_char = self.session.base_character_stats[char_name]
                        dex_mod = base_char.get_ability_modifier(base_char.dexterity)

                # Roll flee check (d20 + DEX modifier)
                flee_roll = random.randint(1, 20)
                flee_total = flee_roll + dex_mod

                # DC based on number of enemies (10 + number of enemies)
                num_enemies = len(self.combat_manager.npc_monsters)
                flee_dc = 10 + num_enemies

                if flee_total >= flee_dc:
                    # SUCCESS! Escape combat
                    combat_feedback = f"🏃 **FLEE SUCCESSFUL!**\n\n"
                    combat_feedback += f"Flee Check: {flee_roll} + {dex_mod} (DEX) = {flee_total} vs DC {flee_dc}\n\n"

                    # Store current location and NPCs before fleeing
                    old_location = self.session.current_location
                    fled_from_npcs = list(self.session.npcs_present)

                    # Add NPCs as resident enemies at this location (they stay here)
                    current_loc = self.session.get_current_location_obj()
                    if current_loc:
                        for npc in fled_from_npcs:
                            if npc not in current_loc.resident_npcs:
                                current_loc.resident_npcs.append(npc)
                        if DEBUG_PROMPTS:
                            logger.debug(f"🏃 NPCs remaining at {old_location}: {fled_from_npcs}")

                    # End combat without XP
                    end_msg, dead_npcs = self.combat_manager.end_combat()

                    # Clear NPCs from current scene (you fled away from them)
                    self.session.npcs_present.clear()

                    # Find a nearby location to flee to
                    available_destinations = self.session.get_available_destinations()

                    if available_destinations:
                        # Flee to a random connected location
                        flee_destination = random.choice(available_destinations)
                        success, travel_msg = self.session.travel_to(flee_destination)

                        combat_feedback += f"You flee from {old_location} and run to **{flee_destination}**!\n\n"
                        combat_feedback += f"⚠️ **The enemies remain at {old_location}** - they may still be there if you return!\n\n"
                        combat_feedback += end_msg
                    else:
                        # No connected locations - just end combat and stay here
                        combat_feedback += f"You manage to break away from combat!\n\n"
                        combat_feedback += f"⚠️ **The enemies are still nearby** - they may pursue or wait for you!\n\n"
                        combat_feedback += end_msg
                else:
                    # FAILURE! Take opportunity attack damage
                    opp_attack_damage = random.randint(1, 6) * num_enemies  # Simple damage

                    combat_feedback = f"🏃 **FLEE FAILED!**\n\n"
                    combat_feedback += f"Flee Check: {flee_roll} + {dex_mod} (DEX) = {flee_total} vs DC {flee_dc}\n\n"
                    combat_feedback += f"You try to flee but the enemies strike as you run!\n\n"
                    combat_feedback += f"💥 You take {opp_attack_damage} damage from opportunity attacks!\n\n"

                    # Apply damage to character
                    if self.session.character_state:
                        damage_result = self.session.character_state.take_damage(opp_attack_damage, "slashing")
                        combat_feedback += damage_result['message'] + "\n\n"

                    combat_feedback += "Combat continues! (Try fleeing again or fight)"

            combat_command_handled = True

        elif lower_input == Commands.END_COMBAT:
            # Award XP before ending combat
            xp_feedback = ""

            if self.combat_manager.get_total_combat_xp() > 0:
                # Get defeated enemies summary
                enemies_summary = self.combat_manager.get_defeated_enemies_summary()

                # Award XP to character or party
                if self.session.party and len(self.session.party.characters) > 0:
                    # Party mode - distribute XP among party
                    xp_results = self.combat_manager.award_xp_to_party(self.session.party)

                    xp_feedback = f"\n\n💰 **VICTORY REWARDS**\n\n{enemies_summary}\n\n**XP Awards:**\n"
                    for char_name, result in xp_results.items():
                        xp_gained = result.get('xp_gained', 0)
                        xp_feedback += f"- {char_name}: +{xp_gained} XP"

                        if result.get('leveled_up'):
                            new_level = result.get('new_level', 0)
                            xp_feedback += f" 🎉 **LEVEL UP!** Now level {new_level}!"

                        xp_feedback += "\n"

                elif self.session.character_state:
                    # Single character mode
                    xp_result = self.combat_manager.award_xp_to_character(self.session.character_state)

                    xp_feedback = f"\n\n💰 **VICTORY REWARDS**\n\n{enemies_summary}\n\n"
                    xp_feedback += f"✨ {xp_result['message']}"

                    if xp_result.get('leveled_up'):
                        # Auto-level up! Get character info and call level_up()
                        char_name = self.session.character_state.character_name
                        if char_name in self.session.base_character_stats:
                            base_char = self.session.base_character_stats[char_name]
                            character_class = base_char.character_class

                            # Determine hit die size based on class
                            HIT_DIE_BY_CLASS = {
                                "Barbarian": 12,
                                "Fighter": 10, "Paladin": 10, "Ranger": 10,
                                "Bard": 8, "Cleric": 8, "Druid": 8, "Monk": 8, "Rogue": 8, "Warlock": 8,
                                "Sorcerer": 6, "Wizard": 6
                            }
                            hit_die_size = HIT_DIE_BY_CLASS.get(character_class, 8)
                            con_modifier = base_char.get_ability_modifier(base_char.constitution)

                            # Automatically level up!
                            level_up_result = self.session.character_state.level_up(character_class, hit_die_size, con_modifier)

                            if level_up_result['success']:
                                xp_feedback += f"\n\n🎉 **LEVEL UP!** You are now level {level_up_result['new_level']}!\n\n"
                                xp_feedback += f"**Hit Points:**\n"
                                xp_feedback += f"- Rolled {level_up_result['hp_roll']} on d{hit_die_size}\n"
                                xp_feedback += f"- CON modifier: +{con_modifier}\n"
                                xp_feedback += f"- HP gained: +{level_up_result['hp_increase']}\n"
                                xp_feedback += f"- New Max HP: {level_up_result['new_max_hp']}\n\n"

                                if level_up_result['prof_bonus_increased']:
                                    xp_feedback += f"**Proficiency Bonus:** +{level_up_result['proficiency_bonus']} (increased!)\n\n"

                                # Show spell slot upgrades if applicable
                                if level_up_result['spell_slots_updated'] and level_up_result['new_spell_slots']:
                                    xp_feedback += f"**Spell Slots Upgraded:**\n"
                                    slot_display = ", ".join([f"L{lvl}: {curr}/{max_}" for lvl, (curr, max_) in level_up_result['new_spell_slots'].items()])
                                    xp_feedback += f"{slot_display}\n\n"

                                if DEBUG_PROMPTS:
                                    logger.debug(f"🎉 Auto-leveled up: {char_name} L{level_up_result['old_level']} → L{level_up_result['new_level']}")
                        else:
                            # Fallback: just show basic message if we can't auto-level
                            new_level = xp_result.get('new_level', 0)
                            xp_feedback += f"\n\n🎉 **LEVEL UP!** You are now level {new_level}!\n\n💡 *Type `/level_up` to roll for HP and upgrade spell slots*"

            # End combat (this clears defeated_enemies tracking and returns dead NPCs)
            combat_feedback, dead_npcs = self.combat_manager.end_combat()

            # Remove dead NPCs from session's npcs_present list (FIX: prevents targeting corpses)
            for dead_npc in dead_npcs:
                if dead_npc in self.session.npcs_present:
                    self.session.npcs_present.remove(dead_npc)

            # Add XP feedback if any
            if xp_feedback:
                combat_feedback += xp_feedback

            combat_command_handled = True

        elif lower_input == Commands.INITIATIVE:
            if self.session.party and len(self.session.party.characters) > 0:
                combat_feedback = self.combat_manager.get_initiative_tracker(self.session.party)
            else:
                combat_feedback = self.combat_manager.get_initiative_tracker()
            combat_command_handled = True

        elif lower_input.startswith('/use '):
            # Parse item name from command: /use healing potion
            item_name = player_input.split(' ', 1)[1].strip() if ' ' in player_input else ""

            if not item_name:
                combat_feedback = "⚠️ Usage: `/use <item>` (e.g., `/use healing potion`)"
                combat_command_handled = True
            elif not self.session.character_state:
                combat_feedback = "⚠️ No character state loaded!"
                combat_command_handled = True
            else:
                # Check if item is in inventory
                has_item = self.session.character_state.has_item(item_name, 1)

                if not has_item:
                    # List inventory for convenience
                    inv_list = ", ".join(list(self.session.character_state.inventory.keys())[:5]) if self.session.character_state.inventory else "empty"
                    combat_feedback = f"⚠️ You don't have '{item_name}' in your inventory.\n\nYour inventory: {inv_list}"
                    combat_command_handled = True
                else:
                    # Try to use as potion
                    potion_result = self.spell_manager.use_potion(item_name)

                    if potion_result["success"]:
                        # Apply healing
                        healing_amount = potion_result["amount"]
                        heal_result = self.session.character_state.heal(healing_amount)

                        # Remove item from inventory
                        self.session.character_state.remove_item(item_name, 1)

                        # Format response
                        combat_feedback = f"🧪 **{potion_result['message']}**\n\n"
                        combat_feedback += f"✨ {heal_result['message']}"

                        if DEBUG_PROMPTS:
                            logger.debug(f"🧪 Used {item_name}: {potion_result['dice_formula']} = {potion_result['rolls']} = {healing_amount} HP")
                    else:
                        # Not a recognized potion - generic use
                        combat_feedback = f"You use {item_name}, but nothing special happens. (Not a recognized potion)"
                        # Still remove from inventory
                        self.session.character_state.remove_item(item_name, 1)

                    combat_command_handled = True

        elif lower_input.startswith('/pickup '):
            # Parse item name from command: /pickup healing potion
            item_name = player_input.split(' ', 1)[1].strip() if ' ' in player_input else ""

            if not item_name:
                combat_feedback = "⚠️ Usage: `/pickup <item>` (e.g., `/pickup healing potion`)"
                combat_command_handled = True
            elif not self.session.character_state:
                combat_feedback = "⚠️ No character state loaded!"
                combat_command_handled = True
            else:
                # Get current location
                current_loc = self.session.get_current_location_obj()

                if not current_loc:
                    combat_feedback = "⚠️ No location information available."
                    combat_command_handled = True
                elif not current_loc.has_item(item_name):
                    # List available items for convenience
                    available = ", ".join(current_loc.available_items[:5]) if current_loc.available_items else "nothing"
                    combat_feedback = f"⚠️ '{item_name}' is not here.\n\nYou see: {available}"
                    combat_command_handled = True
                else:
                    # Move item from location to character inventory
                    current_loc.remove_item(item_name, moved_to="inventory")
                    self.session.character_state.add_item(item_name, 1)

                    combat_feedback = f"✅ Picked up **{item_name}**"
                    combat_command_handled = True

        elif lower_input == Commands.DEATH_SAVE:
            # Death saving throw
            if not self.session.character_state:
                combat_feedback = "⚠️ No character state loaded!"
                combat_command_handled = True
            elif self.session.character_state.is_conscious():
                combat_feedback = "⚠️ You are not unconscious! Death saving throws are only for unconscious characters (0 HP)."
                combat_command_handled = True
            else:
                # Roll d20 for death saving throw
                roll = random.randint(1, 20)

                combat_feedback = f"🎲 **Death Saving Throw**: Rolled **{roll}**\n\n"

                # Handle critical rolls first
                if roll == 20:
                    # Natural 20: Regain 1 HP and stabilize
                    self.session.character_state.current_hp = 1
                    self.session.character_state.death_saves.reset()
                    combat_feedback += "🌟 **Natural 20!** You regain 1 HP and regain consciousness!\n\n"
                    combat_feedback += f"✅ You are now at **1/{self.session.character_state.max_hp} HP**"
                elif roll == 1:
                    # Natural 1: Count as 2 failures
                    dead, msg1 = self.session.character_state.death_saves.add_failure()
                    if not dead:
                        dead, msg2 = self.session.character_state.death_saves.add_failure()
                        combat_feedback += f"💀 **Natural 1!** That counts as **2 failures**!\n\n"
                        combat_feedback += f"❌ {msg2}"
                        if dead:
                            combat_feedback += "\n\n☠️ **YOU HAVE DIED** ☠️"
                    else:
                        combat_feedback += f"💀 **Natural 1!** {msg1}\n\n☠️ **YOU HAVE DIED** ☠️"
                elif roll >= 10:
                    # Success
                    stabilized, msg = self.session.character_state.death_saves.add_success()
                    combat_feedback += f"✅ **Success!** {msg}"
                    if stabilized:
                        combat_feedback += "\n\n🛡️ You are **stabilized** at 0 HP (no longer dying, but still unconscious)."
                else:
                    # Failure
                    dead, msg = self.session.character_state.death_saves.add_failure()
                    combat_feedback += f"❌ **Failure!** {msg}"
                    if dead:
                        combat_feedback += "\n\n☠️ **YOU HAVE DIED** ☠️"

                # Show current death save status (unless dead or stabilized)
                if self.session.character_state.current_hp == 0 and not self.session.character_state.death_saves.is_dead():
                    if not self.session.character_state.death_saves.is_stable():
                        combat_feedback += f"\n\n**Death Saves**: "
                        combat_feedback += f"✅ {self.session.character_state.death_saves.successes}/3 | "
                        combat_feedback += f"❌ {self.session.character_state.death_saves.failures}/3"

                combat_command_handled = True

        elif lower_input in ['/rest', '/short_rest']:
            # Short rest - spend hit dice to heal
            if not self.session.character_state:
                combat_feedback = "⚠️ No character state loaded!"
                combat_command_handled = True
            else:
                char_state = self.session.character_state

                # Check if character has hit dice to spend
                if char_state.hit_dice_current <= 0:
                    combat_feedback = f"⚠️ You have no hit dice remaining!\n\n"
                    combat_feedback += f"Hit Dice: {char_state.hit_dice_current}/{char_state.hit_dice_max}\n\n"
                    combat_feedback += f"You need a long rest to recover hit dice."
                    combat_command_handled = True
                elif char_state.current_hp >= char_state.max_hp:
                    combat_feedback = f"⚠️ You're already at full HP ({char_state.current_hp}/{char_state.max_hp})!\n\n"
                    combat_feedback += f"Short rests are primarily for healing. You don't need one right now."
                    combat_command_handled = True
                else:
                    # Spend 1 hit die to heal
                    rest_result = char_state.short_rest(hit_dice_spent=1)

                    combat_feedback = f"🛏️ **Short Rest (1 hour)**\n\n"
                    combat_feedback += f"{rest_result['message']}\n\n"
                    combat_feedback += f"**Current Status:**\n"
                    combat_feedback += f"- HP: {char_state.current_hp}/{char_state.max_hp}\n"
                    combat_feedback += f"- Hit Dice: {char_state.hit_dice_current}/{char_state.hit_dice_max}\n\n"
                    combat_feedback += f"💡 *You can take another short rest if needed, or `/long_rest` to fully recover.*"

                    if DEBUG_PROMPTS:
                        logger.debug(f"🛏️ Short rest: {rest_result['hit_dice_spent']} hit dice spent, {rest_result['hp_restored']} HP restored")

                    combat_command_handled = True

        elif lower_input in ['/long_rest', '/longrest']:
            # Long rest - restore all HP, spell slots, and half of hit dice
            if not self.session.character_state:
                combat_feedback = "⚠️ No character state loaded!"
                combat_command_handled = True
            else:
                char_state = self.session.character_state

                # Perform long rest
                rest_result = char_state.long_rest()

                combat_feedback = f"🌙 **Long Rest (8 hours)**\n\n"
                combat_feedback += f"{rest_result['message']}\n\n"
                combat_feedback += f"**Fully Restored:**\n"
                combat_feedback += f"- HP: {char_state.current_hp}/{char_state.max_hp} ✓\n"
                combat_feedback += f"- Hit Dice: {char_state.hit_dice_current}/{char_state.hit_dice_max} (+{rest_result['hit_dice_restored']})\n"

                # Show spell slots if character has any
                available_slots = char_state.spell_slots.get_available()
                if available_slots:
                    combat_feedback += f"- Spell Slots: Fully restored ✓\n"
                    slot_display = ", ".join([f"L{lvl}: {curr}/{max_}" for lvl, (curr, max_) in available_slots.items()])
                    combat_feedback += f"  ({slot_display})\n"

                combat_feedback += f"\n✨ *You feel refreshed and ready for adventure!*"

                if DEBUG_PROMPTS:
                    logger.debug(f"🌙 Long rest: {rest_result['hp_restored']} HP restored, {rest_result['hit_dice_restored']} hit dice restored, spell slots recharged")

                combat_command_handled = True

        elif lower_input in ['/level_up', '/levelup']:
            # Level up character with HP increase and spell slot upgrades
            if not self.session.character_state:
                combat_feedback = "⚠️ No character state loaded!"
                combat_command_handled = True
            else:
                char_state = self.session.character_state
                char_name = char_state.character_name

                # Get base character stats for class and hit die info
                if char_name not in self.session.base_character_stats:
                    combat_feedback = "⚠️ Character base stats not found!"
                    combat_command_handled = True
                else:
                    base_char = self.session.base_character_stats[char_name]
                    character_class = base_char.character_class

                    # Determine hit die size based on class
                    HIT_DIE_BY_CLASS = {
                        "Barbarian": 12,
                        "Fighter": 10, "Paladin": 10, "Ranger": 10,
                        "Bard": 8, "Cleric": 8, "Druid": 8, "Monk": 8, "Rogue": 8, "Warlock": 8,
                        "Sorcerer": 6, "Wizard": 6
                    }
                    hit_die_size = HIT_DIE_BY_CLASS.get(character_class, 8)

                    # Calculate CON modifier
                    con_modifier = base_char.get_ability_modifier(base_char.constitution)

                    # Attempt level up
                    level_up_result = char_state.level_up(character_class, hit_die_size, con_modifier)

                    if level_up_result['success']:
                        # Build success message
                        combat_feedback = f"🎉 **LEVEL UP!**\n\n"
                        combat_feedback += f"**{char_name}** advances to level {level_up_result['new_level']}!\n\n"

                        combat_feedback += f"**Hit Points:**\n"
                        combat_feedback += f"- Rolled {level_up_result['hp_roll']} on d{hit_die_size}\n"
                        combat_feedback += f"- CON modifier: +{con_modifier}\n"
                        combat_feedback += f"- HP gained: +{level_up_result['hp_increase']}\n"
                        combat_feedback += f"- New Max HP: {level_up_result['new_max_hp']}\n\n"

                        if level_up_result['prof_bonus_increased']:
                            combat_feedback += f"**Proficiency Bonus:** +{level_up_result['proficiency_bonus']} (increased!)\n\n"
                        else:
                            combat_feedback += f"**Proficiency Bonus:** +{level_up_result['proficiency_bonus']}\n\n"

                        # Show spell slot upgrades if applicable
                        if level_up_result['spell_slots_updated'] and level_up_result['new_spell_slots']:
                            combat_feedback += f"**Spell Slots Upgraded:**\n"
                            slot_display = ", ".join([f"L{lvl}: {curr}/{max_}" for lvl, (curr, max_) in level_up_result['new_spell_slots'].items()])
                            combat_feedback += f"{slot_display}\n\n"

                        combat_feedback += f"✨ *Congratulations! You're now level {level_up_result['new_level']}!*"

                        if DEBUG_PROMPTS:
                            logger.debug(f"🎉 Level up: {char_name} L{level_up_result['old_level']} → L{level_up_result['new_level']}, HP +{level_up_result['hp_increase']}")
                    else:
                        # Not enough XP
                        combat_feedback = f"⚠️ {level_up_result['message']}\n\n"
                        combat_feedback += f"**Current Status:**\n"
                        combat_feedback += f"- Level: {char_state.level}\n"
                        combat_feedback += f"- XP: {char_state.experience_points}\n"
                        combat_feedback += f"- XP for next level: {char_state.level * 1000}\n\n"
                        combat_feedback += f"💡 *Defeat more enemies to gain XP!*"

                    combat_command_handled = True

        elif lower_input.startswith('/cast '):
            # Cast a spell: /cast <spell> or /cast <spell> on <target>
            # Parse spell name and target
            cmd_parts = player_input.split(' ', 1)[1].strip() if ' ' in player_input else ""

            if not cmd_parts:
                combat_feedback = "⚠️ Usage: `/cast <spell>` or `/cast <spell> on <target>` (e.g., `/cast cure wounds on Thorin`)"
                combat_command_handled = True
            else:
                # Parse "spell on target" or just "spell"
                spell_name = cmd_parts
                target_name = None

                if ' on ' in cmd_parts.lower():
                    parts = cmd_parts.split(' on ', 1)
                    spell_name = parts[0].strip()
                    target_name = parts[1].strip().title()  # Capitalize target name

                # Determine caster (single character or party member)
                caster_state = None
                caster_name = None

                if self.session.party and len(self.session.party.characters) > 0:
                    # Party mode - need to know who's casting
                    # For now, use first character or extract from input
                    # TODO: Better handling for "Elara casts cure wounds on Thorin"
                    if self.session.character_state:
                        caster_state = self.session.character_state
                        caster_name = caster_state.character_name
                    else:
                        # Use first party member
                        caster_name = list(self.session.party.characters.keys())[0]
                        caster_state = self.session.party.characters[caster_name]
                elif self.session.character_state:
                    caster_state = self.session.character_state
                    caster_name = caster_state.character_name
                else:
                    combat_feedback = "⚠️ No character state loaded!"
                    combat_command_handled = True

                if caster_state:
                    # Check if caster knows this spell (check base character stats)
                    knows_spell = False
                    if caster_name in self.session.base_character_stats:
                        base_char = self.session.base_character_stats[caster_name]
                        if hasattr(base_char, 'spells') and base_char.spells:
                            # Case-insensitive spell check
                            spell_lower = spell_name.lower()
                            for known_spell in base_char.spells:
                                if known_spell.lower() == spell_lower:
                                    spell_name = known_spell  # Use correct casing
                                    knows_spell = True
                                    break

                    if not knows_spell:
                        combat_feedback = f"⚠️ {caster_name} doesn't know the spell '{spell_name}'."
                        combat_command_handled = True
                    else:
                        # Look up spell level
                        spell_level = self.spell_manager.lookup_spell_level(spell_name)

                        if spell_level is None:
                            combat_feedback = f"⚠️ Could not find spell level for '{spell_name}' in RAG database."
                            combat_command_handled = True
                        else:
                            # Check if cantrip (level 0)
                            if spell_level == 0:
                                # Cantrips don't consume spell slots
                                # Look up target type to determine if it's healing
                                target_type = self.spell_manager.lookup_spell_target_type(spell_name)

                                if target_type in ["ally", "self"]:
                                    # Try to cast as healing spell
                                    healing_result = self.spell_manager.cast_healing_spell(
                                        spell_name,
                                        caster_name,
                                        target_name or caster_name,
                                        spell_level=0
                                    )

                                    if healing_result["success"]:
                                        # Apply healing to target
                                        target_char = None
                                        if target_name and self.session.party:
                                            target_char = self.session.party.get_character(target_name)
                                        elif not target_name:
                                            target_char = caster_state

                                        if target_char:
                                            heal_result = target_char.heal(healing_result["amount"])
                                            combat_feedback = f"✨ **{healing_result['message']}**\n"
                                            combat_feedback += f"{heal_result['message']}\n\n"
                                            combat_feedback += f"💡 *{spell_name} is a cantrip (no spell slot consumed)*"
                                        else:
                                            combat_feedback = f"⚠️ Target '{target_name}' not found in party."
                                    else:
                                        combat_feedback = healing_result["message"]
                                else:
                                    # Damage/utility cantrip - just acknowledge
                                    combat_feedback = f"✨ {caster_name} casts {spell_name} (cantrip)!"
                                    combat_feedback += f"\n\n💡 *Cantrips don't consume spell slots*"

                                combat_command_handled = True
                            else:
                                # Leveled spell - check spell slot availability
                                if not caster_state.spell_slots.has_slot(spell_level):
                                    available_slots = caster_state.spell_slots.get_available()
                                    slot_display = ", ".join([f"L{lvl}: {curr}/{max_}" for lvl, (curr, max_) in available_slots.items()]) if available_slots else "none"

                                    combat_feedback = f"⚠️ {caster_name} has no level {spell_level} spell slots remaining!\n\n"
                                    combat_feedback += f"**Available Spell Slots:** {slot_display}"
                                    combat_command_handled = True
                                else:
                                    # Determine target type
                                    target_type = self.spell_manager.lookup_spell_target_type(spell_name)

                                    if target_type in ["ally", "self"]:
                                        # Healing/buff spell - apply effect
                                        healing_result = self.spell_manager.cast_healing_spell(
                                            spell_name,
                                            caster_name,
                                            target_name or caster_name,
                                            spell_level=spell_level
                                        )

                                        if healing_result["success"]:
                                            # Consume spell slot
                                            cast_result = caster_state.cast_spell(spell_level, spell_name)

                                            # Apply healing to target
                                            target_char = None
                                            if target_name:
                                                if self.session.party:
                                                    target_char = self.session.party.get_character(target_name)
                                                elif target_name.lower() == caster_name.lower():
                                                    target_char = caster_state
                                            else:
                                                target_char = caster_state

                                            if target_char:
                                                heal_result = target_char.heal(healing_result["amount"])

                                                combat_feedback = f"✨ **{healing_result['message']}**\n\n"
                                                combat_feedback += f"{heal_result['message']}\n\n"
                                                combat_feedback += f"**Spell Slot Used:** Level {spell_level} ({cast_result['remaining_slots']} remaining)"

                                                if DEBUG_PROMPTS:
                                                    logger.debug(f"✨ {caster_name} cast {spell_name}: {healing_result['dice_formula']} = {healing_result['amount']} HP to {target_name or caster_name}")
                                            else:
                                                combat_feedback = f"⚠️ Target '{target_name}' not found."
                                        else:
                                            combat_feedback = healing_result["message"]

                                        combat_command_handled = True
                                    else:
                                        # Damage/utility spell - consume slot but let GM narrate effect
                                        cast_result = caster_state.cast_spell(spell_level, spell_name)

                                        target_display = f" at {target_name}" if target_name else ""
                                        combat_feedback = f"✨ {caster_name} casts **{spell_name}**{target_display}!\n\n"
                                        combat_feedback += f"**Spell Slot Used:** Level {spell_level} ({cast_result['remaining_slots']} remaining)\n\n"
                                        combat_feedback += f"💡 *The GM will narrate the spell's effect*"

                                        if DEBUG_PROMPTS:
                                            logger.debug(f"✨ {caster_name} cast {spell_name} (level {spell_level}) at {target_name or 'no target'}")

                                        combat_command_handled = True

        # World navigation commands
        elif lower_input.startswith('/travel '):
            destination = player_input.split(' ', 1)[1].strip()
            success, message = self.session.travel_to(destination)
            combat_feedback = f"🗺️ {message}"
            combat_command_handled = True

        elif lower_input == Commands.MAP:
            # Show world map - current location + discovered locations
            current_loc = self.session.get_current_location_obj()
            discovered = self.session.get_discovered_locations()
            
            if current_loc:
                combat_feedback = f"🗺️ **WORLD MAP**\n\n"
                combat_feedback += f"📍 **Current Location**: {self.session.current_location}\n"
                combat_feedback += f"   {current_loc.description[:100]}...\n\n"
                
                # Show connections from current location
                destinations = self.session.get_available_destinations()
                if destinations:
                    combat_feedback += f"**🧭 You can travel to**:\n"
                    for dest in destinations:
                        dest_loc = self.session.get_location(dest)
                        if dest_loc and dest_loc.is_discovered:
                            safe_marker = "✅" if dest_loc.is_safe else "⚔️"
                            combat_feedback += f"  {safe_marker} {dest} ({dest_loc.location_type.value})\n"
                        elif dest_loc:
                            combat_feedback += f"  ❓ ??? (undiscovered area)\n"
                    combat_feedback += f"\n"
                
                # Show all discovered locations
                if discovered and len(discovered) > 1:
                    combat_feedback += f"**🌍 All Discovered Locations** ({len(discovered)}):\n"
                    for loc_name in sorted(discovered):
                        loc = self.session.get_location(loc_name)
                        if loc:
                            current_marker = "👉" if loc_name == self.session.current_location else "  "
                            safe_marker = "✅" if loc.is_safe else "⚔️"
                            visits = f" [{loc.visit_count}x]" if loc.visit_count > 1 else ""
                            combat_feedback += f"{current_marker} {safe_marker} {loc_name} ({loc.location_type.value}){visits}\n"
                
                combat_feedback += f"\n💡 Use `/travel <location>` to move, `/explore` to discover new areas."
            else:
                combat_feedback = "📍 Current location not found in world map."
            combat_command_handled = True

        elif lower_input == Commands.LOCATIONS:
            discovered = self.session.get_discovered_locations()
            if discovered:
                combat_feedback = "🗺️ **Discovered Locations**:\n"
                for loc_name in discovered:
                    loc = self.session.get_location(loc_name)
                    if loc:
                        visits = f" (visited {loc.visit_count}x)" if loc.visit_count > 1 else ""
                        combat_feedback += f"  - {loc_name} ({loc.location_type.value}){visits}\n"
            else:
                combat_feedback = "🗺️ No locations discovered yet."
            combat_command_handled = True

        # Discovery Triggers (Natural Language Exploration)
        discovery_triggers = ['find a new path', 'explore further', 'venture out', 'leave this area', 'find new location', '/explore', '/search']
        is_discovery_action = any(phrase in lower_input for phrase in discovery_triggers)

        if is_discovery_action:
            # Lazy location generation with LLM-enhanced descriptions
            current_loc = self.session.get_current_location_obj()
            if current_loc:
                # Check if we already have too many connections from this location
                # Maximum 12 connections per location to avoid overwhelming the player
                if len(current_loc.connections) >= 12:
                    combat_feedback = "🔍 You search the area but find no new paths. All routes from here have been explored."
                else:
                    from dnd_rag_system.systems.world_builder import generate_llm_enhanced_location
                    
                    # Build game context for LLM
                    game_context = {
                        'npcs_present': self.session.npcs_present,
                        'defeated_enemies': current_loc.defeated_enemies if current_loc.defeated_enemies else set(),
                        'time_of_day': self.session.time_of_day,
                        'day': self.session.day
                    }
                    
                    # LLM wrapper function - uses existing LLM setup
                    def llm_generate(prompt: str) -> str:
                        """Call LLM with location generation prompt."""
                        try:
                            response = self.llm.invoke(prompt)
                            if hasattr(response, 'content'):
                                return response.content
                            return str(response)
                        except Exception as e:
                            logger.error(f"LLM call failed in location generation: {e}")
                            return ""  # Will trigger fallback in generate_llm_enhanced_location
                    
                    # Generate location with LLM enhancement
                    new_location = generate_llm_enhanced_location(
                        from_location=current_loc,
                        llm_generate_func=llm_generate,
                        game_context=game_context
                    )

                    # Add to world map (CACHED - won't regenerate on revisit)
                    self.session.add_location(new_location)
                    
                    # Create bidirectional connection
                    self.session.connect_locations(current_loc.name, new_location.name)
                    
                    combat_feedback = f"🔍 **You explore the area and discover a new location!**\n\n"
                    combat_feedback += f"📍 **{new_location.name}** ({new_location.location_type.value})\n"
                    combat_feedback += f"{new_location.description}\n\n"
                    combat_feedback += f"This location is now connected to {current_loc.name}.\n"
                    combat_feedback += f"Use `/travel {new_location.name}` to visit it."
                    
                    if not new_location.is_safe:
                        combat_feedback += f"\n\n⚠️ **Warning**: This area appears dangerous!"
            else:
                combat_feedback = "🔍 Current location not found in world map."
            combat_command_handled = True

        # If combat command was handled, return immediately
        if combat_command_handled:
            self.message_history.append(Message('player', player_input))
            self.message_history.append(Message('system', combat_feedback))
            self._prune_message_history()  # Prevent context overflow
            return combat_feedback

        # Step 0: Shop Transaction Processing (before Reality Check)
        # Check for /buy or /sell commands and process transactions
        is_shop_transaction = False  # Flag to skip mechanics extraction for shop transactions
        is_steal_attempt = False  # Flag for steal attempts
        if self.session.character_state:
            purchase_intent = self.shop.parse_purchase_intent(player_input)
            sell_intent = self.shop.parse_sell_intent(player_input)

            if purchase_intent:
                is_shop_transaction = True
                item_name, quantity = purchase_intent

                # SHOP REALITY CHECK: Validate that we're actually in a shop location
                current_loc = self.session.get_current_location_obj()
                is_shop_available = False

                # Check 1: Does the location have a shop?
                if current_loc and getattr(current_loc, 'has_shop', False):
                    is_shop_available = True

                # Check 2: Is there a merchant/shopkeeper NPC present?
                if not is_shop_available and self.session.npcs_present:
                    merchant_keywords = ['merchant', 'shopkeeper', 'trader', 'vendor', 'seller']
                    for npc in self.session.npcs_present:
                        npc_name_lower = npc.lower()
                        if any(keyword in npc_name_lower for keyword in merchant_keywords):
                            is_shop_available = True
                            break

                if not is_shop_available:
                    location_name = current_loc.name if current_loc else "this location"
                    transaction_feedback = f"**❌ NO SHOP HERE**: There's no shop in {location_name}! You can't just buy things in the middle of nowhere. Find a marketplace, trading post, or merchant NPC first.\n\n"
                    if DEBUG_PROMPTS:
                        logger.debug(f"🚫 Shop Reality Check: Purchase blocked in {location_name}")
                else:
                    transaction = self.shop.attempt_purchase(
                        self.session.character_state,
                        item_name,
                        quantity
                    )
                    transaction_feedback = f"**💰 SHOP TRANSACTION**: {transaction.message}\n\n"

                    if DEBUG_PROMPTS:
                        logger.debug(f"🛒 Purchase: {item_name} x{quantity} - {transaction.message}")

            elif sell_intent:
                is_shop_transaction = True
                item_name, quantity = sell_intent

                # SHOP REALITY CHECK: Validate that we're actually in a shop location
                current_loc = self.session.get_current_location_obj()
                is_shop_available = False

                # Check 1: Does the location have a shop?
                if current_loc and getattr(current_loc, 'has_shop', False):
                    is_shop_available = True

                # Check 2: Is there a merchant/shopkeeper NPC present?
                if not is_shop_available and self.session.npcs_present:
                    merchant_keywords = ['merchant', 'shopkeeper', 'trader', 'vendor', 'seller', 'buyer']
                    for npc in self.session.npcs_present:
                        npc_name_lower = npc.lower()
                        if any(keyword in npc_name_lower for keyword in merchant_keywords):
                            is_shop_available = True
                            break

                if not is_shop_available:
                    location_name = current_loc.name if current_loc else "this location"
                    transaction_feedback = f"**❌ NO SHOP HERE**: There's no merchant in {location_name}! You can't sell items without a buyer. Find a marketplace, trading post, or merchant NPC first.\n\n"
                    if DEBUG_PROMPTS:
                        logger.debug(f"🚫 Shop Reality Check: Sale blocked in {location_name}")
                else:
                    transaction = self.shop.attempt_sale(
                        self.session.character_state,
                        item_name,
                        quantity
                    )
                    transaction_feedback = f"**💵 SHOP TRANSACTION**: {transaction.message}\n\n"

                    if DEBUG_PROMPTS:
                        logger.debug(f"💵 Sale: {item_name} x{quantity} - {transaction.message}")
        
        # Step 0.5: Party Mode Character Parsing
        # If in party mode, extract which character is acting and temporarily set character_state
        acting_character_name = None
        original_character_state = None
        action_input = player_input  # The input to use for action analysis (may have character name stripped)

        if self.session.party and len(self.session.party.characters) > 0:
            # We're in party mode - set party character names for parsing
            party_char_names = list(self.session.party.characters.keys())
            self.action_validator.set_party_characters(party_char_names)

            # Extract which character is acting
            acting_character_name = self.action_validator.extract_acting_character(player_input)

            if acting_character_name:
                # Temporarily switch to acting character's state for validation
                original_character_state = self.session.character_state
                acting_char_state = self.session.party.get_character(acting_character_name)

                if acting_char_state:
                    self.session.character_state = acting_char_state

                    # Remove character name from input for action analysis
                    # e.g., "Thorin attacks the goblin" -> "attacks the goblin"
                    char_name_lower = acting_character_name.lower()
                    input_lower = player_input.lower()
                    if input_lower.startswith(char_name_lower + ' '):
                        action_input = player_input[len(acting_character_name) + 1:].strip()

                    if DEBUG_PROMPTS:
                        logger.debug(f"🎭 Party Mode: {acting_character_name} is acting")
                        logger.debug(f"   Stripped input: '{action_input}'")
                else:
                    if DEBUG_PROMPTS:
                        logger.debug(f"⚠️ Party character '{acting_character_name}' not found in party state")

        # Step 1: Reality Check - Validate action against game state
        action_intent = self.action_validator.analyze_intent(action_input)
        validation = self.action_validator.validate_action(action_intent, self.session)

        if DEBUG_PROMPTS:
            logger.debug(f"🎯 Action Intent: {action_intent}")
            logger.debug(f"✅ Validation: {validation.result.value} - {validation.message}")

        # Step 1.3: Steal Attempt Handling
        # Detect steal attempts and add special instructions to prevent monster hallucinations
        steal_instruction = ""
        if action_intent and action_intent.action_type == ActionType.STEAL:
            is_steal_attempt = True
            item_name = action_intent.resource or "item"
            
            # Check if item exists at location
            current_loc = self.session.get_current_location_obj()
            item_available = current_loc and current_loc.has_item(item_name)
            
            if item_available and self.session.npcs_present:
                # NPCs present - need stealth check
                npc_names = ", ".join(self.session.npcs_present)
                steal_instruction = f"""
STEAL ATTEMPT: Player is trying to steal {item_name} while {npc_names} is present.

CRITICAL INSTRUCTIONS:
1. DO NOT spawn random monsters (goblins, orcs, etc.)
2. ONLY {npc_names} should react
3. Roll stealth check: d20 + DEX modifier vs DC 15
4. If SUCCESS: Player sneaks the item away unnoticed
5. If FAILURE: {npc_names} catches them and reacts with anger/calls guards
6. DO NOT introduce new NPCs or enemies

"""
            elif item_available:
                # No NPCs - auto-succeed
                steal_instruction = f"Player takes the {item_name}. (No one is watching)"
            else:
                steal_instruction = f"The {item_name} is not here."

        # Step 1.5: For INVALID actions, return deterministic response without calling LLM
        # Small LLMs are bad at following "do not" instructions, so we handle this ourselves
        if validation.result == ValidationResult.INVALID:
            response = self._generate_invalid_action_response(validation)

            # Restore original character_state if we swapped it (AFTER generating response)
            if original_character_state is not None:
                self.session.character_state = original_character_state

            # Save to history
            self.message_history.append(Message('player', player_input))
            self.message_history.append(Message('gm', response))
            self._prune_message_history()  # Prevent context overflow
            self.session.add_note(f"Invalid action rejected: {validation.action.action_type.value}")

            return response

        # Restore original character_state if we swapped it (for valid actions, restore before LLM call)
        if original_character_state is not None:
            self.session.character_state = original_character_state

        # Step 1.7: Auto-start combat if player attacks an NPC
        # CRITICAL: This MUST happen BEFORE attack calculation to ensure initiative is rolled first
        # D&D 5e Rules: Initiative determines who attacks first, not who declares the attack!
        from dnd_rag_system.systems.game_state import Condition
        auto_started_combat = False
        if (action_intent.action_type == ActionType.COMBAT and
            self.session.npcs_present and
            not self.combat_manager.is_in_combat()):

            # Auto-start combat with present NPCs (rolls initiative)
            if self.session.character_state:
                combat_feedback = self.combat_manager.start_combat_with_character(
                    self.session.character_state,
                    self.session.npcs_present
                )
                auto_started_combat = True

                if DEBUG_PROMPTS:
                    logger.debug(f"⚔️ Auto-started combat with: {', '.join(self.session.npcs_present)}")
                    current_turn = self.session.combat.get_current_turn()
                    logger.debug(f"⚔️ Initiative Order Set - First Turn: {current_turn}")

                # IMPORTANT: If combat starts with an NPC's turn, process NPC turns immediately
                # This ensures NPCs attack BEFORE the player if they won initiative
                current_turn = self.combat_manager.get_current_turn_name()
                if current_turn and current_turn in self.combat_manager.npc_monsters:
                    # Get player AC for NPC targeting
                    target_ac = 15  # Default
                    if hasattr(self.session.character_state, 'armor_class'):
                        target_ac = self.session.character_state.armor_class

                    # Process all NPC turns (damage is applied inside process_npc_turns)
                    npc_actions = self.combat_manager.process_npc_turns(
                        target_ac,
                        target_character=self.session.character_state
                    )

                    if npc_actions:
                        combat_feedback += "\n\n**🐉 NPC ACTIONS:**\n" + "\n\n".join(npc_actions)

                # IMPORTANT: If combat was auto-started, return the combat feedback immediately
                # This prevents LLM narrative from appearing before the combat start message
                # Return the clean combat start + NPC actions + turn announcement
                if auto_started_combat:
                    return combat_feedback

        # Step 1.8: Calculate Player Attack (ONLY if it's their turn or not in combat)
        # Pre-calculate attack roll and damage so GM can narrate specific numbers
        player_attack_instruction = ""
        player_attack_damage_feedback = ""
        if (action_intent.action_type == ActionType.COMBAT and
            action_intent.target and
            self.session.character_state):

            # Check if it's the player's turn (if in combat)
            is_players_turn = True  # Default to True if not in combat
            if self.combat_manager.is_in_combat():
                current_turn = self.session.combat.get_current_turn()
                is_players_turn = (current_turn == self.session.character_state.character_name)

                if not is_players_turn:
                    # Not the player's turn - they can't attack yet!
                    player_attack_instruction = f"""⚠️ **NOT YOUR TURN!** It's {current_turn}'s turn right now.

**What happened:**
- You attacked, which started combat
- Initiative was rolled: {current_turn} won and goes first!

**What to do:**
- Click "Next Turn" button to advance combat
- Wait for your turn to attack

This is D&D 5e rules - initiative determines who goes first!"""

                    if DEBUG_PROMPTS:
                        logger.debug(f"⚠️ Player tried to attack on {current_turn}'s turn - blocked")

            # Only calculate attack if it's the player's turn (or not in combat)
            if is_players_turn:
                # Use fuzzy-matched target name if available, otherwise use original
                target_name = validation.matched_entity if validation and validation.matched_entity else action_intent.target

                # Calculate player's attack
                attack_result = self._calculate_player_attack(
                    target_name,
                    self.session.character_state
                )

                if attack_result:
                    player_attack_instruction = attack_result
                    if DEBUG_PROMPTS:
                        logger.debug(f"⚔️ Player Attack: {attack_result}")

                    # Parse and apply damage directly (don't rely on mechanics extraction)
                    import re
                    damage_match = re.search(r'💥 (\d+) (\w+) damage', attack_result)
                    if damage_match and "HITS" in attack_result:
                        damage_amount = int(damage_match.group(1))
                        damage_type = damage_match.group(2)
                        # Use matched target name (already calculated above)

                        # Apply damage to NPC directly
                        if target_name in self.combat_manager.npc_monsters:
                            actual_damage, is_dead = self.combat_manager.apply_damage_to_npc(
                                target_name,
                                damage_amount
                            )

                            npc = self.combat_manager.npc_monsters[target_name]
                            if is_dead:
                                player_attack_damage_feedback = f"💥 {target_name} takes {actual_damage} {damage_type} damage and dies! ☠️"
                                # Remove from npcs_present
                                if target_name in self.session.npcs_present:
                                    self.session.npcs_present.remove(target_name)
                            else:
                                player_attack_damage_feedback = f"💥 {target_name} takes {actual_damage} {damage_type} damage! (HP: {npc.current_hp}/{npc.max_hp})"
                    elif "MISSES" in attack_result or "CRITICALLY MISSES" in attack_result:
                        player_attack_damage_feedback = f"❌ Attack missed {target_name}!"

        # Step 2: Search RAG if enabled
        if use_rag:
            rag_results = self.search_rag(player_input)
            rag_context = self.format_rag_context(rag_results)

        # Step 2.5: Random Encounter Check
        # Check if player is exploring/traveling and roll for random encounter
        encounter = None
        encounter_instruction = ""
        
        # Only check for encounters during exploration actions (not in combat, shops, etc.)
        exploration_keywords = ['explore', 'travel', 'venture', 'search', 'wander', 'head', 'go', 
                               'leave', 'continue', 'follow', 'look around', 'investigate']
        is_exploring = any(keyword in player_input.lower() for keyword in exploration_keywords)
        
        # Encounter cooldown: Only check every 5+ turns OR when changing locations
        # This prevents encounter spam (goblin -> owlbear -> manticore in 3 turns)
        # IMPORTANT: Don't trigger on first action (last_encounter_location is empty initially)
        location_changed = (
            self.session.last_encounter_location != "" and
            self.session.last_encounter_location != self.session.current_location
        )
        encounter_cooldown_met = (self.session.turns_since_last_encounter >= 5)

        if (is_exploring and
            not self.combat_manager.is_in_combat() and
            self.session.character_state is not None and
            (encounter_cooldown_met or location_changed)):
            
            # Get current location info
            current_loc = self.session.get_current_location_obj()
            location_type = current_loc.location_type.value if current_loc else "wilderness"
            character_level = self.session.character_state.level
            
            # Roll for encounter
            encounter = self.encounter_system.generate_encounter(location_type, character_level)
            
            if encounter:
                # Reset cooldown
                self.session.turns_since_last_encounter = 0
                self.session.last_encounter_location = self.session.current_location
                
                # Add monster to NPCs present
                self.add_npc(encounter.monster_name)
                
                # Create hidden instruction for GM
                encounter_instruction = self.encounter_system.format_encounter_for_gm(encounter)
                
                if DEBUG_PROMPTS:
                    logger.debug(f"🎲 Random Encounter: {encounter.monster_name} (CR {encounter.monster_cr})")
                    logger.debug(f"   Location: {location_type}, Character Level: {character_level}")
                    if encounter.surprise:
                        logger.debug(f"   💥 SURPRISE ATTACK!")
            else:
                # No encounter this turn, increment cooldown
                self.session.turns_since_last_encounter += 1
        else:
            # Increment turn counter even when not exploring (for cooldown tracking)
            if not self.combat_manager.is_in_combat():
                self.session.turns_since_last_encounter += 1

        # Step 3: Build prompt with history, RAG context, validation guidance, encounter, and player attack
        prompt = self._build_prompt(player_input, rag_context, validation, encounter_instruction, player_attack_instruction, steal_instruction)

        # Step 4: Get LLM response (route based on mode)
        try:
            if self.use_hf_api:
                response = self._query_hf(prompt)
            else:
                response = self._query_ollama(prompt)

            # Step 4.5: Remove prompt leakage (LLM echoing instructions)
            response = self._remove_prompt_leakage(response)

            # Step 5: Post-process response (e.g., auto-add NPCs introduced in conversation)
            self._post_process_response(response, validation)
            
            # Step 5.2: Fallback encounter text if GM didn't mention the monster
            if encounter and encounter.monster_name.lower() not in response.lower():
                encounter_text = self.encounter_system.format_encounter_fallback(encounter)
                response += encounter_text
                
                if DEBUG_PROMPTS:
                    logger.debug(f"🎲 Encounter fallback text added (GM didn't mention {encounter.monster_name})")

            # Step 5.3: Extract mechanics from narrative and auto-update game state
            # SKIP for shop transactions - already handled by shop system
            if not is_shop_transaction and (self.session.character_state or (self.session.party and len(self.session.party.characters) > 0)):
                try:
                    # Get character names for better extraction
                    char_names = []
                    if self.session.party and len(self.session.party.characters) > 0:
                        char_names = list(self.session.party.characters.keys())
                    elif self.session.character_state:
                        char_names = [self.session.character_state.character_name]

                    # Extract mechanics from GM response
                    mechanics = self.mechanics_extractor.extract(
                        response, 
                        char_names,
                        existing_npcs=self.session.npcs_present  # Pass existing NPCs to avoid re-adding them
                    )

                    # Apply to game state if any mechanics found
                    if mechanics.has_mechanics():
                        # Filter NPCs: Remove hallucinations and already-present NPCs
                        if mechanics.npcs_introduced:
                            original_count = len(mechanics.npcs_introduced)
                            filtered_npcs = []
                            existing_lower = [npc.lower() for npc in self.session.npcs_present]
                            
                            for npc in mechanics.npcs_introduced:
                                npc_name = npc.get('name', '').strip()
                                npc_name_lower = npc_name.lower()
                                
                                # Skip if already present
                                if npc_name_lower in existing_lower:
                                    if DEBUG_PROMPTS:
                                        logger.debug(f"🔧 Filtered NPC '{npc_name}' - already present")
                                    continue
                                
                                # If there's an encounter, only allow the encounter monster or non-enemy NPCs
                                if encounter:
                                    encounter_name = encounter.monster_name.strip().lower()
                                    
                                    # Allow the actual encounter monster
                                    if npc_name_lower == encounter_name:
                                        filtered_npcs.append(npc)
                                    # Allow non-monster NPCs (merchants, guards, etc.) if type is not "enemy"
                                    elif npc.get('type') != 'enemy':
                                        filtered_npcs.append(npc)
                                    else:
                                        # This is a hallucinated enemy - skip it
                                        if DEBUG_PROMPTS:
                                            logger.debug(f"🔧 Filtered hallucinated enemy '{npc_name}' - actual encounter is '{encounter_name}'")
                                else:
                                    # No encounter - just add the NPC
                                    filtered_npcs.append(npc)
                            
                            mechanics.npcs_introduced = filtered_npcs
                            if DEBUG_PROMPTS and original_count != len(filtered_npcs):
                                logger.debug(f"🔧 Filtered {original_count - len(filtered_npcs)} NPC(s) from mechanics extraction")
                        
                        npc_feedback = self.mechanics_applicator.apply_npcs_to_session(mechanics, self.session)

                        # Apply damage/healing/conditions to characters
                        if self.session.party and len(self.session.party.characters) > 0:
                            # Apply to party
                            feedback = self.mechanics_applicator.apply_to_party(mechanics, self.session.party)
                        else:
                            # Apply to single character (pass session for item tracking)
                            feedback = self.mechanics_applicator.apply_to_character(
                                mechanics, 
                                self.session.character_state,
                                game_session=self.session
                            )
                        
                        # Apply damage to NPCs (enemies) - NEW!
                        npc_damage_feedback = self.mechanics_applicator.apply_damage_to_npcs(
                            mechanics,
                            self.combat_manager,
                            self.session
                        )

                        # Combine all feedbacks
                        all_feedback = npc_feedback + feedback + npc_damage_feedback

                        # Deduplicate feedback messages (fixes LLM prompt leakage causing duplicate extractions)
                        if all_feedback:
                            unique_feedback = []
                            seen = set()
                            for msg in all_feedback:
                                # Normalize message for comparison (remove emojis/formatting)
                                normalized = msg.strip().lower()
                                if normalized not in seen:
                                    seen.add(normalized)
                                    unique_feedback.append(msg)

                        # Add mechanics feedback to combat output
                        if unique_feedback:
                            mechanics_output = "\n\n**⚙️ MECHANICS:**\n" + "\n".join(unique_feedback)
                            combat_feedback += mechanics_output

                        if DEBUG_PROMPTS and all_feedback:
                            logger.debug("=" * 80)
                            logger.debug("MECHANICS AUTO-APPLIED TO GAME STATE:")
                            for msg in all_feedback:
                                logger.debug(f"  {msg}")
                            logger.debug("=" * 80)

                except Exception as e:
                    logger.error(f"Mechanics extraction/application failed: {e}")

            # Step 5.4: Extract location changes from GM narrative
            # Parse patterns like "You find yourself in X", "You travel to X", "You are in X"
            self._extract_and_update_location(response)

            # Step 5.5: Auto-advance turn in combat mode after character acts
            # In D&D combat: NPCs attack EVERY round regardless of what player does
            # Player tries to run? NPCs get attacks of opportunity
            # Player talks? NPCs still attack
            # Player uses item? NPCs still attack
            player_unconscious = False
            if self.session.character_state:
                player_unconscious = Condition.UNCONSCIOUS.value in self.session.character_state.conditions
            
            if self.combat_manager.is_in_combat():
                # In combat, ALWAYS advance turn after player action (or auto-skip if unconscious)
                # This ensures NPCs attack every round, even if player runs/talks/etc.
                turn_message = self.combat_manager.advance_turn()
                if turn_message:
                    combat_feedback += f"\n\n{turn_message}"

                if DEBUG_PROMPTS:
                    if player_unconscious:
                        logger.debug(f"⚔️ Combat turn auto-advanced (player unconscious)")
                    else:
                        logger.debug(f"⚔️ Combat turn auto-advanced: {turn_message}")

                # Step 5.6: Process NPC turns automatically using monster stats
                # Get player AC for NPC attack targeting
                target_ac = 15  # Default
                if self.session.character_state:
                    # Try to get AC from character (if available)
                    if hasattr(self.session.character_state, 'armor_class'):
                        target_ac = self.session.character_state.armor_class
                elif self.session.party and len(self.session.party.characters) > 0:
                    # For party mode, use average AC or first character's AC
                    first_char = list(self.session.party.characters.values())[0]
                    if hasattr(first_char, 'armor_class'):
                        target_ac = first_char.armor_class

                # Process all consecutive NPC turns (damage is applied inside process_npc_turns)
                npc_actions = self.combat_manager.process_npc_turns(
                    target_ac,
                    target_character=self.session.character_state,
                    target_party=self.session.party
                )

                if npc_actions:
                    # Add NPC attacks to response
                    combat_feedback += "\n\n**🐉 NPC ACTIONS:**\n" + "\n\n".join(npc_actions)

                    if DEBUG_PROMPTS:
                        logger.debug(f"🐉 NPC turns processed: {len(npc_actions)} attacks")
                        for action in npc_actions:
                            logger.debug(f"   {action}")

            # Add shop transaction feedback if any
            if transaction_feedback:
                response = transaction_feedback + response
            
            # Add player attack damage feedback if any
            if player_attack_damage_feedback:
                response = response + f"\n\n**⚙️ MECHANICS:**\n{player_attack_damage_feedback}"

            # Add combat feedback if any (turn advancement)
            if combat_feedback:
                response = response + combat_feedback

            # Save to history
            self.message_history.append(Message('player', player_input, rag_context if use_rag else None))
            self.message_history.append(Message('gm', response))
            self._prune_message_history()  # Prevent context overflow
            self.session.add_note(f"Player: {player_input[:50]}... | GM: {response[:50]}...")

            return response

        except Exception as e:
            return f"Error generating response: {e}"

    def _calculate_player_attack(self, target_name: str, character_state) -> str:
        """
        Calculate player's attack roll and damage against a target.
        Pre-calculates the mechanics so GM can narrate specific numbers.
        
        Args:
            target_name: Name of the NPC being attacked
            character_state: CharacterState object (has character name and equipped items)
            
        Returns:
            Formatted instruction string for GM, or empty string if calculation fails
        """
        import random
        
        # Get base character stats from session (has ability scores, equipment, etc.)
        if not character_state:
            return ""
        
        character_name = character_state.character_name
        if character_name not in self.session.base_character_stats:
            return ""
            
        character = self.session.base_character_stats[character_name]
        
        # Simple weapon damage table (weapon_name: (damage_dice, damage_die_count, damage_die_size, damage_type))
        # Format: "1d8" = (1, 8), "2d6" = (2, 6)
        WEAPON_DAMAGE = {
            "longsword": (1, 8, "slashing"),
            "greatsword": (2, 6, "slashing"),
            "shortsword": (1, 6, "piercing"),
            "dagger": (1, 4, "piercing"),
            "battleaxe": (1, 8, "slashing"),
            "greataxe": (1, 12, "slashing"),
            "mace": (1, 6, "bludgeoning"),
            "warhammer": (1, 8, "bludgeoning"),
            "rapier": (1, 8, "piercing"),
            "scimitar": (1, 6, "slashing"),
            "quarterstaff": (1, 6, "bludgeoning"),
            "spear": (1, 6, "piercing"),
            "bow": (1, 8, "piercing"),
            "longbow": (1, 8, "piercing"),
            "shortbow": (1, 6, "piercing"),
            "crossbow": (1, 8, "piercing"),
            "hand crossbow": (1, 6, "piercing"),
            # Unarmed as fallback
            "unarmed": (1, 4, "bludgeoning"),
        }
        
        # Find equipped weapon in character's equipment
        weapon_name = "unarmed"
        weapon_found = False
        
        if hasattr(character, 'equipment') and character.equipment:
            for item in character.equipment:
                item_lower = item.lower()
                for weapon_key in WEAPON_DAMAGE.keys():
                    if weapon_key in item_lower:
                        weapon_name = weapon_key
                        weapon_found = True
                        break
                if weapon_found:
                    break
        
        # Get weapon stats
        dice_count, die_size, damage_type = WEAPON_DAMAGE.get(weapon_name, (1, 4, "bludgeoning"))
        
        # Calculate attack bonus (STR mod + proficiency for melee weapons)
        str_mod = character.get_ability_modifier(character.strength)
        attack_bonus = str_mod + character.proficiency_bonus
        
        # Get target AC (check if NPC exists in combat manager)
        target_ac = 12  # Default AC
        if target_name in self.combat_manager.npc_monsters:
            target_ac = self.combat_manager.npc_monsters[target_name].ac
        
        # Roll attack (d20 + attack bonus)
        attack_roll = random.randint(1, 20)
        total_attack = attack_roll + attack_bonus
        
        # Check if hit
        if attack_roll == 1:
            # Critical miss
            return (
                f"COMBAT INSTRUCTION: {character.name} attacks {target_name} with {weapon_name} but CRITICALLY MISSES (rolled natural 1)! "
                f"Attack roll: 1 + {attack_bonus} = {total_attack} vs AC {target_ac}. "
                f"Narrate an embarrassing miss or fumble. NO DAMAGE."
            )
        elif total_attack < target_ac and attack_roll != 20:
            # Normal miss
            return (
                f"COMBAT INSTRUCTION: {character.name} attacks {target_name} with {weapon_name} but MISSES. "
                f"Attack roll: {attack_roll} + {attack_bonus} = {total_attack} vs AC {target_ac}. "
                f"Narrate the attack missing. NO DAMAGE."
            )
        else:
            # Hit! Roll damage
            damage = sum(random.randint(1, die_size) for _ in range(dice_count))
            damage += str_mod  # Add STR modifier to damage
            
            if attack_roll == 20:
                # Critical hit! Double damage
                damage *= 2
                return (
                    f"COMBAT INSTRUCTION: {character.name} attacks {target_name} with {weapon_name} and scores a CRITICAL HIT (natural 20)! "
                    f"Attack roll: 20 (critical!) + {attack_bonus} = {total_attack} vs AC {target_ac}. "
                    f"💥 {damage} {damage_type} damage (CRITICAL DOUBLE DAMAGE!). "
                    f"Narrate an epic, devastating strike that deals {damage} damage to {target_name}."
                )
            else:
                return (
                    f"COMBAT INSTRUCTION: {character.name} attacks {target_name} with {weapon_name} and HITS! "
                    f"Attack roll: {attack_roll} + {attack_bonus} = {total_attack} vs AC {target_ac}. "
                    f"💥 {damage} {damage_type} damage. "
                    f"Narrate the successful strike dealing {damage} damage to {target_name}."
                )

    def _build_prompt(self, player_input: str, rag_context: str, validation=None, encounter_instruction: str = "", player_attack_instruction: str = "", steal_instruction: str = "") -> str:
        """
        Build complete prompt for LLM with full game state context.

        Args:
            player_input: Player's action
            rag_context: Retrieved RAG information
            validation: ValidationReport from action validator (optional)
            encounter_instruction: Hidden instruction for random encounter (optional)
        """

        # Get recent conversation history
        from dnd_rag_system.config.settings import RECENT_MESSAGES_FOR_PROMPT
        
        recent_messages = self.message_history[-RECENT_MESSAGES_FOR_PROMPT:] if len(self.message_history) > RECENT_MESSAGES_FOR_PROMPT else self.message_history
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

        # Add conversation summary if it exists (for context continuity)
        if self.conversation_summary:
            prompt += f"\nPREVIOUS SESSION SUMMARY:\n{self.conversation_summary[-500:]}\n"  # Last 500 chars of summary

        # Add location context for better narrative consistency
        current_loc = self.session.get_current_location_obj()
        if current_loc:
            # Don't explicitly mention visit count - just note it's a return
            if current_loc.visit_count > 1:
                prompt += f"NOTE: The party has been here before. Describe naturally without explicitly counting visits.\n"
            
            # Mention defeated enemies for atmosphere
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
        
        # Add encounter instruction if present (hidden from player, only GM sees this)
        if encounter_instruction:
            prompt += f"""{encounter_instruction}

"""
        
        # Add player attack instruction if present (hidden from player, only GM sees this)
        if player_attack_instruction:
            prompt += f"""{player_attack_instruction}

"""

        prompt += """INSTRUCTIONS:
1. Apply D&D 5e rules accurately using the retrieved information
2. Consider the current location, NPCs present, and combat state
3. Ask for appropriate dice rolls (d20 for attacks/checks, damage dice, saves, etc.)
4. Be concise and engaging (2-4 sentences max)
5. Maintain narrative flow while being mechanically precise
6. If rules are unclear, use standard D&D 5e mechanics
7. Be concise, respond in 3-5 sentences unless more detail is explicitly required.

"""

        # Add steal instruction PROMINENTLY before GM response (like INVALID validation)
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
        # IMPORTANT: Use the acting character's stats, not just character_state!
        char_name = "You"
        char_race = ""
        char_class = ""

        # First, try to extract which character is acting (for party mode)
        acting_character_name = self.action_validator.extract_acting_character(action.raw_input)

        if acting_character_name and acting_character_name in self.session.base_character_stats:
            # Use the specific character's stats (e.g., Elara's stats when "Elara casts...")
            base_char = self.session.base_character_stats[acting_character_name]
            char_name = base_char.name
            char_race = getattr(base_char, 'race', '').lower()
            char_class = getattr(base_char, 'character_class', '')
        elif hasattr(self.session, 'character_state') and self.session.character_state:
            # Fallback: use session character_state (single player mode)
            char_name = getattr(self.session.character_state, 'character_name', 'You')
            char_race = getattr(self.session.character_state, 'race', '').lower()
            char_class = getattr(self.session.character_state, 'character_class', '')

        # Combat-specific responses
        if action.action_type == ActionType.COMBAT:
            # Check WHY combat is invalid (weapon missing vs target missing)
            is_weapon_missing = "don't have that weapon" in validation.message.lower()
            is_target_missing = "no such enemy" in validation.message.lower() or "not present" in validation.message.lower()

            if is_weapon_missing and action.resource:
                # Weapon validation failed
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

            elif is_target_missing and action.target:
                # Target validation failed (this should be the most common invalid combat)
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
            # Check if it's a target validation issue
            is_target_missing = "no such target" in validation.message.lower() or "target doesn't exist" in validation.message.lower()
            
            if is_target_missing and action.target:
                # Spell target doesn't exist - different from spell unknown!
                if char_race == 'elf':
                    return (
                        f"You channel your arcane energy and prepare to cast {action.resource}, "
                        f"but you quickly realize there's no {action.target} here to target. "
                        f"The spell fizzles harmlessly as you release the energy. "
                        f"Perhaps you should look around more carefully before casting?"
                    )
                else:
                    return (
                        f"You begin the incantation for {action.resource}, arcane energy building around you... "
                        f"but then you realize: there's no {action.target} here! "
                        f"The spell dissipates harmlessly as you stop mid-cast. "
                        f"You can't target something that isn't there."
                    )
            elif action.resource:
                # Spell validation failed (unknown spell or non-caster)
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

    def _extract_and_update_location(self, response: str) -> None:
        """
        Extract location from GM narrative and update session state.
        
        CRITICAL: Do NOT allow location changes during combat!
        
        Patterns detected:
        - "You find yourself in X"
        - "You are in X"  
        - "You travel to X"
        - "You arrive at X"
        - "You enter X"
        
        Args:
            response: GM's narrative response
        """
        import re
        
        # CRITICAL: Prevent location changes during combat
        if self.combat_manager.is_in_combat():
            if DEBUG_PROMPTS:
                logger.debug("🔒 Location locked - in combat, ignoring any location mentions in GM response")
            return
        
        # Patterns for location mentions
        patterns = [
            r'[Yy]ou find yourself (?:in|at) (?:the )?([A-Z][^.!?\n]+?)(?:\.|!|\?|,|\n)',
            r'[Yy]ou (?:are|\'re) (?:now )?(?:in|at) (?:the )?([A-Z][^.!?\n]+?)(?:\.|!|\?|,|\n)',
            r'[Yy]ou travel to (?:the )?([A-Z][^.!?\n]+?)(?:\.|!|\?|,|\n)',
            r'[Yy]ou arrive (?:at|in) (?:the )?([A-Z][^.!?\n]+?)(?:\.|!|\?|,|\n)',
            r'[Yy]ou enter (?:the )?([A-Z][^.!?\n]+?)(?:\.|!|\?|,|\n)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response)
            if match:
                new_location = match.group(1).strip()
                
                # Clean up common artifacts
                new_location = new_location.rstrip('.,!?')
                
                # Only update if it's actually different
                if new_location != self.session.current_location:
                    old_location = self.session.current_location
                    self.session.current_location = new_location
                    
                    # Clear NPCs when changing location (NPCs don't follow the player!)
                    # Only keep resident NPCs of the new location
                    new_loc_obj = self.session.get_current_location_obj()
                    if new_loc_obj:
                        # Keep only resident NPCs of new location
                        self.session.npcs_present = list(new_loc_obj.resident_npcs)
                    else:
                        # Unknown location - clear all NPCs
                        self.session.npcs_present = []
                    
                    if DEBUG_PROMPTS:
                        logger.debug(f"📍 Location changed: '{old_location}' → '{new_location}'")
                        logger.debug(f"🎭 NPCs cleared, now present: {self.session.npcs_present}")
                    
                    self.session.add_note(f"Traveled to: {new_location}")
                
                # Only match first occurrence
                break

    def _remove_prompt_leakage(self, response: str) -> str:
        """
        Remove common prompt leakage patterns from LLM response.

        LLMs sometimes echo back instructions that were meant to be hidden.
        This method filters out common instruction patterns.

        Args:
            response: Raw LLM response

        Returns:
            Cleaned response with instruction patterns removed
        """
        import re

        # Patterns to remove (instruction leakage)
        patterns = [
            r'Narrate the .+?\.',  # "Narrate the successful strike dealing X damage."
            r'Taking the above information into consideration.+?roleplay conversation with',  # System prompt leakage
            r'You are .+?\.\s*Taking.+?into consideration',  # Context setup leakage
            r'Initiative Order:.+?You are',  # Initiative context leakage
        ]

        cleaned = response
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Remove excessive whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()

        return cleaned

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
            
            # CRITICAL: Remove leaked system prompts from model training data
            # The model sometimes hallucinates roleplay card formats
            import re
            
            # Remove {{user}} template markers and everything after
            if "{{user}}" in response:
                response = response.split("{{user}}")[0].strip()
            
            # Remove "Take the role of" instruction blocks
            if "Take the role of" in response:
                response = response.split("Take the role of")[0].strip()
            
            # Remove "You must engage in roleplay" blocks
            if "you must roleplay" in response.lower():
                parts = re.split(r'you must (?:engage in )?roleplay', response, flags=re.IGNORECASE)
                response = parts[0].strip()
            
            # Remove "Never write for" instruction blocks
            if "Never write for" in response:
                response = response.split("Never write for")[0].strip()
            
            # Remove "Scenario:" metadata blocks
            if "Scenario:" in response:
                response = response.split("Scenario:")[0].strip()
            
            # Remove markdown code fences that sometimes appear
            response = re.sub(r'```[\w]*\n.*?```', '', response, flags=re.DOTALL)
            
            # Remove duplicate paragraphs (hallucination symptom)
            paragraphs = response.split('\n\n')
            seen = set()
            cleaned_paragraphs = []
            for para in paragraphs:
                para_clean = para.strip()
                if para_clean and para_clean not in seen:
                    seen.add(para_clean)
                    cleaned_paragraphs.append(para)
            response = '\n\n'.join(cleaned_paragraphs)
            
            # Final trim
            response = response.strip()

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
