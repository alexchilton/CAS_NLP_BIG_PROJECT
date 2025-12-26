"""
Action Validator - Reality Check System for D&D RAG

Implements hybrid entity tracking:
- Strictly validates key entities (combatants, NPCs, items, spells)
- Allows LLM to improvise environmental flavor
- Prevents hallucination of non-existent targets
- Encourages NPC conversation with smart introduction logic
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
import re
from enum import Enum


class ActionType(Enum):
    """Types of player actions"""
    COMBAT = "combat"           # Attack, damage dealing
    SPELL_CAST = "spell_cast"   # Casting spells
    CONVERSATION = "conversation"  # Talking to NPCs
    ITEM_USE = "item_use"       # Using items/equipment
    EXPLORATION = "exploration" # Looking, searching, moving
    UNKNOWN = "unknown"         # Couldn't determine


class ValidationResult(Enum):
    """Result of validation"""
    VALID = "valid"              # Action is valid, proceed normally
    INVALID = "invalid"          # Action is invalid, prompt GM to narrate failure
    NPC_INTRODUCTION = "npc_introduction"  # NPC doesn't exist, allow GM to introduce
    FUZZY_MATCH = "fuzzy_match"  # Close match found (e.g., "goblin" → "Goblin Scout")


@dataclass
class ActionIntent:
    """Parsed player action intent"""
    action_type: ActionType
    target: Optional[str] = None      # Who/what is being targeted
    resource: Optional[str] = None    # Spell name, item name, etc.
    raw_input: str = ""               # Original player input

    def __repr__(self):
        return f"ActionIntent(type={self.action_type.value}, target={self.target}, resource={self.resource})"


@dataclass
class ValidationReport:
    """Result of validating an action against game state"""
    result: ValidationResult
    action: ActionIntent
    message: str = ""                 # Explanation for GM prompt
    matched_entity: Optional[str] = None  # If fuzzy matched, the actual entity name
    suggestions: List[str] = None     # Alternative suggestions

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class ActionValidator:
    """
    Validates player actions against game state before GM generation.
    Prevents hallucinations while preserving narrative flexibility.
    """

    # Keywords for intent detection
    COMBAT_KEYWORDS = [
        'attack', 'hit', 'strike', 'slash', 'stab', 'shoot', 'fire at',
        'punch', 'kick', 'swing', 'swing at', 'charge', 'lunge at', 'fight',
        'smash', 'bash', 'cleave', 'thrust', 'parry', 'block and attack'
    ]

    SPELL_KEYWORDS = [
        'cast', 'casting', 'spell', 'magic missile', 'fireball', 'healing word',
        'cure wounds', 'eldritch blast', 'sacred flame', 'guiding bolt'
    ]

    CONVERSATION_KEYWORDS = [
        'talk to', 'speak to', 'ask', 'tell', 'say to', 'greet', 'chat with',
        'question', 'inquire', 'converse', 'discuss with', 'address',
        'hello', 'hi', 'hey', '"'  # Quoted speech
    ]

    ITEM_KEYWORDS = [
        'use', 'drink', 'eat', 'equip', 'wear', 'wield', 'open',
        'pull out', 'take out', 'consume', 'apply', 'ready', 'draw',
        'hold', 'grab', 'reach for'
    ]

    def __init__(self, debug: bool = False):
        self.debug = debug

    def analyze_intent(self, user_input: str) -> ActionIntent:
        """
        Parse user input to determine action type, target, and resources.

        Args:
            user_input: Raw player input

        Returns:
            ActionIntent with parsed information
        """
        lower_input = user_input.lower().strip()

        # Check for combat actions
        if any(keyword in lower_input for keyword in self.COMBAT_KEYWORDS):
            target = self._extract_target(lower_input, self.COMBAT_KEYWORDS)
            return ActionIntent(
                action_type=ActionType.COMBAT,
                target=target,
                raw_input=user_input
            )

        # Check for spell casting
        if any(keyword in lower_input for keyword in self.SPELL_KEYWORDS):
            target = self._extract_target(lower_input, self.SPELL_KEYWORDS)
            spell = self._extract_spell(lower_input)
            return ActionIntent(
                action_type=ActionType.SPELL_CAST,
                target=target,
                resource=spell,
                raw_input=user_input
            )

        # Check for conversation
        if any(keyword in lower_input for keyword in self.CONVERSATION_KEYWORDS):
            target = self._extract_conversation_target(lower_input)
            return ActionIntent(
                action_type=ActionType.CONVERSATION,
                target=target,
                raw_input=user_input
            )

        # Check for item use
        if any(keyword in lower_input for keyword in self.ITEM_KEYWORDS):
            item = self._extract_item(lower_input)
            return ActionIntent(
                action_type=ActionType.ITEM_USE,
                resource=item,
                raw_input=user_input
            )

        # Default to exploration
        return ActionIntent(
            action_type=ActionType.EXPLORATION,
            raw_input=user_input
        )

    def validate_action(self, intent: ActionIntent, game_session) -> ValidationReport:
        """
        Validate action intent against current game state.

        Args:
            intent: Parsed action intent
            game_session: Current GameSession object

        Returns:
            ValidationReport with result and guidance for GM prompting
        """

        # Exploration actions always valid (LLM handles description)
        if intent.action_type == ActionType.EXPLORATION:
            return ValidationReport(
                result=ValidationResult.VALID,
                action=intent,
                message="Player is exploring the environment. Narrate what they discover."
            )

        # Validate combat actions
        if intent.action_type == ActionType.COMBAT:
            return self._validate_combat(intent, game_session)

        # Validate spell casting
        if intent.action_type == ActionType.SPELL_CAST:
            return self._validate_spell(intent, game_session)

        # Validate NPC conversation
        if intent.action_type == ActionType.CONVERSATION:
            return self._validate_conversation(intent, game_session)

        # Validate item use
        if intent.action_type == ActionType.ITEM_USE:
            return self._validate_item(intent, game_session)

        # Unknown action - let GM handle
        return ValidationReport(
            result=ValidationResult.VALID,
            action=intent,
            message="Process player action naturally."
        )

    def _validate_combat(self, intent: ActionIntent, game_session) -> ValidationReport:
        """Validate combat action - STRICT validation"""

        if not intent.target:
            return ValidationReport(
                result=ValidationResult.VALID,
                action=intent,
                message="Player is attacking but didn't specify target clearly. Ask for clarification or describe a miss."
            )

        # Check combat state first
        combatants = []
        if game_session.combat and game_session.combat.initiative_order:
            combatants = [c[0].lower() for c in game_session.combat.initiative_order]  # initiative_order is list of tuples (name, init)

        # Check NPCs present
        npcs = [npc.lower() for npc in game_session.npcs_present]

        all_targets = combatants + npcs
        target_lower = intent.target.lower()

        # Exact match
        if target_lower in all_targets:
            matched = intent.target
            if target_lower in combatants:
                # Find actual name from combat state
                for c in game_session.combat_state.initiative_order:
                    if c.name.lower() == target_lower:
                        matched = c.name
                        break
            return ValidationReport(
                result=ValidationResult.VALID,
                action=intent,
                matched_entity=matched,
                message=f"Player attacks {matched}. Resolve the attack and describe the outcome."
            )

        # Fuzzy match (e.g., "goblin" → "Goblin Scout")
        fuzzy_match = self._fuzzy_match(target_lower, all_targets)
        if fuzzy_match:
            return ValidationReport(
                result=ValidationResult.FUZZY_MATCH,
                action=intent,
                matched_entity=fuzzy_match,
                message=f"Player attacks {fuzzy_match}. Resolve the attack and describe the outcome."
            )

        # No match - invalid combat target
        available = ", ".join([n.title() for n in all_targets]) if all_targets else "none"
        return ValidationReport(
            result=ValidationResult.INVALID,
            action=intent,
            message=f"Player tries to attack '{intent.target}', but no such enemy is present. "
                   f"Available targets: {available}. Narrate the player's confusion or missed swing at empty air."
        )

    def _validate_conversation(self, intent: ActionIntent, game_session) -> ValidationReport:
        """Validate conversation - LENIENT validation, encourage NPC introduction"""

        if not intent.target:
            # No specific target, just general speech
            return ValidationReport(
                result=ValidationResult.VALID,
                action=intent,
                message="Player is speaking. If NPCs are present, they may respond. Otherwise, describe the echo or atmosphere."
            )

        npcs = [npc.lower() for npc in game_session.npcs_present]
        target_lower = intent.target.lower()

        # Exact match
        if target_lower in npcs:
            return ValidationReport(
                result=ValidationResult.VALID,
                action=intent,
                matched_entity=intent.target,
                message=f"Player converses with {intent.target}. Roleplay this NPC's response based on their personality and the situation."
            )

        # Fuzzy match
        fuzzy_match = self._fuzzy_match(target_lower, npcs)
        if fuzzy_match:
            return ValidationReport(
                result=ValidationResult.FUZZY_MATCH,
                action=intent,
                matched_entity=fuzzy_match,
                message=f"Player converses with {fuzzy_match}. Roleplay this NPC's response."
            )

        # NPC doesn't exist - ALLOW GM TO INTRODUCE
        # This is the magic for rich NPC interactions!
        return ValidationReport(
            result=ValidationResult.NPC_INTRODUCTION,
            action=intent,
            message=f"Player attempts to interact with '{intent.target}'. "
                   f"If such an NPC would logically exist in this location (e.g., bartender in tavern, "
                   f"guard at gate, merchant in shop), introduce them naturally and roleplay their response. "
                   f"If it makes no sense for this NPC to exist here, narrate that no such person is present. "
                   f"Remember to maintain consistency with the established scene."
        )

    def _validate_spell(self, intent: ActionIntent, game_session) -> ValidationReport:
        """Validate spell casting - check spell known and slots available"""

        if not game_session.character_state:
            return ValidationReport(
                result=ValidationResult.VALID,
                action=intent,
                message="No character loaded. Process spell casting narratively."
            )

        char_state = game_session.character_state
        spell_name = intent.resource

        # Check if spell is known (from character's spells list)
        known_spells = [s.lower() for s in getattr(char_state, 'spells', [])]
        character_class = getattr(char_state, 'character_class', '')

        # If character has no spells AND tries to cast one, it's invalid
        # (e.g., Fighter trying to cast Fireball)
        if spell_name and not known_spells:
            non_caster_classes = ['Fighter', 'Barbarian', 'Rogue', 'Monk']
            if character_class in non_caster_classes:
                return ValidationReport(
                    result=ValidationResult.INVALID,
                    action=intent,
                    message=f"Player tries to cast '{spell_name}', but as a {character_class}, they have no spellcasting ability. "
                           f"Narrate the character's inability to use magic.",
                )

        # If character HAS spells, check if this specific spell is known
        if spell_name and known_spells and spell_name.lower() not in known_spells:
            return ValidationReport(
                result=ValidationResult.INVALID,
                action=intent,
                message=f"Player tries to cast '{spell_name}', but this spell is not in their known spells. "
                       f"Narrate the character's inability to recall or cast this spell.",
                suggestions=known_spells[:5]  # Show first 5 known spells
            )

        # TODO: Check spell slots when spell slot tracking is fully implemented
        # For now, assume spell slots are available

        target_msg = f" at {intent.target}" if intent.target else ""
        return ValidationReport(
            result=ValidationResult.VALID,
            action=intent,
            message=f"Player casts {spell_name}{target_msg}. Describe the spell's effects and outcome."
        )

    def _validate_item(self, intent: ActionIntent, game_session) -> ValidationReport:
        """Validate item use - check if character has the item"""

        if not game_session.character_state:
            return ValidationReport(
                result=ValidationResult.VALID,
                action=intent,
                message="No character loaded. Process item use narratively."
            )

        char_state = game_session.character_state
        item_name = intent.resource

        if not item_name:
            return ValidationReport(
                result=ValidationResult.VALID,
                action=intent,
                message="Player wants to use an item. Ask for clarification or list available items."
            )

        # Check inventory
        inventory_items = [item.lower() for item in char_state.inventory]

        if item_name.lower() not in inventory_items and inventory_items:
            return ValidationReport(
                result=ValidationResult.INVALID,
                action=intent,
                message=f"Player tries to use '{item_name}', but it's not in their inventory. "
                       f"Narrate that they search their pack but don't find it.",
                suggestions=inventory_items[:5]
            )

        return ValidationReport(
            result=ValidationResult.VALID,
            action=intent,
            message=f"Player uses {item_name}. Describe the item's effect or outcome."
        )

    def _extract_target(self, text: str, keywords: List[str]) -> Optional[str]:
        """Extract target entity from text after action keywords"""
        for keyword in keywords:
            if keyword in text:
                # Get text after the keyword
                parts = text.split(keyword, 1)
                if len(parts) > 1:
                    # Clean up and extract first noun-like word(s)
                    after = parts[1].strip()
                    # Remove common leading prepositions
                    after = re.sub(r'^(the|at|a|an)\s+', '', after)
                    # Stop at common prepositions that indicate end of target
                    # e.g., "goblin with my sword" -> stop at "with"
                    stop_words = ['with', 'using', 'and', 'then', ',']
                    for stop in stop_words:
                        if ' ' + stop + ' ' in ' ' + after:
                            after = after.split(' ' + stop + ' ')[0]
                            break
                    # Take first 1-2 words as target (reduced from 3)
                    words = after.split()[:2]
                    if words:
                        return ' '.join(words).strip('.,!?')
        return None

    def _extract_conversation_target(self, text: str) -> Optional[str]:
        """Extract NPC name from conversation text"""
        # Pattern: "talk to X", "ask X", "say to X", etc.
        patterns = [
            r'(?:talk|speak|say)\s+(?:to|with)\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(?:ask|tell|greet|question)\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(?:hello|hi|hey)\s+(\w+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # If there's quoted speech, try to find name before/after quote
        if '"' in text or "'" in text:
            # Look for pattern like "X, ..." or "... X"
            parts = re.split(r'["\']', text)
            if len(parts) >= 2:
                before = parts[0].strip()
                after = parts[-1].strip() if len(parts) > 2 else ""

                # Check for name in "to X" or just "X"
                for part in [before, after]:
                    match = re.search(r'(?:to\s+)?(?:the\s+)?(\w+(?:\s+\w+)?)$', part, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()

        return None

    def _extract_spell(self, text: str) -> Optional[str]:
        """Extract spell name from text"""
        # Common spell names (could expand this or use RAG)
        common_spells = [
            'magic missile', 'fireball', 'cure wounds', 'healing word',
            'eldritch blast', 'sacred flame', 'guiding bolt', 'shield',
            'mage armor', 'detect magic', 'identify', 'sleep', 'charm person'
        ]

        for spell in common_spells:
            if spell in text:
                return spell.title()

        # Try to extract after "cast"
        if 'cast' in text:
            after_cast = text.split('cast', 1)[1].strip()
            # Remove "at", "on", etc.
            after_cast = re.sub(r'\s+(at|on|towards?)\s+.*', '', after_cast)
            words = after_cast.split()[:3]
            if words:
                return ' '.join(words).strip('.,!?').title()

        return None

    def _extract_item(self, text: str) -> Optional[str]:
        """Extract item name from text"""
        item_keywords = ['use', 'drink', 'eat', 'equip', 'wear', 'wield', 'ready', 'draw', 'hold', 'grab', 'reach for', 'pull out', 'take out']

        for keyword in item_keywords:
            if keyword in text:
                after = text.split(keyword, 1)[1].strip()
                # Remove articles
                after = re.sub(r'^(the|a|an|my)\s+', '', after)
                # Remove trailing "and..." phrases
                after = re.sub(r'\s+and\s+.*', '', after)
                # Take first 1-3 words
                words = after.split()[:3]
                if words:
                    return ' '.join(words).strip('.,!?').title()

        return None

    def _fuzzy_match(self, target: str, entities: List[str], threshold: float = 0.6) -> Optional[str]:
        """
        Attempt fuzzy matching for target against entity list.
        e.g., "goblin" matches "Goblin Scout"
        """
        target = target.lower()

        for entity in entities:
            entity_lower = entity.lower()
            # Substring match
            if target in entity_lower or entity_lower in target:
                return entity

            # Word overlap
            target_words = set(target.split())
            entity_words = set(entity_lower.split())
            overlap = len(target_words & entity_words)

            if overlap > 0 and overlap / max(len(target_words), len(entity_words)) >= threshold:
                return entity

        return None


def create_context_aware_prompt(validation: ValidationReport, base_context: str) -> str:
    """
    Create GM prompt that incorporates validation results.

    Args:
        validation: ValidationReport from action validation
        base_context: Base context (location, NPCs, etc.)

    Returns:
        Enhanced prompt for GM LLM
    """

    # Add validation guidance to prompt
    guidance = f"\n\n**Action Guidance**: {validation.message}"

    if validation.result == ValidationResult.INVALID:
        guidance += "\n**IMPORTANT**: This action should FAIL or be impossible. Narrate accordingly without introducing the non-existent entity."

    if validation.result == ValidationResult.NPC_INTRODUCTION:
        guidance += "\n**NPC Introduction**: You may introduce this NPC if contextually appropriate. If introduced, describe them vividly."

    if validation.matched_entity and validation.matched_entity != validation.action.target:
        guidance += f"\n**Note**: Player said '{validation.action.target}', but they likely mean '{validation.matched_entity}'."

    if validation.suggestions:
        guidance += f"\n**Available alternatives**: {', '.join(validation.suggestions)}"

    return base_context + guidance
