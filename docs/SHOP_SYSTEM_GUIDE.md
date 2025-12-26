# 🏪 D&D Shop System - Usage Guide

## Overview

The D&D shop system is built around **natural conversation with NPC shopkeepers**. Players interact with shops through the GM chat, and the system automatically handles transactions while the GM brings the shopkeeper to life with personality and roleplay!

## Philosophy

**Chat-first, mechanics-second** 🎭
- Players talk to shopkeepers naturally through GM chat
- GM controls shopkeeper personality (friendly, grumpy, mysterious, etc.)
- System validates transactions and manages gold/inventory automatically
- GM narrates outcomes naturally based on transaction results

## How It Works

### 1. Setting the Scene

The GM sets up a shop visit by introducing a shopkeeper NPC:

```
🏪 GM: "You push open the creaky door of 'Grundle's Armory'. Behind the counter stands a gruff dwarf, hammering at a piece of metal. He looks up."

"Aye, adventurers! Welcome to me shop! Looking for weapons? Armor? I've got the finest steel this side of the mountains!"
```

### 2. Players Browse & Ask Questions

Players can naturally ask about items:

```
🗨️ Player: "What swords do you have?"

🏪 GM (uses shop.search_shop_inventory("sword")):
"Ahh, interested in swords, are ye? Let me show you what I've got..."
- Longsword (15 gp) - "Classic adventurer's blade!"
- Greatsword (50 gp) - "For the strong of arm!"
- Rapier (25 gp) - "Elegant, if you're into that sort of thing..."
- Shortsword (10 gp) - "Good for tight spaces!"

🗨️ Player: "How much for the longsword?"

🏪 GM: "The longsword? Aye, that's a fine blade. 15 gold pieces, and I'll throw in a free polish!"
```

### 3. Purchasing Items

Players can buy items using natural language OR commands:

**Natural Language:**
```
🗨️ Player: "I'll buy the longsword"
🗨️ Player: "Can I buy a healing potion?"
🗨️ Player: "I want to purchase 2 torches"
🗨️ Player: "Get me the backpack please"
```

**Commands:**
```
🗨️ Player: "/buy longsword"
🗨️ Player: "/buy 3 healing potions"
```

**System Processing:**
```
💼 System: Purchase successful! Bought 1x Longsword for 15 gp. Remaining gold: 85 gp
```

**GM Narration:**
```
🏪 GM: "Excellent choice! *The dwarf carefully wraps the sword in oiled cloth* That'll be 15 gold pieces. May it serve ye well in battle!"

*Your gold pouch feels lighter (85 gp remaining)*
```

### 4. Selling Items

Players can sell items they no longer need:

```
🗨️ Player: "I want to sell my old sword"
OR
🗨️ Player: "/sell old sword"

💼 System: Sold 1x Old Sword for 7.5 gp. Total gold: 92.5 gp

🏪 GM: "*The dwarf examines the blade, running his thumb along the edge*"

"Hmm, seen better days, but the steel's still good. I'll give ye 7 gold and 5 silver for it."

*He counts out the coins and adds them to your purse*
```

### 5. Haggling (Optional Roleplay)

Players can try to haggle for better prices:

```
🗨️ Player: "That's a bit steep! How about 12 gold?"

🏪 GM: "Roll Persuasion!"

🎲 Player: *rolls 18*

🏪 GM: "*The dwarf strokes his beard thoughtfully*"

"Bah! You drive a hard bargain, adventurer. 13 gold, and that's me final offer!"

🗨️ Player: "/buy longsword"
💼 System (GM can manually set haggled price): Purchase successful! Bought 1x Longsword for 13 gp.

🏪 GM: "*He grumbles but hands over the sword with a slight smile*"
```

## Shop System Features

### Automatic Transaction Validation ✅

- **Gold Check**: Ensures player has enough gold
- **Inventory Management**: Adds/removes items automatically
- **Price Lookup**: Searches equipment database for item prices
- **Fuzzy Matching**: "longsword", "long sword", "Longsword" all work

### Equipment Database 📦

58 items loaded from D&D 5e equipment tables:
- **Weapons**: Swords, axes, bows, daggers, etc.
- **Armor**: Leather, chain mail, plate, shields
- **Gear**: Rope, torches, rations, backpacks, tents
- **Potions**: Healing potions (50 gp, heals 2d4+2)
- **Tools**: Thieves' tools, herbalism kit, etc.
- **Mounts**: Horses, ponies, warhorses

### Shopkeeper Personalities 🎭

GM can set shopkeeper personality for roleplay:
- **Friendly**: Cheerful and helpful
- **Grumpy**: Irritable but fair
- **Mysterious**: Cryptic, speaks in riddles
- **Greedy**: Always trying to upsell
- **Paranoid**: Worried about thieves
- **Eccentric**: Quirky, has unusual items

## Example Shopping Session

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Scene: The Prancing Pony Inn - General Store
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏪 GM: "Behind the counter stands a plump halfling woman with a warm smile."

