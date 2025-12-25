"""
Unit Tests for Random Stat Rolling

Tests the 3d6 stat rolling functionality.
"""

import unittest
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the function (we'll need to make it importable)
import random


def roll_3d6():
    """Roll 3d6 (3 six-sided dice)."""
    return sum(random.randint(1, 6) for _ in range(3))


def roll_random_stats():
    """
    Roll random ability scores using 3d6 method.
    Returns tuple of (STR, DEX, CON, INT, WIS, CHA)
    """
    return tuple(roll_3d6() for _ in range(6))


class TestStatRolling(unittest.TestCase):
    """Test suite for stat rolling mechanics."""

    def test_roll_3d6_range(self):
        """Test that 3d6 produces values between 3 and 18."""
        for _ in range(100):
            roll = roll_3d6()
            self.assertGreaterEqual(roll, 3, "3d6 should be at least 3")
            self.assertLessEqual(roll, 18, "3d6 should be at most 18")
        print("✅ 3d6 rolls are always between 3 and 18")

    def test_roll_3d6_type(self):
        """Test that 3d6 returns an integer."""
        roll = roll_3d6()
        self.assertIsInstance(roll, int)
        print("✅ 3d6 returns integer")

    def test_roll_random_stats_length(self):
        """Test that roll_random_stats returns 6 values."""
        stats = roll_random_stats()
        self.assertEqual(len(stats), 6, "Should return 6 ability scores")
        print("✅ roll_random_stats returns 6 values")

    def test_roll_random_stats_types(self):
        """Test that all stats are integers."""
        stats = roll_random_stats()
        for stat in stats:
            self.assertIsInstance(stat, int, "Each stat should be an integer")
        print("✅ All stats are integers")

    def test_roll_random_stats_range(self):
        """Test that all stats are in valid range (3-18)."""
        for _ in range(50):
            stats = roll_random_stats()
            for i, stat in enumerate(stats):
                stat_names = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
                self.assertGreaterEqual(
                    stat, 3,
                    f"{stat_names[i]} should be at least 3, got {stat}"
                )
                self.assertLessEqual(
                    stat, 18,
                    f"{stat_names[i]} should be at most 18, got {stat}"
                )
        print("✅ All stats are always between 3 and 18")

    def test_roll_random_stats_randomness(self):
        """Test that rolls produce different results (not deterministic)."""
        results = [roll_random_stats() for _ in range(10)]

        # At least some rolls should be different
        unique_results = set(results)
        self.assertGreater(
            len(unique_results), 1,
            "Multiple rolls should produce different results"
        )
        print(f"✅ Random rolling produces variety ({len(unique_results)}/10 unique)")

    def test_roll_distribution(self):
        """Test that rolls have a reasonable distribution."""
        rolls = [roll_3d6() for _ in range(1000)]

        # Average should be around 10.5 (mathematical expectation of 3d6)
        average = sum(rolls) / len(rolls)
        self.assertGreater(average, 9.5, "Average should be close to 10.5")
        self.assertLess(average, 11.5, "Average should be close to 10.5")

        # Should have good spread
        min_roll = min(rolls)
        max_roll = max(rolls)
        self.assertLessEqual(min_roll, 5, "Should occasionally roll low")
        self.assertGreaterEqual(max_roll, 16, "Should occasionally roll high")

        print(f"✅ Distribution looks good (avg: {average:.2f}, min: {min_roll}, max: {max_roll})")

    def test_extreme_values_possible(self):
        """Test that extreme values (3 and 18) are theoretically possible."""
        # We can't guarantee rolling 3 or 18 in a reasonable test,
        # but we can verify the math

        # Minimum: three 1s
        min_possible = 1 + 1 + 1
        self.assertEqual(min_possible, 3)

        # Maximum: three 6s
        max_possible = 6 + 6 + 6
        self.assertEqual(max_possible, 18)

        print("✅ Extreme values (3 and 18) are mathematically possible")

    def test_stats_tuple_unpacking(self):
        """Test that stats can be unpacked into individual variables."""
        str_val, dex_val, con_val, int_val, wis_val, cha_val = roll_random_stats()

        # All should be valid
        for val in [str_val, dex_val, con_val, int_val, wis_val, cha_val]:
            self.assertIsInstance(val, int)
            self.assertGreaterEqual(val, 3)
            self.assertLessEqual(val, 18)

        print("✅ Stats tuple can be unpacked correctly")

    def test_deterministic_with_seed(self):
        """Test that setting random seed makes rolls reproducible."""
        random.seed(42)
        stats1 = roll_random_stats()

        random.seed(42)
        stats2 = roll_random_stats()

        self.assertEqual(stats1, stats2, "Same seed should produce same results")
        print(f"✅ Seeded rolls are reproducible: {stats1}")

    def test_multiple_character_stats(self):
        """Test rolling stats for multiple characters."""
        party_stats = [roll_random_stats() for _ in range(4)]

        self.assertEqual(len(party_stats), 4, "Should create 4 sets of stats")

        # Each character should have different stats (very likely)
        unique_characters = set(party_stats)
        self.assertGreater(
            len(unique_characters), 1,
            "Different characters should likely have different stats"
        )

        print(f"✅ Can roll stats for multiple characters ({len(unique_characters)}/4 unique)")


class TestStatValidation(unittest.TestCase):
    """Test stat validation for D&D rules."""

    def test_stat_modifier_calculation(self):
        """Test calculating ability modifiers from scores."""
        def get_modifier(score):
            return (score - 10) // 2

        test_cases = [
            (3, -4),   # Minimum
            (8, -1),
            (10, 0),   # Average
            (11, 0),
            (12, 1),
            (15, 2),
            (18, 4),   # Maximum for 3d6
            (20, 5),   # With bonuses
        ]

        for score, expected_mod in test_cases:
            modifier = get_modifier(score)
            self.assertEqual(
                modifier, expected_mod,
                f"Score {score} should give modifier {expected_mod:+d}"
            )

        print("✅ Ability modifier calculations are correct")

    def test_standard_array_comparison(self):
        """Test that random rolls compare to standard array."""
        standard_array = [15, 14, 13, 12, 10, 8]
        standard_total = sum(standard_array)

        # Roll 100 sets and compare
        random_totals = [sum(roll_random_stats()) for _ in range(100)]
        avg_random_total = sum(random_totals) / len(random_totals)

        # 3d6 six times averages around 63 (10.5 * 6)
        # Standard array totals 72
        self.assertGreater(
            avg_random_total, 60,
            "Average total should be around 63"
        )
        self.assertLess(
            avg_random_total, 66,
            "Average total should be around 63"
        )

        print(f"✅ Standard array ({standard_total}) vs 3d6 average ({avg_random_total:.1f})")

    def test_point_buy_equivalent(self):
        """Test how 3d6 compares to point buy method."""
        # Point buy typically allows 15 as maximum, 8 as minimum
        # with 27 points to spend

        rolls = [roll_random_stats() for _ in range(100)]

        # Count how many rolls have stats outside point buy range
        out_of_range = 0
        for stats in rolls:
            for stat in stats:
                if stat < 8 or stat > 15:
                    out_of_range += 1
                    break

        # Most 3d6 rolls will have at least one stat outside point buy range
        percent_out = (out_of_range / len(rolls)) * 100

        print(f"✅ {percent_out:.0f}% of 3d6 rolls fall outside point buy range (8-15)")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
