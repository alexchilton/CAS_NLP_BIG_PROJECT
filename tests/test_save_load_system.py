"""
Unit tests for Save/Load System

Tests serialization and deserialization of:
- Location
- CharacterState
- PartyState
- CombatState
- GameSession
"""

import pytest
import json
import tempfile
from pathlib import Path

from dnd_rag_system.systems.game_state import (
    Location, LocationType, CharacterState, PartyState,
    CombatState, GameSession, SpellSlots, DeathSaves
)


class TestLocationSerialization:
    """Test Location.to_dict() and from_dict()."""

    def test_location_basic_serialization(self):
        """Test basic location serialization."""
        loc = Location(
            name="Town Square",
            location_type=LocationType.TOWN,
            description="A bustling town square",
            has_shop=True,
            is_safe=True,
            connections=["Market Street", "Temple"],
            resident_npcs=["Merchant", "Guard"]
        )

        # Serialize
        data = loc.to_dict()

        # Verify structure
        assert data["name"] == "Town Square"
        assert data["location_type"] == "town"
        assert data["description"] == "A bustling town square"
        assert data["has_shop"] is True
        assert data["connections"] == ["Market Street", "Temple"]

        # Deserialize
        loc2 = Location.from_dict(data)

        assert loc2.name == loc.name
        assert loc2.location_type == loc.location_type
        assert loc2.description == loc.description
        assert loc2.has_shop == loc.has_shop
        assert loc2.connections == loc.connections

    def test_location_with_state_changes(self):
        """Test location with defeated enemies and moved items."""
        loc = Location(
            name="Goblin Cave",
            location_type=LocationType.CAVE,
            description="A dark cave",
            is_safe=False,
            available_items=["Treasure Chest", "Gold Coins"]  # Add items first
        )

        # Add state changes
        loc.mark_enemy_defeated("Goblin Chief")
        loc.remove_item("Treasure Chest", moved_to="inventory")  # Now this will work
        loc.mark_event_completed("secret_door_opened")
        loc.record_visit(5)

        # Serialize and deserialize
        data = loc.to_dict()
        loc2 = Location.from_dict(data)

        assert loc2.is_enemy_defeated("Goblin Chief")
        assert "Treasure Chest" in loc2.moved_items
        assert loc2.is_event_completed("secret_door_opened")
        assert loc2.visit_count == 1
        assert loc2.last_visited_day == 5


class TestCharacterStateSerialization:
    """Test CharacterState.to_dict() and from_dict()."""

    def test_character_state_basic(self):
        """Test basic character state serialization."""
        char = CharacterState(
            character_name="Thorin",
            max_hp=30,
            current_hp=25,
            level=3,
            inventory={"Longsword": 1, "Shield": 1},
            gold=100
        )

        # Serialize
        data = char.to_dict()

        # Verify
        assert data["character_name"] == "Thorin"
        assert data["current_hp"] == 25
        assert data["max_hp"] == 30
        assert data["gold"] == 100

        # Deserialize
        char2 = CharacterState.from_dict(data)

        assert char2.character_name == char.character_name
        assert char2.current_hp == char.current_hp
        assert char2.max_hp == char.max_hp
        assert char2.inventory == char.inventory

    def test_character_state_with_spell_slots(self):
        """Test character with spell slots."""
        char = CharacterState(
            character_name="Elara",
            max_hp=20,
            current_hp=20,
            level=5
        )

        # Set spell slots (max values)
        char.spell_slots = SpellSlots(level_1=4, level_2=3, level_3=2)

        # Serialize and deserialize
        data = char.to_dict()
        char2 = CharacterState.from_dict(data)

        # Verify max spell slots are preserved
        assert char2.spell_slots.level_1 == 4
        assert char2.spell_slots.level_2 == 3
        assert char2.spell_slots.level_3 == 2

    def test_character_state_with_conditions(self):
        """Test character with conditions and death saves."""
        char = CharacterState(
            character_name="Gimli",
            max_hp=30,
            current_hp=0  # Unconscious
        )

        char.conditions.append("unconscious")
        char.death_saves.add_success()
        char.death_saves.add_failure()

        # Serialize and deserialize
        data = char.to_dict()
        char2 = CharacterState.from_dict(data)

        assert "unconscious" in char2.conditions
        assert char2.death_saves.successes == 1
        assert char2.death_saves.failures == 1


class TestPartyStateSerialization:
    """Test PartyState.to_dict() and from_dict()."""

    def test_party_state_serialization(self):
        """Test party state with multiple characters."""
        party = PartyState(party_name="Dragon Slayers")
        party.gold = 500

        # Add characters
        thorin = CharacterState(
            character_name="Thorin",
            max_hp=30,
            current_hp=30
        )
        elara = CharacterState(
            character_name="Elara",
            max_hp=20,
            current_hp=15
        )

        party.add_character(thorin)
        party.add_character(elara)

        # Add shared inventory
        party.add_shared_item("Rope", 2)
        party.add_shared_item("Torch", 5)

        # Serialize
        data = party.to_dict()

        # Verify
        assert data["party_name"] == "Dragon Slayers"
        assert data["gold"] == 500
        assert "Thorin" in data["characters"]
        assert "Elara" in data["characters"]

        # Deserialize
        party2 = PartyState.from_dict(data)

        assert party2.party_name == party.party_name
        assert party2.gold == party.gold
        assert len(party2.characters) == 2
        assert "Thorin" in party2.characters
        assert party2.shared_inventory["Rope"] == 2


