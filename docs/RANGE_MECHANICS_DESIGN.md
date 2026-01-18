# Distance/Range Mechanics Design Document

## Overview
Add tactical positioning and range mechanics to the D&D 5e combat system, allowing for:
- Ranged vs melee combat distinction
- Movement and positioning strategy
- Cover and hiding mechanics
- Range-based attack modifiers
- Tactical decision-making based on distance

---

## 1. Core Mechanics

### 1.1 Range Bands (Simplified Theater-of-Mind)
Instead of exact grid positioning (which is complex for text-based gameplay), use abstract range bands:

```
MELEE:       0-5 feet   (Adjacent, can use melee weapons)
CLOSE:       5-30 feet  (Short range for most ranged weapons)
MEDIUM:      30-60 feet (Normal range for bows/spells)
LONG:        60-120 feet (Long range - disadvantage on attacks)
EXTREME:     120+ feet  (Out of range for most attacks)
```

### 1.2 Distance Tracking Per Combatant
```python
@dataclass
class CombatantPosition:
    """Track position and range relationships between combatants."""
    name: str
    range_band: str = "MEDIUM"  # Default starting position
    in_cover: bool = False
    cover_type: str = "NONE"  # NONE, HALF, THREE_QUARTERS, FULL
    is_hidden: bool = False
    prone: bool = False
    
    # Relative distances to specific targets
    distances_to: Dict[str, str] = field(default_factory=dict)  # {target_name: range_band}
```

### 1.3 Weapon/Spell Range Properties
```python
WEAPON_RANGES = {
    # Melee weapons
    "Dagger": {"melee": True, "thrown": True, "range_normal": 20, "range_long": 60},
    "Shortsword": {"melee": True, "range_normal": 5},
    "Longsword": {"melee": True, "range_normal": 5},
    "Greatsword": {"melee": True, "range_normal": 5, "reach": 5},
    "Spear": {"melee": True, "thrown": True, "range_normal": 20, "range_long": 60, "reach": 5},
    
    # Ranged weapons
    "Shortbow": {"ranged": True, "range_normal": 80, "range_long": 320},
    "Longbow": {"ranged": True, "range_normal": 150, "range_long": 600},
    "Light Crossbow": {"ranged": True, "range_normal": 80, "range_long": 320},
    "Heavy Crossbow": {"ranged": True, "range_normal": 100, "range_long": 400},
    "Hand Crossbow": {"ranged": True, "range_normal": 30, "range_long": 120},
    
    # Thrown weapons
    "Javelin": {"melee": True, "thrown": True, "range_normal": 30, "range_long": 120},
    "Handaxe": {"melee": True, "thrown": True, "range_normal": 20, "range_long": 60},
}

SPELL_RANGES = {
    "Fire Bolt": {"range": 120, "type": "ranged_spell_attack"},
    "Magic Missile": {"range": 120, "type": "auto_hit"},
    "Cure Wounds": {"range": "touch", "type": "touch"},
    "Fireball": {"range": 150, "type": "aoe", "radius": 20},
    "Thunderwave": {"range": "self", "type": "aoe", "radius": 15},
    "Eldritch Blast": {"range": 120, "type": "ranged_spell_attack"},
}
```

---

## 2. Combat Rules Integration

### 2.1 Attack Modifiers Based on Range

#### Ranged Attacks
```python
def calculate_ranged_attack_modifier(attacker_pos, target_pos, weapon_range):
    """
    Calculate attack roll modifiers based on distance.
    
    D&D 5e Rules:
    - Long range: Disadvantage on attack
    - Target in cover: +2 AC (half) or +5 AC (three-quarters)
    - Prone target at range: Disadvantage
    - Attacker prone: Disadvantage on ranged attacks
    - Ranged attack while enemy in melee: Disadvantage
    """
    modifiers = []
    
    # Get distance to target
    distance_band = attacker_pos.distances_to.get(target_pos.name, "MEDIUM")
    distance_feet = BAND_TO_FEET[distance_band]
    
    # Long range disadvantage
    if distance_feet > weapon_range["range_normal"]:
        if distance_feet <= weapon_range.get("range_long", 0):
            modifiers.append(("DISADVANTAGE", "Long range attack"))
        else:
            return None, ["Target out of range"]
    
    # Cover AC bonus (not disadvantage)
    if target_pos.cover_type == "HALF":
        modifiers.append(("AC_BONUS", "+2 AC from half cover"))
    elif target_pos.cover_type == "THREE_QUARTERS":
        modifiers.append(("AC_BONUS", "+5 AC from three-quarters cover"))
    
    # Prone target at range
    if target_pos.prone and distance_band != "MELEE":
        modifiers.append(("DISADVANTAGE", "Attacking prone target at range"))
    
    # Prone attacker
    if attacker_pos.prone:
        modifiers.append(("DISADVANTAGE", "Attacking while prone"))
    
    # Enemy in melee range (shooting in melee)
    if has_enemy_in_melee(attacker_pos):
        modifiers.append(("DISADVANTAGE", "Ranged attack with enemy in melee"))
    
    return modifiers
```

