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
from dnd_rag_system.core.llm_client import LLMClient
from dnd_rag_system.config import settings
from dnd_rag_system.systems.game_state import GameSession, CombatState, PartyState
from dnd_rag_system.systems.action_validator import (
    ActionValidator, ValidationResult, ActionType, create_context_aware_prompt
)
from dnd_rag_system.systems.shop_system import ShopSystem
from dnd_rag_system.systems.combat_manager import CombatManager
from dnd_rag_system.systems.encounter_system import EncounterSystem
from dnd_rag_system.systems.spell_manager import SpellManager
from dnd_rag_system.systems.commands import CommandDispatcher, CommandContext
from dnd_rag_system.constants import Commands, ActionKeywords
from dnd_rag_system.dialogue.rag_retriever import RAGRetriever
from dnd_rag_system.dialogue.conversation_history_manager import ConversationHistoryManager, Message
from dnd_rag_system.dialogue.prompt_builder import PromptBuilder

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


# Environment detection moved to dnd_rag_system.config.environment
# Imported above for backward compatibility


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

        # Conversation History System (Phase 2 refactoring: extracted from GameMaster)
        from dnd_rag_system.config.settings import MAX_MESSAGE_HISTORY
        self.history_manager = ConversationHistoryManager(max_history=MAX_MESSAGE_HISTORY)

        self.action_validator = ActionValidator(debug=DEBUG_PROMPTS)  # Reality check system
        self.shop = ShopSystem(db_manager, debug=DEBUG_PROMPTS)  # Shop transaction system
        self.spell_manager = SpellManager(db_manager)  # Spell and resource management
        self.combat_manager = CombatManager(self.session.combat, spell_manager=self.spell_manager, debug=DEBUG_PROMPTS)  # Combat system with XP tracking

        # Unified Mechanics Service (Phase 6 refactoring: facade for extraction + application)
        from dnd_rag_system.systems.mechanics_service import MechanicsService
        self.mechanics_service = MechanicsService(debug=DEBUG_PROMPTS)

        # Random Encounter System
        self.encounter_system = EncounterSystem(chromadb_manager=db_manager)

        # Command Dispatcher (Command Pattern for slash commands)
        self.command_dispatcher = CommandDispatcher(debug=DEBUG_PROMPTS)

        # RAG Retrieval System (Phase 1 refactoring: extracted from GameMaster)
        self.rag_retriever = RAGRetriever(db_manager)

        # Prompt Builder (Phase 3 refactoring: extracted from GameMaster)
        self.prompt_builder = PromptBuilder()

        # Initialize world map with starting locations
        from dnd_rag_system.systems.world_builder import initialize_world
        initialize_world(self.session)

        # Unified LLM Client (Phase 7 refactoring: centralize all LLM query logic)
        self.llm_client = LLMClient(
            model_name=model_name,
            hf_token=hf_token,
            debug=DEBUG_PROMPTS
        )
        # Keep these for backward compatibility with code that checks them
        self.client = self.llm_client.client
        self.model_name = self.llm_client.model_name
        self.use_hf_api = self.llm_client.use_hf_api

    # NOTE: Phase 1, 2, & 3 Refactoring - Methods moved to extracted classes:
    # - search_rag() and format_rag_context() → RAGRetriever class
    #   Access via: self.rag_retriever.search_rag() and self.rag_retriever.format_rag_context()
    # - _prune_message_history() and _create_message_summary() → ConversationHistoryManager class
    #   Access via: self.history_manager.prune_history() and other methods
    # - _build_prompt() → PromptBuilder class
    #   Access via: self.prompt_builder.build_prompt()

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

        # Step -1: Command Processing (Using Command Pattern)
        # Dispatch slash commands to appropriate handlers
        # This replaces the massive if/elif block with clean, modular command handlers
        command_context = CommandContext(
            session=self.session,
            combat_manager=self.combat_manager,
            spell_manager=self.spell_manager,
            shop_system=self.shop,
            debug=DEBUG_PROMPTS,
            gm=self,  # Pass GameMaster for LLM access in explore command
            llm_client=self.client,
            use_hf_api=self.use_hf_api
        )

        command_result = self.command_dispatcher.dispatch(player_input, command_context)

        if command_result.handled:
            # Command was processed by dispatcher
            combat_feedback = command_result.feedback if command_result.feedback else ""

            # Log to message history
            self.history_manager.add_message('player', player_input)
            self.history_manager.add_message('system', combat_feedback)
            is_party_mode = self.session.party and len(self.session.party.characters) > 0
            self.history_manager.prune_history(is_party_mode)  # Prevent context overflow

            return combat_feedback

        # If we get here, no command handler matched - continue with normal dialogue generation
        # (The rest of the method handles shop transactions, RAG, and narrative generation)
        combat_command_handled = False
        lower_input = player_input.lower().strip()

        # NOTE: The massive if/elif command handling block (792 lines!) has been removed.
        # All slash commands are now handled by the CommandDispatcher above using the Command Pattern.
        # This eliminates the "God Method" anti-pattern and makes the code much more maintainable.

        # Step 0: Shop Transaction Processing (before Reality Check)
        # Check for /buy or /sell commands and process transactions
        is_shop_transaction = False  # Flag to skip mechanics extraction for shop transactions
        is_steal_attempt = False  # Flag for steal attempts
        if self.session.character_state:
            is_shop_transaction, transaction_feedback = self.shop.handle_shop_transaction(
                player_input,
                self.session.character_state,
                self.session.get_current_location_obj(),
                self.session.npcs_present,
                debug=DEBUG_PROMPTS
            )
        
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
            self.history_manager.add_message('player', player_input)
            self.history_manager.add_message('gm', response)
            is_party_mode = self.session.party and len(self.session.party.characters) > 0
            self.history_manager.prune_history(is_party_mode)  # Prevent context overflow
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
                attack_result = self.combat_manager.calculate_player_attack(
                    target_name,
                    self.session.character_state,
                    self.session.base_character_stats
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
            rag_results = self.rag_retriever.search_rag(player_input)
            rag_context = self.rag_retriever.format_rag_context(rag_results)

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
        from dnd_rag_system.config.settings import RECENT_MESSAGES_FOR_PROMPT
        history_text = self.history_manager.format_for_prompt(RECENT_MESSAGES_FOR_PROMPT)
        conversation_summary = self.history_manager.get_summary(max_chars=500)

        prompt = self.prompt_builder.build_prompt(
            player_input=player_input,
            game_session=self.session,
            history_text=history_text,
            conversation_summary=conversation_summary,
            rag_context=rag_context,
            validation=validation,
            encounter_instruction=encounter_instruction,
            player_attack_instruction=player_attack_instruction,
            steal_instruction=steal_instruction
        )

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
                    # Process narrative through mechanics service (extraction + application)
                    encounter_name = encounter.monster_name if encounter else None
                    feedback_messages = self.mechanics_service.process_narrative(
                        response,
                        self.session,
                        combat_manager=self.combat_manager,
                        encounter_monster_name=encounter_name
                    )
                    
                    # Add mechanics feedback to combat output
                    if feedback_messages:
                        mechanics_output = "\n\n**⚙️ MECHANICS:**\n" + "\n".join(feedback_messages)
                        combat_feedback += mechanics_output
                    
                    if DEBUG_PROMPTS and feedback_messages:
                        logger.debug("=" * 80)
                        logger.debug("MECHANICS AUTO-APPLIED TO GAME STATE:")
                        for msg in feedback_messages:
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
            self.history_manager.add_message('player', player_input, rag_context if use_rag else None)
            self.history_manager.add_message('gm', response)
            is_party_mode = self.session.party and len(self.session.party.characters) > 0
            self.history_manager.prune_history(is_party_mode)  # Prevent context overflow
            self.session.add_note(f"Player: {player_input[:50]}... | GM: {response[:50]}...")

            return response

        except Exception as e:
            return f"Error generating response: {e}"

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
        
        DEPRECATED: Use self.llm_client.query() instead.
        Kept for backward compatibility.
        """
        return self.llm_client.query(prompt, timeout=timeout, clean_response=True)

    def _query_hf(self, prompt: str, timeout: int = 60) -> str:
        """
        Send prompt to Hugging Face Inference API and get response (HF mode).
        
        DEPRECATED: Use self.llm_client.query() instead.
        Kept for backward compatibility.
        """
        return self.llm_client.query(prompt, timeout=timeout, clean_response=True)

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
