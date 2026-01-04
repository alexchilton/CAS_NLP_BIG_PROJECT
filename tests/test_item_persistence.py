"""
Tests for Item Persistence System (Fix #6)

Tests that items can be picked up from locations and don't respawn.
Simplified version focusing on core functionality.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.game_state import Location, LocationType


@pytest.fixture
def cave():
    """Standard cave location"""
    return Location(
        name="Cave",
        location_type=LocationType.DUNGEON,
        description="A dark cave",
    )


@pytest.fixture
def forest():
    """Forest location"""
    return Location(
        name="Forest",
        location_type=LocationType.WILDERNESS,
        description="A dense forest",
    )


class TestItemTracking:
    """Test item add/remove/check methods"""

    def test_add_and_check_item(self, cave):
        """Test adding and checking for items"""
        cave.add_item("Rope")
        assert cave.has_item("Rope") is True
        assert cave.has_item("Torch") is False

    def test_remove_item(self, cave):
        """Test removing items"""
        cave.add_item("Rope")
        cave.add_item("Torch")
        
        removed = cave.remove_item("Rope")
        
        assert removed is True
        assert cave.has_item("Rope") is False
        assert cave.has_item("Torch") is True

    def test_remove_nonexistent_item(self, cave):
        """Test removing item that doesn't exist"""
        removed = cave.remove_item("Nonexistent")
        assert removed is False


class TestItemPersistence:
    """Test items don't respawn after removal"""

    def test_item_stays_removed(self, cave):
        """Test item doesn't reappear"""
        cave.add_item("Rope")
        cave.remove_item("Rope")
        
        # Item still gone
        assert cave.has_item("Rope") is False
        assert "Rope" in cave.moved_items

    def test_multiple_items(self, cave):
        """Test multiple items persist correctly"""
        cave.add_item("Rope")
        cave.add_item("Torch")
        cave.add_item("Chest")
        
        cave.remove_item("Rope")
        
        assert cave.has_item("Rope") is False
        assert cave.has_item("Torch") is True
        assert cave.has_item("Chest") is True


class TestLocationSeparation:
    """Test each location tracks items separately"""

    def test_separate_item_lists(self, cave, forest):
        """Test locations have separate item lists"""
        cave.add_item("Rope")
        forest.add_item("Berries")
        
        assert cave.has_item("Rope") is True
        assert cave.has_item("Berries") is False
        assert forest.has_item("Berries") is True
        assert forest.has_item("Rope") is False

    def test_removal_doesnt_affect_others(self, cave, forest):
        """Test removing from one location doesn't affect others"""
        cave.add_item("Rope")
        forest.add_item("Rope")
        
        cave.remove_item("Rope")
        
        assert cave.has_item("Rope") is False
        assert forest.has_item("Rope") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