#### Melee Attacks
```python
def calculate_melee_attack_modifier(attacker_pos, target_pos, weapon):
    """
    Melee attacks require MELEE range (or CLOSE with reach weapons).
    
    D&D 5e Rules:
    - Prone attacker: Disadvantage
    - Prone target: Advantage (easier to hit)
    - Target in cover: +2 or +5 AC
    """
    modifiers = []
    
    distance_band = attacker_pos.distances_to.get(target_pos.name, "MEDIUM")
    
    # Check if in melee range
    weapon_reach = weapon.get("reach", 5)
    if distance_band == "MELEE" or (distance_band == "CLOSE" and weapon_reach >= 10):
        # In range, proceed with modifiers
        
        # Prone attacker
        if attacker_pos.prone:
            modifiers.append(("DISADVANTAGE", "Attacking while prone"))
        
        # Prone target (advantage for melee)
        if target_pos.prone:
            modifiers.append(("ADVANTAGE", "Attacking prone target in melee"))
        
        # Cover
        if target_pos.cover_type == "HALF":
            modifiers.append(("AC_BONUS", "+2 AC from half cover"))
        elif target_pos.cover_type == "THREE_QUARTERS":
            modifiers.append(("AC_BONUS", "+5 AC from three-quarters cover"))
        
        return modifiers
    else:
        return None, ["Target out of melee range - must move closer or use ranged attack"]
```

### 2.2 Movement Actions

```python
MOVEMENT_ACTIONS = {
    "/move_closer <target>": "Move toward target (EXTREME→LONG→MEDIUM→CLOSE→MELEE)",
    "/move_away <target>": "Move away from target (MELEE→CLOSE→MEDIUM→LONG→EXTREME)",
    "/take_cover": "Find cover (half or three-quarters based on terrain)",
    "/leave_cover": "Leave cover position",
    "/hide": "Attempt to hide (Dexterity Stealth check)",
    "/go_prone": "Drop prone (+AC vs ranged, harder to hide, harder to move)",
    "/stand_up": "Stand from prone (costs half movement)",
}

def move_closer(attacker_name, target_name, combat_positions):
    """Move one range band closer to target."""
    attacker_pos = combat_positions[attacker_name]
    current_range = attacker_pos.distances_to.get(target_name, "MEDIUM")
    
    range_progression = ["EXTREME", "LONG", "MEDIUM", "CLOSE", "MELEE"]
    current_idx = range_progression.index(current_range)
    
    if current_idx > 0:
        new_range = range_progression[current_idx - 1]
        attacker_pos.distances_to[target_name] = new_range
        
        # Moving provokes opportunity attacks if leaving melee
        if current_range == "MELEE":
            return new_range, "⚔️ Moved away from melee - provokes opportunity attack!"
        
        return new_range, f"📍 Moved to {new_range} range"
    else:
        return current_range, "Already in melee range"
```

### 2.3 Hiding and Stealth

