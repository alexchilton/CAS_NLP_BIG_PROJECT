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
import logging

logger = logging.getLogger(__name__)


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
        'attack', 'hit', 'strike', 'slash', 'stab', 'shoot', 'fire at', 'fire',
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
        self.party_character_names = []  # List of party member names for parsing

    def set_party_characters(self, character_names: List[str]):
        """
        Set the list of party character names for parsing.

        Args:
            character_names: List of character names in the party
        """
        self.party_character_names = [name.lower() for name in character_names]

    def extract_acting_character(self, user_input: str) -> Optional[str]:
        """
        Extract which character is acting from the player input.

        Looks for patterns like:
        - "Thorin attacks the goblin" -> "Thorin"
        - "Elara casts Fire Bolt" -> "Elara"
        - "Gimli drinks a healing potion" -> "Gimli"

        Args:
            user_input: Raw player input

        Returns:
            Character name (title-cased) if found, None otherwise
        """
        if not self.party_character_names:
            return None

        lower_input = user_input.lower().strip()

        # Check if input starts with a character name
        # e.g., "Thorin attacks", "Elara casts", "Gimli drinks"
        for char_name in self.party_character_names:
            # Pattern: "CharName <verb>" (character name at start)
            if lower_input.startswith(char_name + ' '):
                # Return title-cased version
                return char_name.title()

            # Pattern: "<verb> CharName" (less common, but possible)
            # e.g., "I command Thorin to attack"
            if char_name in lower_input:
                # More specific check - char name followed by action verb
                char_pattern = rf'\b{re.escape(char_name)}\b'
                if re.search(char_pattern, lower_input):
                    return char_name.title()

        return None

    def analyze_intent(self, user_input: str) -> ActionIntent:
        """
        Parse user input to determine action type, target, and resources.

        Args:
            user_input: Raw player input

        Returns:
            ActionIntent with parsed information
        """
        lower_input = user_input.lower().strip()

        # Check for spell casting FIRST (before combat, to avoid "fireball" matching "fire")
        if any(keyword in lower_input for keyword in self.SPELL_KEYWORDS):
            spell = self._extract_spell(lower_input)
            target = self._extract_spell_target(lower_input, spell)  # NEW: spell-aware target extraction
            return ActionIntent(
                action_type=ActionType.SPELL_CAST,
                target=target,
                resource=spell,
                raw_input=user_input
            )

        # Check for combat actions
        if any(keyword in lower_input for keyword in self.COMBAT_KEYWORDS):
            target = self._extract_target(lower_input, self.COMBAT_KEYWORDS)
            weapon = self._extract_weapon(lower_input)  # NEW: Extract weapon used
            return ActionIntent(
                action_type=ActionType.COMBAT,
                target=target,
                resource=weapon,  # Store weapon in resource field
                raw_input=user_input
            )

        # Check for item use (BEFORE conversation to catch "use", "drink", etc.)
        # Use pattern matching instead of keyword list since we updated _extract_item to use patterns
        item = self._extract_item(lower_input)
        if item:
            return ActionIntent(
                action_type=ActionType.ITEM_USE,
                resource=item,
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
        """Validate combat action - STRICT validation including weapon check"""

        # NEW: Check if player specified a weapon they don't have
        if intent.resource and game_session.character_state:
            inventory_items = [item.lower() for item in game_session.character_state.inventory]
            weapon_lower = intent.resource.lower()

            if weapon_lower not in inventory_items:
                # Player is trying to use a weapon they don't have!
                return ValidationReport(
                    result=ValidationResult.INVALID,
                    action=intent,
                    message=f"Player tries to attack with '{intent.resource}', but they don't have that weapon. "
                           f"Narrate that they reach for it but it's not there.",
                    suggestions=inventory_items[:5]
                )

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
                for name, init in game_session.combat.initiative_order:
                    if name.lower() == target_lower:
                        matched = name
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
        """Validate spell casting - check spell known, slots available, AND target exists"""

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

        # CRITICAL: Validate target exists if spell has a target
        # This prevents hallucination of non-existent enemies!
        if intent.target:
            # Check if target exists in current game state
            combatants = []
            if game_session.combat and game_session.combat.initiative_order:
                combatants = [c[0].lower() for c in game_session.combat.initiative_order]
            
            npcs = [npc.lower() for npc in game_session.npcs_present]
            all_targets = combatants + npcs
            target_lower = intent.target.lower()
            
            # Exact match
            if target_lower in all_targets:
                matched = intent.target
                return ValidationReport(
                    result=ValidationResult.VALID,
                    action=intent,
                    matched_entity=matched,
                    message=f"Player casts {spell_name} at {matched}. Describe the spell's effects and outcome."
                )
            
            # Fuzzy match
            fuzzy_match = self._fuzzy_match(target_lower, all_targets)
            if fuzzy_match:
                return ValidationReport(
                    result=ValidationResult.FUZZY_MATCH,
                    action=intent,
                    matched_entity=fuzzy_match,
                    message=f"Player casts {spell_name} at {fuzzy_match}. Describe the spell's effects and outcome."
                )
            
            # No match - target doesn't exist!
            available = ", ".join([n.title() for n in all_targets]) if all_targets else "none"
            return ValidationReport(
                result=ValidationResult.INVALID,
                action=intent,
                message=f"Player tries to cast '{spell_name}' at '{intent.target}', but no such target is present. "
                       f"Available targets: {available}. Narrate that the target doesn't exist.",
                suggestions=all_targets[:5]
            )

        # TODO: Check spell slots when spell slot tracking is fully implemented
        # For now, assume spell slots are available

        # Spell valid, no specific target
        return ValidationReport(
            result=ValidationResult.VALID,
            action=intent,
            message=f"Player casts {spell_name}. Describe the spell's effects and outcome."
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
        item_lower = item_name.lower()

        # Exact match - item is in inventory
        if item_lower in inventory_items:
            return ValidationReport(
                result=ValidationResult.VALID,
                action=intent,
                message=f"Player uses {item_name}. Describe the item's effect or outcome."
            )

        # Check for generic category terms (e.g., "weapon" matches "longsword")
        matched_item = self._match_item_category(item_lower, inventory_items)
        if matched_item:
            return ValidationReport(
                result=ValidationResult.VALID,
                action=intent,
                matched_entity=matched_item,
                message=f"Player uses {matched_item} (they said '{item_name}'). Describe the item's effect or outcome."
            )

        # Item not found
        if inventory_items:
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
        if self.debug:
            logger.debug(f"[ACTION_PARSER] _extract_target() called with text: '{text}'")
        for keyword in keywords:
            # Use word boundary regex to avoid matching "attack" inside "attacks"
            pattern = rf'\b{re.escape(keyword)}\b'
            match = re.search(pattern, text)

            if match:
                # Get text after the keyword
                start_pos = match.end()
                after = text[start_pos:].strip()

                if self.debug:
                    logger.debug(f"[ACTION_PARSER] Keyword '{keyword}' matched. Text after: '{after}'")

                # Remove possessives and articles at the start
                # This handles "my longsword at the goblin" → "longsword at the goblin"
                after = re.sub(r'^(my|his|her|their|the|a|an)\s+', '', after)

                if self.debug:
                    logger.debug(f"[ACTION_PARSER] After removing possessives: '{after}'")

                # Look for "at X" pattern first - this is a strong indicator of target
                at_match = re.search(r'\bat\s+(?:the\s+)?(\w+(?:\s+\w+)?)', after)
                if at_match:
                    target = at_match.group(1).strip()
                    if self.debug:
                        logger.debug(f"[ACTION_PARSER] Found 'at X' pattern. Target: '{target}'")
                    return target

                # Stop at common prepositions that indicate end of target or start of weapon
                # e.g., "goblin with my sword" -> stop at "with"
                stop_words = ['with', 'using', 'and', 'then', ',', 'at']
                for stop in stop_words:
                    if ' ' + stop + ' ' in ' ' + after:
                        after = after.split(' ' + stop + ' ')[0]
                        break

                # Remove leading articles/prepositions after splitting
                after = re.sub(r'^(the|a|an)\s+', '', after)

                # Take first 1-2 words as target
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

    def _extract_spell_target(self, text: str, spell_name: Optional[str]) -> Optional[str]:
        """
        Extract target for a spell, looking AFTER the spell name.
        
        For "I cast Magic Missile at the goblin", extract "goblin"
        
        Args:
            text: Lower-case user input
            spell_name: The spell name (if detected)
        
        Returns:
            Target name or None
        """
        # Look for "at X", "on X", "towards X" patterns
        target_patterns = [
            r'\bat\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'\bon\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'\btowards?\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'\btargeting\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
        ]
        
        for pattern in target_patterns:
            match = re.search(pattern, text)
            if match:
                target = match.group(1).strip()
                # Don't return if it's just the spell name again
                if spell_name and target.lower() != spell_name.lower():
                    return target
                elif not spell_name:
                    return target
        
        return None

    def _extract_spell(self, text: str) -> Optional[str]:
        """Extract spell name from text"""
        # Common spell names (could expand this or use RAG)
        common_spells = [
            'magic missile', 'fireball', 'cure wounds', 'healing word',
            'eldritch blast', 'sacred flame', 'guiding bolt', 'shield',
            'mage armor', 'detect magic', 'identify', 'sleep', 'charm person',
            'fire bolt'  # Add Fire Bolt
        ]

        for spell in common_spells:
            if spell in text:
                return spell.title()

        # Try to extract after "cast" with word boundaries
        pattern = r'\bcast(?:s|ing)?\b'
        match = re.search(pattern, text)

        if match:
            # Get text after "cast/casts/casting"
            after_cast = text[match.end():].strip()
            # Remove "at", "on", etc.
            after_cast = re.sub(r'\s+(at|on|towards?)\s+.*', '', after_cast)
            words = after_cast.split()[:3]
            if words:
                return ' '.join(words).strip('.,!?').title()

        return None

    def _extract_item(self, text: str) -> Optional[str]:
        """Extract item name from text"""
        # Item keywords with patterns to match verb conjugations
        item_patterns = [
            r'\b(?:use|uses|using)\b',
            r'\b(?:drink|drinks|drinking)\b',
            r'\b(?:eat|eats|eating)\b',
            r'\b(?:equip|equips|equipping)\b',
            r'\b(?:wear|wears|wearing)\b',
            r'\b(?:wield|wields|wielding)\b',
            r'\b(?:ready|readies|readying)\b',
            r'\b(?:draw|draws|drawing)\b',
            r'\b(?:hold|holds|holding)\b',
            r'\b(?:grab|grabs|grabbing)\b',
            r'\breach\s+for\b',
            r'\bpull\s+out\b',
            r'\btake\s+out\b'
        ]

        for pattern in item_patterns:
            match = re.search(pattern, text)

            if match:
                after = text[match.end():].strip()
                # Remove articles and possessives
                after = re.sub(r'^(the|a|an|my|his|her|their)\s+', '', after)
                # Remove trailing "and..." phrases
                after = re.sub(r'\s+and\s+.*', '', after)
                # Take first 1-3 words
                words = after.split()[:3]
                if words:
                    item_name = ' '.join(words).strip('.,!?')
                    # Filter out non-item phrases (e.g., "ready for battle", "ready to fight")
                    # Check if this looks like an actual item vs a state/condition
                    non_item_phrases = ['for', 'to', 'if', 'when', 'as', 'because']
                    first_word = words[0].lower()
                    if first_word in non_item_phrases:
                        continue  # Skip this match, try next pattern
                    return item_name.title()

        return None

    def _extract_weapon(self, text: str) -> Optional[str]:
        """
        Extract weapon from combat action.
        Looks for patterns like "my bow", "with my sword", "using a crossbow", "with her bow"
        """
        # Common weapon names to look for
        common_weapons = [
            'bow', 'longbow', 'shortbow', 'crossbow',
            'sword', 'longsword', 'shortsword', 'greatsword',
            'axe', 'greataxe', 'battleaxe', 'handaxe',
            'dagger', 'knife', 'rapier', 'scimitar',
            'mace', 'club', 'staff', 'quarterstaff',
            'spear', 'javelin', 'halberd', 'pike',
            'hammer', 'warhammer', 'maul'
        ]

        # Look for "my X" or "the X" patterns
        for weapon in common_weapons:
            # Pattern: "my bow", "the bow", "a bow", "her bow", "his bow"
            if re.search(rf'\b(my|the|a|an|her|his|their)\s+{weapon}\b', text):
                return weapon.title()

        # Look for "with X" pattern
        with_match = re.search(r'\bwith\s+(my|a|the|an|her|his|their)\s+(\w+)', text)
        if with_match:
            potential_weapon = with_match.group(2)
            if potential_weapon in common_weapons:
                return potential_weapon.title()

        # Look for "using X" pattern
        using_match = re.search(r'\busing\s+(my|a|the|an|her|his|their)\s+(\w+)', text)
        if using_match:
            potential_weapon = using_match.group(2)
            if potential_weapon in common_weapons:
                return potential_weapon.title()

        return None

    def _match_item_category(self, generic_term: str, inventory: List[str]) -> Optional[str]:
        """
        Match generic category terms to specific items in inventory.
        Examples:
        - "weapon" matches "longsword", "bow", "dagger", etc.
        - "sword" matches "longsword", "shortsword", "greatsword", etc.
        - "armor" matches "plate armor", "leather armor", etc.

        Args:
            generic_term: Generic category term (e.g., "weapon", "sword", "armor")
            inventory: List of inventory items (lowercase)

        Returns:
            First matching item title-cased, or None
        """
        # Define category mappings
        weapon_categories = {
            'weapon': ['sword', 'bow', 'axe', 'mace', 'dagger', 'spear', 'hammer', 'staff', 'club', 'javelin', 'crossbow', 'knife', 'rapier', 'scimitar', 'halberd', 'pike', 'quarterstaff', 'warhammer', 'maul', 'sling'],
            'sword': ['longsword', 'shortsword', 'greatsword', 'scimitar', 'rapier'],
            'bow': ['longbow', 'shortbow', 'crossbow'],
            'axe': ['battleaxe', 'handaxe', 'greataxe'],
            'armor': ['leather', 'hide', 'chain', 'scale', 'plate', 'splint', 'studded', 'breastplate', 'half plate', 'ring mail'],
            'shield': ['shield'],
        }

        # Check if generic term matches a category
        if generic_term in weapon_categories:
            category_items = weapon_categories[generic_term]
            for inv_item in inventory:
                # Check if any category item is contained in the inventory item
                for cat_item in category_items:
                    if cat_item in inv_item:
                        # Return the title-cased version
                        return inv_item.title()

        return None

    def _fuzzy_match(self, target: str, entities: List[str], threshold: float = 0.6) -> Optional[str]:
        """
        Attempt fuzzy matching for target against entity list.
        e.g., "goblin" matches "Goblin Scout", "the dragon" matches "Ancient Red Dragon"
        """
        target = target.lower()
        # Remove common articles that might interfere
        target_clean = re.sub(r'\b(the|a|an)\b\s*', '', target).strip()

        for entity in entities:
            entity_lower = entity.lower()
            # Substring match
            if target_clean in entity_lower or entity_lower in target_clean:
                return entity

            # Word overlap (using cleaned target)
            target_words = set(target_clean.split())
            entity_words = set(entity_lower.split())
            # Filter out articles from comparison
            target_words = {w for w in target_words if w not in ['the', 'a', 'an']}
            entity_words = {w for w in entity_words if w not in ['the', 'a', 'an']}
            
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
