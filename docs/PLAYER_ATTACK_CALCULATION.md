# Player Attack Damage Calculation (Fix #14)

## Problem
**User Report**: "I don't see any damage being done to the wolf or goblin when I attack"

### Root Cause
- GM narrative doesn't include damage numbers: "Your sword strikes the goblin"
- Mechanics extractor can't extract damage without explicit amounts
- NPC attacks work because `generate_npc_attack()` rolls dice and includes numbers
- Player attacks relied on vague GM descriptions

## Solution
Pre-calculate player attack rolls and damage, pass to GM as instruction.

### Implementation

#### 1. Architecture Change - Base Character Stats Storage
**Problem**: CharacterState doesn't have ability scores (STR, DEX, etc.)  
**Solution**: Store base Character objects in GameSession by name

```python
# game_state.py - GameSession
base_character_stats: Dict[str, Any] = field(default_factory=dict)
# Works for both solo and party mode: {character_name: Character}
```

**Why Dict instead of single Character?**
- ✅ Works for solo mode: `{thorin.name: thorin}`
- ✅ Works for party mode: `{thorin.name: thorin, elara.name: elara}`
- ✅ Scales to multiple characters without refactoring

#### 2. Attack Calculation Method

```python
def _calculate_player_attack(self, target_name: str, character_state) -> str:
    """Calculate player attack roll and damage."""
    
    # Get base character stats (STR, DEX, equipment)
    character = self.session.base_character_stats[character_state.character_name]
    
    # Find equipped weapon from equipment list
    weapon_name = find_weapon_in_equipment(character.equipment)
    
    # Calculate attack: d20 + STR mod + proficiency
    attack_roll = random.randint(1, 20)
    str_mod = character.get_ability_modifier(character.strength)
    total = attack_roll + str_mod + character.proficiency_bonus
    
    # Get target AC from combat manager
    target_ac = self.combat_manager.npc_monsters[target_name].ac
    
    # Check hit/miss/crit
    if total >= target_ac:
        # Roll weapon damage dice + STR mod
        damage = roll_weapon_damage(weapon_name) + str_mod
        if attack_roll == 20:
            damage *= 2  # Critical hit
        
        return f"COMBAT INSTRUCTION: {name} HITS {target} for {damage} damage"
    else:
        return f"COMBAT INSTRUCTION: {name} MISSES {target}"
```

#### 3. Weapon Damage Table
Simple mapping for common D&D weapons:

```python
WEAPON_DAMAGE = {
    "longsword": (1, 8, "slashing"),    # 1d8
    "greatsword": (2, 6, "slashing"),   # 2d6
    "dagger": (1, 4, "piercing"),       # 1d4
    "battleaxe": (1, 8, "slashing"),    # 1d8
    "greataxe": (1, 12, "slashing"),    # 1d12
    "bow": (1, 8, "piercing"),          # 1d8
    "unarmed": (1, 4, "bludgeoning"),   # Fallback
}
```

#### 4. Flow Integration

```
1. Player: "attack the goblin"
2. Action validator: ActionType.COMBAT, target="goblin"
3. GM detects combat action → calls _calculate_player_attack()
4. Method rolls: d20=14, +3 STR, +2 prof = 19 vs AC 15 (HIT!)
5. Method rolls damage: 1d8=5, +3 STR = 8 damage
6. Returns: "COMBAT INSTRUCTION: Thorin hits Goblin for 8 slashing damage"
7. GM receives instruction (hidden from player)
8. GM narrates: "Your blade bites deep into the goblin's shoulder!"
9. Mechanics extractor parses: "8 slashing damage to goblin"
10. Applicator applies damage to goblin NPC
11. Display: "⚙️ MECHANICS: 💥 Goblin takes 8 damage! (HP: 7/15)"
```

## Testing

### Manual Test Results
```bash
$ python3 test_player_attack.py

Attack #1: Thorin attacks Goblin - HITS! (14+5=19 vs AC 15) → 7 slashing damage
Attack #2: Thorin attacks Goblin - HITS! (19+5=24 vs AC 15) → 7 slashing damage  
Attack #3: Thorin attacks Goblin - HITS! (12+5=17 vs AC 15) → 11 slashing damage
Attack #4: Thorin attacks Goblin - MISSES (9+5=14 vs AC 15) → NO DAMAGE
Attack #5: Thorin attacks Goblin - MISSES (6+5=11 vs AC 15) → NO DAMAGE

✅ Attack rolls: d20 + 5 (STR +3, Prof +2)
✅ Damage range: 1d8+3 = 4-11 (got 7, 7, 11)
✅ Misses when < AC, hits when >= AC
```

## Code Changes

### Files Modified

**1. `dnd_rag_system/systems/game_state.py`**
- Added `base_character_stats: Dict[str, Any]` to GameSession
- Stores Character objects by name for solo/party mode

**2. `web/app_gradio.py`** (line 221)
```python
gm.session.base_character_stats[char.name] = char
```

**3. `dnd_rag_system/systems/gm_dialogue_unified.py`**

Lines 496-514: Detect combat action and calculate attack
```python
player_attack_instruction = ""
if (action_intent.action_type == ActionType.COMBAT and 
    action_intent.target and 
    self.session.character_state):
    
    attack_result = self._calculate_player_attack(
        action_intent.target,
        self.session.character_state
    )
    if attack_result:
        player_attack_instruction = attack_result
```

Lines 783-895: New `_calculate_player_attack()` method
- Finds equipped weapon
- Rolls d20 + mods vs AC
- Calculates damage with weapon dice + STR
- Handles crits (nat 20 = double damage)
- Handles crit fails (nat 1 = fumble)

Lines 972-977: Add instruction to prompt (hidden from player)
```python
if player_attack_instruction:
    prompt += f"""{player_attack_instruction}

"""
```

## Benefits

✅ **Player sees damage numbers**: "💥 Goblin takes 8 damage! (HP: 7/15)"  
✅ **Accurate D&D 5e mechanics**: d20 + mods, weapon damage dice, crits  
✅ **Works for both solo and party mode**: Dict-based storage scales  
✅ **No LLM parsing errors**: Damage pre-calculated, not extracted from vague text  
✅ **Consistent with NPC attacks**: Same display format for player and NPC damage

## Known Limitations

⚠️ **Simple weapon detection**: Matches weapon names in equipment list  
⚠️ **No finesse weapons**: Always uses STR, doesn't check for DEX-based weapons  
⚠️ **No magic weapons**: +1/+2 bonuses not implemented  
⚠️ **No special attacks**: Power Attack, Sneak Attack, Smite not implemented  

## Future Improvements

1. **Store weapon stats in CharacterState.equipped**: Proper weapon object with all stats
2. **Finesse weapon support**: Check weapon properties, use max(STR, DEX)
3. **Magic weapon bonuses**: +1/+2/+3 to hit and damage
4. **Action economy**: Extra Attack for fighters, bonus actions
5. **Class features**: Rage damage, Sneak Attack, Divine Smite
6. **Advantage/Disadvantage**: Roll twice, take higher/lower

## Related Fixes

This completes the damage tracking system:
- Fix #9: NPC damage tracking (NPCs taking damage from player)
- Fix #11: Damage target parsing (who receives damage)
- **Fix #14: Player damage calculation** (THIS FIX)

Now damage flows correctly in both directions:
- Player → NPC: Pre-calculated, displayed in MECHANICS
- NPC → Player: Generated by combat manager, displayed in NPC ACTIONS