class TestCombatStateSerialization:
    """Test CombatState.to_dict() and from_dict()."""

    def test_combat_state_basic(self):
        """Test combat state serialization."""
        combat = CombatState()

        # Start combat
        initiatives = {
            "Thorin": 15,
            "Goblin": 12,
            "Elara": 18
        }
        combat.start_combat(initiatives)

        # Advance turn
        combat.next_turn()

        # Serialize
        data = combat.to_dict()

        # Verify
        assert data["in_combat"] is True
        assert data["round_number"] == 1
        assert len(data["initiative_order"]) == 3

        # Deserialize
        combat2 = CombatState.from_dict(data)

        assert combat2.in_combat is True
        assert combat2.round_number == 1
        assert combat2.initiative_order == combat.initiative_order
        assert combat2.current_turn_index == combat.current_turn_index

    def test_combat_state_with_effects(self):
        """Test combat state with active effects."""
        combat = CombatState()
        combat.start_combat({"Hero": 15, "Monster": 10})

        # Add effects
        combat.add_effect("Bless", "Hero", 3, "Blessed by cleric")
        combat.add_effect("Poisoned", "Monster", 2, "Poisoned condition")

        # Serialize and deserialize
        data = combat.to_dict()
        combat2 = CombatState.from_dict(data)

        assert "Bless" in combat2.active_effects
        assert "Poisoned" in combat2.active_effects
        target, duration, desc = combat2.active_effects["Bless"]
        assert target == "Hero"
        assert duration == 3


class TestGameSessionSerialization:
    """Test GameSession.save_to_json() and load_from_json()."""

    def test_game_session_basic_save_load(self):
        """Test basic game session save and load."""
        session = GameSession(
            session_name="Test Adventure",
            current_location="Town Square",
            scene_description="A bustling marketplace"
        )

        # Add character
        char = CharacterState(
            character_name="Thorin",
            max_hp=30,
            current_hp=25,
            gold=100
        )
        session.character_state = char

        # Add location to world map
        town = Location(
            name="Town Square",
            location_type=LocationType.TOWN,
            description="A bustling marketplace"
        )
        session.add_location(town)

        # Save to temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "test_save.json"
            session.save_to_json(save_path)

            # Verify file exists
            assert save_path.exists()

            # Load
            session2 = GameSession.load_from_json(save_path)

            # Verify data
            assert session2.session_name == "Test Adventure"
            assert session2.current_location == "Town Square"
            assert session2.character_state.character_name == "Thorin"
            assert session2.character_state.current_hp == 25
            assert "Town Square" in session2.world_map

    def test_game_session_with_party(self):
        """Test game session save/load with party."""
        session = GameSession(session_name="Party Adventure")

        # Create party
        party = PartyState(party_name="Heroes")
        thorin = CharacterState(character_name="Thorin", max_hp=30)
        elara = CharacterState(character_name="Elara", max_hp=20)
        party.add_character(thorin)
        party.add_character(elara)
        session.party = party

        # Save and load
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "party_save.json"
            session.save_to_json(save_path)

            session2 = GameSession.load_from_json(save_path)

            assert session2.party.party_name == "Heroes"
            assert len(session2.party.characters) == 2
            assert "Thorin" in session2.party.characters

    def test_game_session_with_combat(self):
        """Test game session save/load during combat."""
        session = GameSession(session_name="Combat Test")

        # Start combat
        char = CharacterState(character_name="Hero", max_hp=30)
        session.character_state = char

        session.combat.start_combat({"Hero": 18, "Goblin": 12})
        session.combat.next_turn()  # Advance turn

        # Save and load
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "combat_save.json"
            session.save_to_json(save_path)

            session2 = GameSession.load_from_json(save_path)

            assert session2.combat.in_combat is True
            assert session2.combat.round_number == 1
            assert len(session2.combat.initiative_order) == 2

    def test_game_session_with_quests(self):
        """Test game session save/load with quests."""
        session = GameSession(session_name="Quest Test")

        # Add quests
        session.add_quest("Find the Dragon", "Locate the ancient dragon")
        session.add_quest("Rescue the Princess", "Save her from the tower")
        session.complete_quest("Find the Dragon")

        # Save and load
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "quest_save.json"
            session.save_to_json(save_path)

            session2 = GameSession.load_from_json(save_path)

            assert len(session2.active_quests) == 2
            assert "Find the Dragon" in session2.completed_quests

    def test_game_session_with_complex_world(self):
        """Test game session with multiple locations and connections."""
        session = GameSession(session_name="World Test")

        # Create world map
        town = Location(
            name="Town Square",
            location_type=LocationType.TOWN,
            description="Town center"
        )
        cave = Location(
            name="Goblin Cave",
            location_type=LocationType.CAVE,
            description="A dark cave",
            is_safe=False
        )

        session.add_location(town)
        session.add_location(cave)
        session.connect_locations("Town Square", "Goblin Cave")

        # Mark enemy defeated in cave
        session.current_location = "Goblin Cave"
        session.mark_enemy_defeated_at_current_location("Goblin Chief")

        # Save and load
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "world_save.json"
            session.save_to_json(save_path)

            session2 = GameSession.load_from_json(save_path)

            assert "Town Square" in session2.world_map
            assert "Goblin Cave" in session2.world_map
            assert "Goblin Cave" in session2.world_map["Town Square"].connections
            assert session2.world_map["Goblin Cave"].is_enemy_defeated("Goblin Chief")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