```python
def attempt_hide(character, combat_positions, enemy_positions):
    """
    Attempt to hide using Dexterity (Stealth) check.
    
    D&D 5e Rules:
    - Must have cover or be heavily obscured
    - Contested by enemy Perception (passive or active)
    - Hidden attacker gets advantage
    - Being hidden breaks on attack
    """
    char_pos = combat_positions[character.name]
    
    # Must be in cover to hide
    if char_pos.cover_type == "NONE":
        return False, "⚠️ Cannot hide without cover!"
    
    # Disadvantage if prone (harder to sneak around)
    stealth_roll = roll_d20()
    dex_mod = (character.dex - 10) // 2
    
    # Cover provides advantage on Stealth
    if char_pos.cover_type in ["THREE_QUARTERS", "FULL"]:
        stealth_roll = max(roll_d20(), roll_d20())  # Advantage
    
    stealth_total = stealth_roll + dex_mod
    
    # Check against enemy passive Perception
    hidden_from = []
    for enemy_name, enemy in enemy_positions.items():
        enemy_perception = 10 + ((enemy.wis - 10) // 2)
        if stealth_total >= enemy_perception:
            hidden_from.append(enemy_name)
    
    if hidden_from:
        char_pos.is_hidden = True
        return True, f"🥷 Successfully hidden! (Stealth: {stealth_total})"
    else:
        return False, f"⚠️ Failed to hide (Stealth: {stealth_total})"
```

---

### 3.1 Extended ExtractedMechanics
```python
@dataclass
class ExtractedMechanics:
    # ... existing fields (damage, healing, conditions, etc.) ...
    
    # NEW: Movement and positioning
    movements: List[Dict[str, Any]] = field(default_factory=list)
    # [{"character": "Thorin", "action": "move_closer", "target": "Goblin"}]
    # [{"character": "Elara", "action": "move_away", "target": "Orc"}]
    # [{"character": "Rogue", "action": "dash"}]
    
    cover_changes: List[Dict[str, Any]] = field(default_factory=list)
    # [{"character": "Archer", "action": "take_cover", "cover_type": "HALF"}]
    # [{"character": "Fighter", "action": "leave_cover"}]
    
    stealth_attempts: List[Dict[str, Any]] = field(default_factory=list)
    # [{"character": "Rogue", "action": "hide"}]
    
    stance_changes: List[Dict[str, Any]] = field(default_factory=list)
    # [{"character": "Fighter", "action": "go_prone"}]
    # [{"character": "Wizard", "action": "stand_up"}]
```

### 3.2 Extended CombatState
```python
@dataclass
class CombatState:
    # ... existing fields ...
    
    # NEW: Position tracking
    combat_positions: Dict[str, CombatantPosition] = field(default_factory=dict)
    battlefield_terrain: str = "OPEN"  # OPEN, FOREST, RUINS, DUNGEON, etc.
    cover_available: bool = True
```

### 3.2 Extended CombatState
```python
@dataclass
class CombatState:
    # ... existing fields ...
    
    # NEW: Position tracking
    combat_positions: Dict[str, CombatantPosition] = field(default_factory=dict)
    battlefield_terrain: str = "OPEN"  # OPEN, FOREST, RUINS, DUNGEON, etc.
    cover_available: bool = True
```

### 3.3 MechanicsExtractor Prompt Extension
The extractor needs to recognize positioning in natural language:

```python
POSITIONING_EXTRACTION_PROMPT = """
Extract positioning and movement from natural language:

MOVEMENT PATTERNS:
- "move closer/toward/at" → move_closer
- "back away/retreat/withdraw" → move_away  
- "dash/sprint/charge" → dash
- "step back/give ground" → move_away

COVER PATTERNS:
- "take cover/behind/duck behind" → take_cover
- "peek out/leave cover" → leave_cover

STEALTH PATTERNS:
- "hide/sneak/stay hidden" → hide attempt
- "reveal/show myself" → leave hiding

STANCE PATTERNS:
- "drop prone/hit the deck/go low" → go_prone
- "stand/get up/rise" → stand_up

Example extractions:
Input: "I move closer to the goblin"
Output: {"movements": [{"character": "player_name", "action": "move_closer", "target": "Goblin"}]}

Input: "I take cover behind the rocks and hide"
Output: {
  "cover_changes": [{"character": "player_name", "action": "take_cover", "cover_type": "HALF"}],
  "stealth_attempts": [{"character": "player_name", "action": "hide"}]
}

Input: "I back away from the orc"
Output: {"movements": [{"character": "player_name", "action": "move_away", "target": "Orc"}]}
"""
```

