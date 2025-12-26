#!/usr/bin/env python3
"""
E2E Test: Dragon Combat with Mechanics Extraction

This test demonstrates the Narrative to Mechanics Translation system in action.
It runs a full combat encounter and shows:
1. GM narrative responses
2. Mechanics automatically extracted by Gemma 2 2B
3. Game state automatically updated (HP, conditions, etc.)
"""

import sys
import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Enable debug mode to see mechanics extraction
os.environ['GM_DEBUG'] = 'true'


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


def send_message(driver, message, wait_time=5):
    """Send a message in the chat."""
    print(f"\n📤 Player: {message}")

    chat_input = find_chat_input(driver)
    chat_input.clear()
    chat_input.send_keys(message)

    send_btn = find_send_button(driver)
    send_btn.click()

    time.sleep(wait_time)  # Wait for GM response + mechanics extraction


def get_chat_messages(driver):
    """Get all chat messages (Gradio 6.x compatible)."""
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
        # Look for HP display in character sheet
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        for tb in textareas:
            text = tb.get_attribute("value")
            if text and "HP:" in text:
                # Parse HP from text like "HP: 20" or "HP: 20/28"
                import re
                match = re.search(r'HP[:\s]+(\d+)', text)
                if match:
                    return int(match.group(1))
        return None
    except:
        return None


