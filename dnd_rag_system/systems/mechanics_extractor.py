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
DEFAULT_MECHANICS_MODEL = "qwen2.5:3b"  # Fast and accurate for structured extraction


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

    # Character deaths: [{"character": "character_name"}]
    deaths: List[Dict[str, Any]] = field(default_factory=list)

    # Character knocked unconscious: [{"character": "character_name"}]
    unconscious: List[Dict[str, Any]] = field(default_factory=list)

    def has_mechanics(self) -> bool:
        """Check if any mechanics were extracted."""
        return any([
            self.damage,
            self.healing,
            self.conditions_added,
            self.conditions_removed,
            self.spell_slots_used,
            self.items_consumed,
            self.deaths,
            self.unconscious
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
            "deaths": self.deaths,
            "unconscious": self.unconscious
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
            deaths=data.get("deaths", []),
            unconscious=data.get("unconscious", [])
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

    def extract(
        self,
        narrative: str,
        character_names: Optional[List[str]] = None
    ) -> ExtractedMechanics:
        """
        Extract game mechanics from narrative text.

        Args:
            narrative: GM narrative response
            character_names: List of character names in the party (helps with extraction)

        Returns:
            ExtractedMechanics object with all extracted mechanics
        """
        if not narrative or len(narrative.strip()) < 10:
            return ExtractedMechanics()

        # Build extraction prompt
        prompt = self._build_extraction_prompt(narrative, character_names)

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
        character_names: Optional[List[str]] = None
    ) -> str:
        """Build the extraction prompt for the LLM."""

        char_context = ""
        if character_names:
            char_context = f"\nKNOWN CHARACTERS: {', '.join(character_names)}\n"

        prompt = f"""Extract D&D game mechanics from this narrative. Output ONLY valid JSON, no other text.

NARRATIVE:
{narrative}
{char_context}
Extract mechanics and output as JSON with this exact schema:
{{
  "damage": [
    {{"target": "character_name", "amount": 8, "type": "slashing"}}
  ],
  "healing": [
    {{"target": "character_name", "amount": 5, "source": "potion"}}
  ],
  "conditions_added": [
    {{"target": "character_name", "condition": "poisoned", "duration": 3}}
  ],
  "conditions_removed": [
    {{"target": "character_name", "condition": "stunned"}}
  ],
  "spell_slots_used": [
    {{"caster": "character_name", "level": 2, "spell": "hold person"}}
  ],
  "items_consumed": [
    {{"character": "character_name", "item": "health potion", "quantity": 1}}
  ],
  "deaths": [
    {{"character": "character_name"}}
  ],
  "unconscious": [
    {{"character": "character_name"}}
  ]
}}

RULES:
- Only include fields where something happened
- Empty arrays are OK
- Use exact character names from the narrative
- Damage types: slashing, piercing, bludgeoning, fire, cold, lightning, poison, acid, etc.
- Conditions: poisoned, stunned, paralyzed, frightened, charmed, etc.
- If no mechanics found, return {{"damage": [], "healing": []}}

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
            if mechanics.deaths:
                print(f"  ☠️  Deaths: {mechanics.deaths}")
            if mechanics.unconscious:
                print(f"  😵 Unconscious: {mechanics.unconscious}")

            print("=" * 80)
        else:
            if self.debug:
                print(f"No mechanics extracted from: {narrative[:100]}...")

        return mechanics