### 3.4 Position Manager
```python
class PositionManager:
    """Manages positioning and range mechanics in combat."""
    
    def __init__(self, combat_state: CombatState):
        self.combat = combat_state
        self.positions = combat_state.combat_positions
    
    def initialize_positions(self, combatants: List[str], terrain: str = "OPEN"):
        """
        Initialize starting positions based on encounter type.
        
        Ambush: Enemies at MELEE/CLOSE, party at CLOSE/MEDIUM
        Standard: Everyone at MEDIUM range
        Ranged encounter: Everyone at LONG range
        """
        for combatant in combatants:
            self.positions[combatant] = CombatantPosition(
                name=combatant,
                range_band="MEDIUM"  # Default
            )
        
        # Set distances between all combatants
        self._update_all_distances()
    
    def _update_all_distances(self):
        """Calculate distances between all combatants."""
        combatant_names = list(self.positions.keys())
        
        for i, name1 in enumerate(combatant_names):
            for name2 in combatant_names[i+1:]:
                # For simplicity, assume symmetric distances
                # Could make asymmetric for flanking/pursuit scenarios
                distance = self._calculate_distance(name1, name2)
                self.positions[name1].distances_to[name2] = distance
                self.positions[name2].distances_to[name1] = distance
    
    def get_attack_modifiers(self, attacker: str, target: str, weapon_or_spell: dict) -> List[Tuple[str, str]]:
        """Get all attack modifiers based on positioning."""
        attacker_pos = self.positions[attacker]
        target_pos = self.positions[target]
        
        if weapon_or_spell.get("melee"):
            return calculate_melee_attack_modifier(attacker_pos, target_pos, weapon_or_spell)
        elif weapon_or_spell.get("ranged"):
            return calculate_ranged_attack_modifier(attacker_pos, target_pos, weapon_or_spell)
        else:
            return calculate_spell_attack_modifier(attacker_pos, target_pos, weapon_or_spell)
```

---

## 4. Natural Language Player Input

### 4.1 Movement Examples (Natural Language)
Players type natural language, GM interprets via MechanicsExtractor:
```
Player: "I move closer to the goblin"
Player: "I back away from the orc and try to get some distance"
Player: "I dash forward to reach the wizard"
Player: "I retreat to a safer position"
Player: "I charge at the enemy"

→ Mechanics Extractor identifies movement intent
→ PositionManager updates range band
→ GM narrates the movement with range context
```

### 4.2 Positioning Examples (Natural Language)
```
Player: "I take cover behind the rocks"
Player: "I hide behind the pillar"
Player: "I drop to the ground and try to stay low"
Player: "I stand up from prone"
Player: "I try to sneak around while staying hidden"

→ Mechanics Extractor identifies positioning action
→ PositionManager applies cover/prone/hidden status
→ GM narrates with stealth/perception checks if needed
```

### 4.3 Attack Examples with Range Awareness
```
Player: "I shoot the goblin with my longbow"
→ GM checks range, applies modifiers automatically
→ Narrative: "You draw your longbow and aim at the distant goblin (120 feet away). 
   The shot is challenging at this range... [roll with disadvantage]"

Player: "I cast Fire Bolt at the wizard"
→ GM checks spell range (120 ft)
→ If out of range: "The enemy wizard is too far away for Fire Bolt (170 feet). 
   You'll need to move closer or use a different spell."

Player: "I swing my sword at the orc"
→ GM checks melee range
→ If too far: "The orc is 30 feet away - too far for your sword. You could move 
   closer, or switch to your javelin."
```

### 4.4 Tactical Positioning Examples
```
Player: "I want to position myself so I can shoot without being in melee"
→ GM: "You step back 20 feet, creating distance from the goblin. You're now at 
   close range - perfect for archery without the penalty of melee threats."

Player: "Can I see where everyone is positioned?"
→ GM provides position summary (auto-generated from PositionManager)
```

---

## 5. GM Narrative Integration

### 5.1 Position-Aware Narrative Prompts
The GM system prompt should include positioning context:

