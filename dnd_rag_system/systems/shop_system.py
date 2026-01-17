"""
D&D Shop System - GM-Driven with NPC Shopkeeper Interaction

The shop system is primarily conversational:
1. Players talk to shopkeeper NPCs naturally through the GM chat
2. GM controls shopkeeper personality (friendly, grumpy, mysterious, etc.)
3. Players can ask about items, prices, haggle, get recommendations
4. Transactions happen via chat commands: "/buy <item>" or natural language
5. System validates gold, updates inventory, provides feedback to GM
6. GM narrates the transaction success/failure naturally
"""


from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import re


@dataclass
class ShopTransaction:
    """Result of a shop transaction."""
    success: bool
    item_name: str
    cost_gp: float
    message: str
    remaining_gold: Optional[float] = None


class ShopSystem:
    """
    Manages shop transactions with GM-controlled NPC shopkeepers.

    The magic is in the conversation! The GM roleplay the shopkeeper,
    and this system handles the mechanical side (gold, inventory).
    """

    def __init__(self, chroma_manager, debug: bool = False):
        """
        Initialize shop system.

        Args:
            chroma_manager: ChromaDB manager for equipment lookups
            debug: Enable debug logging
        """
        self.db = chroma_manager
        self.debug = debug

    def search_shop_inventory(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search shop inventory for items matching query.
        Used by GM to describe available items to players.

        Args:
            query: Search query (e.g., "sword", "healing potion", "armor")
            n_results: Number of results to return

        Returns:
            List of matching items with name, description, cost
        """
        try:
            results = self.db.search(
                collection_name="dnd_equipment",
                query_text=query,
                n_results=n_results
            )

            items = []
            if results['documents'] and results['documents'][0]:
                for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                    items.append({
                        'name': meta.get('name', 'Unknown'),
                        'description': doc,
                        'cost_gp': meta.get('cost_gp', 0),
                        'category': meta.get('category', 'gear')
                    })

            return items

        except Exception as e:
            if self.debug:
                print(f"Shop inventory search error: {e}")
            return []

    def get_item_price(self, item_name: str) -> Optional[float]:
        """
        Get price of a specific item.

        Args:
            item_name: Name of item

        Returns:
            Price in gold pieces, or None if not found
        """
        # Search for exact or close match
        results = self.search_shop_inventory(item_name, n_results=5)

        item_name_lower = item_name.lower().strip()

        for item in results:
            item_name_db = item['name'].lower().strip()

            # Check for exact match first
            if item_name_lower == item_name_db:
                return item['cost_gp']

            # Check if either contains the other
            if item_name_lower in item_name_db or item_name_db in item_name_lower:
                return item['cost_gp']

            # Check word overlap (e.g., "healing potion" matches "Potion of Healing")
            query_words = set(item_name_lower.split())
            db_words = set(item_name_db.split())
            overlap = query_words & db_words

            # If significant overlap, consider it a match
            if len(overlap) >= min(len(query_words), len(db_words)) * 0.6:
                return item['cost_gp']

        return None

    def attempt_purchase(
        self,
        character_state,
        item_name: str,
        quantity: int = 1,
        haggled_price: Optional[float] = None
    ) -> ShopTransaction:
        """
        Attempt to purchase an item.
        Validates gold, updates inventory.

        Args:
            character_state: CharacterState object
            item_name: Name of item to purchase
            quantity: Number of items to buy
            haggled_price: Optional haggled price (if player succeeded persuasion check)

        Returns:
            ShopTransaction with success status and message
        """
        # Get item price
        if haggled_price is not None:
            price = haggled_price
            price_source = "haggled"
        else:
            price = self.get_item_price(item_name)
            price_source = "standard"

        if price is None:
            return ShopTransaction(
                success=False,
                item_name=item_name,
                cost_gp=0,
                message=f"'{item_name}' is not available in this shop. Try asking the shopkeeper about what they have in stock!"
            )

        total_cost = price * quantity

        # Check if character has inventory attribute
        if not hasattr(character_state, 'inventory'):
            character_state.inventory = {}

        # Get character's gold from dedicated gold field
        character_gold = getattr(character_state, 'gold', 0)

        # Check if enough gold
        if character_gold < total_cost:
            return ShopTransaction(
                success=False,
                item_name=item_name,
                cost_gp=total_cost,
                remaining_gold=character_gold,
                message=f"Not enough gold! {item_name} costs {total_cost} gp ({price_source} price), but you only have {character_gold} gp."
            )

        # Process purchase - deduct gold
        character_state.gold = character_gold - total_cost

        # Add item to inventory
        if item_name in character_state.inventory:
            character_state.inventory[item_name] += quantity
        else:
            character_state.inventory[item_name] = quantity

        # DEBUG: Verify inventory was updated
        print(f"🛒 DEBUG: Added {quantity}x {item_name} to inventory")
        print(f"🛒 DEBUG: Current inventory: {character_state.inventory}")

        return ShopTransaction(
            success=True,
            item_name=item_name,
            cost_gp=total_cost,
            remaining_gold=character_state.gold,
            message=f"Purchase successful! Bought {quantity}x {item_name} for {total_cost} gp. Remaining gold: {character_state.gold} gp"
        )

    def attempt_sale(
        self,
        character_state,
        item_name: str,
        quantity: int = 1
    ) -> ShopTransaction:
        """
        Attempt to sell an item.
        Sells for half market price (D&D 5e standard).

        Args:
            character_state: CharacterState object
            item_name: Name of item to sell
            quantity: Number of items to sell

        Returns:
            ShopTransaction with success status and message
        """
        # Check if character has the item
        if not hasattr(character_state, 'inventory'):
            character_state.inventory = {}

        if item_name not in character_state.inventory or character_state.inventory[item_name] < quantity:
            available = character_state.inventory.get(item_name, 0)
            return ShopTransaction(
                success=False,
                item_name=item_name,
                cost_gp=0,
                message=f"You don't have {quantity}x {item_name} to sell. You have {available}."
            )

        # Get market price
        market_price = self.get_item_price(item_name)
        if market_price is None:
            # If not in equipment database, assume 1 gp
            market_price = 1.0

        # Sell for half price (D&D 5e rule)
        sell_price = (market_price / 2) * quantity

        # Remove item from inventory
        character_state.inventory[item_name] -= quantity
        if character_state.inventory[item_name] <= 0:
            del character_state.inventory[item_name]

        # Add gold to character's gold field
        current_gold = getattr(character_state, 'gold', 0)
        character_state.gold = current_gold + sell_price

        return ShopTransaction(
            success=True,
            item_name=item_name,
            cost_gp=sell_price,
            remaining_gold=character_state.gold,
            message=f"Sold {quantity}x {item_name} for {sell_price} gp. Total gold: {character_state.gold} gp"
        )

    def parse_purchase_intent(self, player_input: str) -> Optional[Tuple[str, int]]:
        """
        Parse player input for purchase intent.
        Detects commands like: "/buy longsword", "buy 2 healing potions", "I'll take the rope"

        Args:
            player_input: Player's message

        Returns:
            (item_name, quantity) or None if not a purchase
        """
        lower_input = player_input.lower().strip()

        # Pattern 1: /buy <quantity> <item>
        match = re.match(r'/buy\s+(\d+)\s+(.+)', lower_input)
        if match:
            quantity = int(match.group(1))
            item_name = match.group(2).strip()
            return (item_name, quantity)

        # Pattern 2: /buy <item>
        match = re.match(r'/buy\s+(.+)', lower_input)
        if match:
            item_name = match.group(1).strip()
            return (item_name, 1)

        # Pattern 3: Natural language "buy <quantity> <item>"
        match = re.search(r'\b(?:buy|purchase|get|take)\s+(\d+)\s+(.+)', lower_input)
        if match:
            quantity = int(match.group(1))
            item_name = match.group(2).strip()
            # Remove common endings
            item_name = re.sub(r'\s+(please|thanks|thank you)$', '', item_name)
            return (item_name, quantity)

        # Pattern 4: Natural language "buy/take/get <item>"
        # Including "get me the", "give me", etc.
        match = re.search(r'\b(?:buy|purchase|get|take|i\'ll take|give|gimme)(?:\s+me)?\s+(?:the|a|an)\s*(.+)', lower_input)
        if match:
            item_name = match.group(1).strip()
            # Remove common endings and punctuation
            item_name = re.sub(r'\s+(please|thanks|thank you)$', '', item_name)
            item_name = re.sub(r'[?!.,;]$', '', item_name).strip()
            return (item_name, 1)

        return None

    def parse_sell_intent(self, player_input: str) -> Optional[Tuple[str, int]]:
        """
        Parse player input for sell intent.

        Args:
            player_input: Player's message

        Returns:
            (item_name, quantity) or None if not a sale
        """
        lower_input = player_input.lower().strip()

        # Pattern 1: /sell <quantity> <item>
        match = re.match(r'/sell\s+(\d+)\s+(.+)', lower_input)
        if match:
            quantity = int(match.group(1))
            item_name = match.group(2).strip()
            return (item_name, quantity)

        # Pattern 2: /sell <item>
        match = re.match(r'/sell\s+(.+)', lower_input)
        if match:
            item_name = match.group(1).strip()
            return (item_name, 1)

        # Pattern 3: Natural language
        match = re.search(r'\b(?:sell|selling)\s+(\d+)?\s*(.+)', lower_input)
        if match:
            quantity = int(match.group(1)) if match.group(1) else 1
            item_name = match.group(2).strip()
            # Remove possessives and common words
            item_name = re.sub(r'^(my|the|a|an)\s+', '', item_name)
            item_name = re.sub(r'\s+(please|thanks|thank you)$', '', item_name)
            return (item_name, quantity)

        return None

    def create_shopkeeper_context(
        self,
        shop_type: str = "general store",
        shopkeeper_name: str = "Shopkeeper",
        personality: str = "friendly"
    ) -> str:
        """
        Create context for GM to roleplay shopkeeper.

        Args:
            shop_type: Type of shop (general store, weapon smith, apothecary, etc.)
            shopkeeper_name: Name of shopkeeper NPC
            personality: Personality trait (friendly, grumpy, mysterious, greedy, etc.)

        Returns:
            Context string for GM prompt
        """
        personalities = {
            "friendly": "cheerful and helpful, eager to assist customers",
            "grumpy": "irritable and impatient, but fair in business",
            "mysterious": "cryptic and enigmatic, speaks in riddles",
            "greedy": "obsessed with profit, always trying to upsell",
            "paranoid": "suspicious and nervous, worried about thieves",
            "eccentric": "quirky and strange, has unusual items"
        }

        personality_desc = personalities.get(personality, "neutral and professional")

        context = f"""
🏪 SHOPKEEPER MODE ACTIVE

You are roleplaying {shopkeeper_name}, proprietor of this {shop_type}.
Personality: {personality_desc}

**Shopkeeper Behavior**:
- Greet customers warmly (or grumpily, depending on personality)
- Describe items with flavor and personality
- Answer questions about products, prices, and uses
- React to haggling (make players roll Persuasion!)
- Provide rumors or local gossip while browsing
- React naturally to purchases/sales

**Available Inventory**: Search the equipment database for items related to your shop type.
Use context from D&D equipment RAG to describe items accurately.

**Transaction Commands** (players can use these):
- "/buy <item>" or natural: "I'll buy the longsword"
- "/sell <item>" or natural: "I want to sell my old armor"
- System will validate gold and update inventory automatically

**Example Shopkeeper Responses**:
- *"Ahh, interested in that longsword, are ye? Fine craftsmanship, that one! 15 gold pieces and it's yours!"*
- *"Selling that rusty chain mail? *squints* I'll give ye... 25 gold. Best I can do."*
- *"Healing potions? Aye, I've got a few. Brewed 'em myself! 50 gold each, guaranteed to patch ye right up!"*
"""
        return context


def enhance_gm_with_shop(gm_response_func):
    """
    Decorator to enhance GM responses with shop transaction processing.

    When player input contains purchase/sell intent, process transaction
    and add result to GM's context so they can narrate it naturally.
    """
    def wrapper(self, player_input: str, use_rag: bool = True):
        # Check for shop commands
        shop = ShopSystem(self.db)

        purchase_intent = shop.parse_purchase_intent(player_input)
        sell_intent = shop.parse_sell_intent(player_input)

        transaction_feedback = ""

        if purchase_intent and self.session.character_state:
            item_name, quantity = purchase_intent
            transaction = shop.attempt_purchase(
                self.session.character_state,
                item_name,
                quantity
            )
            transaction_feedback = f"\n\n**TRANSACTION RESULT**: {transaction.message}\n"

        elif sell_intent and self.session.character_state:
            item_name, quantity = sell_intent
            transaction = shop.attempt_sale(
                self.session.character_state,
                item_name,
                quantity
            )
            transaction_feedback = f"\n\n**TRANSACTION RESULT**: {transaction.message}\n"

        # Call original GM response function
        response = gm_response_func(self, player_input, use_rag)

        # Add transaction feedback if any
        if transaction_feedback:
            response = transaction_feedback + response

        return response

    return wrapper
