"""
Unit Tests for Spell Preparation and Learning System

Tests D&D 5e spell mechanics:
- Known vs Prepared spells distinction
- Spell learning
- Spell preparation (Wizard, Cleric, Druid, Paladin)
- Spell casting validation
- Serialization of spell data
"""

import pytest
from dnd_rag_system.systems.game_state import CharacterState, SpellSlots


class TestSpellCasterTypes:
    """Test different spellcaster types."""

    def test_prepared_caster_identification(self):
        """Test that prepared casters are correctly identified."""
        # Prepared casters
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard"
        )
        assert wizard.is_prepared_caster() is True
        assert wizard.is_known_caster() is False

        cleric = CharacterState(
            character_name="Friar Tuck",
            max_hp=25,
            spellcasting_class="Cleric"
        )
        assert cleric.is_prepared_caster() is True

        druid = CharacterState(
            character_name="Radagast",
            max_hp=22,
            spellcasting_class="Druid"
        )
        assert druid.is_prepared_caster() is True

        paladin = CharacterState(
            character_name="Aragorn",
            max_hp=30,
            spellcasting_class="Paladin",
            level=2  # Paladins get spells at level 2
        )
        assert paladin.is_prepared_caster() is True

    def test_known_caster_identification(self):
        """Test that known casters are correctly identified."""
        # Known casters
        sorcerer = CharacterState(
            character_name="Merlin",
            max_hp=18,
            spellcasting_class="Sorcerer"
        )
        assert sorcerer.is_known_caster() is True
        assert sorcerer.is_prepared_caster() is False

        bard = CharacterState(
            character_name="Orpheus",
            max_hp=20,
            spellcasting_class="Bard"
        )
        assert bard.is_known_caster() is True

        warlock = CharacterState(
            character_name="Faust",
            max_hp=19,
            spellcasting_class="Warlock"
        )
        assert warlock.is_known_caster() is True

        ranger = CharacterState(
            character_name="Legolas",
            max_hp=28,
            spellcasting_class="Ranger"
        )
        assert ranger.is_known_caster() is True

    def test_non_caster(self):
        """Test that non-casters are correctly identified."""
        fighter = CharacterState(
            character_name="Conan",
            max_hp=35,
            spellcasting_class=None
        )
        assert fighter.is_prepared_caster() is False
        assert fighter.is_known_caster() is False


class TestSpellLearning:
    """Test spell learning mechanics."""

    def test_learn_spell_wizard(self):
        """Test wizard learning a spell."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            level=3
        )

        result = wizard.learn_spell("Fireball")

        assert result["success"] is True
        assert "Fireball" in wizard.known_spells
        assert "Fireball" not in wizard.prepared_spells  # Not auto-prepared
        assert "must prepare" in result["message"]

    def test_learn_spell_sorcerer(self):
        """Test sorcerer learning a spell (auto-prepares)."""
        sorcerer = CharacterState(
            character_name="Merlin",
            max_hp=18,
            spellcasting_class="Sorcerer",
            level=3
        )

        result = sorcerer.learn_spell("Magic Missile")

        assert result["success"] is True
        assert "Magic Missile" in sorcerer.known_spells
        assert "Magic Missile" in sorcerer.prepared_spells  # Auto-prepared for known casters
        assert "automatically prepared" in result["message"]

    def test_learn_spell_already_known(self):
        """Test learning a spell that's already known."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard"
        )

        wizard.learn_spell("Fireball")
        result = wizard.learn_spell("Fireball")  # Try to learn again

        assert result["success"] is False
        assert "Already know" in result["message"]

    def test_learn_spell_non_caster(self):
        """Test that non-casters cannot learn spells."""
        fighter = CharacterState(
            character_name="Conan",
            max_hp=35,
            spellcasting_class=None
        )

        result = fighter.learn_spell("Fireball")

        assert result["success"] is False
        assert "not a spellcaster" in result["message"]


