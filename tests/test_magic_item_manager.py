"""
Tests for Magic Item Manager

Comprehensive test suite for magic item lookups, effects, and integration.
"""

import pytest
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.magic_item_manager import MagicItemManager, lookup_magic_item
from dnd_rag_system.data.magic_items import get_magic_item


class TestMagicItemLookup:
    """Test magic item lookup functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = MagicItemManager()

    def test_lookup_existing_item(self):
        """Test looking up an item that exists."""
        item = self.manager.lookup_item("Ring of Protection")
        assert item is not None
        assert item["name"] == "Ring of Protection"
        assert item["rarity"] == "rare"

    def test_lookup_nonexistent_item(self):
        """Test looking up an item that doesn't exist."""
        item = self.manager.lookup_item("Ring of Ultimate Power")
        assert item is None

    def test_lookup_case_insensitive(self):
        """Test that lookup is case-insensitive."""
        item1 = self.manager.lookup_item("Ring of Protection")
        item2 = self.manager.lookup_item("ring of protection")
        item3 = self.manager.lookup_item("RING OF PROTECTION")

        assert item1 is not None
        assert item2 is not None
        assert item3 is not None
        assert item1["name"] == item2["name"] == item3["name"]

    def test_get_all_items(self):
        """Test getting all item names."""
        items = self.manager.get_all_items()
        assert len(items) > 20
        assert "Ring of Protection" in items
        assert "Bag of Holding" in items
        assert "Vorpal Sword" in items

    def test_convenience_function(self):
        """Test the convenience lookup function."""
        item = lookup_magic_item("Bag of Holding")
        assert item is not None
        assert item["name"] == "Bag of Holding"


class TestItemFiltering:
    """Test filtering items by rarity and type."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = MagicItemManager()

    def test_get_by_rarity_common(self):
        """Test getting common items."""
        items = self.manager.get_by_rarity("common")
        assert len(items) >= 1
        assert all(item["rarity"] == "common" for item in items)
        assert any(item["name"] == "Potion of Healing" for item in items)

    def test_get_by_rarity_uncommon(self):
        """Test getting uncommon items."""
        items = self.manager.get_by_rarity("uncommon")
        assert len(items) >= 5
        assert all(item["rarity"] == "uncommon" for item in items)

    def test_get_by_rarity_rare(self):
        """Test getting rare items."""
        items = self.manager.get_by_rarity("rare")
        assert len(items) >= 5
        assert all(item["rarity"] == "rare" for item in items)
        assert any(item["name"] == "Ring of Protection" for item in items)

    def test_get_by_rarity_very_rare(self):
        """Test getting very rare items."""
        items = self.manager.get_by_rarity("very rare")
        assert len(items) >= 3
        assert all(item["rarity"] == "very rare" for item in items)

    def test_get_by_rarity_legendary(self):
        """Test getting legendary items."""
        items = self.manager.get_by_rarity("legendary")
        assert len(items) >= 2
        assert all(item["rarity"] == "legendary" for item in items)
        assert any(item["name"] == "Vorpal Sword" for item in items)

    def test_get_by_type_ring(self):
        """Test getting rings."""
        items = self.manager.get_by_type("ring")
        assert len(items) >= 4
        assert all(item["type"] == "ring" for item in items)

    def test_get_by_type_wondrous(self):
        """Test getting wondrous items."""
        items = self.manager.get_by_type("wondrous")
        assert len(items) >= 5
        assert all(item["type"] == "wondrous" for item in items)
        assert any(item["name"] == "Bag of Holding" for item in items)

    def test_get_by_type_weapon(self):
        """Test getting weapons."""
        items = self.manager.get_by_type("weapon")
        assert len(items) >= 4
        assert all(item["type"] == "weapon" for item in items)

    def test_get_by_type_armor(self):
        """Test getting armor."""
        items = self.manager.get_by_type("armor")
        assert len(items) >= 4
        assert all(item["type"] == "armor" for item in items)

    def test_get_by_type_potion(self):
        """Test getting potions."""
        items = self.manager.get_by_type("potion")
        assert len(items) >= 4
        assert all(item["type"] == "potion" for item in items)


class TestAttunement:
    """Test attunement checking."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = MagicItemManager()

    def test_requires_attunement_true(self):
        """Test items that require attunement."""
        assert self.manager.requires_attunement("Ring of Protection") is True
        assert self.manager.requires_attunement("Boots of Speed") is True
        assert self.manager.requires_attunement("Cloak of Elvenkind") is True

    def test_requires_attunement_false(self):
        """Test items that don't require attunement."""
        assert self.manager.requires_attunement("Bag of Holding") is False
        assert self.manager.requires_attunement("Potion of Healing") is False
        assert self.manager.requires_attunement("Weapon +1") is False

    def test_requires_attunement_nonexistent(self):
        """Test attunement check for nonexistent item."""
        assert self.manager.requires_attunement("Fake Item") is False


