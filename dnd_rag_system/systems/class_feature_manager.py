"""
Class Feature Manager

Handles class feature lookups, level progression, and feature mechanics.
"""

from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.data.class_features import (
    get_class_data,
    get_class_features_at_level,
    get_all_class_features,
    get_available_classes,
    ClassData
)


class ClassFeatureManager:
    """Manages class features and level progression."""

    def __init__(self):
        """Initialize the class feature manager."""
        pass

    def get_class_info(self, class_name: str) -> Optional[ClassData]:
        """
        Get complete class information.

        Args:
            class_name: Name of the class

        Returns:
            Class data dictionary or None
        """
        return get_class_data(class_name)

    def get_features_at_level(self, class_name: str, level: int) -> List[Dict]:
        """
        Get features gained at a specific level.

        Args:
            class_name: Name of the class
            level: Character level

        Returns:
            List of features gained at that level
        """
        return get_class_features_at_level(class_name, level)

    def get_all_features(self, class_name: str, up_to_level: int = 20) -> Dict[int, List[Dict]]:
        """
        Get all features up to a certain level.

        Args:
            class_name: Name of the class
            up_to_level: Maximum level (default 20)

        Returns:
            Dictionary mapping level to features
        """
        return get_all_class_features(class_name, up_to_level)

    def get_available_classes(self) -> List[str]:
        """
        Get list of all available classes.

        Returns:
            List of class names
        """
        return get_available_classes()

    def lookup_feature(self, class_name: str, feature_name: str) -> Optional[Dict]:
        """
        Look up a specific feature by name.

        Args:
            class_name: Name of the class
            feature_name: Name of the feature to find

        Returns:
            Feature dictionary or None
        """
        all_features = get_all_class_features(class_name)

        for level, features in all_features.items():
            for feature in features:
                if feature["name"].lower() == feature_name.lower():
                    return {
                        "level": level,
                        **feature
                    }

        return None

    def calculate_feature_value(self, feature_name: str, level: int, class_name: str) -> Any:
        """
        Calculate the value of a feature at a specific level.

        Args:
            feature_name: Name of the feature
            level: Character level
            class_name: Name of the class

        Returns:
            Feature value (damage dice, uses, etc.)
        """
        feature = self.lookup_feature(class_name, feature_name)
        if not feature:
            return None

        # Sneak Attack damage scaling
        if feature_name.lower() == "sneak attack":
            damage_by_level = feature.get("damage_by_level", {})
            # Find the highest level <= current level
            applicable_levels = [lvl for lvl in damage_by_level.keys() if lvl <= level]
            if applicable_levels:
                highest_level = max(applicable_levels)
                return damage_by_level[highest_level]

        # Rage uses scaling
        elif feature_name.lower() == "rage":
            uses_by_level = feature.get("uses_by_level", {})
            applicable_levels = [lvl for lvl in uses_by_level.keys() if lvl <= level]
            if applicable_levels:
                highest_level = max(applicable_levels)
                return uses_by_level[highest_level]

        # Extra Attack scaling
        elif feature_name.lower() == "extra attack":
            attacks_by_level = feature.get("attacks_by_level", {})
            applicable_levels = [lvl for lvl in attacks_by_level.keys() if lvl <= level]
            if applicable_levels:
                highest_level = max(applicable_levels)
                return attacks_by_level[highest_level]

        # Channel Divinity uses
        elif feature_name.lower() == "channel divinity":
            uses_by_level = feature.get("uses_by_level", {})
            applicable_levels = [lvl for lvl in uses_by_level.keys() if lvl <= level]
            if applicable_levels:
                highest_level = max(applicable_levels)
                return uses_by_level[highest_level]

        # Action Surge uses
        elif feature_name.lower() == "action surge":
            uses_by_level = feature.get("uses_by_level", {})
            applicable_levels = [lvl for lvl in uses_by_level.keys() if lvl <= level]
            if applicable_levels:
                highest_level = max(applicable_levels)
                return uses_by_level[highest_level]

        # Rage damage bonus
        elif "damage_bonus_by_level" in feature:
            damage_bonus_by_level = feature.get("damage_bonus_by_level", {})
            applicable_levels = [lvl for lvl in damage_bonus_by_level.keys() if lvl <= level]
            if applicable_levels:
                highest_level = max(applicable_levels)
                return damage_bonus_by_level[highest_level]

        return None

    def get_spell_slots(self, class_name: str, level: int) -> Dict[str, int]:
        """
        Get spell slots for a spellcasting class at a specific level.

        Args:
            class_name: Name of the class
            level: Character level

        Returns:
            Dictionary of spell slots by level
        """
        class_data = get_class_data(class_name)
        if not class_data:
            return {}

        spell_slots_by_level = class_data.get("spell_slots_by_level", {})
        return spell_slots_by_level.get(level, {})

    def get_hit_die(self, class_name: str) -> str:
        """
        Get the hit die for a class.

        Args:
            class_name: Name of the class

        Returns:
            Hit die (e.g., "d8", "d10")
        """
        class_data = get_class_data(class_name)
        if class_data:
            return class_data.get("hit_dice", "d8")
        return "d8"

    def get_saving_throw_proficiencies(self, class_name: str) -> List[str]:
        """
        Get saving throw proficiencies for a class.

        Args:
            class_name: Name of the class

        Returns:
            List of ability names (e.g., ["strength", "constitution"])
        """
        class_data = get_class_data(class_name)
        if class_data:
            return class_data.get("saving_throw_proficiencies", [])
        return []

    def check_feature_prerequisites(self, class_name: str, feature_name: str, character_level: int) -> tuple[bool, str]:
        """
        Check if a character meets the prerequisites for a feature.

        Args:
            class_name: Name of the character's class
            feature_name: Name of the feature to check
            character_level: Current character level

        Returns:
            Tuple of (has_feature: bool, reason: str)
        """
        feature = self.lookup_feature(class_name, feature_name)

        if not feature:
            return False, f"Feature '{feature_name}' not found for {class_name}"

        required_level = feature.get("level")
        if character_level < required_level:
            return False, f"Requires level {required_level} (you are level {character_level})"

        return True, "OK"

    def get_feature_summary(self, class_name: str, up_to_level: int) -> str:
        """
        Get a text summary of all features up to a level.

        Args:
            class_name: Name of the class
            up_to_level: Maximum level

        Returns:
            Formatted text summary
        """
        all_features = get_all_class_features(class_name, up_to_level)

        lines = [f"**{class_name} Features (Levels 1-{up_to_level})**\n"]

        for level in sorted(all_features.keys()):
            features = all_features[level]
            if features:
                lines.append(f"\n**Level {level}:**")
                for feature in features:
                    lines.append(f"  • {feature['name']}")
                    if "description" in feature:
                        desc = feature["description"]
                        if len(desc) > 100:
                            desc = desc[:100] + "..."
                        lines.append(f"    {desc}")

        return "\n".join(lines)


