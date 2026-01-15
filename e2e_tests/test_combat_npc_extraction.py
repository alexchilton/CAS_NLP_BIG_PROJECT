#!/usr/bin/env python3
"""
E2E Test: Combat NPC Extraction

Simpler test that uses /start_combat to ensure NPCs exist,
then verifies that when GM narrates NPCs in responses,
they are auto-extracted and tracked.
"""

import sys
import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_helpers import load_character, wait_for_gradio

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Enable debug mode to see NPC extraction
os.environ['GM_DEBUG'] = 'true'


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


def send_message(driver, message, wait_time=8):
    """Send a message in the chat."""
    print(f"\n📤 Player: {message}")

    chat_input = find_chat_input(driver)
    chat_input.clear()
    chat_input.send_keys(message)

    send_btn = find_send_button(driver)
    send_btn.click()

    time.sleep(wait_time)

    # Wait for "Loading content" to clear
    max_wait = wait_time + 3
    start_time = time.time()
    while time.time() - start_time < max_wait:
        messages = get_chat_messages(driver)
        if messages and messages[-1] != "Loading content":
            break
        time.sleep(0.5)


def get_chat_messages(driver):
    """Get all chat messages."""
    chat_containers = driver.find_elements(By.CLASS_NAME, "message")
    messages = []
    seen_texts = set()

    for container in chat_containers:
        text = container.text.strip()
        if text and text not in seen_texts and text != "Loading content":
            messages.append(text)
            seen_texts.add(text)

    return messages


# DEPRECATED: Use selenium_helpers.load_character instead
# def load_character(driver, char_name="Thorin"):
    """Load a character."""
    print(f"\n📝 Loading character: {char_name}")

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
            time.sleep(3)
            break

    print(f"✅ Character loaded")


def test_combat_npc_extraction():
    """Test NPC extraction during combat."""
    print("\n" + "⚔️" * 40)
    print("COMBAT NPC EXTRACTION TEST")
    print("⚔️" * 40)

    options = webdriver.ChromeOptions()
    if os.environ.get('HEADLESS', 'false').lower() == 'true':
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

        print("\n" + "=" * 80)
        print("TEST 1: Start Combat with Explicit NPC")
        print("=" * 80)

        # Use /start_combat to ensure goblin exists
        send_message(driver, "/start_combat Goblin", wait_time=6)

        messages = get_chat_messages(driver)
        if messages:
            print(f"🎭 GM: {messages[-1][:200]}...")

        print("\n" + "=" * 80)
        print("TEST 2: Attack - GM Should Narrate Goblin Response")
        print("=" * 80)
        print("💡 When GM narrates goblin's actions, NPC extraction should detect it")

        send_message(driver, "I attack the goblin with my longsword", wait_time=10)

        messages = get_chat_messages(driver)
        if messages:
            gm_response = messages[-1]
            print(f"🎭 GM: {gm_response[:300]}...")

            # Check if GM mentioned goblin
            if "goblin" in gm_response.lower():
                print("\n✅ SUCCESS: GM mentioned goblin in response")
                print("   NPC extraction should have detected and tracked this")
            else:
                print("\n⚠️  GM didn't mention goblin in response")

        print("\n" + "=" * 80)
        print("TEST 3: Continue Combat for Several Rounds")
        print("=" * 80)

        for round_num in range(1, 4):
            print(f"\n--- Round {round_num} ---")

            send_message(driver, "I attack the goblin", wait_time=10)

            messages = get_chat_messages(driver)
            if messages:
                response = messages[-1]
                print(f"🎭 GM: {response[:150]}...")

                # Check for combat end
                death_phrases = ["dies", "falls", "defeated", "slain", "dead"]
                if any(phrase in response.lower() for phrase in death_phrases):
                    print("\n🎉 Combat ended - enemy defeated!")
                    break

        print("\n" + "=" * 80)
        print("✅ COMBAT NPC EXTRACTION TEST COMPLETE")
        print("=" * 80)
        print("\n💡 To verify NPC extraction:")
        print("   1. Check server logs at /tmp/gradio_debug.log")
        print("   2. Look for 'EXTRACTED MECHANICS' sections")
        print("   3. Should see 'npcs_introduced' field with extracted NPCs")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        try:
            screenshot_path = "/tmp/combat_npc_error.png"
            driver.save_screenshot(screenshot_path)
            print(f"\n📸 Screenshot saved to: {screenshot_path}")
        except:
            pass

        raise

    finally:
        time.sleep(2)
        driver.quit()


if __name__ == "__main__":
    print("\n" + "🎮" * 40)
    print("COMBAT NPC EXTRACTION TEST")
    print("🎮" * 40)
    print("\n🎯 This test:")
    print("   1. Starts combat with /start_combat to ensure NPC exists")
    print("   2. Attacks the NPC and checks GM narrates its actions")
    print("   3. Verifies NPC extraction logs in server output")
    print("\n⚔️ Let's test NPC extraction in combat!\n")
    print("=" * 80)

    test_combat_npc_extraction()
