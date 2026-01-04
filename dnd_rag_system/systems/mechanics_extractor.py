"""
D&D Mechanics Extraction System

Uses a small LLM to extract game mechanics from GM narrative responses.
Automatically parses damage, healing, conditions, spell usage, etc. from natural language.

Example:
    Narrative: "The goblin's rusty axe strikes Thorin's shoulder, dealing 8 slashing damage!"
    Extracted: {"damage": [{"target": "Thorin", "amount": 8, "type": "slashing"}]}
"""

import json
import subprocess
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Default model for mechanics extraction
# Change this in one place to switch models across the entire system
# qwen2.5:3b is fast and reliable for structured extraction
# Note: gemma3:4b was tested but is slower; qwen models are optimized for JSON output
DEFAULT_MECHANICS_MODEL = "qwen2.5:3b"  # Fast, reliable JSON extraction (1.9GB)


class MechanicType(Enum):
    """Types of game mechanics that can be extracted."""
    DAMAGE = "damage"
    HEALING = "healing"
    CONDITION_ADD = "condition_add"
    CONDITION_REMOVE = "condition_remove"
    SPELL_CAST = "spell_cast"
    ITEM_USE = "item_use"
    DEATH = "death"
    UNCONSCIOUS = "unconscious"


@dataclass
class ExtractedMechanics:
    """
    Structured representation of game mechanics extracted from narrative.

    All fields are lists to handle multiple effects in one narrative.
    """
    # Damage dealt: [{"target": "character_name", "amount": 8, "type": "slashing"}]
    damage: List[Dict[str, Any]] = field(default_factory=list)

    # Healing: [{"target": "character_name", "amount": 5, "source": "potion"}]
    healing: List[Dict[str, Any]] = field(default_factory=list)

    # Conditions added: [{"target": "character_name", "condition": "poisoned", "duration": 3}]
    conditions_added: List[Dict[str, Any]] = field(default_factory=list)

    # Conditions removed: [{"target": "character_name", "condition": "stunned"}]
    conditions_removed: List[Dict[str, Any]] = field(default_factory=list)

    # Spell slots used: [{"caster": "character_name", "level": 2, "spell": "hold person"}]
    spell_slots_used: List[Dict[str, Any]] = field(default_factory=list)

    # Items consumed: [{"character": "character_name", "item": "health potion", "quantity": 1}]
    items_consumed: List[Dict[str, Any]] = field(default_factory=list)
    
    # Items acquired/picked up: [{"character": "character_name", "item": "rope", "quantity": 1}]
    items_acquired: List[Dict[str, Any]] = field(default_factory=list)

    # Character deaths: [{"character": "character_name"}]
    deaths: List[Dict[str, Any]] = field(default_factory=list)

    # Character knocked unconscious: [{"character": "character_name"}]
    unconscious: List[Dict[str, Any]] = field(default_factory=list)

    # NPCs/Monsters introduced: [{"name": "Goblin", "description": "rusty sword wielding goblin"}]
    npcs_introduced: List[Dict[str, Any]] = field(default_factory=list)

    def has_mechanics(self) -> bool:
        """Check if any mechanics were extracted."""
        return any([
            self.damage,
            self.healing,
            self.conditions_added,
            self.conditions_removed,
            self.spell_slots_used,
            self.items_consumed,
            self.items_acquired,
            self.deaths,
            self.unconscious,
            self.npcs_introduced
        ])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "damage": self.damage,
            "healing": self.healing,
            "conditions_added": self.conditions_added,
            "conditions_removed": self.conditions_removed,
            "spell_slots_used": self.spell_slots_used,
            "items_consumed": self.items_consumed,
            "items_acquired": self.items_acquired,
            "deaths": self.deaths,
            "unconscious": self.unconscious,
            "npcs_introduced": self.npcs_introduced
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedMechanics":
        """Create from dictionary."""
        return cls(
            damage=data.get("damage", []),
            healing=data.get("healing", []),
            conditions_added=data.get("conditions_added", []),
            conditions_removed=data.get("conditions_removed", []),
            spell_slots_used=data.get("spell_slots_used", []),
            items_consumed=data.get("items_consumed", []),
            items_acquired=data.get("items_acquired", []),
            deaths=data.get("deaths", []),
            unconscious=data.get("unconscious", []),
            npcs_introduced=data.get("npcs_introduced", [])
        )