class TestSpellPreparation:
    """Test spell preparation mechanics for prepared casters."""

    def test_prepare_spell_wizard(self):
        """Test wizard preparing a spell."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            spellcasting_ability="INT",
            level=3
        )

        # Learn spells first
        wizard.learn_spell("Fireball")
        wizard.learn_spell("Magic Missile")

        # Prepare Fireball (INT modifier = 3 for example)
        result = wizard.prepare_spell("Fireball", ability_modifier=3)

        assert result["success"] is True
        assert "Fireball" in wizard.prepared_spells
        assert result["prepared_count"] == 1
        assert result["max_prepared"] == 6  # 3 + 3 = 6

    def test_prepare_multiple_spells(self):
        """Test preparing multiple spells up to limit."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            level=1
        )

        # Learn several spells
        wizard.learn_spell("Magic Missile")
        wizard.learn_spell("Shield")
        wizard.learn_spell("Detect Magic")

        # Prepare spells (INT mod = 2, so max = 2 + 1 = 3)
        wizard.prepare_spell("Magic Missile", ability_modifier=2)
        wizard.prepare_spell("Shield", ability_modifier=2)
        wizard.prepare_spell("Detect Magic", ability_modifier=2)

        assert len(wizard.prepared_spells) == 3
        assert wizard.get_max_prepared_spells(ability_modifier=2) == 3

    def test_prepare_spell_limit_reached(self):
        """Test that preparation limit is enforced."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            level=1
        )

        # Learn spells
        for spell in ["Magic Missile", "Shield", "Detect Magic", "Mage Armor"]:
            wizard.learn_spell(spell)

        # Prepare up to limit (INT mod = 0, so max = 0 + 1 = 1)
        wizard.prepare_spell("Magic Missile", ability_modifier=0)

        # Try to prepare another (should fail)
        result = wizard.prepare_spell("Shield", ability_modifier=0)

        assert result["success"] is False
        assert "limit reached" in result["message"]

    def test_prepare_unknown_spell(self):
        """Test that you can't prepare a spell you don't know."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard"
        )

        result = wizard.prepare_spell("Fireball", ability_modifier=3)

        assert result["success"] is False
        assert "Don't know" in result["message"]

    def test_prepare_already_prepared(self):
        """Test that you can't prepare a spell twice."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard"
        )

        wizard.learn_spell("Fireball")
        wizard.prepare_spell("Fireball", ability_modifier=3)

        result = wizard.prepare_spell("Fireball", ability_modifier=3)

        assert result["success"] is False
        assert "already prepared" in result["message"]

    def test_prepare_spell_known_caster_fails(self):
        """Test that known casters can't use prepare_spell()."""
        sorcerer = CharacterState(
            character_name="Merlin",
            max_hp=18,
            spellcasting_class="Sorcerer"
        )

        sorcerer.learn_spell("Magic Missile")  # Auto-prepares

        result = sorcerer.prepare_spell("Magic Missile", ability_modifier=3)

        assert result["success"] is False
        assert "known spells" in result["message"]


class TestUnprepareSpell:
    """Test spell unpreparing."""

    def test_unprepare_spell(self):
        """Test unpreparing a spell."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard"
        )

        wizard.learn_spell("Fireball")
        wizard.prepare_spell("Fireball", ability_modifier=3)

        result = wizard.unprepare_spell("Fireball")

        assert result["success"] is True
        assert "Fireball" not in wizard.prepared_spells
        assert "Fireball" in wizard.known_spells  # Still known

    def test_unprepare_not_prepared(self):
        """Test unpreparing a spell that isn't prepared."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard"
        )

        wizard.learn_spell("Fireball")

        result = wizard.unprepare_spell("Fireball")

        assert result["success"] is False
        assert "not prepared" in result["message"]


class TestSpellCastingValidation:
    """Test spell casting validation."""

    def test_can_cast_prepared_spell(self):
        """Test that prepared spell can be cast."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            spell_slots=SpellSlots(level_1=2)
        )

        wizard.learn_spell("Magic Missile")
        wizard.prepare_spell("Magic Missile", ability_modifier=3)

        can_cast, reason = wizard.can_cast_spell("Magic Missile")

        assert can_cast is True
        assert reason == "Can cast"

    def test_cannot_cast_unprepared_spell(self):
        """Test that unprepared spell cannot be cast (prepared casters)."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            spell_slots=SpellSlots(level_1=2)
        )

        wizard.learn_spell("Fireball")
        # Don't prepare it

        can_cast, reason = wizard.can_cast_spell("Fireball")

        assert can_cast is False
        assert "not prepared" in reason

    def test_can_cast_known_spell(self):
        """Test that known spell can be cast (known casters)."""
        sorcerer = CharacterState(
            character_name="Merlin",
            max_hp=18,
            spellcasting_class="Sorcerer",
            spell_slots=SpellSlots(level_1=2)
        )

        sorcerer.learn_spell("Magic Missile")  # Auto-prepares

        can_cast, reason = sorcerer.can_cast_spell("Magic Missile")

        assert can_cast is True

    def test_cannot_cast_unknown_spell(self):
        """Test that unknown spell cannot be cast."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard"
        )

        can_cast, reason = wizard.can_cast_spell("Fireball")

        assert can_cast is False
        assert "Don't know" in reason

    def test_non_caster_cannot_cast(self):
        """Test that non-casters cannot cast spells."""
        fighter = CharacterState(
            character_name="Conan",
            max_hp=35,
            spellcasting_class=None
        )

        can_cast, reason = fighter.can_cast_spell("Fireball")

        assert can_cast is False
        assert "not a spellcaster" in reason


class TestCastSpellIntegration:
    """Test cast_spell() with spell validation."""

    def test_cast_prepared_spell_success(self):
        """Test casting a properly prepared spell."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            spell_slots=SpellSlots(level_1=2)
        )

        wizard.learn_spell("Magic Missile")
        wizard.prepare_spell("Magic Missile", ability_modifier=3)

        result = wizard.cast_spell(
            spell_level=1,
            spell_name="Magic Missile"
        )

        assert result["success"] is True
        assert wizard.spell_slots.current_1 == 1  # Slot consumed

    def test_cast_unprepared_spell_fails(self):
        """Test that casting unprepared spell fails."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            spell_slots=SpellSlots(level_1=2)
        )

        wizard.learn_spell("Magic Missile")
        # Don't prepare it

        result = wizard.cast_spell(
            spell_level=1,
            spell_name="Magic Missile"
        )

        assert result["success"] is False
        assert "not prepared" in result["message"]
        assert wizard.spell_slots.current_1 == 2  # Slot not consumed

    def test_cast_spell_skip_validation(self):
        """Test that skip_validation parameter works (backwards compatibility)."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            spell_slots=SpellSlots(level_1=2)
        )

        # Don't learn or prepare spell, but skip validation
        result = wizard.cast_spell(
            spell_level=1,
            spell_name="Magic Missile",
            skip_validation=True  # Old behavior
        )

        assert result["success"] is True  # Succeeds despite not being prepared
        assert wizard.spell_slots.current_1 == 1  # Slot consumed


