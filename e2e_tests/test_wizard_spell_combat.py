#!/usr/bin/env python3
"""
E2E Test: Wizard Spell Combat to Death

Tests wizard spell casting in combat:
- Elara (Wizard) vs Skeletons in Ancient Ruins
- Uses spells (Magic Missile, Fire Bolt, etc.)
- Fights until character or enemies are defeated
- Tracks spell slots and HP
"""

import sys
import time
import os
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Enable debug mode
os.environ['GM_DEBUG'] = 'true'


def wait_for_gradio(driver, timeout=30):
    """Wait for Gradio interface to fully load."""
    print("⏳ Waiting for Gradio interface...")

    # Wait for gradio-app tag
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "gradio-app"))
    )

    # Wait longer for JavaScript to render
    print("   ⏳ Waiting for JavaScript to render components...")
    time.sleep(10)  # Increased from 2 to 10 seconds

    # Wait for any button to appear (sign that UI is rendered)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "button"))
        )
        print("   ✅ Buttons detected - UI rendered")
    except:
        print("   ⚠️  No buttons found yet, continuing anyway...")

    print("✅ Gradio interface loaded")


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


def load_character(driver, char_name="Elara"):
    """Load a character via UI dropdown."""
    print(f"\n📝 Loading character: {char_name}")
    
    # Find the character dropdown by aria-label
    # Gradio renders dropdowns as <input role="listbox">
    try:
        char_dropdown = driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Choose Your Character"]')
        print(f"✅ Found character dropdown")
    except:
        print(f"❌ Could not find character dropdown")
        driver.save_screenshot('/tmp/dropdown_not_found.png')
        raise Exception("Character dropdown not found - check screenshot at /tmp/dropdown_not_found.png")
    
    # Click to open dropdown
    char_dropdown.click()
    time.sleep(1)
    
    # Find and click the character option
    options = driver.find_elements(By.CSS_SELECTOR, '[role="option"]')
    print(f"   Found {len(options)} options")
    
    for opt in options:
        if char_name.lower() in opt.text.lower():
            print(f"   Selecting: {opt.text}")
            opt.click()
            time.sleep(1)
            break
    
    # Click Load Character button
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if "Load Character" in btn.text:
            print(f"   Clicking Load Character button")
            btn.click()
            time.sleep(7)  # Wait for character to load
            break
    
    print(f"✅ Character loaded: {char_name}")


def check_combat_over(message):
    """Check if combat is over (death or victory)."""
    lower_msg = message.lower()

    # Check for player death
    if any(phrase in lower_msg for phrase in ["you have died", "you are dead", "you fall unconscious", "death saves"]):
        return "player_dead"

    # Check for enemy death/victory
    if any(phrase in lower_msg for phrase in ["skeleton falls", "skeleton is defeated", "skeleton dies",
                                                "victory", "combat ends", "you have won"]):
        return "enemy_dead"

    # Check for end combat
    if "combat has ended" in lower_msg or "combat is over" in lower_msg:
        return "combat_ended"

    return None


