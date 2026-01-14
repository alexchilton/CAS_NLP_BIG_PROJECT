"""
Tests for Class Feature Manager

Comprehensive test suite for class features, level progression, and mechanics.
"""

import pytest
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dnd_rag_system.systems.class_feature_manager import ClassFeatureManager, lookup_class_feature
from dnd_rag_system.data.class_features import get_class_data


class TestClassLookup:
    """Test class information lookup."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_get_class_info_rogue(self):
        """Test getting Rogue class info."""
        info = self.manager.get_class_info("Rogue")
        assert info is not None
        assert info["hit_dice"] == "d8"
        assert info["primary_ability"] == "dexterity"

    def test_get_class_info_fighter(self):
        """Test getting Fighter class info."""
        info = self.manager.get_class_info("Fighter")
        assert info is not None
        assert info["hit_dice"] == "d10"

    def test_get_class_info_wizard(self):
        """Test getting Wizard class info."""
        info = self.manager.get_class_info("Wizard")
        assert info is not None
        assert info["hit_dice"] == "d6"
        assert info["spellcasting_ability"] == "intelligence"

    def test_get_class_info_case_insensitive(self):
        """Test that class lookup is case-insensitive."""
        info1 = self.manager.get_class_info("Rogue")
        info2 = self.manager.get_class_info("rogue")
        info3 = self.manager.get_class_info("ROGUE")

        assert info1 is not None
        assert info2 is not None
        assert info3 is not None

    def test_get_class_info_nonexistent(self):
        """Test looking up a nonexistent class."""
        info = self.manager.get_class_info("Dragonborn")
        assert info is None

    def test_get_available_classes(self):
        """Test getting all available classes."""
        classes = self.manager.get_available_classes()
        assert len(classes) >= 4
        assert "Rogue" in classes
        assert "Fighter" in classes
        assert "Wizard" in classes
        assert "Cleric" in classes


class TestFeatureLookup:
    """Test feature lookup functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_lookup_sneak_attack(self):
        """Test looking up Sneak Attack."""
        feature = self.manager.lookup_feature("Rogue", "Sneak Attack")
        assert feature is not None
        assert feature["name"] == "Sneak Attack"
        assert feature["level"] == 1
        assert "damage_by_level" in feature

    def test_lookup_action_surge(self):
        """Test looking up Action Surge."""
        feature = self.manager.lookup_feature("Fighter", "Action Surge")
        assert feature is not None
        assert feature["name"] == "Action Surge"
        assert feature["level"] == 2

    def test_lookup_rage(self):
        """Test looking up Rage."""
        feature = self.manager.lookup_feature("Barbarian", "Rage")
        assert feature is not None
        assert feature["name"] == "Rage"
        assert feature["level"] == 1

    def test_lookup_divine_smite(self):
        """Test looking up Divine Smite."""
        feature = self.manager.lookup_feature("Paladin", "Divine Smite")
        assert feature is not None
        assert feature["name"] == "Divine Smite"
        assert feature["level"] == 2

    def test_lookup_case_insensitive(self):
        """Test that feature lookup is case-insensitive."""
        feature1 = self.manager.lookup_feature("Rogue", "Sneak Attack")
        feature2 = self.manager.lookup_feature("Rogue", "sneak attack")
        feature3 = self.manager.lookup_feature("Rogue", "SNEAK ATTACK")

        assert feature1 is not None
        assert feature2 is not None
        assert feature3 is not None

    def test_lookup_nonexistent_feature(self):
        """Test looking up a feature that doesn't exist."""
        feature = self.manager.lookup_feature("Rogue", "Fireball")
        assert feature is None

    def test_convenience_function(self):
        """Test the convenience lookup function."""
        feature = lookup_class_feature("Fighter", "Second Wind")
        assert feature is not None
        assert feature["name"] == "Second Wind"


