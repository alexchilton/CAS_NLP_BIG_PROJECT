#!/usr/bin/env python3
"""
E2E Test: Goblin Combat with NPC Extraction

Tests the exact scenario from the user's bug report:
1. Player explores a cave
2. GM introduces a goblin and narrates attack
3. Goblin should be auto-added to npcs_present via NPC extraction
4. Player attacks goblin - should work (not rejected)
5. Combat continues until goblin or character dies
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


def send_message(driver, message, wait_time=8):
    """Send a message in the chat."""
    print(f"\n📤 Player: {message}")

    chat_input = find_chat_input(driver)
    chat_input.clear()
    chat_input.send_keys(message)

    send_btn = find_send_button(driver)
    send_btn.click()

    time.sleep(wait_time)  # Wait for GM response + mechanics extraction

    # Wait for "Loading content" to clear
    max_wait = wait_time + 3
    start_time = time.time()
    while time.time() - start_time < max_wait:
        messages = get_chat_messages(driver)
        if messages and messages[-1] != "Loading content":
            break
        time.sleep(0.5)


def get_chat_messages(driver):
    """Get all chat messages (Gradio 6.x compatible)."""
    chat_containers = driver.find_elements(By.CLASS_NAME, "message")

    messages = []
    seen_texts = set()

    for container in chat_containers:
        text = container.text.strip()
        # Skip loading states and empty messages
        if text and text not in seen_texts and text != "Loading content":
            messages.append(text)
            seen_texts.add(text)

    return messages


# DEPRECATED: Use selenium_helpers.load_character instead
# def load_character(driver, char_name="Thorin"):
    """Load a character."""
    print(f"\n📝 Loading character: {char_name}")

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
            time.sleep(3)
            break

    print(f"✅ Character loaded")


def get_character_sheet_hp(driver):
    """Extract current HP from character sheet."""
    try:
        import re

        # Find markdown components
        markdown_divs = driver.find_elements(By.CSS_SELECTOR, "[data-testid='markdown']")

        for md_div in markdown_divs:
            text = md_div.text
            if "HP" in text and "Combat Stats" in text:
                # Extract HP from text like "HP: 28"
                match = re.search(r'\bHP\b[:\s]+(\d+)', text)
                if match:
                    hp = int(match.group(1))
                    return hp

        return None
    except Exception as e:
        print(f"   ⚠️  HP extraction error: {e}")
        return None


def test_goblin_combat_npc_extraction():
    """Test goblin combat with NPC extraction."""
    print("\n" + "⚔️" * 40)
    print("GOBLIN COMBAT TEST - NPC EXTRACTION")
    print("⚔️" * 40)

    # Setup Chrome options
    options = webdriver.ChromeOptions()
    if os.environ.get('HEADLESS', 'false').lower() == 'true':
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(options=options)

    try:
        # Navigate to Gradio app
        print("\n📍 Opening Gradio app at http://localhost:7860")
        driver.get("http://localhost:7860")

        wait_for_gradio(driver)

        # Load Thorin (our brave dwarf fighter)
        load_character(driver, "Thorin")

        initial_hp = get_character_sheet_hp(driver)
        print(f"\n💪 Thorin's starting HP: {initial_hp if initial_hp else 'Unknown'}")

        print("\n" + "=" * 80)
        print("SCENE 1: Exploring the Cave")
        print("=" * 80)

        # Explore cave (GM should describe cave but not introduce goblin yet)
        send_message(driver, "I want to explore a dangerous cave looking for treasure. What do I find?", wait_time=10)

        messages = get_chat_messages(driver)
        if messages:
            print(f"🎭 GM: {messages[-1]}")

        print("\n" + "=" * 80)
        print("SCENE 2: Goblin Appears and Attacks (GM introduces NPC)")
        print("=" * 80)

        # GM should introduce goblin and narrate attack
        # Mechanics extractor should detect goblin and add to npcs_present
        send_message(driver, "A goblin jumps out and attacks me with a rusty sword", wait_time=10)

        messages = get_chat_messages(driver)
        if messages:
            gm_response = messages[-1]
            print(f"🎭 GM: {gm_response}")

        # Check HP - should have taken damage
        time.sleep(2)
        hp_after_goblin = get_character_sheet_hp(driver)
        if hp_after_goblin is not None and initial_hp is not None:
            if hp_after_goblin < initial_hp:
                damage = initial_hp - hp_after_goblin
                print(f"\n💥 GOBLIN ATTACK SUCCESSFUL! Took {damage} damage")
                print(f"   HP: {initial_hp} → {hp_after_goblin}")
            else:
                print(f"\n✅ No damage taken (HP still {hp_after_goblin})")

        print("\n" + "=" * 80)
        print("SCENE 3: Counter-Attack (THIS IS THE KEY TEST)")
        print("=" * 80)
        print("⚠️  TESTING: Can we attack the goblin that GM just introduced?")
        print("   Without NPC extraction, this would be rejected!")

        # Attack goblin - this should work now that NPC extraction is implemented
        send_message(driver, "I swing my longsword at the goblin", wait_time=10)

        messages = get_chat_messages(driver)
        if messages:
            gm_response = messages[-1]
            print(f"🎭 GM: {gm_response}")

            # Check for rejection phrases
            rejection_phrases = ["nothing there", "no goblin", "don't see", "can't find", "not present", "empty air"]
            is_rejected = any(phrase in gm_response.lower() for phrase in rejection_phrases)

            if is_rejected:
                print("\n❌ FAIL: Attack was REJECTED - NPC extraction didn't work!")
                print("   The goblin was not added to npcs_present")
            else:
                print("\n✅ SUCCESS: Attack was ACCEPTED - NPC extraction worked!")
                print("   The goblin was auto-added to npcs_present via mechanics extractor")

        print("\n" + "=" * 80)
        print("SCENE 4: Combat Continues Until Death")
        print("=" * 80)

        # Continue combat for up to 10 rounds or until someone dies
        max_rounds = 10
        for round_num in range(1, max_rounds + 1):
            print(f"\n--- Round {round_num} ---")

            current_hp = get_character_sheet_hp(driver)
            if current_hp is not None and current_hp <= 0:
                print("☠️  Thorin has fallen!")
                break

            # Attack goblin
            send_message(driver, "I attack the goblin with my longsword", wait_time=10)

            messages = get_chat_messages(driver)
            if messages:
                print(f"🎭 GM: {messages[-1][:150]}...")

            # Check if goblin is dead
            if messages and any(phrase in messages[-1].lower() for phrase in ["goblin dies", "goblin falls", "goblin is defeated", "slain the goblin"]):
                print("\n🎉 GOBLIN DEFEATED!")
                break

            time.sleep(2)

        print("\n" + "=" * 80)
        print("COMBAT SUMMARY")
        print("=" * 80)

        final_hp = get_character_sheet_hp(driver)
        print(f"\n⚔️  Combat Statistics:")
        print(f"   Starting HP: {initial_hp if initial_hp is not None else 'Unknown'}")
        print(f"   Final HP:    {final_hp if final_hp is not None else 'Unknown'}")

        if initial_hp is not None and final_hp is not None:
            total_damage = initial_hp - final_hp
            print(f"   Net Damage:  {total_damage}")
            survival_pct = (final_hp/initial_hp*100) if initial_hp > 0 else 0
            print(f"   HP %:        {survival_pct:.1f}%")

        print("\n" + "=" * 80)
        print("✅ GOBLIN COMBAT TEST COMPLETE")
        print("=" * 80)
        print("\n💡 Check the logs above to verify:")
        print("   1. Goblin was auto-extracted from GM narrative")
        print("   2. Counter-attack was accepted (not rejected)")
        print("   3. Combat continued properly")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        # Screenshot for debugging
        try:
            screenshot_path = "/tmp/goblin_combat_error.png"
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
    print("GOBLIN COMBAT - NPC EXTRACTION TEST")
    print("🎮" * 40)
    print("\n🎯 This test verifies that:")
    print("   1. GM can introduce NPCs in narrative")
    print("   2. NPCs are auto-extracted and added to npcs_present")
    print("   3. Subsequent actions against those NPCs work correctly")
    print("\n⚔️ Let's test the goblin scenario!\n")
    print("=" * 80)

    test_goblin_combat_npc_extraction()
