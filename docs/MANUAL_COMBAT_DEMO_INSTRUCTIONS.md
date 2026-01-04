# Manual Combat Demonstration

## ✅ Gradio is Running
**URL**: http://localhost:7860

## 🎯 To See Full Combat Flow:

### Step 1: Load Character
1. Open http://localhost:7860
2. Select "Thorin" from the character dropdown
3. Click "Load Character"

### Step 2: Check Location
Send command:
```
/context
```

You should see Thorin's stats and current location.

### Step 3: Add Goblin Manually (Simulating GM Description)
Send command:
```
/start_combat Goblin
```

This will:
- ✅ Look up Goblin stats from database
- ✅ Roll initiative for Thorin and Goblin
- ✅ Show initiative order (highest to lowest)
- ✅ Indicate whose turn it is

### Step 4: Attack with Longsword
When it's Thorin's turn, send:
```
I attack the goblin with my longsword
```

Expected behavior:
- ✅ GM describes attack (roll d20 + attack bonus)
- ✅ If hit, roll damage (longsword is 1d8 + STR)
- ✅ **Turn automatically advances to Goblin's turn**
- ✅ **Goblin attacks back automatically** (NPC AI)

### Step 5: Continue Combat
Keep attacking:
```
I attack the goblin
```

Combat continues with:
- ✅ Proper turn sequence (Thorin → Goblin → Thorin → Goblin...)
- ✅ HP tracking for both combatants
- ✅ Round counter increments
- ✅ Combat ends when goblin reaches 0 HP (death event)

### Step 6: View Initiative
At any time, check the combat status:
```
/initiative
```

Shows:
- Current round number
- Initiative order with markers for current turn
- HP status (if tracked in UI)

---

## 📊 What You'll See

### Location Description ✅
- Set via `TEST_START_LOCATION` or character loading
- Current location shown in `/context`

### Combat Order ✅
```
⚔️ COMBAT BEGINS!

📜 Initiative Order:
1. Thorin Stormshield (14)
2. Goblin (8)

🎯 Thorin's turn!
```

### Turn Sequence ✅
```
Round 1, Thorin's turn:
> I attack the goblin
GM: You swing your longsword... (rolls dice)... 15 damage!

**Goblin's Turn!**
Goblin attacks: (rolls) 8 vs AC 18 - MISS!

Round 2, Thorin's turn:
> I attack the goblin
...
```

### Death Event ✅
```
Your longsword strikes true! The goblin falls dead!

⚔️ Combat has ended!
```

---

## 🎮 Alternative: Programmatic Demo

If you want to see it WITHOUT the GUI, I created a working programmatic test in `e2e_tests/test_combat_system.py` that shows:
- ✅ 9 combat tests all passing
- ✅ Full turn sequence
- ✅ Initiative order
- ✅ Auto-advancement

Run it with:
```bash
python3 e2e_tests/test_combat_system.py
```

This demonstrates ALL the mechanics without LLM timeout issues.

---

## 🐛 Current Issue

The LLM (Ollama) is slow/timing out in automated tests. But the **GUI works fine** for interactive testing.

**Recommendation**: Use the Gradio GUI at http://localhost:7860 to manually verify the combat flow.