class TestFeaturesAtLevel:
    """Test getting features at specific levels."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_rogue_level_1_features(self):
        """Test Rogue level 1 features."""
        features = self.manager.get_features_at_level("Rogue", 1)
        assert len(features) >= 2
        feature_names = [f["name"] for f in features]
        assert "Sneak Attack" in feature_names
        assert "Expertise" in feature_names

    def test_rogue_level_2_features(self):
        """Test Rogue level 2 features."""
        features = self.manager.get_features_at_level("Rogue", 2)
        assert len(features) >= 1
        assert features[0]["name"] == "Cunning Action"

    def test_fighter_level_1_features(self):
        """Test Fighter level 1 features."""
        features = self.manager.get_features_at_level("Fighter", 1)
        assert len(features) >= 2
        feature_names = [f["name"] for f in features]
        assert "Fighting Style" in feature_names
        assert "Second Wind" in feature_names

    def test_fighter_level_2_features(self):
        """Test Fighter level 2 features."""
        features = self.manager.get_features_at_level("Fighter", 2)
        assert len(features) >= 1
        assert features[0]["name"] == "Action Surge"

    def test_level_with_no_features(self):
        """Test a level with no new features."""
        features = self.manager.get_features_at_level("Rogue", 4)
        assert features == []

    def test_get_all_features_up_to_level(self):
        """Test getting all features up to a level."""
        all_features = self.manager.get_all_features("Rogue", 5)
        assert 1 in all_features
        assert 2 in all_features
        assert 5 in all_features
        assert 6 not in all_features  # Should not include level 6


class TestFeatureScaling:
    """Test feature value scaling by level."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_sneak_attack_level_1(self):
        """Test Sneak Attack damage at level 1."""
        damage = self.manager.calculate_feature_value("Sneak Attack", 1, "Rogue")
        assert damage == "1d6"

    def test_sneak_attack_level_3(self):
        """Test Sneak Attack damage at level 3."""
        damage = self.manager.calculate_feature_value("Sneak Attack", 3, "Rogue")
        assert damage == "2d6"

    def test_sneak_attack_level_5(self):
        """Test Sneak Attack damage at level 5."""
        damage = self.manager.calculate_feature_value("Sneak Attack", 5, "Rogue")
        assert damage == "3d6"

    def test_sneak_attack_level_20(self):
        """Test Sneak Attack damage at level 20."""
        damage = self.manager.calculate_feature_value("Sneak Attack", 20, "Rogue")
        assert damage == "10d6"

    def test_action_surge_level_2(self):
        """Test Action Surge uses at level 2."""
        uses = self.manager.calculate_feature_value("Action Surge", 2, "Fighter")
        assert uses == 1

    def test_action_surge_level_17(self):
        """Test Action Surge uses at level 17."""
        uses = self.manager.calculate_feature_value("Action Surge", 17, "Fighter")
        assert uses == 2

    def test_extra_attack_level_5(self):
        """Test Extra Attack at level 5."""
        attacks = self.manager.calculate_feature_value("Extra Attack", 5, "Fighter")
        assert attacks == 2

    def test_extra_attack_level_11(self):
        """Test Extra Attack at level 11."""
        attacks = self.manager.calculate_feature_value("Extra Attack", 11, "Fighter")
        assert attacks == 3

    def test_extra_attack_level_20(self):
        """Test Extra Attack at level 20."""
        attacks = self.manager.calculate_feature_value("Extra Attack", 20, "Fighter")
        assert attacks == 4

    def test_rage_uses_level_1(self):
        """Test Rage uses at level 1."""
        uses = self.manager.calculate_feature_value("Rage", 1, "Barbarian")
        assert uses == 2

    def test_rage_uses_level_6(self):
        """Test Rage uses at level 6."""
        uses = self.manager.calculate_feature_value("Rage", 6, "Barbarian")
        assert uses == 4

    def test_channel_divinity_level_2(self):
        """Test Channel Divinity uses at level 2."""
        uses = self.manager.calculate_feature_value("Channel Divinity", 2, "Cleric")
        assert uses == 1

    def test_channel_divinity_level_6(self):
        """Test Channel Divinity uses at level 6."""
        uses = self.manager.calculate_feature_value("Channel Divinity", 6, "Cleric")
        assert uses == 2