```python
COMBAT_POSITIONING_CONTEXT = """
CURRENT BATTLEFIELD POSITIONS:
{position_summary}

When narrating combat:
- Mention range when relevant ("The distant goblin", "the orc charging toward you")
- Describe movement cinematically ("You dart between cover", "You close the distance")
- Note tactical advantages ("From behind cover, you have protection", "At long range, your shot is difficult")
- Warn about range limitations ("The enemy is too far for your sword", "Moving away will provoke an attack")
- NPCs should use tactics (archers stay back, melee fighters close in)

Auto-apply range modifiers to attacks:
- Long range ranged attacks: disadvantage
- Melee attacks out of range: prevent and suggest movement
- Cover: add AC bonus to target
"""
```

### 5.2 Example Natural Flow
```
Player: "I shoot the goblin with my bow"

GM Internal Processing:
1. MechanicsExtractor: attack with ranged weapon
2. PositionManager: Check range to goblin → LONG (100 ft)
3. Check weapon range: Longbow normal=150ft, long=600ft → within range but beyond normal
4. Apply disadvantage modifier
5. Generate narrative with position context

GM Response:
"You draw your longbow and take aim at the goblin across the battlefield, about 100 feet 
away. At this distance, the shot is challenging. [Rolling with disadvantage]

Attack roll: 8 + 5 = 13 vs AC 15
The arrow flies wide, missing the distant target as he ducks behind a stone pillar."

→ Auto-updated: Goblin now has HALF cover
→ State tracked transparently, no player commands needed
```

### 5.3 Movement Example
```
Player: "I need to get away from this orc, he's too close!"

GM Internal Processing:
1. MechanicsExtractor: move_away from Orc
2. Current position: MELEE with Orc
3. Apply movement: MELEE → CLOSE
4. Trigger opportunity attack (leaving melee)
5. Generate narrative

GM Response:
"You attempt to disengage from the orc, backing away quickly. As you retreat, the 
orc swings his greataxe at your exposed back!

Opportunity Attack: 16 + 6 = 22 vs AC 15 - HIT!
The axe catches your shoulder for 9 slashing damage.

You successfully create distance, now 15 feet away from the orc. Far enough to 
use your bow, but he could charge back into melee on his turn."

→ Position updated: MELEE → CLOSE
→ HP reduced: auto-applied
→ Tactical context: provided naturally
```

### 5.4 Cover & Hiding Example
```
Player: "I duck behind the pillar and try to stay hidden"

GM Internal Processing:
1. MechanicsExtractor: take_cover + hide
2. Check terrain: RUINS → cover available = TRUE
3. Apply cover: THREE_QUARTERS (+5 AC)
4. Roll Stealth check vs enemy Perception
5. Generate narrative

GM Response:
"You dive behind the stone pillar, pressing yourself against the cold marble. The 
thick pillar provides excellent cover.

Stealth Check: 18 + 4 = 22
Goblin Passive Perception: 11

You successfully blend into the shadows behind the pillar. The goblin loses sight 
of you, scanning the area with confusion. On your next attack from hiding, you'll 
have advantage!

Your position: Hidden, three-quarters cover (+5 AC if spotted)"

→ is_hidden: True
→ cover_type: THREE_QUARTERS
→ Next attack: advantage (auto-applied)
```

---

## 6. Implementation Details

### 6.1 MechanicsExtractor Extension
Add to `mechanics_extractor.py`:

```python
# In _build_extraction_prompt:
POSITIONING_FIELDS = """
"movements": [
  {"character": "character_name", "action": "move_closer|move_away|dash", "target": "enemy_name"}
],
"cover_changes": [
  {"character": "character_name", "action": "take_cover|leave_cover", "cover_type": "HALF|THREE_QUARTERS"}
],
"stealth_attempts": [
  {"character": "character_name", "action": "hide|reveal"}
],
"stance_changes": [
  {"character": "character_name", "action": "go_prone|stand_up"}
]
"""

# Natural language patterns to detect:
MOVEMENT_KEYWORDS = [
    "move closer", "move toward", "advance", "approach", "charge",
    "back away", "retreat", "withdraw", "fall back", "give ground",
    "dash", "sprint", "run"
]

COVER_KEYWORDS = [
    "take cover", "duck behind", "hide behind", "use cover",
    "leave cover", "step out", "peek out"
]

STEALTH_KEYWORDS = [
    "hide", "sneak", "stay hidden", "try to hide",
    "reveal", "step out", "show myself"
]

STANCE_KEYWORDS = [
    "drop prone", "hit the deck", "dive down", "go prone",
    "stand up", "get up", "rise", "stand"
]
```