class TestItemEffects:
    """Test applying item effects."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = MagicItemManager()

    def test_ring_of_protection_effects(self):
        """Test Ring of Protection effects."""
        item = self.manager.lookup_item("Ring of Protection")
        effects = self.manager.apply_item_effects(None, item)

        assert effects["ac_bonus"] == 1
        assert effects["saving_throw_bonus"] == 1

    def test_weapon_plus_one_effects(self):
        """Test +1 weapon effects."""
        item = self.manager.lookup_item("Weapon +1")
        effects = self.manager.apply_item_effects(None, item)

        assert effects["attack_bonus"] == 1
        assert effects["damage_bonus"] == 1

    def test_weapon_plus_two_effects(self):
        """Test +2 weapon effects."""
        item = self.manager.lookup_item("Weapon +2")
        effects = self.manager.apply_item_effects(None, item)

        assert effects["attack_bonus"] == 2
        assert effects["damage_bonus"] == 2

    def test_flametongue_effects(self):
        """Test Flametongue sword effects."""
        item = self.manager.lookup_item("Flametongue")
        effects = self.manager.apply_item_effects(None, item)

        assert "extra_damage" in effects
        assert effects["extra_damage"]["type"] == "fire"
        assert effects["extra_damage"]["dice"] == "2d6"

    def test_frost_brand_effects(self):
        """Test Frost Brand effects."""
        item = self.manager.lookup_item("Frost Brand")
        effects = self.manager.apply_item_effects(None, item)

        assert "extra_damage" in effects
        assert effects["extra_damage"]["type"] == "cold"
        assert effects["fire_resistance"] is True

    def test_armor_plus_one_effects(self):
        """Test +1 armor effects."""
        item = self.manager.lookup_item("Armor +1")
        effects = self.manager.apply_item_effects(None, item)

        assert effects["ac_bonus"] == 1

    def test_boots_of_elvenkind_effects(self):
        """Test Boots of Elvenkind effects."""
        item = self.manager.lookup_item("Boots of Elvenkind")
        effects = self.manager.apply_item_effects(None, item)

        assert effects["stealth_advantage"] is True

    def test_cloak_of_protection_effects(self):
        """Test Cloak of Protection effects."""
        item = self.manager.lookup_item("Cloak of Protection")
        effects = self.manager.apply_item_effects(None, item)

        assert effects["ac_bonus"] == 1
        assert effects["saving_throw_bonus"] == 1


class TestCanEquipItem:
    """Test equipment validation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = MagicItemManager()

    def test_can_equip_first_item(self):
        """Test equipping first item with no restrictions."""
        ring = self.manager.lookup_item("Ring of Protection")
        can_equip, reason = self.manager.can_equip_item(None, ring, [])

        assert can_equip is True
        assert reason == "OK"

    def test_attunement_limit_three_items(self):
        """Test that you can equip 3 attuned items."""
        equipped = ["Ring of Protection", "Ring of Spell Storing", "Boots of Speed"]
        bag = self.manager.lookup_item("Bag of Holding")
        can_equip, reason = self.manager.can_equip_item(None, bag, equipped)

        # Bag of Holding doesn't require attunement, so should be OK
        assert can_equip is True

    def test_attunement_limit_exceeded(self):
        """Test that you can't equip 4 attuned items."""
        equipped = ["Ring of Protection", "Ring of Spell Storing", "Boots of Speed"]
        cloak = self.manager.lookup_item("Cloak of Protection")
        can_equip, reason = self.manager.can_equip_item(None, cloak, equipped)

        assert can_equip is False
        assert "attune to 3 items" in reason

    def test_ring_limit_two_rings(self):
        """Test that you can wear 2 rings."""
        equipped = ["Ring of Protection"]
        ring2 = self.manager.lookup_item("Ring of Spell Storing")
        can_equip, reason = self.manager.can_equip_item(None, ring2, equipped)

        assert can_equip is True

    def test_ring_limit_exceeded(self):
        """Test that you can't wear 3 rings."""
        equipped = ["Ring of Protection", "Ring of Spell Storing"]
        ring3 = self.manager.lookup_item("Ring of Feather Falling")
        can_equip, reason = self.manager.can_equip_item(None, ring3, equipped)

        assert can_equip is False
        assert "2 rings" in reason

    def test_armor_conflict(self):
        """Test that you can't wear two armors."""
        equipped = ["Armor +1"]
        armor2 = self.manager.lookup_item("Armor +2")
        can_equip, reason = self.manager.can_equip_item(None, armor2, equipped)

        assert can_equip is False
        assert "already wearing" in reason

    def test_boots_conflict(self):
        """Test that you can't wear two boots."""
        equipped = ["Boots of Speed"]
        boots2 = self.manager.lookup_item("Boots of Elvenkind")
        can_equip, reason = self.manager.can_equip_item(None, boots2, equipped)

        assert can_equip is False
        assert "already wearing" in reason

    def test_cloak_conflict(self):
        """Test that you can't wear two cloaks."""
        equipped = ["Cloak of Protection"]
        cloak2 = self.manager.lookup_item("Cloak of Elvenkind")
        can_equip, reason = self.manager.can_equip_item(None, cloak2, equipped)

        assert can_equip is False
        assert "already wearing" in reason