class TestSpellcasting:
    """Test spellcasting features."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_wizard_spell_slots_level_1(self):
        """Test Wizard spell slots at level 1."""
        slots = self.manager.get_spell_slots("Wizard", 1)
        assert slots["1st"] == 2

    def test_wizard_spell_slots_level_5(self):
        """Test Wizard spell slots at level 5."""
        slots = self.manager.get_spell_slots("Wizard", 5)
        assert slots["1st"] == 4
        assert slots["2nd"] == 3
        assert slots["3rd"] == 2

    def test_cleric_spell_slots_level_3(self):
        """Test Cleric spell slots at level 3."""
        slots = self.manager.get_spell_slots("Cleric", 3)
        assert slots["1st"] == 4
        assert slots["2nd"] == 2

    def test_paladin_spell_slots_level_5(self):
        """Test Paladin spell slots at level 5."""
        slots = self.manager.get_spell_slots("Paladin", 5)
        assert slots["1st"] == 4
        assert slots["2nd"] == 2

    def test_non_caster_spell_slots(self):
        """Test that non-casters have no spell slots."""
        slots = self.manager.get_spell_slots("Rogue", 5)
        assert slots == {}

    def test_paladin_no_slots_at_level_1(self):
        """Test that Paladin has no slots at level 1."""
        slots = self.manager.get_spell_slots("Paladin", 1)
        assert slots == {}


class TestClassMetadata:
    """Test class metadata (hit dice, saves, etc.)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_rogue_hit_die(self):
        """Test Rogue hit die."""
        hit_die = self.manager.get_hit_die("Rogue")
        assert hit_die == "d8"

    def test_fighter_hit_die(self):
        """Test Fighter hit die."""
        hit_die = self.manager.get_hit_die("Fighter")
        assert hit_die == "d10"

    def test_wizard_hit_die(self):
        """Test Wizard hit die."""
        hit_die = self.manager.get_hit_die("Wizard")
        assert hit_die == "d6"

    def test_barbarian_hit_die(self):
        """Test Barbarian hit die."""
        hit_die = self.manager.get_hit_die("Barbarian")
        assert hit_die == "d12"

    def test_rogue_saving_throws(self):
        """Test Rogue saving throw proficiencies."""
        saves = self.manager.get_saving_throw_proficiencies("Rogue")
        assert "dexterity" in saves
        assert "intelligence" in saves

    def test_fighter_saving_throws(self):
        """Test Fighter saving throw proficiencies."""
        saves = self.manager.get_saving_throw_proficiencies("Fighter")
        assert "strength" in saves
        assert "constitution" in saves

    def test_wizard_saving_throws(self):
        """Test Wizard saving throw proficiencies."""
        saves = self.manager.get_saving_throw_proficiencies("Wizard")
        assert "intelligence" in saves
        assert "wisdom" in saves

    def test_cleric_saving_throws(self):
        """Test Cleric saving throw proficiencies."""
        saves = self.manager.get_saving_throw_proficiencies("Cleric")
        assert "wisdom" in saves
        assert "charisma" in saves


class TestPrerequisites:
    """Test feature prerequisite checking."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_has_level_1_feature_at_level_1(self):
        """Test that level 1 character has level 1 features."""
        has_feature, reason = self.manager.check_feature_prerequisites("Rogue", "Sneak Attack", 1)
        assert has_feature is True
        assert reason == "OK"

    def test_has_level_2_feature_at_level_2(self):
        """Test that level 2 character has level 2 features."""
        has_feature, reason = self.manager.check_feature_prerequisites("Rogue", "Cunning Action", 2)
        assert has_feature is True

    def test_does_not_have_level_5_feature_at_level_3(self):
        """Test that level 3 character doesn't have level 5 features."""
        has_feature, reason = self.manager.check_feature_prerequisites("Rogue", "Uncanny Dodge", 3)
        assert has_feature is False
        assert "level 5" in reason.lower()

    def test_has_level_5_feature_at_level_5(self):
        """Test that level 5 character has level 5 features."""
        has_feature, reason = self.manager.check_feature_prerequisites("Rogue", "Uncanny Dodge", 5)
        assert has_feature is True

    def test_has_level_5_feature_at_level_10(self):
        """Test that higher level character has lower level features."""
        has_feature, reason = self.manager.check_feature_prerequisites("Rogue", "Uncanny Dodge", 10)
        assert has_feature is True

    def test_nonexistent_feature(self):
        """Test checking prerequisites for nonexistent feature."""
        has_feature, reason = self.manager.check_feature_prerequisites("Rogue", "Fireball", 10)
        assert has_feature is False
        assert "not found" in reason