### 6.2 MechanicsApplicator Extension
Add to `mechanics_applicator.py`:

```python
class MechanicsApplicator:
    def __init__(self, ...):
        # ... existing init ...
        self.position_manager = PositionManager()
    
    def apply(self, mechanics: ExtractedMechanics, session: GameSession) -> List[str]:
        """Apply extracted mechanics to game state."""
        results = []
        
        # ... existing applications (damage, healing, etc.) ...
        
        # NEW: Apply movements
        for movement in mechanics.movements:
            result = self._apply_movement(movement, session)
            results.append(result)
        
        # NEW: Apply cover changes
        for cover in mechanics.cover_changes:
            result = self._apply_cover_change(cover, session)
            results.append(result)
        
        # NEW: Apply stealth attempts
        for stealth in mechanics.stealth_attempts:
            result = self._apply_stealth(stealth, session)
            results.append(result)
        
        # NEW: Apply stance changes
        for stance in mechanics.stance_changes:
            result = self._apply_stance_change(stance, session)
            results.append(result)
        
        return results
    
    def _apply_movement(self, movement: Dict, session: GameSession) -> str:
        """Apply movement between range bands."""
        character = movement['character']
        action = movement['action']
        target = movement.get('target')
        
        if action == 'move_closer':
            result, message = self.position_manager.move_closer(character, target, session.combat_positions)
            return message
        elif action == 'move_away':
            result, message = self.position_manager.move_away(character, target, session.combat_positions)
            return message
        elif action == 'dash':
            # Double movement
            result1, _ = self.position_manager.move_closer(character, target, session.combat_positions)
            result2, msg = self.position_manager.move_closer(character, target, session.combat_positions)
            return f"Dashed! {msg}"
    
    def _apply_stealth(self, stealth: Dict, session: GameSession) -> str:
        """Apply stealth check."""
        character_name = stealth['character']
        character = session.character_state
        
        success, message = self.position_manager.attempt_hide(
            character, 
            session.combat_positions,
            session.npcs_present
        )
        
        return message
```

---

## 7. Example Combat Flow (Natural Language)

```
🎭 TURN 1 - ARCHER (Player)

Positions:
├─ Archer: MEDIUM range from Goblin (60 ft)
├─ Fighter: CLOSE range from Goblin (20 ft)  
└─ Goblin: MEDIUM from Archer, CLOSE from Fighter

Player Input: "I shoot the goblin with my longbow"

GM: "You draw your longbow and loose an arrow at the goblin 60 feet away.
     Attack: 14 + 5 = 19 vs AC 15 - HIT!
     Damage: 1d8+3 = 7 piercing damage
     The arrow strikes the goblin in the shoulder!"

---

🎭 TURN 2 - FIGHTER (Player)

Player Input: "I charge at the goblin and swing my sword"

GM: "You dash forward, closing the distance to the goblin!
     [Position: CLOSE → MELEE]
     
     With a battle cry, you swing your longsword at the now-adjacent goblin.
     Attack: 16 + 6 = 22 vs AC 15 - HIT!
     Damage: 1d8+4 = 9 slashing damage
     The goblin staggers from the blow!"

---

🎭 TURN 3 - GOBLIN (NPC, AI-controlled)

GM (auto-narrates with positioning logic):
"The wounded goblin, realizing he's outmatched in melee, attempts to retreat!
 [NPC AI: low HP, move away from melee]
 
 The goblin backs away from the Fighter.
 Opportunity Attack triggered!
 
 Fighter's opportunity attack: 18 + 6 = 24 vs AC 15 - HIT!
 Damage: 1d8+4 = 11 slashing damage
 
 Your blade catches the retreating goblin, finishing him off!
 💀 Goblin defeated!"

---

🎭 TURN 4 - ARCHER (Player)

New enemy appears: Goblin Archer at LONG range (90 ft) with HALF cover

Player Input: "I want to move closer to get a better shot, then fire"

GM: "You advance toward the enemy archer, moving from 90 feet to about 50 feet away.
     [Position: LONG → MEDIUM]
     
     From this range, you have a clear shot. The goblin is partially obscured 
     behind a rock (+2 AC from half cover).
     
     Attack: 15 + 5 = 20 vs AC 17 (15 + 2 cover) - HIT!
     Damage: 1d8+3 = 6 piercing damage
     
     Your arrow finds its mark despite the cover!"

---

🎭 TURN 5 - GOBLIN ARCHER (NPC, AI-controlled)

GM: "The goblin archer, seeing you advancing, fires back!
     [NPC still has HALF cover, you're at MEDIUM range]
     
     Goblin's attack: 12 + 4 = 16 vs AC 15 - HIT!
     Damage: 1d6+2 = 5 piercing damage
     
     The goblin's arrow strikes your arm!"

Player Input: "I need protection! I take cover behind the nearby tree"

GM: "You dive behind a thick oak tree, using it as a barrier.
     [Cover: HALF COVER applied, +2 AC]
     
     You're now both using cover, making this a battle of patience and accuracy."
```