class MechanicsExtractor:
    """
    Extracts game mechanics from GM narrative using a small LLM.

    Uses structured prompting to get consistent JSON output.
    The default model can be changed via DEFAULT_MECHANICS_MODEL constant.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MECHANICS_MODEL,
        debug: bool = False,
        timeout: int = 30
    ):
        """
        Initialize mechanics extractor.

        Args:
            model_name: Ollama model to use (default: DEFAULT_MECHANICS_MODEL)
            debug: Enable debug logging
            timeout: Query timeout in seconds
        """
        self.model_name = model_name
        self.debug = debug
        self.timeout = timeout

        if self.debug:
            logger.setLevel(logging.DEBUG)
            # Add console handler if not already present
            if not logger.handlers:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)
                formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)

    def extract(
        self,
        narrative: str,
        character_names: Optional[List[str]] = None,
        existing_npcs: Optional[List[str]] = None
    ) -> ExtractedMechanics:
        """
        Extract game mechanics from narrative text.

        Args:
            narrative: GM narrative response
            character_names: List of character names in the party (helps with extraction)
            existing_npcs: List of NPCs already present (to avoid re-adding them)

        Returns:
            ExtractedMechanics object with all extracted mechanics
        """
        if not narrative or len(narrative.strip()) < 10:
            return ExtractedMechanics()

        # Build extraction prompt
        prompt = self._build_extraction_prompt(narrative, character_names, existing_npcs)

        if self.debug:
            logger.debug("=" * 80)
            logger.debug("MECHANICS EXTRACTION PROMPT:")
            logger.debug("-" * 80)
            logger.debug(prompt)
            logger.debug("=" * 80)

        # Query LLM
        try:
            raw_response = self._query_ollama(prompt)

            if self.debug:
                logger.debug("RAW LLM RESPONSE:")
                logger.debug(raw_response)

            # Parse JSON response
            mechanics = self._parse_response(raw_response)
            
            # Post-process: Filter out NPCs that are already present
            # The LLM sometimes includes them despite instructions
            if mechanics.npcs_introduced and existing_npcs:
                existing_lower = [npc.lower() for npc in existing_npcs]
                filtered_npcs = []
                for npc in mechanics.npcs_introduced:
                    npc_name = npc.get('name', '').strip()
                    if npc_name.lower() not in existing_lower:
                        filtered_npcs.append(npc)
                    elif self.debug:
                        logger.debug(f"🔧 Filtered already-present NPC: {npc_name}")
                mechanics.npcs_introduced = filtered_npcs

            if self.debug and mechanics.has_mechanics():
                logger.debug("EXTRACTED MECHANICS:")
                logger.debug(json.dumps(mechanics.to_dict(), indent=2))

            return mechanics

        except Exception as e:
            logger.error(f"Mechanics extraction failed: {e}")
            return ExtractedMechanics()

    def _build_extraction_prompt(
        self,
        narrative: str,
        character_names: Optional[List[str]] = None,
        existing_npcs: Optional[List[str]] = None
    ) -> str:
        """Build the extraction prompt for the LLM."""

        char_context = ""
        if character_names:
            char_context = f"\nKNOWN CHARACTERS: {', '.join(character_names)}\n"
        
        npc_context = ""
        if existing_npcs:
            npc_context = f"\nALREADY PRESENT NPCs: {', '.join(existing_npcs)}\n**IMPORTANT**: Do NOT add these NPCs to npcs_introduced - they already exist!\n"

        prompt = f"""Extract D&D game mechanics from this narrative. Output ONLY valid JSON, no other text.

NARRATIVE:
{narrative}
{char_context}{npc_context}
Extract mechanics and output as JSON with this exact schema:
{{
  "damage": [
    {{"target": "TARGET_NAME", "amount": NUMBER, "type": "DAMAGE_TYPE"}}
  ],
  "healing": [
    {{"target": "TARGET_NAME", "amount": NUMBER, "source": "SOURCE"}}
  ],
  "conditions_added": [
    {{"target": "TARGET_NAME", "condition": "CONDITION_NAME", "duration": NUMBER}}
  ],
  "conditions_removed": [
    {{"target": "TARGET_NAME", "condition": "CONDITION_NAME"}}
  ],
  "spell_slots_used": [
    {{"caster": "CASTER_NAME", "level": NUMBER, "spell": "SPELL_NAME"}}
  ],
  "items_consumed": [
    {{"character": "CHARACTER_NAME", "item": "ITEM_NAME", "quantity": NUMBER}}
  ],
  "items_acquired": [
    {{"character": "CHARACTER_NAME", "item": "ITEM_NAME", "quantity": NUMBER}}
  ],
  "deaths": [
    {{"character": "CHARACTER_NAME"}}
  ],
  "unconscious": [
    {{"character": "CHARACTER_NAME"}}
  ],
  "npcs_introduced": [
    {{"name": "NPC_NAME", "type": "NPC_TYPE"}}
  ]
}}

DAMAGE EXAMPLES (who receives damage):
- "Thorin strikes the goblin" → {{"target": "goblin", "amount": X}}
- "The goblin hits Thorin" → {{"target": "Thorin", "amount": X}}
- "Your sword cuts the wolf" → {{"target": "wolf", "amount": X}}
- "The wolf bites you" → {{"target": "you", "amount": X}}
- "Arrow embeds into the orc" → {{"target": "orc", "amount": X}}

