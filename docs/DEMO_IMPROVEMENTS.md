# Demo Script Improvements

## Problems Fixed

### 1. **Combat Spam** ❌ → ✅
**Before:** Script would spam `/start_combat` repeatedly, even creating new enemies while one was still alive.

**After:** 
- Detects if already in combat before starting new combat
- Checks if enemy is actually dead before re-engaging
- Only 5% chance of forced combat (down from 15%)
- Prefers natural encounters from exploration

### 2. **Immortal Enemies** ❌ → ✅
**Before:** Wolves and other enemies would "live forever" because script didn't properly detect defeats.

**After:**
- `is_enemy_dead()` function checks for defeat indicators
- Auto-ends combat when enemy is clearly defeated
- Stuck combat detection: force-ends after 20 rounds
- Tracks `last_combat_target` to avoid re-fighting dead enemies

### 3. **Boring Exploration** ❌ → ✅
**Before:** Generic exploration actions like "We look for trouble" repeated constantly.

**After:** **Class-specific exploration actions:**

#### **Garret (Rogue)** - Every ~5 turns
- Checks for traps
- Searches for hidden doors
- Picks locks on chests
- Listens at doors
- Examines mechanisms

#### **Lyra (Wizard)** - Every ~7 turns
- Examines ancient runes
- Detects magic
- Consults spellbook for lore
- Identifies magical items

#### **Seraphina (Cleric)** - Every ~6 turns
- Prays for divine guidance
- Checks if places are consecrated/cursed
- Uses Religion knowledge
- Asks deity for wisdom

### 4. **No Class Abilities in Combat** ❌ → ✅
**Before:** Generic "party attacks" - no differentiation between classes.

**After:** **Class-based combat actions:**

#### **Lyra (Wizard)**
- Magic Missile
- Fire Bolt
- Burning Hands
- Mage Armor
- Tactical analysis

#### **Seraphina (Cleric)**
- Cure Wounds (when allies wounded)
- Healing Word
- Sacred Flame
- Bless
- Divine Smite

#### **Garret (Rogue)**
- Sneak attacks
- Dagger throws
- Tactical positioning
- Distraction tactics

#### **Thonk (Barbarian)**
- Rage attacks
- Reckless swings
- Fury charges
- Battle roars

#### **Sir Gideon (Paladin)**
- Divine Smite
- Holy strikes
- Lay on Hands (when wounded)
- Shield bash

### 5. **Context Window Testing** ✅
**New Feature:**
- Pauses every 10 turns to check context accumulation
- Logs when checking context window
- Good for detecting context limit issues

---

## Example Improved Flow

### Turn 1-4: Exploration
```
Turn 1: "The party cautiously explores the area, weapons ready."
Turn 2: "We search the room for treasure and useful items."
Turn 3: "The party investigates their surroundings carefully."
Turn 4: "We look for any signs of recent activity or tracks."
```

### Turn 5: Rogue Action
```
Turn 5: "Garret checks for traps in the area."
        (Rogue-specific action every ~5 turns)
```

### Turn 6: Cleric Guidance
```
Turn 6: "Seraphina prays for divine guidance."
        (Cleric-specific action every ~6 turns)
```

### Turn 7: Wizard Lore
```
Turn 7: "Lyra examines any ancient runes or magical symbols."
        (Wizard-specific action every ~7 turns)
```

### Turn 8: Natural Encounter
```
Turn 8: "⚠️ ENCOUNTER! (Goblin) - Rolling initiative..."
        (GM mentioned goblin naturally in description)
```

### Turn 9-12: Smart Combat
```
Turn 9:  "Lyra casts Magic Missile at the Goblin!"
Turn 10: "Garret sneaks behind the Goblin and attempts a sneak attack!"
Turn 11: "Thonk rages and charges at the Goblin!"
Turn 12: "💀 Goblin appears defeated! Ending combat..."
         (Detects death, ends combat cleanly)
```

### Turn 13+: Back to Exploration
```
Turn 13: "The party searches the goblin's corpse for loot."
Turn 14: "We mark our path so we can find the way back."
```

---

## Configuration

### Combat Settings
- **Forced Combat Chance:** 5% (down from 15%)
- **Stuck Combat Threshold:** 20 rounds (auto-ends)
- **Combat Detection Keywords:** Initiative Order, turn indicators, attack rolls

### Exploration Settings
- **Rogue Actions:** Every ~5 turns
- **Wizard Lore:** Every ~7 turns  
- **Cleric Divine:** Every ~6 turns
- **General Exploration:** All other turns

### Timing
- **Normal Turn Wait:** 6 seconds
- **Context Check Wait:** 12 seconds (every 10 turns)

---

## Context Window Testing

The demo is designed to stress-test context window limits:

1. **Long conversations** - Runs indefinitely, accumulating messages
2. **Combat descriptions** - Detailed turn-by-turn combat narratives
3. **Exploration variety** - Many different exploration descriptions
4. **Character actions** - Each class generates unique action text
5. **Periodic pauses** - Every 10 turns, longer pause to observe behavior

**Watch for:**
- Message quality degradation over time
- Repeated responses (context forgetting)
- Slower response times
- Out-of-memory errors

---

## Running the Demo

```bash
./run_demo.sh
```

Or manually:
```bash
python3 e2e_tests/demo_endless_adventure_playwright.py
```

The browser window will open in **non-headless mode** so you can watch the adventure unfold!

Press `Ctrl+C` to stop.

---

## Future Enhancements

### Potential Additions
- [ ] Inter-party dialogue (characters talking to each other)
- [ ] Inventory management (checking equipment, using items)
- [ ] Spell slot tracking (wizards/clerics running out of spells)
- [ ] Rest mechanics (short/long rests to recover)
- [ ] Shopping (visiting towns, buying potions)
- [ ] Quest tracking (picking up and completing quests)
- [ ] Strategic retreat (fleeing when low HP)
- [ ] Formation tactics (front-line vs back-line positioning)

### Context Window Solutions (if issues found)
- [ ] Implement conversation summarization
- [ ] Use RAG for long-term memory
- [ ] Periodic context pruning (keep only recent turns)
- [ ] Separate combat/exploration context windows