---

## 8. Testing Strategy

### Phase 1: Core Infrastructure (1-2 days)
1. Create `PositionManager` class
2. Add `CombatantPosition` dataclass
3. Extend `CombatState` with position tracking
4. Add weapon/spell range data

### Phase 2: Range Mechanics (2-3 days)
1. Implement range band system
2. Add distance calculation functions
3. Implement attack modifier calculations
4. Add range validation for attacks

### Phase 3: Movement System (1-2 days)
1. Implement movement commands
2. Add opportunity attack on leaving melee
3. Add dash action
4. Update turn tracking to include movement

### Phase 4: Cover & Hiding (2-3 days)
1. Add cover mechanics
2. Implement hiding system
3. Add terrain-based cover availability
4. Add Stealth vs Perception checks

### Phase 5: Integration & Testing (2-3 days)
1. Integrate with existing combat flow
2. Update AI prompts to consider positioning
3. Add position display to combat status
4. Write comprehensive tests
5. Update documentation

---

## 6. Example Combat Flow

```
Turn 1 - Archer (150 ft from Goblin)
> /positions
📍 Combat Positions:
   Archer: LONG range from Goblin
   Fighter: MEDIUM range from Goblin
   Goblin: (MEDIUM from Fighter, LONG from Archer)

> /attack Goblin with Longbow
🎯 Attack Roll: 15 + 5 = 20 vs AC 15
✅ HIT! Rolled 1d8+3 = 7 piercing damage
   Range: 150ft (Normal range for longbow)

Turn 2 - Fighter
> /move_closer Goblin
📍 Moved to CLOSE range from Goblin

Turn 3 - Goblin
> /move_closer Fighter
⚔️ Moved to MELEE range with Fighter

Turn 4 - Archer (30 ft from Goblin)
> /move_away Goblin
📍 Moved to MEDIUM range from Goblin

> /attack Goblin with Longbow
🎯 Attack Roll: 18 + 5 = 23 vs AC 15
✅ HIT! Rolled 1d8+3 = 9 piercing damage

Turn 5 - Fighter (in melee with Goblin)
> /attack Goblin with Longsword
🎯 Attack Roll: 14 + 6 = 20 vs AC 15
✅ HIT! Rolled 1d8+4 = 10 slashing damage
💀 Goblin defeated!

Turn 6 - New Goblin Archer appears!
🏹 Goblin Archer is at LONG range, takes cover behind rocks
   Cover: Half cover (+2 AC)

> /move_closer Goblin Archer
📍 Moved to MEDIUM range

> /take_cover
🛡️ You take cover behind a fallen tree (Half cover, +2 AC)
```

---

## 7. AI Integration

### 7.1 GM Narrative Prompts
```
Include in system prompt:
"Track combat positioning. Describe attacks considering range:
- Melee attacks are close, personal, brutal
- Ranged attacks at medium range are precise shots
- Long range attacks are distant, difficult shots
- Cover provides tactical protection
- Hidden enemies can strike with surprise"
```