class TestSpellSerialization:
    """Test serialization of spell data."""

    def test_serialize_spell_data(self):
        """Test that spell data is saved correctly."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            spellcasting_ability="INT"
        )

        wizard.learn_spell("Fireball")
        wizard.learn_spell("Magic Missile")
        wizard.prepare_spell("Fireball", ability_modifier=3)

        data = wizard.to_dict()

        assert data["spellcasting_class"] == "Wizard"
        assert data["spellcasting_ability"] == "INT"
        assert "Fireball" in data["known_spells"]
        assert "Magic Missile" in data["known_spells"]
        assert "Fireball" in data["prepared_spells"]
        assert "Magic Missile" not in data["prepared_spells"]

    def test_deserialize_spell_data(self):
        """Test that spell data is loaded correctly."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            spellcasting_ability="INT"
        )

        wizard.learn_spell("Fireball")
        wizard.prepare_spell("Fireball", ability_modifier=3)

        # Serialize and deserialize
        data = wizard.to_dict()
        wizard2 = CharacterState.from_dict(data)

        assert wizard2.spellcasting_class == "Wizard"
        assert wizard2.spellcasting_ability == "INT"
        assert "Fireball" in wizard2.known_spells
        assert "Fireball" in wizard2.prepared_spells


class TestMaxPreparedSpells:
    """Test calculation of maximum prepared spells."""

    def test_prepared_caster_max_spells(self):
        """Test prepared caster max spell calculation."""
        wizard = CharacterState(
            character_name="Gandalf",
            max_hp=20,
            spellcasting_class="Wizard",
            level=5
        )

        # INT mod = 3: max = 3 + 5 = 8
        max_spells = wizard.get_max_prepared_spells(ability_modifier=3)
        assert max_spells == 8

        # INT mod = -1: max = max(1, -1 + 5) = 4
        max_spells = wizard.get_max_prepared_spells(ability_modifier=-1)
        assert max_spells == 4

        # Edge case: level 1, INT mod = -1: max = max(1, -1 + 1) = 1 (minimum)
        wizard.level = 1
        max_spells = wizard.get_max_prepared_spells(ability_modifier=-1)
        assert max_spells == 1

    def test_known_caster_max_spells(self):
        """Test known caster max spell calculation (unlimited prepared)."""
        sorcerer = CharacterState(
            character_name="Merlin",
            max_hp=18,
            spellcasting_class="Sorcerer",
            level=3
        )

        # Learn spells
        sorcerer.learn_spell("Magic Missile")
        sorcerer.learn_spell("Fireball")
        sorcerer.learn_spell("Shield")

        # Known casters can cast all known spells
        max_spells = sorcerer.get_max_prepared_spells(ability_modifier=3)
        assert max_spells == 3  # All 3 known spells

    def test_non_caster_max_spells(self):
        """Test non-caster returns 0."""
        fighter = CharacterState(
            character_name="Conan",
            max_hp=35,
            spellcasting_class=None
        )

        max_spells = fighter.get_max_prepared_spells(ability_modifier=0)
        assert max_spells == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
