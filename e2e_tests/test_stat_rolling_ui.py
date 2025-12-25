"""
E2E Tests for Random Stat Rolling UI

Tests the "Roll Random Stats" button in the character creation interface.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from config import BASE_URL, EXPLICIT_WAIT


@pytest.mark.character
class TestStatRollingUI:
    """Test suite for stat rolling UI functionality."""

    def _navigate_to_create_tab(self, driver):
        """Helper to navigate to Create Character tab."""
        driver.get(BASE_URL)
        time.sleep(2)

        # Find and click Create Character tab
        tabs = driver.find_elements(By.TAG_NAME, "button")
        create_tab = None
        for tab in tabs:
            if "Create" in tab.text:
                create_tab = tab
                break

        assert create_tab is not None, "Create Character tab not found"
        create_tab.click()
        time.sleep(1)

    def _get_slider_value(self, driver, label_text):
        """Get the value of a slider by its label."""
        labels = driver.find_elements(By.TAG_NAME, "label")
        for label in labels:
            if label_text in label.text:
                # Find associated input (slider)
                parent = label.find_element(By.XPATH, "..")
                sliders = parent.find_elements(By.CSS_SELECTOR, "input[type='range']")
                if sliders:
                    return int(sliders[0].get_attribute("value"))
        return None

    def _get_all_stat_values(self, driver):
        """Get all six ability score values."""
        stats = {}
        stat_names = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]

        sliders = driver.find_elements(By.CSS_SELECTOR, "input[type='range']")

        # Get first 6 sliders (ability scores)
        for i, stat_name in enumerate(stat_names):
            if i < len(sliders):
                value = int(sliders[i].get_attribute("value"))
                stats[stat_name] = value

        return stats

    def test_roll_stats_button_exists(self, driver):
        """Test that Roll Random Stats button exists."""
        self._navigate_to_create_tab(driver)

        buttons = driver.find_elements(By.TAG_NAME, "button")
        button_texts = [btn.text for btn in buttons if btn.text]

        roll_button_found = any("Roll" in text and "Random" in text for text in button_texts)

        assert roll_button_found, f"Roll Random Stats button not found. Buttons: {button_texts}"
        print("✅ Roll Random Stats button exists")

    def test_roll_stats_button_clickable(self, driver):
        """Test that Roll Random Stats button is clickable."""
        self._navigate_to_create_tab(driver)

        buttons = driver.find_elements(By.TAG_NAME, "button")
        roll_button = None
        for btn in buttons:
            if "Roll" in btn.text and "Random" in btn.text:
                roll_button = btn
                break

        assert roll_button is not None, "Roll button not found"
        assert roll_button.is_displayed(), "Roll button not visible"
        assert roll_button.is_enabled(), "Roll button not enabled"

        print("✅ Roll Random Stats button is clickable")

    def test_initial_slider_values(self, driver):
        """Test that sliders start at default value (10)."""
        self._navigate_to_create_tab(driver)

        stats = self._get_all_stat_values(driver)

        # All should start at 10
        for stat_name, value in stats.items():
            assert value == 10, f"{stat_name} should start at 10, got {value}"

        print("✅ All sliders start at default value (10)")

    def test_slider_range(self, driver):
        """Test that sliders have correct range (3-18)."""
        self._navigate_to_create_tab(driver)

        sliders = driver.find_elements(By.CSS_SELECTOR, "input[type='range']")

        # Check first 6 sliders (ability scores)
        for i in range(min(6, len(sliders))):
            slider = sliders[i]
            min_val = int(slider.get_attribute("min"))
            max_val = int(slider.get_attribute("max"))

            assert min_val == 3, f"Slider {i} should have min=3, got {min_val}"
            assert max_val == 18, f"Slider {i} should have max=18, got {max_val}"

        print("✅ All sliders have correct range (3-18)")

    def test_roll_stats_changes_values(self, driver):
        """Test that clicking Roll button changes slider values."""
        self._navigate_to_create_tab(driver)

        # Get initial values
        stats_before = self._get_all_stat_values(driver)

        # Find and click Roll button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        roll_button = None
        for btn in buttons:
            if "Roll" in btn.text and "Random" in btn.text:
                roll_button = btn
                break

        assert roll_button is not None
        roll_button.click()
        time.sleep(1)  # Wait for update

        # Get new values
        stats_after = self._get_all_stat_values(driver)

        # At least some values should have changed
        changes = sum(1 for stat in stats_before if stats_before[stat] != stats_after.get(stat, stats_before[stat]))

        assert changes > 0, f"At least some stats should change after rolling. Before: {stats_before}, After: {stats_after}"

        print(f"✅ Roll button changed {changes}/6 stats")
        print(f"   Before: {stats_before}")
        print(f"   After: {stats_after}")

    def test_rolled_values_in_range(self, driver):
        """Test that rolled values are within valid range (3-18)."""
        self._navigate_to_create_tab(driver)

        # Click Roll button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Roll" in btn.text and "Random" in btn.text:
                btn.click()
                break

        time.sleep(1)

        # Check all values
        stats = self._get_all_stat_values(driver)

        for stat_name, value in stats.items():
            assert 3 <= value <= 18, f"{stat_name} should be 3-18, got {value}"

        print("✅ All rolled values are in valid range (3-18)")
        print(f"   Rolled: {stats}")

    def test_multiple_rolls_produce_different_values(self, driver):
        """Test that rolling multiple times produces different results."""
        self._navigate_to_create_tab(driver)

        # Find Roll button once
        buttons = driver.find_elements(By.TAG_NAME, "button")
        roll_button = None
        for btn in buttons:
            if "Roll" in btn.text and "Random" in btn.text:
                roll_button = btn
                break

        assert roll_button is not None

        # Roll 5 times and collect results
        all_rolls = []
        for i in range(5):
            roll_button.click()
            time.sleep(1)
            stats = self._get_all_stat_values(driver)
            stats_tuple = tuple(stats.values())
            all_rolls.append(stats_tuple)

        # At least some rolls should be different
        unique_rolls = set(all_rolls)
        assert len(unique_rolls) > 1, f"Multiple rolls should produce different results. Got: {all_rolls}"

        print(f"✅ Multiple rolls produce variety ({len(unique_rolls)}/5 unique)")
        for i, roll in enumerate(all_rolls, 1):
            print(f"   Roll {i}: STR={roll[0]}, DEX={roll[1]}, CON={roll[2]}, INT={roll[3]}, WIS={roll[4]}, CHA={roll[5]}")

    def test_manual_override_after_roll(self, driver):
        """Test that manual slider adjustment works after rolling."""
        self._navigate_to_create_tab(driver)

        # Roll stats
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Roll" in btn.text and "Random" in btn.text:
                btn.click()
                break

        time.sleep(1)

        # Manually adjust first slider (Strength)
        sliders = driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
        if sliders:
            first_slider = sliders[0]
            driver.execute_script("arguments[0].value = 15;", first_slider)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", first_slider)
            time.sleep(0.5)

            new_value = int(first_slider.get_attribute("value"))
            assert new_value == 15, f"Manual adjustment should work, got {new_value}"

            print("✅ Can manually adjust sliders after rolling")

    def test_roll_button_styling(self, driver):
        """Test that Roll button has dice emoji."""
        self._navigate_to_create_tab(driver)

        buttons = driver.find_elements(By.TAG_NAME, "button")
        roll_button_text = None
        for btn in buttons:
            if "Roll" in btn.text and "Random" in btn.text:
                roll_button_text = btn.text
                break

        assert roll_button_text is not None
        assert "🎲" in roll_button_text, f"Roll button should have dice emoji. Got: '{roll_button_text}'"

        print(f"✅ Roll button has proper styling: '{roll_button_text}'")

    def test_roll_with_character_creation_flow(self, driver):
        """Test rolling stats as part of full character creation."""
        self._navigate_to_create_tab(driver)

        # Enter character name
        inputs = driver.find_elements(By.TAG_NAME, "input")
        name_input = None
        for inp in inputs:
            placeholder = inp.get_attribute("placeholder") or ""
            if "name" in placeholder.lower():
                name_input = inp
                break

        if name_input:
            name_input.clear()
            name_input.send_keys("Test Roller")
            time.sleep(0.5)

        # Roll stats
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Roll" in btn.text and "Random" in btn.text:
                btn.click()
                break

        time.sleep(1)

        # Get rolled stats
        stats = self._get_all_stat_values(driver)

        # Verify character can be created with rolled stats
        # (We won't actually click Create to avoid cluttering the character list)
        assert all(3 <= v <= 18 for v in stats.values()), "All rolled stats should be valid"

        print("✅ Rolled stats work in full character creation flow")
        print(f"   Character 'Test Roller' would have: {stats}")

    @pytest.mark.slow
    def test_stress_test_multiple_rapid_rolls(self, driver):
        """Stress test: Click roll button rapidly multiple times."""
        self._navigate_to_create_tab(driver)

        # Find Roll button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        roll_button = None
        for btn in buttons:
            if "Roll" in btn.text and "Random" in btn.text:
                roll_button = btn
                break

        assert roll_button is not None

        # Click rapidly 10 times
        for i in range(10):
            roll_button.click()
            time.sleep(0.2)  # Brief pause

        time.sleep(1)  # Final wait

        # Check that values are still valid
        stats = self._get_all_stat_values(driver)

        for stat_name, value in stats.items():
            assert 3 <= value <= 18, f"{stat_name} should still be valid after rapid rolls, got {value}"

        print("✅ Rapid clicking doesn't break the interface")
        print(f"   Final values: {stats}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