class TestTotalBonuses:
    """Test calculating total bonuses from equipped items."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = MagicItemManager()

    def test_single_item_bonuses(self):
        """Test bonuses from a single item."""
        equipped = ["Ring of Protection"]
        bonuses = self.manager.get_total_bonuses(equipped)

        assert bonuses["ac_bonus"] == 1
        assert bonuses["saving_throw_bonus"] == 1

    def test_stacking_ac_bonuses(self):
        """Test that AC bonuses from different items stack."""
        equipped = ["Ring of Protection", "Cloak of Protection"]
        bonuses = self.manager.get_total_bonuses(equipped)

        assert bonuses["ac_bonus"] == 2  # +1 from ring, +1 from cloak
        assert bonuses["saving_throw_bonus"] == 2

    def test_weapon_bonuses_dont_stack(self):
        """Test that weapon bonuses don't stack (only highest)."""
        equipped = ["Weapon +1", "Weapon +2"]  # Unrealistic but tests logic
        bonuses = self.manager.get_total_bonuses(equipped)

        assert bonuses["attack_bonus"] == 2  # Only highest
        assert bonuses["damage_bonus"] == 2

    def test_resistance_tracking(self):
        """Test tracking damage resistances."""
        equipped = ["Armor of Resistance"]  # Assuming fire resistance
        bonuses = self.manager.get_total_bonuses(equipped)

        # Note: Armor of Resistance has "varies" resistance
        assert "resistances" in bonuses

    def test_fire_resistance_from_frost_brand(self):
        """Test fire resistance from Frost Brand."""
        equipped = ["Frost Brand"]
        bonuses = self.manager.get_total_bonuses(equipped)

        assert "fire" in bonuses["resistances"]

    def test_stealth_advantage(self):
        """Test stealth advantage tracking."""
        equipped = ["Boots of Elvenkind"]
        bonuses = self.manager.get_total_bonuses(equipped)

        assert "stealth" in bonuses["advantages"]

    def test_extra_damage_from_flametongue(self):
        """Test extra damage tracking."""
        equipped = ["Flametongue"]
        bonuses = self.manager.get_total_bonuses(equipped)

        assert len(bonuses["extra_damage"]) == 1
        assert bonuses["extra_damage"][0]["type"] == "fire"
        assert bonuses["extra_damage"][0]["dice"] == "2d6"

    def test_multiple_items_complex(self):
        """Test complex combination of items."""
        equipped = ["Ring of Protection", "Weapon +2", "Boots of Elvenkind"]
        bonuses = self.manager.get_total_bonuses(equipped)

        assert bonuses["ac_bonus"] == 1
        assert bonuses["saving_throw_bonus"] == 1
        assert bonuses["attack_bonus"] == 2
        assert bonuses["damage_bonus"] == 2
        assert "stealth" in bonuses["advantages"]


