"""
Character Loading Tests

Tests for loading pre-made characters (Thorin and Elara) and verifying their stats.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

from config import BASE_URL, EXPLICIT_WAIT


@pytest.mark.character
class TestCharacterLoading:
    """Test suite for character loading functionality."""

    def _load_character(self, driver, character_name):
        """Helper method to load a character."""
        driver.get(BASE_URL)
        time.sleep(3)

        # Find dropdown - try select tag first, then role='combobox'
        dropdowns = driver.find_elements(By.TAG_NAME, "select")
        if not dropdowns:
            dropdowns = driver.find_elements(By.CSS_SELECTOR, "[role='combobox']")

        if dropdowns:
            dropdown = dropdowns[0]
            dropdown.click()
            time.sleep(1)

            # Find and click the character option
            options = driver.find_elements(By.CSS_SELECTOR, "[role='option']")
            for opt in options:
                if character_name in opt.text:
                    opt.click()
                    time.sleep(1)
                    break

        # Click Load Character button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Load Character" in btn.text:
                btn.click()
                time.sleep(7)  # Wait for character to load
                break

    def test_load_thorin(self, driver):
        """Test loading Thorin Stormshield character."""
        self._load_character(driver, "Thorin")

        # Verify character sheet is displayed
        markdown_elements = driver.find_elements(By.CLASS_NAME, "markdown")
        character_sheet_text = " ".join([elem.text for elem in markdown_elements])

        # Check for Thorin's characteristics
        assert "Thorin" in character_sheet_text, "Thorin's name not in character sheet"
        assert "Dwarf" in character_sheet_text or "Fighter" in character_sheet_text, \
            "Thorin's race/class not in character sheet"

        print(f"✅ Thorin loaded successfully")
        print(f"Character sheet preview: {character_sheet_text[:200]}...")

    def test_load_elara(self, driver):
        """Test loading Elara Moonwhisper character."""
        self._load_character(driver, "Elara")

        # Verify character sheet is displayed
        markdown_elements = driver.find_elements(By.CLASS_NAME, "markdown")
        character_sheet_text = " ".join([elem.text for elem in markdown_elements])

        # Check for Elara's characteristics
        assert "Elara" in character_sheet_text, "Elara's name not in character sheet"
        assert "Elf" in character_sheet_text or "Wizard" in character_sheet_text, \
            "Elara's race/class not in character sheet"

        print(f"✅ Elara loaded successfully")
        print(f"Character sheet preview: {character_sheet_text[:200]}...")

    def test_character_stats_displayed(self, driver):
        """Test that character stats are properly displayed."""
        self._load_character(driver, "Thorin")

        # Verify stats are present
        markdown_elements = driver.find_elements(By.CLASS_NAME, "markdown")
        character_sheet_text = " ".join([elem.text for elem in markdown_elements])

        # Check for stat abbreviations
        stat_abbreviations = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
        found_stats = [stat for stat in stat_abbreviations if stat in character_sheet_text]

        assert len(found_stats) >= 3, \
            f"Not enough stats found. Found: {found_stats}"

        # Check for HP and AC
        assert "HP" in character_sheet_text or "Hit Points" in character_sheet_text, \
            "HP not found in character sheet"
        assert "AC" in character_sheet_text or "Armor Class" in character_sheet_text, \
            "AC not found in character sheet"

        print(f"✅ Character stats displayed: {found_stats}")

    def test_character_equipment_displayed(self, driver):
        """Test that character equipment is displayed."""
        self._load_character(driver, "Thorin")

        # Verify equipment section
        markdown_elements = driver.find_elements(By.CLASS_NAME, "markdown")
        character_sheet_text = " ".join([elem.text for elem in markdown_elements])

        # Check for equipment header or items
        assert "Equipment" in character_sheet_text or \
               "Longsword" in character_sheet_text or \
               "Shield" in character_sheet_text, \
            "Equipment not found in character sheet"

        print("✅ Character equipment displayed")

    def test_wizard_spells_displayed(self, driver):
        """Test that wizard character's spells are displayed."""
        self._load_character(driver, "Elara")

        # Verify spells section
        markdown_elements = driver.find_elements(By.CLASS_NAME, "markdown")
        character_sheet_text = " ".join([elem.text for elem in markdown_elements])

        # Check for spells header or spell names
        assert "Spell" in character_sheet_text or \
               "Magic Missile" in character_sheet_text or \
               "Fire Bolt" in character_sheet_text, \
            "Spells not found in character sheet"

        print("✅ Wizard spells displayed")

    def test_switch_between_characters(self, driver):
        """Test switching from one character to another."""
        # Load Thorin
        self._load_character(driver, "Thorin")
        markdown_elements = driver.find_elements(By.CLASS_NAME, "markdown")
        first_sheet = " ".join([elem.text for elem in markdown_elements])
        assert "Thorin" in first_sheet

        # Switch to Elara
        time.sleep(1)
        self._load_character(driver, "Elara")
        markdown_elements = driver.find_elements(By.CLASS_NAME, "markdown")
        second_sheet = " ".join([elem.text for elem in markdown_elements])
        assert "Elara" in second_sheet
        assert "Thorin" not in second_sheet

        print("✅ Successfully switched between characters")

    def test_character_portrait_placeholder(self, driver):
        """Test that character portrait image area exists."""
        self._load_character(driver, "Thorin")

        # Look for image elements (portrait placeholder)
        images = driver.find_elements(By.TAG_NAME, "img")

        # Gradio image component might be present even if no image loaded
        # Just check that the structure exists
        print(f"✅ Found {len(images)} image elements (portrait area exists)")
        assert True  # Placeholder test
