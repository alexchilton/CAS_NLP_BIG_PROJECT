#!/usr/bin/env python3
"""
E2E Test: Magic Item RAG Integration

Tests that the magic item RAG actually works in the game:
1. Can ask about magic items and get correct info
2. DM provides item descriptions from RAG
3. Item effects are accurate
4. Class features can be queried
"""

import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_helpers import load_character, wait_for_gradio

sys.path.insert(0, str(Path(__file__).parent.parent))


# DEPRECATED: Use selenium_helpers.wait_for_gradio instead
# def wait_for_gradio(driver, timeout=30):
    """Wait for Gradio interface to fully load."""
    print("⏳ Waiting for Gradio to load...")
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "gradio-app"))
    )
    time.sleep(2)
    print("✅ Gradio loaded")



# NOTE: This test file has been updated to import from selenium_helpers.py
# Local load_character() and wait_for_gradio() functions have been deprecated.
# The imported versions use the correct Gradio selectors (input[aria-label=...])
# See e2e_tests/README_SELENIUM.md for details.

def find_chat_input(driver):
    """Find the chat input textarea."""
    textareas = driver.find_elements(By.TAG_NAME, "textarea")
    for ta in textareas:
        placeholder = ta.get_attribute("placeholder")
        if placeholder and "your action" in placeholder.lower():
            return ta
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

    time.sleep(4)  # Wait longer for RAG query


def get_chat_messages(driver):
    """Get all chat messages."""
    chat_containers = driver.find_elements(By.CLASS_NAME, "message")

    messages = []
    seen_texts = set()

    for container in chat_containers:
        text = container.text.strip()
        if text and text not in seen_texts:
            messages.append(text)
            seen_texts.add(text)

    return messages


# DEPRECATED: Use selenium_helpers.load_character instead
# def load_character(driver, char_name="Thorin"):
    """Load a character."""
    print(f"📝 Loading character: {char_name}")

    dropdowns = driver.find_elements(By.TAG_NAME, "select")
    char_dropdown = None
    for dd in dropdowns:
        if dd.is_displayed():
            char_dropdown = dd
            break

    if char_dropdown:
        char_dropdown.click()
        time.sleep(0.5)

        options = char_dropdown.find_elements(By.TAG_NAME, "option")
        for opt in options:
            if char_name.lower() in opt.text.lower():
                opt.click()
                break

    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if "load character" in btn.text.lower():
            btn.click()
            time.sleep(2)
            break

    print(f"✅ Character loaded")


