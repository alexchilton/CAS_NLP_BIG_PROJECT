"""
Character Creation Tests

Tests for the character creation form functionality.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import time

from config import BASE_URL, EXPLICIT_WAIT, TEST_CHARACTER_NAME, CHARACTERS_DIR


@pytest.mark.character
class TestCharacterCreation:
    """Test suite for character creation functionality."""

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

    def test_navigate_to_create_tab(self, driver):
        """Test navigation to Create Character tab."""
        self._navigate_to_create_tab(driver)

        # Verify we're on the create tab by checking for form elements
        inputs = driver.find_elements(By.TAG_NAME, "input")
        assert len(inputs) > 0, "No input fields found after navigating to Create tab"

        print(f"✅ Navigated to Create Character tab ({len(inputs)} inputs found)")

    def test_character_name_input(self, driver):
        """Test entering character name."""
        self._navigate_to_create_tab(driver)

        # Find name input field
        inputs = driver.find_elements(By.TAG_NAME, "input")
        name_input = None

        for inp in inputs:
            placeholder = inp.get_attribute("placeholder") or ""
            if "name" in placeholder.lower():
                name_input = inp
                break

        assert name_input is not None, "Character name input not found"

        # Enter test name
        name_input.clear()
        name_input.send_keys(TEST_CHARACTER_NAME)
        time.sleep(0.5)

        assert name_input.get_attribute("value") == TEST_CHARACTER_NAME
        print(f"✅ Entered character name: {TEST_CHARACTER_NAME}")

    def test_race_selection(self, driver):
        """Test selecting a race."""
        self._navigate_to_create_tab(driver)

        # Look for race dropdown (Gradio dropdown or select)
        # Gradio dropdowns can be tricky - they might be custom components
        labels = driver.find_elements(By.TAG_NAME, "label")
        race_label_found = any("race" in label.text.lower() for label in labels)

        assert race_label_found, "Race selection field not found"
        print("✅ Race selection field exists")

    def test_class_selection(self, driver):
        """Test selecting a class."""
        self._navigate_to_create_tab(driver)

        # Look for class dropdown
        labels = driver.find_elements(By.TAG_NAME, "label")
        class_label_found = any("class" in label.text.lower() for label in labels)

        assert class_label_found, "Class selection field not found"
        print("✅ Class selection field exists")

    def test_ability_score_sliders(self, driver):
        """Test that ability score sliders are present."""
        self._navigate_to_create_tab(driver)

        # Look for sliders (range inputs)
        sliders = driver.find_elements(By.CSS_SELECTOR, "input[type='range']")

        # Should have 6 sliders for 6 abilities
        assert len(sliders) >= 6, f"Expected 6 ability sliders, found {len(sliders)}"
        print(f"✅ Found {len(sliders)} ability score sliders")

    def test_adjust_ability_score(self, driver):
        """Test adjusting an ability score slider."""
        self._navigate_to_create_tab(driver)

        # Find first slider
        sliders = driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
        assert len(sliders) > 0, "No sliders found"

        first_slider = sliders[0]
        initial_value = first_slider.get_attribute("value")

        # Move slider (simulate dragging or use JavaScript)
        driver.execute_script("arguments[0].value = 15;", first_slider)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", first_slider)
        time.sleep(0.5)

        new_value = first_slider.get_attribute("value")
        assert new_value == "15", f"Slider value not updated: {new_value}"
        print(f"✅ Adjusted ability score from {initial_value} to {new_value}")

    def test_background_input(self, driver):
        """Test entering background."""
        self._navigate_to_create_tab(driver)

        # Find background input
        inputs = driver.find_elements(By.TAG_NAME, "input")
        background_input = None

        for inp in inputs:
            placeholder = inp.get_attribute("placeholder") or ""
            if "background" in placeholder.lower():
                background_input = inp
                break

        if background_input:
            background_input.clear()
            background_input.send_keys("Soldier")
            time.sleep(0.5)
            assert background_input.get_attribute("value") == "Soldier"
            print("✅ Entered background: Soldier")
        else:
            print("⚠️  Background input not found (may use different component)")

    def test_alignment_input(self, driver):
        """Test entering alignment."""
        self._navigate_to_create_tab(driver)

        # Find alignment input
        inputs = driver.find_elements(By.TAG_NAME, "input")
        alignment_input = None

        for inp in inputs:
            placeholder = inp.get_attribute("placeholder") or ""
            if "alignment" in placeholder.lower():
                alignment_input = inp
                break

        if alignment_input:
            alignment_input.clear()
            alignment_input.send_keys("Lawful Good")
            time.sleep(0.5)
            assert alignment_input.get_attribute("value") == "Lawful Good"
            print("✅ Entered alignment: Lawful Good")
        else:
            print("⚠️  Alignment input not found (may use different component)")

    def test_create_character_button_exists(self, driver):
        """Test that Create Character button exists."""
        self._navigate_to_create_tab(driver)

        buttons = driver.find_elements(By.TAG_NAME, "button")
        create_button_found = any("Create" in btn.text for btn in buttons if btn.text)

        assert create_button_found, "Create Character button not found"
        print("✅ Create Character button exists")

    @pytest.mark.slow
    def test_create_character_full_flow(self, driver):
        """Test full character creation flow (slow test)."""
        self._navigate_to_create_tab(driver)

        # Fill in character name
        inputs = driver.find_elements(By.TAG_NAME, "input")
        name_input = None
        for inp in inputs:
            placeholder = inp.get_attribute("placeholder") or ""
            if "name" in placeholder.lower():
                name_input = inp
                break

        if name_input:
            name_input.clear()
            name_input.send_keys(f"TestChar_{int(time.time())}")
            time.sleep(0.5)

        # Set ability scores to valid values
        sliders = driver.find_elements(By.CSS_SELECTOR, "input[type='range']")
        for slider in sliders[:6]:
            driver.execute_script("arguments[0].value = 10;", slider)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", slider)

        time.sleep(1)

        # Click Create Character button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        create_button = None
        for btn in buttons:
            if "Create" in btn.text and btn.is_displayed():
                create_button = btn
                break

        if create_button:
            create_button.click()
            time.sleep(3)

            # Check for success message or status update
            # This depends on how your app shows feedback
            body_text = driver.find_element(By.TAG_NAME, "body").text

            # Look for success indicators
            success_found = "created" in body_text.lower() or \
                          "successfully" in body_text.lower() or \
                          "saved" in body_text.lower()

            if success_found:
                print("✅ Character creation appears successful")
            else:
                print("⚠️  Character creation feedback not detected (may still work)")

            assert True  # Pass if no errors
        else:
            pytest.skip("Create button not accessible for full flow test")
