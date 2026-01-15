"""
Integration Test: Save/Load Full Game Workflow

Tests a complete game session save and load cycle:
1. Create character and start game
2. Explore world, combat, loot
3. Save game
4. Load game and verify state persistence
"""

import pytest
import tempfile
from pathlib import Path

from dnd_rag_system.systems.game_state import GameSession, CharacterState, Location, LocationType
from dnd_rag_system.systems.world_builder import create_starting_world


class TestSaveLoadIntegration:
    """Integration tests for save/load system."""

    def test_full_game_session_workflow(self):
        """
        Test complete game workflow with save/load.

        Simulates a real game session:
        1. Start in town, travel to dungeon
        2. Fight enemies, collect loot
        3. Save game mid-adventure
        4. Load game and verify everything is preserved
        """
        # ===== PART 1: Initial Game Session =====
        session1 = GameSession(session_name="Epic Adventure")

        # Create character
        hero = CharacterState(
            character_name="Adventurer",
            max_hp=30,
            current_hp=25,  # Took some damage
            level=3,
            gold=150,
            inventory={"Longsword": 1, "Shield": 1, "Health Potion": 2}
        )
        session1.character_state = hero

        # Create starting world
        world = create_starting_world()
        session1.world_map = world
        session1.current_location = "Town Square"

        # Create a dungeon location and connect it
        forest_path = Location(
            name="Forest Path",
            location_type=LocationType.FOREST,
            description="A winding path through the forest",
            is_safe=False,
            is_discovered=True
        )
        session1.add_location(forest_path)
        session1.connect_locations("Town Square", "Forest Path")

        # Travel to forest
        success, msg = session1.travel_to("Forest Path")
        assert success, f"Travel failed: {msg}"

        # Explore and discover new location
        dungeon = Location(
            name="Ancient Crypt",
            location_type=LocationType.DUNGEON,
            description="A dark crypt filled with undead",
            is_safe=False,
            is_discovered=True
        )
        session1.add_location(dungeon)
        session1.connect_locations("Forest Path", "Ancient Crypt")

        # Travel to dungeon
        session1.travel_to("Ancient Crypt")

        # Start combat
        session1.combat.start_combat({
            "Adventurer": 18,
            "Skeleton": 10,
            "Zombie": 8
        })

        # Defeat skeleton
        session1.mark_enemy_defeated_at_current_location("Skeleton")

        # Take damage during combat
        hero.take_damage(5)  # Now at 20/30 HP

        # Collect loot
        hero.add_item("Ancient Sword", 1)
        hero.gold += 50  # Now 200 gold

        # Add a quest
        session1.add_quest(
            "Clear the Crypt",
            "Defeat all undead and recover the ancient artifact"
        )

        # Advance time
        session1.advance_time()
        session1.advance_time()  # Now evening

        # ===== PART 2: Save Game =====
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "adventure_save.json"
            session1.save_to_json(save_path)

            # Verify save file exists and has content
            assert save_path.exists()
            assert save_path.stat().st_size > 100  # Should be substantial file

            # ===== PART 3: Load Game =====
            session2 = GameSession.load_from_json(save_path)

            # ===== PART 4: Verify Everything Persisted =====

            # Session info
            assert session2.session_name == "Epic Adventure"
            assert session2.current_location == "Ancient Crypt"
            assert session2.time_of_day == "evening"
            assert session2.day == 1

            # Character state
            assert session2.character_state.character_name == "Adventurer"
            assert session2.character_state.current_hp == 20  # Damaged HP preserved
            assert session2.character_state.max_hp == 30
            assert session2.character_state.gold == 200  # Gold preserved
            assert session2.character_state.level == 3

            # Inventory preserved
            assert "Ancient Sword" in session2.character_state.inventory
            assert "Health Potion" in session2.character_state.inventory
            assert session2.character_state.inventory["Health Potion"] == 2

            # Combat state preserved
            assert session2.combat.in_combat is True
            assert session2.combat.round_number == 1
            assert len(session2.combat.initiative_order) == 3
            # Verify initiative order
            names_in_combat = [name for name, _ in session2.combat.initiative_order]
            assert "Adventurer" in names_in_combat
            assert "Skeleton" in names_in_combat
            assert "Zombie" in names_in_combat

            # World map preserved
            assert "Town Square" in session2.world_map
            assert "Forest Path" in session2.world_map
            assert "Ancient Crypt" in session2.world_map

            # Location connections preserved
            assert "Forest Path" in session2.world_map["Town Square"].connections
            assert "Ancient Crypt" in session2.world_map["Forest Path"].connections

            # Defeated enemies preserved
            current_loc = session2.get_current_location_obj()
            assert current_loc.is_enemy_defeated("Skeleton")

            # Quests preserved
            assert len(session2.active_quests) == 1
            assert session2.active_quests[0]["name"] == "Clear the Crypt"
            assert session2.active_quests[0]["status"] == "active"

    def test_save_load_with_party_mode(self):
        """Test save/load with multiple party members."""
        session1 = GameSession(session_name="Party Adventure")

        # Create party
        from dnd_rag_system.systems.game_state import PartyState

        party = PartyState(party_name="Dragon Slayers")
        party.gold = 500

        # Add party members
        warrior = CharacterState(
            character_name="Warrior",
            max_hp=40,
            current_hp=35,
            level=4,
            gold=100
        )
        mage = CharacterState(
            character_name="Mage",
            max_hp=20,
            current_hp=18,
            level=4,
            gold=100
        )

        party.add_character(warrior)
        party.add_character(mage)
        party.add_shared_item("Rope", 3)
        party.add_shared_item("Torch", 10)

        session1.party = party

        # Create world
        session1.world_map = create_starting_world()
        session1.current_location = "Town Square"

        # Save and load
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "party_save.json"
            session1.save_to_json(save_path)

            session2 = GameSession.load_from_json(save_path)

            # Verify party preserved
            assert session2.party.party_name == "Dragon Slayers"
            assert session2.party.gold == 500
            assert len(session2.party.characters) == 2

            # Verify individual characters
            warrior2 = session2.party.get_character("Warrior")
            assert warrior2 is not None
            assert warrior2.current_hp == 35
            assert warrior2.max_hp == 40

            mage2 = session2.party.get_character("Mage")
            assert mage2 is not None
            assert mage2.current_hp == 18

            # Verify shared inventory
            assert session2.party.shared_inventory["Rope"] == 3
            assert session2.party.shared_inventory["Torch"] == 10

    def test_save_load_preserves_location_state(self):
        """Test that location-specific state is preserved."""
        session1 = GameSession(session_name="State Test")

        # Create locations with state
        cave = Location(
            name="Goblin Cave",
            location_type=LocationType.CAVE,
            description="A dark cave",
            is_safe=False,
            available_items=["Treasure Chest", "Gold Pile"]
        )

        # Add state changes
        cave.mark_enemy_defeated("Goblin Chief")
        cave.remove_item("Treasure Chest", moved_to="inventory")
        cave.mark_event_completed("trap_disarmed")
        cave.record_visit(3)

        session1.add_location(cave)
        session1.current_location = "Goblin Cave"

        # Save and load
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = Path(tmpdir) / "location_save.json"
            session1.save_to_json(save_path)

            session2 = GameSession.load_from_json(save_path)

            # Verify location state
            cave2 = session2.world_map["Goblin Cave"]
            assert cave2.is_enemy_defeated("Goblin Chief")
            assert "Treasure Chest" in cave2.moved_items
            assert cave2.is_event_completed("trap_disarmed")
            assert cave2.visit_count == 1
            assert cave2.last_visited_day == 3
            assert "Gold Pile" in cave2.available_items  # Remaining item

    def test_multiple_save_slots(self):
        """Test saving to different save files."""
        session1 = GameSession(session_name="Save 1")
        session1.character_state = CharacterState(
            character_name="Hero1",
            max_hp=30,
            current_hp=30
        )

        session2 = GameSession(session_name="Save 2")
        session2.character_state = CharacterState(
            character_name="Hero2",
            max_hp=25,
            current_hp=25
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            save1_path = Path(tmpdir) / "save1.json"
            save2_path = Path(tmpdir) / "save2.json"

            # Save both sessions
            session1.save_to_json(save1_path)
            session2.save_to_json(save2_path)

            # Load and verify they're different
            loaded1 = GameSession.load_from_json(save1_path)
            loaded2 = GameSession.load_from_json(save2_path)

            assert loaded1.session_name == "Save 1"
            assert loaded1.character_state.character_name == "Hero1"

            assert loaded2.session_name == "Save 2"
            assert loaded2.character_state.character_name == "Hero2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