"Welcome, dearies! I'm Rosie. What can I get for you today?"

💰 Your gold: 100 gp

🗨️ Player: "What do you have for adventurers?"

🏪 Rosie: "Oh, all sorts of useful things! We've got:"
- Backpacks (2 gp) - "For carrying your treasures!"
- Rope, hempen 50 ft (1 gp) - "Never go adventuring without it!"
- Torches (1 cp each) - "Light your way in those dark dungeons!"
- Rations, 1 day (5 sp) - "Keep your strength up!"
- Healing Potions (50 gp) - "Life-savers, these are!"

🗨️ Player: "I'll take a backpack, 50 feet of rope, 5 torches, and 2 healing potions"

🏪 Rosie: "Excellent choices, dear! Let me get those for you..."

💼 Transactions:
- Backpack: 2 gp ✓
- Rope, hempen (50 feet): 1 gp ✓
- Torch x5: 0.05 gp ✓
- Potion of Healing x2: 100 gp ✗ (insufficient gold!)

🏪 Rosie: "Oh my! The healing potions alone are 100 gold for two. I can sell you one for 50 gold if you'd like?"

🗨️ Player: "/buy potion of healing"

💼 Purchase successful! Bought 1x Potion of Healing for 50 gp. Remaining: 47 gp

🏪 Rosie: "*She carefully wraps the glowing red vial in soft cloth*"

"There you are, dear! That'll heal you right up if you get hurt. Be careful out there!"

📦 Your Inventory:
- Backpack x1
- Rope, Hempen (50 feet) x1
- Torch x5
- Potion of Healing x1
💰 Gold: 47 gp

🗨️ Player: "Thank you! By the way, do you want to buy this old rusty dagger I found?"

🗨️ Player: "/sell old dagger"

💼 Sold 1x Old Dagger for 1 gp. Total gold: 48 gp

🏪 Rosie: "*She examines it skeptically*"

"Hmm, not worth much, but I can melt it down. 1 gold piece."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Technical Details

### For GMs/Developers

**Shop System API:**
```python
from dnd_rag_system.systems.shop_system import ShopSystem

# Initialize
shop = ShopSystem(chroma_manager, debug=False)

# Search inventory
items = shop.search_shop_inventory("sword", n_results=5)

# Get item price
price = shop.get_item_price("Longsword")  # Returns 15.0

# Process purchase
transaction = shop.attempt_purchase(
    character_state,
    item_name="Longsword",
    quantity=1,
    haggled_price=None  # Optional
)

# Process sale
transaction = shop.attempt_sale(
    character_state,
    item_name="Old Sword",
    quantity=1
)

# Generate shopkeeper context for GM
context = shop.create_shopkeeper_context(
    shop_type="weapon smith",
    shopkeeper_name="Grumak",
    personality="grumpy"
)
```

**Transaction Object:**
```python
@dataclass
class ShopTransaction:
    success: bool              # True if transaction succeeded
    item_name: str            # Name of item
    cost_gp: float            # Cost/revenue in gold
    message: str              # Feedback message
    remaining_gold: float     # Character's gold after transaction
```

### Natural Language Parsing

The system understands:
- **Commands**: `/buy <item>`, `/sell <item>`
- **Natural**: "I'll buy the", "Can I get", "I want to purchase"
- **Quantities**: "buy 3 potions", "/buy 5 torches"
- **Variations**: "longsword", "long sword", "Longsword" all match

## Best Practices

### For GMs 🎲

1. **Set the Scene**: Describe the shop and introduce the shopkeeper with personality
2. **Use RAG Search**: Search shop inventory to describe available items
3. **Roleplay**: Let the shopkeeper have opinions, stories, and quirks
4. **Narrate Transactions**: Don't just say "you buy it" - describe the exchange!
5. **Add Flavor**: Shopkeepers can gossip, give quests, or have special items

### For Players 🗡️

1. **Talk Naturally**: Don't worry about exact commands
2. **Ask Questions**: "What do you have?", "How much for...?"
3. **Roleplay**: Haggle, complain about prices, ask for recommendations
4. **Use Commands**: `/buy` and `/sell` work if you prefer directness

## Files

- **Equipment Loader**: `dnd_rag_system/loaders/equipment_loader.py`
- **Shop System**: `dnd_rag_system/systems/shop_system.py`
- **Tests**: `test_shop_system.py` (run with `python3 test_shop_system.py`)
- **Equipment Data**: `web/equipment.txt` (D&D 5e equipment tables)

## Future Enhancements

Potential additions:
- **Shop-specific inventory**: Different shops have different items
- **Shop gold limits**: Small shops can't buy expensive items
- **Reputation system**: Discounts for loyal customers
- **Quest-giver shopkeepers**: Special items unlock after quests
- **Magical item shops**: Rare and powerful gear

---

**The shop system is ready! Happy shopping, adventurers!** 🏪⚔️