class TestFeatureSummary:
    """Test feature summary generation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_rogue_summary_level_5(self):
        """Test Rogue feature summary up to level 5."""
        summary = self.manager.get_feature_summary("Rogue", 5)
        assert "Rogue Features" in summary
        assert "Sneak Attack" in summary
        assert "Cunning Action" in summary
        assert "Uncanny Dodge" in summary

    def test_fighter_summary_level_5(self):
        """Test Fighter feature summary up to level 5."""
        summary = self.manager.get_feature_summary("Fighter", 5)
        assert "Fighter Features" in summary
        assert "Second Wind" in summary
        assert "Action Surge" in summary
        assert "Extra Attack" in summary

    def test_summary_includes_levels(self):
        """Test that summary includes level markers."""
        summary = self.manager.get_feature_summary("Rogue", 3)
        assert "Level 1" in summary
        assert "Level 2" in summary
        assert "Level 3" in summary


class TestRogueFeatures:
    """Detailed tests for Rogue features."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_sneak_attack_metadata(self):
        """Test Sneak Attack feature metadata."""
        feature = self.manager.lookup_feature("Rogue", "Sneak Attack")
        assert feature["trigger"] == "advantage on attack roll OR ally within 5 feet of target"
        assert feature["frequency"] == "once per turn"
        assert feature["weapon_restriction"] == "finesse or ranged weapon"

    def test_cunning_action_metadata(self):
        """Test Cunning Action feature metadata."""
        feature = self.manager.lookup_feature("Rogue", "Cunning Action")
        assert feature["usage"] == "bonus action"
        assert "Dash" in feature["options"]
        assert "Disengage" in feature["options"]
        assert "Hide" in feature["options"]

    def test_uncanny_dodge_metadata(self):
        """Test Uncanny Dodge feature metadata."""
        feature = self.manager.lookup_feature("Rogue", "Uncanny Dodge")
        assert feature["usage"] == "reaction"
        assert feature["effect"] == "halve damage"

    def test_evasion_metadata(self):
        """Test Evasion feature metadata."""
        feature = self.manager.lookup_feature("Rogue", "Evasion")
        assert feature["trigger"] == "Dexterity saving throw"


class TestFighterFeatures:
    """Detailed tests for Fighter features."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_second_wind_metadata(self):
        """Test Second Wind feature metadata."""
        feature = self.manager.lookup_feature("Fighter", "Second Wind")
        assert feature["usage"] == "bonus action"
        assert feature["uses"] == "1 per short or long rest"
        assert feature["healing"] == "1d10 + fighter_level"

    def test_action_surge_metadata(self):
        """Test Action Surge feature metadata."""
        feature = self.manager.lookup_feature("Fighter", "Action Surge")
        assert feature["usage"] == "once per turn"
        assert feature["recharge"] == "short or long rest"

    def test_fighting_style_options(self):
        """Test Fighting Style options."""
        feature = self.manager.lookup_feature("Fighter", "Fighting Style")
        assert "Archery" in feature["options"]
        assert "Defense" in feature["options"]
        assert "Dueling" in feature["options"]


class TestBarbarianFeatures:
    """Detailed tests for Barbarian features."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_rage_metadata(self):
        """Test Rage feature metadata."""
        feature = self.manager.lookup_feature("Barbarian", "Rage")
        assert feature["usage"] == "bonus action"
        assert feature["duration"] == "1 minute"
        assert len(feature["benefits"]) >= 3

    def test_rage_damage_bonus_scaling(self):
        """Test Rage damage bonus scaling."""
        feature = self.manager.lookup_feature("Barbarian", "Rage")
        assert feature["damage_bonus_by_level"][1] == 2
        assert feature["damage_bonus_by_level"][9] == 3
        assert feature["damage_bonus_by_level"][16] == 4

    def test_unarmored_defense_metadata(self):
        """Test Unarmored Defense metadata."""
        feature = self.manager.lookup_feature("Barbarian", "Unarmored Defense")
        assert feature["ac_formula"] == "10 + Dexterity_modifier + Constitution_modifier"

    def test_reckless_attack_metadata(self):
        """Test Reckless Attack metadata."""
        feature = self.manager.lookup_feature("Barbarian", "Reckless Attack")
        assert "advantage" in feature["benefit"].lower()
        assert "advantage" in feature["drawback"].lower()


class TestPaladinFeatures:
    """Detailed tests for Paladin features."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize manager for all tests."""
        self.manager = ClassFeatureManager()

    def test_lay_on_hands_metadata(self):
        """Test Lay on Hands metadata."""
        feature = self.manager.lookup_feature("Paladin", "Lay on Hands")
        assert feature["healing_pool"] == "paladin_level * 5"
        assert feature["recharge"] == "long rest"

    def test_divine_smite_metadata(self):
        """Test Divine Smite metadata."""
        feature = self.manager.lookup_feature("Paladin", "Divine Smite")
        assert feature["damage"] == "2d8 + 1d8 per spell level above 1st (max 5d8)"
        assert feature["extra_damage"] == "+1d8 vs undead/fiends"

    def test_divine_sense_metadata(self):
        """Test Divine Sense metadata."""
        feature = self.manager.lookup_feature("Paladin", "Divine Sense")
        assert feature["usage"] == "action"
        assert feature["range"] == "60 feet"


if __name__ == '__main__':
    # Run with: python -m pytest tests/test_class_feature_manager.py -v
    pytest.main([__file__, '-v', '--tb=short'])