# Convenience function
def lookup_class_feature(class_name: str, feature_name: str) -> Optional[Dict]:
    """
    Quick lookup for a class feature.

    Args:
        class_name: Name of the class
        feature_name: Name of the feature

    Returns:
        Feature dictionary or None
    """
    manager = ClassFeatureManager()
    return manager.lookup_feature(class_name, feature_name)


if __name__ == "__main__":
    # Quick test
    manager = ClassFeatureManager()

    print("📖 Class Feature Manager Test\n")

    # Test class info
    rogue_info = manager.get_class_info("Rogue")
    print(f"Rogue Hit Die: {rogue_info['hit_dice']}")
    print(f"Rogue Saves: {', '.join(rogue_info['saving_throw_proficiencies'])}")

    # Test feature lookup
    print("\n🗡️  Sneak Attack:")
    sneak_attack = manager.lookup_feature("Rogue", "Sneak Attack")
    print(f"  Level gained: {sneak_attack['level']}")
    print(f"  Frequency: {sneak_attack['frequency']}")

    # Test damage scaling
    print("\n📈 Sneak Attack damage by level:")
    for level in [1, 5, 10, 15, 20]:
        damage = manager.calculate_feature_value("Sneak Attack", level, "Rogue")
        print(f"  Level {level}: {damage}")

    # Test Fighter features
    print("\n⚔️  Fighter Level 2:")
    fighter_lvl2 = manager.get_features_at_level("Fighter", 2)
    for feature in fighter_lvl2:
        print(f"  • {feature['name']}")

    # Test Action Surge uses
    print("\n🔥 Action Surge uses by level:")
    for level in [2, 10, 17, 20]:
        uses = manager.calculate_feature_value("Action Surge", level, "Fighter")
        print(f"  Level {level}: {uses} use(s)")

    # Test spell slots
    print("\n✨ Wizard Spell Slots at Level 5:")
    slots = manager.get_spell_slots("Wizard", 5)
    for slot_level, count in slots.items():
        print(f"  {slot_level}: {count} slots")

    # Test prerequisites
    print("\n✅ Feature Prerequisites:")
    has_feature, reason = manager.check_feature_prerequisites("Rogue", "Uncanny Dodge", 5)
    print(f"  Rogue level 5 has Uncanny Dodge: {has_feature} ({reason})")

    has_feature, reason = manager.check_feature_prerequisites("Rogue", "Uncanny Dodge", 3)
    print(f"  Rogue level 3 has Uncanny Dodge: {has_feature} ({reason})")