### 7.2 Strategic NPC Behavior
```python
def npc_tactical_decision(npc, player_positions, npc_positions):
    """
    NPCs make smart tactical decisions based on:
    - Their role (archer stays back, melee moves in)
    - HP status (wounded enemies seek cover or retreat)
    - Player positioning (flank isolated targets)
    """
    if npc.type == "archer" and npc.hp > npc.max_hp * 0.5:
        # Healthy archer maintains distance
        if range_to_nearest_enemy(npc) == "MELEE":
            return "move_away", "Archer retreats to shooting range"
    
    elif npc.type == "melee" and range_to_nearest_enemy(npc) != "MELEE":
        return "move_closer", "Warrior charges into melee"
    
    elif npc.hp < npc.max_hp * 0.3:
        # Wounded - seek cover
        if not npc.in_cover:
            return "take_cover", "Wounded enemy seeks cover"
```

---

## 8. Balance Considerations

### 8.1 Advantages of Range System
- **Tactical depth**: Positioning matters
- **Class differentiation**: Archers, mages, melee fighters play differently
- **Realism**: Matches D&D 5e rules
- **Player agency**: More choices in combat

### 8.2 Potential Challenges
- **Complexity**: More to track and explain
- **AI understanding**: LLM must grasp positioning
- **Balance**: Ranged characters could become overpowered
- **Text-based limitations**: Hard to visualize without map

### 8.3 Simplification Strategies
- Use range bands instead of exact feet
- Auto-calculate modifiers (player doesn't need to remember)
- Provide clear `/positions` command for situational awareness
- Show applicable modifiers before each attack
- Smart defaults (melee fighters start in melee, archers at range)

---

## 9. Testing Strategy

```python
# tests/test_range_mechanics.py

def test_range_bands():
    """Test basic range band system."""
    
def test_movement_closer():
    """Test moving closer to target."""
    
def test_movement_away():
    """Test moving away from target."""
    
def test_ranged_attack_long_range_disadvantage():
    """Test long range attack has disadvantage."""
    
def test_melee_attack_out_of_range():
    """Test melee attack fails if out of range."""
    
def test_cover_provides_ac_bonus():
    """Test half cover gives +2 AC."""
    
def test_hiding_requires_cover():
    """Test can't hide without cover."""
    
def test_opportunity_attack_on_leaving_melee():
    """Test leaving melee provokes opportunity attack."""
    
def test_prone_melee_advantage():
    """Test attacking prone target in melee gives advantage."""
    
def test_prone_ranged_disadvantage():
    """Test attacking prone target at range gives disadvantage."""
```

---

## 10. Future Enhancements

### 10.1 Advanced Positioning
- Flanking rules (advantage when allies surround enemy)
- Height advantage (higher ground = advantage)
- Difficult terrain (costs extra movement)

### 10.2 Advanced Tactics
- Readied actions based on position ("Attack when enemy enters range")
- Grappling and shoving (forced movement)
- Mounted combat (longer reach, faster movement)

### 10.3 Visualization
- ASCII art battlefield map
- Simple text diagram showing relative positions
- Emoji-based position indicators

---

## Summary

This design adds meaningful tactical depth while:
✅ Using **natural language input** (no slash commands needed)
✅ Following D&D 5e rules accurately
✅ Staying text-friendly (no complex grids)
✅ **Transparent to players** - GM narrates positioning naturally
✅ Integrating smoothly with existing MechanicsExtractor/Applicator pattern
✅ Balancing complexity vs usability

### How It Works:
1. **Player types natural language**: "I move closer to the goblin"
2. **MechanicsExtractor parses intent**: Identifies "move_closer" action
3. **PositionManager updates state**: Changes range band MEDIUM → CLOSE
4. **GM narrates with context**: "You advance toward the goblin, now 20 feet away..."
5. **Future attacks auto-apply modifiers**: Range checked transparently

### Key Advantages:
- 🎭 **Natural storytelling** - No mechanical commands break immersion
- 🧠 **Smart AI integration** - LLM interprets intent from player's words
- ⚔️ **Tactical depth** - Positioning matters, class roles differentiate
- 🎯 **Auto-applied rules** - Players don't memorize range penalties
- 📊 **State tracking** - GM maintains battlefield awareness

**Estimated Implementation Time**: 8-12 days
**Complexity**: Medium-High
**Impact**: High (fundamentally changes combat tactics while staying natural)