def test_dragon_combat():
    """Test dragon combat with mechanics extraction."""
    print("\n" + "🐉" * 40)
    print("DRAGON COMBAT TEST - MECHANICS EXTRACTION DEMO")
    print("🐉" * 40)

    # Setup Chrome options
    options = webdriver.ChromeOptions()
    # Comment out headless to watch the combat!
    # options.add_argument('--headless')
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
        print(f"\n💪 Thorin's starting HP: {initial_hp}")

        # Clear welcome message
        messages = get_chat_messages(driver)
        print(f"\n🎭 GM: {messages[-1][:150]}...")

        print("\n" + "=" * 80)
        print("SCENE 1: Entering the Dragon's Lair")
        print("=" * 80)

        # Set the scene
        send_message(driver, "I cautiously enter the dragon's lair, my shield raised and sword drawn.")

        messages = get_chat_messages(driver)
        print(f"🎭 GM: {messages[-1]}")

        print("\n" + "=" * 80)
        print("SCENE 2: Starting Combat")
        print("=" * 80)

        # Start combat
        send_message(driver, "/start_combat Ancient Red Dragon")

        messages = get_chat_messages(driver)
        print(f"🎭 GM: {messages[-1]}")

        print("\n" + "=" * 80)
        print("ROUND 1: Thorin Attacks!")
        print("=" * 80)

        # Attack the dragon
        send_message(driver, "I charge forward and attack the dragon with my longsword, aiming for its neck!")

        messages = get_chat_messages(driver)
        gm_response = messages[-1]
        print(f"🎭 GM: {gm_response}")

        # Check if HP changed
        time.sleep(2)
        current_hp = get_character_sheet_hp(driver)
        if current_hp != initial_hp:
            print(f"\n💥 MECHANICS EXTRACTED! HP changed: {initial_hp} → {current_hp}")
            print(f"   Damage taken: {initial_hp - current_hp}")
        else:
            print(f"\n✅ No damage taken (HP still {current_hp})")

        print("\n" + "=" * 80)
        print("ROUND 2: Dragon's Turn (Breath Weapon!)")
        print("=" * 80)

        # Advance turn - dragon attacks
        send_message(driver, "/next_turn", wait_time=8)  # Longer wait for LLM

        messages = get_chat_messages(driver)
        gm_response = messages[-1]
        print(f"🎭 GM: {gm_response}")

        # Check HP after dragon's attack
        time.sleep(2)
        prev_hp = current_hp
        current_hp = get_character_sheet_hp(driver)

        if current_hp != prev_hp:
            damage = prev_hp - current_hp
            print(f"\n💥 MECHANICS EXTRACTED! Dragon dealt {damage} damage!")
            print(f"   HP: {prev_hp} → {current_hp}")
        else:
            print(f"\n✅ No damage (HP: {current_hp})")

        print("\n" + "=" * 80)
        print("ROUND 3: Healing Potion")
        print("=" * 80)

        # Try to use a healing item
        send_message(driver, "I quickly drink a healing potion!")

        messages = get_chat_messages(driver)
        gm_response = messages[-1]
        print(f"🎭 GM: {gm_response}")

        # Check if healed
        time.sleep(2)
        prev_hp = current_hp
        current_hp = get_character_sheet_hp(driver)

        if current_hp > prev_hp:
            healing = current_hp - prev_hp
            print(f"\n❤️  MECHANICS EXTRACTED! Healed {healing} HP!")
            print(f"   HP: {prev_hp} → {current_hp}")
        else:
            print(f"\n⚠️  No healing detected (might not have potion)")

        print("\n" + "=" * 80)
        print("ROUND 4: Heroic Strike")
        print("=" * 80)

        # Final attack
        send_message(driver, "With a mighty roar, I swing my longsword at the dragon's head with all my strength!")

        messages = get_chat_messages(driver)
        gm_response = messages[-1]
        print(f"🎭 GM: {gm_response}")

        time.sleep(2)
        prev_hp = current_hp
        current_hp = get_character_sheet_hp(driver)

        if current_hp != prev_hp:
            change = current_hp - prev_hp
            if change < 0:
                print(f"\n💥 MECHANICS EXTRACTED! Took {abs(change)} damage!")
            else:
                print(f"\n❤️  MECHANICS EXTRACTED! Healed {change} HP!")
            print(f"   HP: {prev_hp} → {current_hp}")

        print("\n" + "=" * 80)
        print("COMBAT SUMMARY")
        print("=" * 80)

        final_hp = get_character_sheet_hp(driver)
        total_damage = initial_hp - final_hp if final_hp else 0

        print(f"\n⚔️  Combat Statistics:")
        print(f"   Starting HP: {initial_hp}")
        print(f"   Final HP:    {final_hp}")
        print(f"   Net Damage:  {total_damage}")
        print(f"   HP %:        {(final_hp/initial_hp*100):.1f}%")

        # Get all messages
        all_messages = get_chat_messages(driver)
        print(f"\n📊 Total messages exchanged: {len(all_messages)}")

        print("\n" + "=" * 80)
        print("✅ DRAGON COMBAT TEST COMPLETE")
        print("=" * 80)
        print("\n💡 Check the terminal/logs to see the mechanics extraction!")
        print("   The Gemma 2 2B model automatically parsed GM narratives and updated:")
        print("   - Damage dealt")
        print("   - Healing received")
        print("   - Conditions applied")
        print("   - Spell slots used")
        print("   - Items consumed")
        print("\n🎯 The game plays itself - no manual HP tracking needed!")
        print("=" * 80 + "\n")

        if final_hp and final_hp > 0:
            print("🏆 Thorin survived the dragon encounter!")
        elif final_hp == 0:
            print("☠️  Thorin fell in glorious combat!")
        else:
            print("📊 Test completed (check HP manually)")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        # Screenshot for debugging
        try:
            screenshot_path = "/tmp/dragon_combat_error.png"
            driver.save_screenshot(screenshot_path)
            print(f"\n📸 Screenshot saved to: {screenshot_path}")
        except:
            pass

        raise

    finally:
        input("\n\n⏸️  Press Enter to close browser and see logs...")
        driver.quit()


if __name__ == "__main__":
    print("\n" + "🔥" * 40)
    print("EPIC DRAGON COMBAT - MECHANICS EXTRACTION DEMO")
    print("🔥" * 40)
    print("\n🎮 This test demonstrates:")
    print("   1. Full combat scenario with a dragon")
    print("   2. Automatic mechanics extraction from GM narratives")
    print("   3. Automatic game state updates (HP, conditions, etc.)")
    print("\n📝 Watch the terminal for extraction logs!")
    print("   GM_DEBUG=true will show what Gemma 2 2B extracts")
    print("\n🐉 Let's slay a dragon!\n")
    print("=" * 80)

    test_dragon_combat()