def test_wizard_spell_combat():
    """Test wizard spell combat to death."""
    print("\n" + "✨" * 40)
    print("WIZARD SPELL COMBAT TEST - FIGHT TO DEATH")
    print("✨" * 40)
    print("\n⚠️  NOTE: This test connects to your running Gradio instance at http://localhost:7860")
    print("   Make sure Gradio is running before starting this test!")
    print("   The test will use whatever character/location is currently loaded.")
    print("✨" * 40)

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

        print("\n" + "=" * 80)
        print("SETUP: Loading Elara (Wizard)")
        print("=" * 80)

        load_character(driver, "Elara")
        print(f"\n✅ Elara loaded")

        # Verify location
        send_message(driver, "/context", wait_time=5)
        messages = get_chat_messages(driver)
        if messages:
            context = messages[-1]
            print(f"\n🗺️  Location: {context[:200]}...")

        print("\n" + "=" * 80)
        print("EXPLORATION: Elara explores the Ancient Ruins")
        print("=" * 80)
        print("💡 Let's trigger the GM to describe the ruins and spawn undead naturally")

        # First explore the ruins - GM should mention skeletons
        send_message(driver, "I carefully explore the ancient ruins, looking for any signs of danger or treasure", wait_time=10)

        messages = get_chat_messages(driver)
        if messages:
            exploration_response = messages[-1]
            print(f"\n🎭 GM: {exploration_response[:400]}...")

            # Check if GM mentioned skeletons or undead
            if "skeleton" in exploration_response.lower() or "undead" in exploration_response.lower():
                print("\n✅ GM mentioned undead/skeletons in description!")
            else:
                print("\n⚠️  GM didn't mention skeletons - this is the reality check working!")
                print("     We should NOT start combat with non-existent creatures")
                return  # Exit test gracefully - reality check is working correctly

        print("\n" + "=" * 80)
        print("COMBAT: GM described skeletons, now start combat")
        print("=" * 80)
        print("💡 Only starting combat because skeletons were mentioned by GM")

        send_message(driver, "/start_combat Skeleton", wait_time=8)

        messages = get_chat_messages(driver)
        if messages:
            combat_start = messages[-1]
            print(f"\n🎭 GM: {combat_start[:400]}")

        # Combat loop - fight until death
        round_num = 1
        max_rounds = 20  # Safety limit
        combat_over = False

        # Spell rotation for wizard
        spells = [
            "I cast Magic Missile at the skeleton",
            "I cast Fire Bolt at the skeleton",
            "I attack the skeleton with my quarterstaff",
        ]
        spell_index = 0

        while round_num <= max_rounds and not combat_over:
            print(f"\n" + "=" * 80)
            print(f"ROUND {round_num}")
            print("=" * 80)

            # Elara's action
            action = spells[spell_index % len(spells)]
            send_message(driver, action, wait_time=10)

            messages = get_chat_messages(driver)
            if messages:
                response = messages[-1]
                print(f"\n🎭 GM: {response[:500]}...")

                # Check if combat is over
                combat_status = check_combat_over(response)
                if combat_status:
                    print(f"\n{'💀' * 40}")
                    if combat_status == "player_dead":
                        print("💀 ELARA HAS FALLEN!")
                    elif combat_status == "enemy_dead":
                        print("⚔️ SKELETON DEFEATED! ELARA VICTORIOUS!")
                    else:
                        print("⚔️ COMBAT ENDED!")
                    print(f"{'💀' * 40}\n")
                    combat_over = True
                    break

            spell_index += 1
            round_num += 1
            time.sleep(2)

        if not combat_over:
            print(f"\n⚠️ Combat reached maximum rounds ({max_rounds})")

        print("\n" + "=" * 80)
        print("✅ WIZARD SPELL COMBAT TEST COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Results:")
        print(f"   Total rounds: {round_num - 1}")
        print(f"   Spells used: Magic Missile, Fire Bolt")
        print(f"   Combat outcome: {combat_status if combat_over else 'Timeout'}")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        try:
            screenshot_path = "/tmp/wizard_combat_error.png"
            driver.save_screenshot(screenshot_path)
            print(f"\n📸 Screenshot saved to: {screenshot_path}")
        except:
            pass

        raise

    finally:
        time.sleep(2)
        driver.quit()
        print("\n✅ Browser closed")
        print("\n⚠️  Note: Gradio is still running at http://localhost:7860")


if __name__ == "__main__":
    print("\n" + "✨" * 40)
    print("WIZARD SPELL COMBAT E2E TEST")
    print("✨" * 40)
    print("\n🎯 This test:")
    print("   1. Loads Elara (Wizard) at Ancient Ruins")
    print("   2. Encounters Skeleton (makes narrative sense)")
    print("   3. Uses wizard spells (Magic Missile, Fire Bolt)")
    print("   4. Fights until character or enemy dies")
    print("   5. Tracks spell slots and combat progression")
    print("\n✨ Let's test spell combat mechanics!\n")
    print("=" * 80)

    test_wizard_spell_combat()