class TestPotions:
    """Test potion consumption."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = MagicItemManager()

    def test_consume_healing_potion(self):
        """Test consuming a healing potion."""
        result = self.manager.consume_potion("Potion of Healing")

        assert result is not None
        assert result["name"] == "Potion of Healing"
        assert result["effects"]["healing"] == "2d4+2"

    def test_consume_greater_healing_potion(self):
        """Test consuming a greater healing potion."""
        result = self.manager.consume_potion("Potion of Greater Healing")

        assert result is not None
        assert result["effects"]["healing"] == "4d4+4"

    def test_consume_invisibility_potion(self):
        """Test consuming invisibility potion."""
        result = self.manager.consume_potion("Potion of Invisibility")

        assert result is not None
        assert result["effects"]["invisibility"] is True
        assert result["effects"]["duration"] == 60

    def test_consume_flying_potion(self):
        """Test consuming flying potion."""
        result = self.manager.consume_potion("Potion of Flying")

        assert result is not None
        assert result["effects"]["flying_speed"] == 60
        assert result["effects"]["duration"] == 60

    def test_consume_non_potion(self):
        """Test that consuming non-potion returns None."""
        result = self.manager.consume_potion("Ring of Protection")

        assert result is None

    def test_consume_nonexistent_potion(self):
        """Test consuming a nonexistent potion."""
        result = self.manager.consume_potion("Potion of Ultimate Power")

        assert result is None


class TestItemMetadata:
    """Test item metadata completeness."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = MagicItemManager()

    def test_all_items_have_required_fields(self):
        """Test that all items have required fields."""
        all_items = self.manager.get_all_items()

        for item_name in all_items:
            item = self.manager.lookup_item(item_name)

            assert "name" in item, f"{item_name} missing name"
            assert "rarity" in item, f"{item_name} missing rarity"
            assert "attunement" in item, f"{item_name} missing attunement"
            assert "type" in item, f"{item_name} missing type"
            assert "effects" in item, f"{item_name} missing effects"
            assert "description" in item, f"{item_name} missing description"

    def test_all_items_have_valid_rarity(self):
        """Test that all items have valid rarity."""
        valid_rarities = ["common", "uncommon", "rare", "very rare", "legendary"]
        all_items = self.manager.get_all_items()

        for item_name in all_items:
            item = self.manager.lookup_item(item_name)
            assert item["rarity"] in valid_rarities, f"{item_name} has invalid rarity: {item['rarity']}"

    def test_all_items_have_valid_type(self):
        """Test that all items have valid type."""
        valid_types = ["ring", "armor", "weapon", "wondrous", "potion"]
        all_items = self.manager.get_all_items()

        for item_name in all_items:
            item = self.manager.lookup_item(item_name)
            assert item["type"] in valid_types, f"{item_name} has invalid type: {item['type']}"

    def test_database_size(self):
        """Test that we have a good number of items."""
        all_items = self.manager.get_all_items()
        assert len(all_items) >= 25, f"Expected at least 25 items, got {len(all_items)}"


if __name__ == '__main__':
    # Run with: python -m pytest tests/test_magic_item_manager.py -v
    pytest.main([__file__, '-v', '--tb=short'])
