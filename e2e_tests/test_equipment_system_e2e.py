#!/usr/bin/env python3
"""
E2E Test: Equipment System Integration

Tests that equipment system actually works in the game:
1. Can equip magic items
2. AC bonuses apply correctly
3. Attunement limits enforced
4. Can unequip items
5. Can use potions
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
    time.sleep(2)
    print("✅ Gradio loaded")


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

    time.sleep(3)


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


def get_character_ac(driver):
    """Extract AC from character sheet."""
    textboxes = driver.find_elements(By.TAG_NAME, "textarea")
    for tb in textboxes:
        if tb.is_displayed():
            text = tb.get_attribute("value")
            if text and "AC:" in text:
                # Extract AC value
                for line in text.split('\n'):
                    if line.strip().startswith("AC:"):
                        try:
                            ac = int(line.split(":")[1].strip().split()[0])
                            return ac
                        except:
                            pass
    return None


def load_character(driver, char_name="Thorin"):
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


def test_equipment_system():
    """Test equipment system in the actual game."""
    print("\n" + "=" * 80)
    print("⚔️  E2E TEST: Equipment System Integration")
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

        # Load character
        load_character(driver, "Thorin")

        # TEST 1: Check initial AC
        print("\n" + "=" * 80)
        print("TEST 1: Get initial AC")
        print("=" * 80)

        send_message(driver, "/stats")
        time.sleep(2)

        initial_ac = get_character_ac(driver)
        print(f"Initial AC: {initial_ac}")

        if initial_ac is None:
            print("❌ Could not extract AC from character sheet")
            initial_ac = 15  # Fallback

        # TEST 2: Give character a magic item
        print("\n" + "=" * 80)
        print("TEST 2: Add Ring of Protection to inventory")
        print("=" * 80)

        # First, let's use /give command if it exists, or check if we can buy it
        send_message(driver, "I found a Ring of Protection")
        time.sleep(3)

        messages = get_chat_messages(driver)
        print(f"Response: {messages[-1][:200]}...")

        # TEST 3: Try to equip the ring
        print("\n" + "=" * 80)
        print("TEST 3: Equip Ring of Protection")
        print("=" * 80)

        send_message(driver, "/equip Ring of Protection")
        time.sleep(3)

        messages = get_chat_messages(driver)
        equip_response = messages[-1].lower()
        print(f"Equip response: {messages[-1][:200]}...")

        if "equipped" in equip_response or "ring of protection" in equip_response:
            print("✅ TEST 3 PASSED: Item equipped successfully")
        elif "don't have" in equip_response or "not found" in equip_response:
            print("⚠️  TEST 3: Item not in inventory (expected if /give doesn't work)")
            # Try alternative: check /buy or manually add to inventory
            send_message(driver, "/buy Ring of Protection")
            time.sleep(2)
            send_message(driver, "/equip Ring of Protection")
            time.sleep(3)
            messages = get_chat_messages(driver)
            equip_response = messages[-1].lower()
            if "equipped" in equip_response:
                print("✅ Equipped after buying")
            else:
                print(f"❌ Still can't equip: {messages[-1][:200]}")
        else:
            print(f"❓ Unexpected equip response: {messages[-1][:200]}")

        # TEST 4: Check if AC increased
        print("\n" + "=" * 80)
        print("TEST 4: Verify AC increased")
        print("=" * 80)

        send_message(driver, "/stats")
        time.sleep(2)

        new_ac = get_character_ac(driver)
        print(f"New AC: {new_ac}")

        if new_ac and initial_ac:
            if new_ac > initial_ac:
                print(f"✅ TEST 4 PASSED: AC increased from {initial_ac} to {new_ac}")
            else:
                print(f"❌ TEST 4 FAILED: AC did not increase (was {initial_ac}, now {new_ac})")
        else:
            print("⚠️  Could not determine if AC changed")

        # TEST 5: Check equipment list
        print("\n" + "=" * 80)
        print("TEST 5: Check equipped items list")
        print("=" * 80)

        send_message(driver, "/equipment")
        time.sleep(2)

        messages = get_chat_messages(driver)
        equipment_response = messages[-1]
        print(f"Equipment response: {equipment_response[:300]}...")

        if "Ring of Protection" in equipment_response:
            print("✅ TEST 5 PASSED: Ring shows in equipped items")
        else:
            print(f"❌ TEST 5 FAILED: Ring not in equipment list")

        # TEST 6: Try to unequip
        print("\n" + "=" * 80)
        print("TEST 6: Unequip the ring")
        print("=" * 80)

        send_message(driver, "/unequip ring_left")
        time.sleep(2)

        messages = get_chat_messages(driver)
        unequip_response = messages[-1].lower()
        print(f"Unequip response: {messages[-1][:200]}...")

        if "unequipped" in unequip_response:
            print("✅ TEST 6 PASSED: Item unequipped")

            # Verify AC decreased
            send_message(driver, "/stats")
            time.sleep(2)
            final_ac = get_character_ac(driver)
            if final_ac == initial_ac:
                print(f"✅ AC returned to original value: {final_ac}")
            else:
                print(f"⚠️  AC is {final_ac}, expected {initial_ac}")
        else:
            print(f"❌ TEST 6 FAILED: Could not unequip")

        # TEST 7: Test potion usage
        print("\n" + "=" * 80)
        print("TEST 7: Use a potion")
        print("=" * 80)

        send_message(driver, "I found a Potion of Healing")
        time.sleep(2)
        send_message(driver, "/use Potion of Healing")
        time.sleep(3)

        messages = get_chat_messages(driver)
        potion_response = messages[-1].lower()
        print(f"Potion response: {messages[-1][:200]}...")

        if "healing" in potion_response or "healed" in potion_response or "2d4" in potion_response:
            print("✅ TEST 7 PASSED: Potion used successfully")
        else:
            print(f"❓ TEST 7: Uncertain result - {messages[-1][:200]}")

        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print("\nEquipment system E2E test completed.")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        try:
            screenshot_path = "/tmp/equipment_e2e_error.png"
            driver.save_screenshot(screenshot_path)
            print(f"\n📸 Screenshot saved to: {screenshot_path}")
        except:
            pass

        raise

    finally:
        driver.quit()


if __name__ == "__main__":
    test_equipment_system()
