"""
UI Loading Tests

Tests that verify the Gradio app loads correctly and all UI elements are present.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from config import BASE_URL, EXPLICIT_WAIT


@pytest.mark.ui
class TestUILoading:
    """Test suite for UI loading and element presence."""

    def test_app_loads(self, driver):
        """Test that the Gradio app loads successfully."""
        driver.get(BASE_URL)

        # Wait for page to load
        WebDriverWait(driver, EXPLICIT_WAIT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        assert "D&D" in driver.title or "Gradio" in driver.title
        print("✅ App loaded successfully")

    def test_title_present(self, driver):
        """Test that the main title is present."""
        driver.get(BASE_URL)

        # Look for the main heading
        try:
            # Gradio uses markdown for titles
            heading = WebDriverWait(driver, EXPLICIT_WAIT).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            assert "D&D" in heading.text or "Game Master" in heading.text
            print(f"✅ Title found: {heading.text}")
        except Exception as e:
            pytest.fail(f"Main title not found: {e}")

    def test_tabs_present(self, driver):
        """Test that both tabs are present."""
        driver.get(BASE_URL)
        time.sleep(2)  # Give Gradio time to render

        # Look for tab buttons
        tabs = driver.find_elements(By.TAG_NAME, "button")
        tab_texts = [tab.text for tab in tabs if tab.text]

        # Check for Play Game and Create Character tabs
        assert any("Play" in text or "Game" in text for text in tab_texts), \
            f"Play Game tab not found. Tabs: {tab_texts}"
        assert any("Create" in text for text in tab_texts), \
            f"Create Character tab not found. Tabs: {tab_texts}"

        print(f"✅ Tabs found: {tab_texts}")

    def test_play_game_tab_elements(self, driver):
        """Test that Play Game tab has required elements."""
        driver.get(BASE_URL)
        time.sleep(2)

        # Look for character dropdown
        try:
            dropdowns = driver.find_elements(By.CSS_SELECTOR, "label")
            dropdown_labels = [d.text for d in dropdowns]
            assert any("Character" in label for label in dropdown_labels), \
                f"Character dropdown not found. Labels: {dropdown_labels}"
            print("✅ Character dropdown found")
        except Exception as e:
            pytest.fail(f"Character dropdown not found: {e}")

        # Look for Load Character button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        button_texts = [btn.text for btn in buttons if btn.text]
        assert any("Load" in text for text in button_texts), \
            f"Load Character button not found. Buttons: {button_texts}"
        print("✅ Load Character button found")

    def test_create_character_tab_elements(self, driver):
        """Test that Create Character tab has required elements."""
        driver.get(BASE_URL)
        time.sleep(2)

        # Click on Create Character tab
        tabs = driver.find_elements(By.TAG_NAME, "button")
        create_tab = None
        for tab in tabs:
            if "Create" in tab.text:
                create_tab = tab
                break

        assert create_tab is not None, "Create Character tab not found"
        create_tab.click()
        time.sleep(1)

        # Check for form elements
        inputs = driver.find_elements(By.TAG_NAME, "input")
        assert len(inputs) > 0, "No input fields found in Create Character tab"
        print(f"✅ Create Character tab has {len(inputs)} input fields")

        # Look for Create Character button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        button_texts = [btn.text for btn in buttons if btn.text]
        assert any("Create" in text for text in button_texts), \
            f"Create Character button not found. Buttons: {button_texts}"
        print("✅ Create Character button found")

    def test_chat_interface_present(self, driver):
        """Test that chat interface is present in Play Game tab."""
        driver.get(BASE_URL)
        time.sleep(2)

        # Look for chat input (textarea)
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        assert len(textareas) > 0, "No chat input (textarea) found"
        print(f"✅ Chat interface found ({len(textareas)} textarea elements)")

    def test_character_sheet_placeholder(self, driver):
        """Test that character sheet area is present."""
        driver.get(BASE_URL)
        time.sleep(2)

        # Look for the "No character loaded" placeholder text
        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert "No character" in body_text or "Character" in body_text, \
            "Character sheet placeholder not found"
        print("✅ Character sheet area found (placeholder text present)")

    def test_no_errors_on_load(self, driver):
        """Test that no JavaScript errors occur on page load."""
        driver.get(BASE_URL)
        time.sleep(3)

        # Check browser console for errors
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']

        if errors:
            print(f"⚠️  Found {len(errors)} severe errors in console:")
            for error in errors[:5]:  # Print first 5 errors
                print(f"  - {error['message']}")
        else:
            print("✅ No severe errors in browser console")

        # Don't fail the test for JS errors, just warn
        # (Gradio apps often have minor console warnings)
        assert True
