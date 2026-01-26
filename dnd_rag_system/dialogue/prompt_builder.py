"""
Prompt Building for LLM

Constructs prompts for the Game Master LLM with game state, history, and instructions.
"""

from typing import Optional
from dnd_rag_system.systems.action_validator import ValidationResult


class PromptBuilder:
    """
    Builds LLM prompts with game state context and instructions.

    Responsibilities:
    - Assemble game state context (location, NPCs, combat, quests)
    - Include conversation history and summary
    - Add RAG context when available
    - Format validation guidance
    - Add special instructions (encounters, attacks, steal attempts)

    Extracted from GameMaster class to follow Single Responsibility Principle.
    """

    def __init__(self):
        """Initialize prompt builder."""
        pass

    def build_prompt(
        self,
        player_input: str,
        game_session,
        history_text: str,
        conversation_summary: str = "",
        rag_context: str = "",
        validation=None,
        encounter_instruction: str = "",
        player_attack_instruction: str = "",
        steal_instruction: str = ""
    ) -> str:
        """
        Build complete prompt for LLM with full game state context.

        Args:
            player_input: Player's action
            game_session: GameSession object with current game state
            history_text: Formatted recent conversation history
            conversation_summary: Summary of older conversations
            rag_context: Retrieved RAG information
            validation: ValidationReport from action validator (optional)
            encounter_instruction: Hidden instruction for random encounter (optional)
            player_attack_instruction: Pre-calculated player attack result (optional)
            steal_instruction: Instructions for steal attempts (optional)

        Returns:
            Complete prompt string for LLM
        """
        # Build base game state context
        prompt = f"""You are an experienced Dungeon Master running a D&D 5e game.

CURRENT LOCATION: {game_session.current_location}
SCENE: {game_session.scene_description if game_session.scene_description else "The adventure continues..."}
TIME: Day {game_session.day}, {game_session.time_of_day}
"""

        # Add conversation summary if it exists (for context continuity)
        if conversation_summary:
            prompt += f"\nPREVIOUS SESSION SUMMARY:\n{conversation_summary}\n"

        # Add location context for better narrative consistency
        current_loc = game_session.get_current_location_obj()
        if current_loc:
            # Don't explicitly mention visit count - just note it's a return
            if current_loc.visit_count > 1:
                prompt += f"NOTE: The party has been here before. Describe naturally without explicitly counting visits.\n"

            # Mention defeated enemies for atmosphere
            if current_loc.defeated_enemies:
                enemies = ", ".join(list(current_loc.defeated_enemies)[:3])
                prompt += f"AFTERMATH: These enemies were defeated here previously: {enemies}. You may mention remains/corpses if appropriate.\n"

        # Add NPCs/Monsters if present
        if game_session.npcs_present:
            prompt += f"\nNPCs/CREATURES PRESENT: {', '.join(game_session.npcs_present)}\n"

        # Add combat state if in combat
        if game_session.combat.in_combat:
            prompt += f"\nCOMBAT STATUS: Round {game_session.combat.round_number}, {game_session.combat.get_current_turn()}'s turn\n"
            prompt += f"Initiative Order: {', '.join([f'{name} ({init})' for name, init in game_session.combat.initiative_order])}\n"

        # Add active quests
        if game_session.active_quests:
            active = [q for q in game_session.active_quests if q.get('status') == 'active']
            if active:
                quest_names = [q['name'] for q in active[:2]]  # Show up to 2 active quests
                prompt += f"\nACTIVE QUESTS: {', '.join(quest_names)}\n"

        prompt += "\n"

        # Add RAG context if relevant
        if rag_context and rag_context != "No specific rules retrieved." and rag_context != "No highly relevant rules found.":
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

        # Add encounter instruction if present (hidden from player, only GM sees this)
        if encounter_instruction:
            prompt += f"""{encounter_instruction}

"""

        # Add player attack instruction if present (hidden from player, only GM sees this)
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
