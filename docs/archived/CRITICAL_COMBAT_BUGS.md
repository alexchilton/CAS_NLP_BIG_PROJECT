# Critical Combat Bugs - Game Breaking Issues

## 🚨 Bug 1: Player Can Act While Unconscious

### Description
When player is knocked unconscious (via narrative or HP = 0), they can still take actions (attack, cast spells, etc.) and the game continues as normal.

### What Actually Works
- ✅ Mechanics extractor **can** detect "unconscious" in GM narrative
- ✅ Applicator **does** add `Condition.UNCONSCIOUS` to character
- ✅ System **does** track unconscious state in `character_state.conditions`

### What's Broken
- ❌ No validation in `generate_response()` checks conditions before allowing actions
- ❌ Player can attack, move, cast spells while unconscious
- ❌ No death saving throw system

### Expected Behavior (D&D 5e Rules)
- **Unconscious condition**: Character is incapacitated, can't move or speak, **can't take actions**
- **Death Saving Throws**: Must make death saves (DC 10) each turn
- **3 successes**: Stabilize at 0 HP
- **3 failures**: Character dies

### Root Cause
`dnd_rag_system/systems/gm_dialogue_unified.py` line 213+ (`generate_response()`)
- No check for `Condition.UNCONSCIOUS` before processing player input
- Should block ALL actions except `/help`, `/stats`, death save attempts

### Fix Required
```python
# At start of generate_response(), add:
if self.session.character_state:
    if Condition.UNCONSCIOUS in self.session.character_state.conditions:
        # Only allow death saves, viewing stats, or admin commands
        if not player_input.startswith(('/stats', '/help', '/death_save')):
            return "You are unconscious and cannot act. Type /death_save to make a death saving throw."
```

### Impact
⚠️ **CRITICAL** - Completely breaks D&D rules, unconscious players can fight normally

---

## 🚨 Bug 2: NPCs Stop Acting When Player Unconscious

### Description
When player falls unconscious, enemy NPCs stop taking their turns and attacking.

### Expected Behavior (D&D 5e Rules)
- NPCs continue attacking unconscious players (auto-crits within 5ft, advantage beyond)
- Each hit on unconscious player = 1 failed death save
- 2 hits = 2 failed saves (can kill in one round if crits)
- Combat continues until player dies or is stabilized

### Current Behavior
- Player knocked unconscious
- Goblin stops attacking
- Combat effectively pauses
- Player can still act (see Bug 1)

### Root Cause
Unknown - need to investigate NPC turn system in combat_manager.py

### Impact
⚠️ **CRITICAL** - Makes unconscious state harmless instead of deadly

---

## 🚨 Bug 3: Excessive Random Encounters (Encounter Spam)

### Description
Random encounters trigger **every turn** when not in combat, causing:
- Goblin → Owlbear → Manticore appearing in 3 consecutive turns
- Impossible to explore without constant combat
- Breaks immersion and pacing

### Expected Behavior
Encounters should be rare and spaced out:
- Check on **location changes** or **time passage**, not every action
- Perhaps 1 encounter per 10-20 exploration actions
- Or based on time: 1 check per hour of in-game time

### Current Behavior
`dnd_rag_system/systems/gm_dialogue_unified.py` lines 486-500:
```python
exploration_keywords = ['explore', 'travel', 'venture', 'search', 'wander', 'head', 'go', 
                       'leave', 'continue', 'follow', 'look around', 'investigate']
is_exploring = any(keyword in player_input.lower() for keyword in exploration_keywords)

if (is_exploring and 
    not self.combat_manager.is_in_combat() and 
    self.session.character_state is not None):
    
    encounter = self.encounter_system.generate_encounter(location_type, character_level)
```

Every time player says "I look around" or "I search" → encounter roll.

### Root Cause
Encounter check happens on **keyword match** rather than **cooldown/timer**

### Suggested Fix
Add cooldown system:
```python
# Only check every N turns or on location change
if self.session.turns_since_last_encounter >= 10:  # Every 10 turns
    encounter = self.encounter_system.generate_encounter(...)
    if encounter:
        self.session.turns_since_last_encounter = 0
else:
    self.session.turns_since_last_encounter += 1
```

Or check only on specific triggers:
- Entering new location
- Resting
- Explicit "I search for enemies" actions

### Impact
⚠️ **HIGH** - Breaks gameplay pacing, makes exploration tedious

---

## Priority Ranking

1. **Bug 1 + 2 (Unconscious State)** - CRITICAL, breaks core D&D rules
2. **Bug 3 (Encounter Spam)** - HIGH, breaks gameplay flow

## Related Files

- `dnd_rag_system/systems/gm_dialogue_unified.py` - Main GM response generation
- `dnd_rag_system/systems/game_state.py` - CharacterState with conditions
- `dnd_rag_system/systems/combat_manager.py` - Combat turn system (need to check)
- `dnd_rag_system/systems/encounter_system.py` - Random encounter generation

## Notes

All three bugs are fixable but require careful implementation:
- Death saves need UI updates (show saves in character sheet)
- NPC turn system needs investigation
- Encounter cooldown needs game state tracking

**User explicitly stated**: "Never worsen system without asking first"
- Should ask user which bugs to fix first
- Should ask about death save implementation approach
- Should ask about encounter frequency preferences