RULES:
- Only include fields where something happened
- Empty arrays are OK
- Use exact names from the narrative for target/character fields
- **DAMAGE TARGET**: Who RECEIVES damage, not who deals it
  - "Thorin strikes the goblin" → target: "Goblin" (goblin receives damage)
  - "The goblin hits you" → target: "you" or player name (player receives damage)
  - "Your sword cuts the wolf" → target: "Wolf" (wolf receives damage)
- Damage types: slashing, piercing, bludgeoning, fire, cold, lightning, poison, acid, etc.
- Conditions: poisoned, stunned, paralyzed, frightened, charmed, etc.
- Items consumed: When character drinks potion, eats food, uses consumable
- Items acquired: When character picks up, takes, finds, or receives items
- NPCs: Extract ONLY NEW creatures/monsters/NPCs that PHYSICALLY APPEAR in THIS narrative
  - CRITICAL: ONLY include if the NPC actually SHOWS UP and is PRESENT in this scene

NPC APPEARANCE EXAMPLES:
- "A goblin jumps out!" → {{"name": "Goblin", "type": "enemy"}} (goblin appears)
- "Guards arrive and surround you" → {{"name": "Guards", "type": "neutral"}} (guards appear)
- "Guards are called" → NO NPC (just mentioned, not present yet)
- "Someone shouts for the guards" → NO NPC (not present yet)
- "The innkeeper watches" → NO NPC if innkeeper is in ALREADY PRESENT list above

IMPORTANT NPC RULES:
- "The innkeeper watches" → DO NOT include if already in ALREADY PRESENT NPCs list
- DO NOT extract NPCs that were already present (see ALREADY PRESENT NPCs above)
- DO NOT hallucinate or invent NPCs not explicitly mentioned
- NPC types: "enemy" for hostile creatures, "friendly" for allies, "neutral" for NPCs
- If no NEW mechanics found, return {{"damage": [], "healing": [], "npcs_introduced": []}}

JSON:"""

        return prompt

    def _query_ollama(self, prompt: str) -> str:
        """Query Ollama with the extraction prompt."""
        try:
            result = subprocess.run(
                ['ollama', 'run', self.model_name, prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                raise Exception(f"Ollama error: {result.stderr}")

            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise Exception(f"Ollama query timed out after {self.timeout}s")
        except FileNotFoundError:
            raise Exception("Ollama not found. Install from https://ollama.ai")
        except Exception as e:
            raise Exception(f"Ollama query failed: {e}")

    def _parse_response(self, raw_response: str) -> ExtractedMechanics:
        """
        Parse LLM response into ExtractedMechanics.

        Handles various JSON formats and error cases.
        """
        # Clean response (remove markdown code blocks if present)
        response = raw_response.strip()

        # Remove markdown code blocks
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        # Try to find JSON in the response
        # Sometimes LLMs add text before/after JSON
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1

        if start_idx >= 0 and end_idx > start_idx:
            response = response[start_idx:end_idx]

        try:
            data = json.loads(response)
            return ExtractedMechanics.from_dict(data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response}")
            return ExtractedMechanics()

    def extract_and_log(
        self,
        narrative: str,
        character_names: Optional[List[str]] = None
    ) -> ExtractedMechanics:
        """
        Extract mechanics and log results (convenience method).

        Useful for debugging and testing.
        """
        mechanics = self.extract(narrative, character_names)

        if mechanics.has_mechanics():
            print("\n" + "=" * 80)
            print("MECHANICS EXTRACTED FROM NARRATIVE:")
            print("-" * 80)
            print(f"Narrative: {narrative[:100]}...")
            print("\nExtracted:")

            if mechanics.damage:
                print(f"  💥 Damage: {mechanics.damage}")
            if mechanics.healing:
                print(f"  ❤️  Healing: {mechanics.healing}")
            if mechanics.conditions_added:
                print(f"  🔴 Conditions Added: {mechanics.conditions_added}")
            if mechanics.conditions_removed:
                print(f"  🟢 Conditions Removed: {mechanics.conditions_removed}")
            if mechanics.spell_slots_used:
                print(f"  ✨ Spells Cast: {mechanics.spell_slots_used}")
            if mechanics.items_consumed:
                print(f"  🎒 Items Used: {mechanics.items_consumed}")
            if mechanics.items_acquired:
                print(f"  📦 Items Acquired: {mechanics.items_acquired}")
            if mechanics.deaths:
                print(f"  ☠️  Deaths: {mechanics.deaths}")
            if mechanics.unconscious:
                print(f"  😵 Unconscious: {mechanics.unconscious}")
            if mechanics.npcs_introduced:
                print(f"  🎭 NPCs Introduced: {mechanics.npcs_introduced}")

            print("=" * 80)
        else:
            if self.debug:
                print(f"No mechanics extracted from: {narrative[:100]}...")

        return mechanics