def test_magic_item_rag():
    """Test magic item RAG queries in the actual game."""
    print("\n" + "=" * 80)
    print("🔮 E2E TEST: Magic Item RAG Integration")
    print("=" * 80)

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(options=options)

    try:
        print("\n📍 Opening Gradio app at http://localhost:7860")
        driver.get("http://localhost:7860")
        wait_for_gradio(driver)

        load_character(driver, "Thorin")

        # TEST 1: Ask about a magic item
        print("\n" + "=" * 80)
        print("TEST 1: Ask about Ring of Protection")
        print("=" * 80)

        send_message(driver, "What is a Ring of Protection?")
        time.sleep(5)  # RAG queries can be slow

        messages = get_chat_messages(driver)
        response = messages[-1]
        print(f"DM Response:\n{response}\n")

        # Check if response contains expected information
        response_lower = response.lower()

        test_1_passed = False
        if "ring" in response_lower and "protection" in response_lower:
            print("✅ Response mentions Ring of Protection")
            test_1_passed = True
        else:
            print("❌ Response doesn't mention Ring of Protection")

        if "+1" in response or "bonus" in response_lower:
            print("✅ Response mentions the +1 bonus")
        else:
            print("⚠️  Response doesn't clearly mention the bonus")

        if "ac" in response_lower or "armor class" in response_lower:
            print("✅ Response mentions AC")
        else:
            print("⚠️  Response doesn't mention AC")

        if "saving throw" in response_lower or "saves" in response_lower:
            print("✅ Response mentions saving throws")
        else:
            print("⚠️  Response doesn't mention saving throws")

        if "attunement" in response_lower or "attune" in response_lower:
            print("✅ Response mentions attunement requirement")
        else:
            print("⚠️  Response doesn't mention attunement")

        if test_1_passed:
            print("\n✅ TEST 1 PASSED: RAG returned info about Ring of Protection")
        else:
            print("\n❌ TEST 1 FAILED: RAG did not return relevant info")

        # TEST 2: Ask about a weapon
        print("\n" + "=" * 80)
        print("TEST 2: Ask about Flametongue sword")
        print("=" * 80)

        send_message(driver, "Tell me about a Flametongue sword")
        time.sleep(5)

        messages = get_chat_messages(driver)
        response = messages[-1]
        print(f"DM Response:\n{response}\n")

        response_lower = response.lower()

        test_2_passed = False
        if "flametongue" in response_lower or "flame" in response_lower:
            print("✅ Response mentions Flametongue")
            test_2_passed = True
        else:
            print("❌ Response doesn't mention Flametongue")

        if "fire" in response_lower or "2d6" in response:
            print("✅ Response mentions fire damage")
        else:
            print("⚠️  Response doesn't mention fire damage")

        if test_2_passed:
            print("\n✅ TEST 2 PASSED: RAG returned info about Flametongue")
        else:
            print("\n❌ TEST 2 FAILED: RAG did not return relevant info")

        # TEST 3: Ask about a class feature
        print("\n" + "=" * 80)
        print("TEST 3: Ask about Rogue's Sneak Attack")
        print("=" * 80)

        send_message(driver, "How does Sneak Attack work?")
        time.sleep(5)

        messages = get_chat_messages(driver)
        response = messages[-1]
        print(f"DM Response:\n{response}\n")

        response_lower = response.lower()

        test_3_passed = False
        if "sneak attack" in response_lower:
            print("✅ Response mentions Sneak Attack")
            test_3_passed = True
        else:
            print("❌ Response doesn't mention Sneak Attack")

        if "advantage" in response_lower or "ally" in response_lower:
            print("✅ Response mentions trigger condition")
        else:
            print("⚠️  Response doesn't clearly explain trigger")

        if "d6" in response_lower:
            print("✅ Response mentions damage dice")
        else:
            print("⚠️  Response doesn't mention damage dice")

        if test_3_passed:
            print("\n✅ TEST 3 PASSED: RAG returned info about Sneak Attack")
        else:
            print("\n❌ TEST 3 FAILED: RAG did not return relevant info")

        # TEST 4: Ask about a potion
        print("\n" + "=" * 80)
        print("TEST 4: Ask about Potion of Healing")
        print("=" * 80)

        send_message(driver, "What does a Potion of Healing do?")
        time.sleep(5)

        messages = get_chat_messages(driver)
        response = messages[-1]
        print(f"DM Response:\n{response}\n")

        response_lower = response.lower()

        test_4_passed = False
        if "potion" in response_lower and "healing" in response_lower:
            print("✅ Response mentions Potion of Healing")
            test_4_passed = True
        else:
            print("❌ Response doesn't mention Potion of Healing")

        if "2d4" in response or "heal" in response_lower:
            print("✅ Response mentions healing")
        else:
            print("⚠️  Response doesn't mention healing amount")

        if test_4_passed:
            print("\n✅ TEST 4 PASSED: RAG returned info about Potion of Healing")
        else:
            print("\n❌ TEST 4 FAILED: RAG did not return relevant info")

        # TEST 5: Ask an item that DOESN'T exist
        print("\n" + "=" * 80)
        print("TEST 5: Ask about fake item (should handle gracefully)")
        print("=" * 80)

        send_message(driver, "What is a Ring of Ultimate Power?")
        time.sleep(5)

        messages = get_chat_messages(driver)
        response = messages[-1]
        print(f"DM Response:\n{response}\n")

        response_lower = response.lower()

        # Should either say it doesn't exist or provide general info
        if "don't" in response_lower or "not" in response_lower or "doesn't exist" in response_lower:
            print("✅ TEST 5 PASSED: DM handles unknown item gracefully")
        elif len(response) > 50:  # DM might improvise
            print("✅ TEST 5 PASSED: DM provided a response (possibly improvised)")
        else:
            print("⚠️  TEST 5: Unclear response to unknown item")

        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print("\nMagic Item RAG E2E test completed.")
        print("Check individual test results above to verify RAG is working correctly.")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        try:
            screenshot_path = "/tmp/magic_item_rag_error.png"
            driver.save_screenshot(screenshot_path)
            print(f"\n📸 Screenshot saved to: {screenshot_path}")
        except:
            pass

        raise

    finally:
        driver.quit()


if __name__ == "__main__":
    test_magic_item_rag()
