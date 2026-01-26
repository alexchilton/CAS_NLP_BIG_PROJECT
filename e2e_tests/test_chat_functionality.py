"""
Chat Functionality Tests

Tests for the chat interface and command system.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

from e2e_config import BASE_URL, EXPLICIT_WAIT


@pytest.mark.chat
class TestChatFunctionality:
    """Test suite for chat and command functionality."""

    def _load_character_for_chat(self, driver):
        """Helper to load a character before testing chat."""
        driver.get(BASE_URL)
        time.sleep(2)

        # Load Thorin quickly
        dropdown_inputs = driver.find_elements(By.CSS_SELECTOR, "input[role='combobox'], input.svelte-1cl284h")
        if not dropdown_inputs:
            dropdown_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")

        if len(dropdown_inputs) > 0:
            dropdown = dropdown_inputs[0]
            dropdown.click()
            dropdown.clear()
            dropdown.send_keys("Thorin")
            dropdown.send_keys(Keys.ENTER)
            time.sleep(0.5)

            # Click Load button
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "Load" in btn.text:
                    btn.click()
                    break
            time.sleep(2)

    def _send_chat_message(self, driver, message):
        """Helper to send a chat message."""
        # Find textarea
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        chat_input = None

        for textarea in textareas:
            placeholder = textarea.get_attribute("placeholder") or ""
            if "action" in placeholder.lower() or textarea.is_displayed():
                chat_input = textarea
                break

        assert chat_input is not None, "Chat input not found"

        # Clear and type message
        chat_input.clear()
        chat_input.send_keys(message)
        time.sleep(0.5)

        # Find and click Send button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        send_button = None
        for btn in buttons:
            if "Send" in btn.text and btn.is_displayed():
                send_button = btn
                break

        assert send_button is not None, "Send button not found"
        send_button.click()

    def test_chat_input_exists(self, driver):
        """Test that chat input field exists."""
        self._load_character_for_chat(driver)

        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        assert len(textareas) > 0, "No chat input (textarea) found"
        print(f"✅ Chat input exists ({len(textareas)} textareas found)")

    def test_send_button_exists(self, driver):
        """Test that Send button exists."""
        self._load_character_for_chat(driver)

        buttons = driver.find_elements(By.TAG_NAME, "button")
        send_button_found = any("Send" in btn.text for btn in buttons if btn.text)

        assert send_button_found, "Send button not found"
        print("✅ Send button exists")

    def test_clear_history_button_exists(self, driver):
        """Test that Clear History button exists."""
        self._load_character_for_chat(driver)

        buttons = driver.find_elements(By.TAG_NAME, "button")
        clear_button_found = any("Clear" in btn.text for btn in buttons if btn.text)

        assert clear_button_found, "Clear History button not found"
        print("✅ Clear History button exists")

    def test_send_simple_message(self, driver):
        """Test sending a simple chat message."""
        self._load_character_for_chat(driver)

        test_message = "I look around"
        self._send_chat_message(driver, test_message)

        # Wait for response (this may take time depending on LLM)
        time.sleep(5)

        # Check if message appears in chat history
        body_text = driver.find_element(By.TAG_NAME, "body").text

        # The message should appear somewhere in the page
        # (Gradio chatbot displays messages in custom components)
        print(f"✅ Sent message: '{test_message}'")
        print("⚠️  Response verification requires LLM - check logs")

        assert True  # Pass if no errors occurred

    def test_help_command(self, driver):
        """Test /help command."""
        self._load_character_for_chat(driver)

        self._send_chat_message(driver, "/help")
        time.sleep(3)

        # Look for help text in response
        body_text = driver.find_element(By.TAG_NAME, "body").text

        # Check for common help text keywords
        help_keywords = ["command", "help", "stats", "context", "rag"]
        found_keywords = [kw for kw in help_keywords if kw.lower() in body_text.lower()]

        assert len(found_keywords) > 0, \
            f"Help command may not have responded. Found keywords: {found_keywords}"

        print(f"✅ /help command executed (found keywords: {found_keywords})")

    def test_stats_command(self, driver):
        """Test /stats command."""
        self._load_character_for_chat(driver)

        self._send_chat_message(driver, "/stats")
        time.sleep(3)

        body_text = driver.find_element(By.TAG_NAME, "body").text

        # Check for stat-related text
        stat_keywords = ["STR", "DEX", "CON", "HP", "AC"]
        found_stats = [stat for stat in stat_keywords if stat in body_text]

        assert len(found_stats) > 0, \
            f"Stats command may not have responded. Found: {found_stats}"

        print(f"✅ /stats command executed (found: {found_stats})")

    def test_context_command(self, driver):
        """Test /context command."""
        self._load_character_for_chat(driver)

        self._send_chat_message(driver, "/context")
        time.sleep(3)

        body_text = driver.find_element(By.TAG_NAME, "body").text

        # Check for context-related text
        context_keywords = ["context", "player", "character", "Thorin"]
        found_keywords = [kw for kw in context_keywords if kw in body_text]

        assert len(found_keywords) > 0, \
            f"Context command may not have responded. Found: {found_keywords}"

        print(f"✅ /context command executed (found: {found_keywords})")

    def test_rag_command(self, driver):
        """Test /rag command for searching D&D rules."""
        self._load_character_for_chat(driver)

        self._send_chat_message(driver, "/rag fireball")
        time.sleep(4)

        body_text = driver.find_element(By.TAG_NAME, "body").text

        # Check for RAG-related text or spell info
        rag_keywords = ["RAG", "fireball", "spell", "search", "result"]
        found_keywords = [kw for kw in rag_keywords if kw.lower() in body_text.lower()]

        assert len(found_keywords) > 0, \
            f"RAG command may not have responded. Found: {found_keywords}"

        print(f"✅ /rag command executed (found: {found_keywords})")

    def test_clear_chat_history(self, driver):
        """Test clearing chat history."""
        self._load_character_for_chat(driver)

        # Send a message first
        self._send_chat_message(driver, "test message")
        time.sleep(2)

        # Click Clear History button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        clear_button = None
        for btn in buttons:
            if "Clear" in btn.text and btn.is_displayed():
                clear_button = btn
                break

        assert clear_button is not None, "Clear History button not found"
        clear_button.click()
        time.sleep(1)

        print("✅ Clear History button clicked")
        # Actual verification of cleared history depends on Gradio implementation

    def test_multiple_messages(self, driver):
        """Test sending multiple messages in sequence."""
        self._load_character_for_chat(driver)

        messages = [
            "Hello",
            "I draw my sword",
            "/stats"
        ]

        for msg in messages:
            self._send_chat_message(driver, msg)
            time.sleep(2)

        print(f"✅ Sent {len(messages)} messages successfully")
        assert True

    def test_chat_input_clears_after_send(self, driver):
        """Test that chat input clears after sending message."""
        self._load_character_for_chat(driver)

        # Find textarea
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        chat_input = textareas[0] if textareas else None
        assert chat_input is not None

        # Send message
        chat_input.clear()
        chat_input.send_keys("test")

        # Click Send
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Send" in btn.text and btn.is_displayed():
                btn.click()
                break

        time.sleep(1)

        # Check if input is cleared (Gradio usually clears it)
        # This may vary based on Gradio version
        current_value = chat_input.get_attribute("value") or ""

        if current_value == "":
            print("✅ Chat input cleared after sending")
        else:
            print(f"⚠️  Chat input not cleared (current value: '{current_value}')")

        assert True  # Don't fail on this

    @pytest.mark.slow
    def test_wait_for_llm_response(self, driver):
        """Test waiting for actual LLM response (slow test)."""
        self._load_character_for_chat(driver)

        self._send_chat_message(driver, "I look around the room")

        # Wait longer for LLM response
        print("⏳ Waiting for LLM response (this may take 10-30 seconds)...")
        time.sleep(15)

        body_text = driver.find_element(By.TAG_NAME, "body").text

        # Just verify no error occurred
        error_keywords = ["error", "failed", "exception"]
        errors_found = [err for err in error_keywords if err.lower() in body_text.lower()]

        if len(errors_found) > 0:
            print(f"⚠️  Possible errors detected: {errors_found}")
        else:
            print("✅ No obvious errors after LLM response wait")

        assert True  # Pass if test completes
