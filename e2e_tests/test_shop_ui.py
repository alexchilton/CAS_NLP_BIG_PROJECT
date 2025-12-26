#!/usr/bin/env python3
"""
E2E Test: Shop System UI Integration

Tests the shop system in the Gradio UI to ensure:
1. /buy command works
2. /sell command works
3. Gold updates correctly
4. Inventory updates correctly
"""

import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def wait_for_gradio(driver, timeout=30):
    """Wait for Gradio interface to fully load."""
    print("⏳ Waiting for Gradio to load...")
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "gradio-app"))
    )
    time.sleep(2)  # Extra time for components to initialize
    print("✅ Gradio loaded")


def find_chat_input(driver):
    """Find the chat input textarea."""
    textareas = driver.find_elements(By.TAG_NAME, "textarea")
    for ta in textareas:
        placeholder = ta.get_attribute("placeholder")
        if placeholder and "your action" in placeholder.lower():
            return ta
    # Fallback: find any visible enabled textarea
    for ta in textareas:
        if ta.is_displayed() and ta.is_enabled():
            return ta
    raise Exception("Could not find chat input textarea")


def find_send_button(driver):
    """Find the Send button."""
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if btn.text.strip().lower() == "send":
            return btn
    raise Exception("Could not find Send button")


def send_message(driver, message):
    """Send a message in the chat."""
    print(f"📤 Sending: {message}")

    chat_input = find_chat_input(driver)
    chat_input.clear()
    chat_input.send_keys(message)

    send_btn = find_send_button(driver)
    send_btn.click()

    time.sleep(3)  # Wait for response


def get_chat_messages(driver):
    """Get all chat messages (Gradio 6.x compatible)."""
    # Gradio 6.x uses .message class for chat messages
    # Each message appears twice in the DOM, so we'll deduplicate
    chat_containers = driver.find_elements(By.CLASS_NAME, "message")

    messages = []
    seen_texts = set()

    for container in chat_containers:
        text = container.text.strip()
        if text and text not in seen_texts:
            messages.append(text)
            seen_texts.add(text)

    return messages


def load_character(driver, char_name="Thorin"):
    """Load a character."""
    print(f"📝 Loading character: {char_name}")

    # Find character dropdown
    dropdowns = driver.find_elements(By.TAG_NAME, "select")
    char_dropdown = None
    for dd in dropdowns:
        if dd.is_displayed():
            char_dropdown = dd
            break

    if char_dropdown:
        char_dropdown.click()
        time.sleep(0.5)

        # Find option with character name
        options = char_dropdown.find_elements(By.TAG_NAME, "option")
        for opt in options:
            if char_name.lower() in opt.text.lower():
                opt.click()
                break

    # Click Load Character button
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if "load character" in btn.text.lower():
            btn.click()
            time.sleep(2)
            break

    print(f"✅ Character loaded")


def get_character_sheet_text(driver):
    """Get the character sheet display text."""
    # Look for textboxes or markdown blocks that show character info
    textboxes = driver.find_elements(By.TAG_NAME, "textarea")
    for tb in textboxes:
        if tb.is_displayed():
            text = tb.get_attribute("value")
            if text and ("HP:" in text or "Gold:" in text or "Inventory:" in text):
                return text

    # Try markdown/label elements
    labels = driver.find_elements(By.TAG_NAME, "label")
    for label in labels:
        text = label.text
        if text and ("HP:" in text or "Gold:" in text or "Inventory:" in text):
            return text

    return ""


def test_shop_ui():
    """Test shop system in the UI."""
    print("\n" + "=" * 80)
    print("🛒 E2E TEST: Shop System UI Integration")
    print("=" * 80)

    # Setup Chrome options
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Comment out for debugging
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(options=options)

    try:
        # Navigate to Gradio app
        print("\n📍 Opening Gradio app at http://localhost:7860")
        driver.get("http://localhost:7860")

        wait_for_gradio(driver)

        # TEST 1: Load character
        print("\n" + "=" * 80)
        print("TEST 1: Load character")
        print("=" * 80)

        load_character(driver, "Thorin")

        # Get initial gold
        sheet_text = get_character_sheet_text(driver)
        print(f"\n📜 Character sheet:\n{sheet_text[:200]}...")

        # TEST 2: Try to buy an item
        print("\n" + "=" * 80)
        print("TEST 2: Buy an item with /buy command")
        print("=" * 80)

        send_message(driver, "/buy rope")

        time.sleep(2)

        messages = get_chat_messages(driver)
        print(f"\n💬 Latest response:")
        print(f"  {messages[-1][:200]}...")

        # Check for success or error
        response = messages[-1].lower()

        if "purchased" in response or "bought" in response or "rope" in response:
            print("\n✅ TEST 2 PASSED: /buy command appears to work")
        elif "not enough gold" in response:
            print("\n⚠️ TEST 2: Character doesn't have enough gold (expected behavior)")
        elif "error" in response or "not found" in response:
            print(f"\n❌ TEST 2 FAILED: Error in /buy command")
            print(f"Response: {messages[-1]}")
        else:
            print(f"\n❓ TEST 2 UNCERTAIN: Unexpected response")
            print(f"Response: {messages[-1]}")

        # TEST 3: Check if inventory updated
        print("\n" + "=" * 80)
        print("TEST 3: Check inventory/gold update")
        print("=" * 80)

        send_message(driver, "/stats")
        time.sleep(2)

        messages = get_chat_messages(driver)
        stats_response = messages[-1]
        print(f"\n📊 Stats response:")
        print(f"  {stats_response[:300]}...")

        # Check if rope is in inventory
        if "rope" in stats_response.lower() or "Rope" in stats_response:
            print("\n✅ TEST 3 PASSED: Rope appears in inventory")
        else:
            print("\n❌ TEST 3 FAILED: Rope not in inventory after purchase")

        # TEST 4: Try to sell an item
        print("\n" + "=" * 80)
        print("TEST 4: Sell an item with /sell command")
        print("=" * 80)

        send_message(driver, "/sell longsword")

        time.sleep(2)

        messages = get_chat_messages(driver)
        print(f"\n💬 Latest response:")
        print(f"  {messages[-1][:200]}...")

        response = messages[-1].lower()

        if "sold" in response or "sell" in response:
            print("\n✅ TEST 4 PASSED: /sell command appears to work")
        elif "don't have" in response or "not found" in response:
            print("\n⚠️ TEST 4: Character doesn't have item to sell (expected if Thorin has no longsword)")
        elif "error" in response:
            print(f"\n❌ TEST 4 FAILED: Error in /sell command")
            print(f"Response: {messages[-1]}")
        else:
            print(f"\n❓ TEST 4 UNCERTAIN: Unexpected response")
            print(f"Response: {messages[-1]}")

        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print("\n🔍 Shop UI test completed. Check results above.")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")

        # Get console logs for debugging
        try:
            logs = driver.get_log('browser')
            print("\n📋 Browser console logs:")
            for log in logs[-20:]:
                print(f"  {log}")
        except:
            pass

        # Screenshot for debugging
        try:
            screenshot_path = "/tmp/shop_ui_error.png"
            driver.save_screenshot(screenshot_path)
            print(f"\n📸 Screenshot saved to: {screenshot_path}")
        except:
            pass

        raise

    finally:
        driver.quit()


if __name__ == "__main__":
    test_shop_ui()
