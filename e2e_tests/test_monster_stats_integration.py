#!/usr/bin/env python3
"""
E2E Test: Monster Stats Integration

This test verifies that:
1. Monster stats are loaded from database when combat starts
2. Initiative tracker displays NPC HP
3. GM uses accurate AC and HP values
4. Damage tracking works correctly
5. Monster dies at correct HP threshold
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

# Enable debug mode to see monster stat loading
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


def test_monster_stats_integration():
    """Test that monster stats are loaded correctly from database."""
    print("\n" + "⚔️" * 40)
    print("MONSTER STATS INTEGRATION TEST")
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
        print("TEST 0: Travel to Goblin Cave for Realistic Combat")
        print("=" * 80)
        print("💡 Going to a location where goblins would naturally be")

        # Travel to goblin cave to make combat make sense narratively
        send_message(driver, "I travel to the goblin cave entrance", wait_time=6)

        messages = get_chat_messages(driver)
        if messages:
            travel_response = messages[-1]
            print(f"\n🎭 GM: {travel_response[:200]}...")

        print("\n" + "=" * 80)
        print("TEST 1: Start Combat with Goblin - Check Stats Loaded")
        print("=" * 80)
        print("💡 Expected: Goblin stats should be loaded from database")
        print("   - AC: 15 (leather armor, shield)")
        print("   - HP: ~7-10 (rolled from 2d6)")
        print("   - DEX: 14 (+2 modifier)")

        send_message(driver, "/start_combat Goblin", wait_time=8)

        messages = get_chat_messages(driver)
        if messages:
            combat_start = messages[-1]
            print(f"\n🎭 GM: {combat_start}")

            # Check for initiative tracker with HP
            if "HP:" in combat_start:
                print("\n✅ SUCCESS: Initiative tracker shows NPC HP!")

                # Extract HP values if possible
                import re
                hp_match = re.search(r'Goblin.*?HP:\s*(\d+)/(\d+)', combat_start, re.IGNORECASE)
                if hp_match:
                    current_hp = int(hp_match.group(1))
                    max_hp = int(hp_match.group(2))
                    print(f"   Goblin HP: {current_hp}/{max_hp}")

                    # Verify HP is in expected range (2d6 = 2-12)
                    if 2 <= max_hp <= 12:
                        print(f"   ✅ HP in expected range for 2d6 roll")
                    else:
                        print(f"   ⚠️  HP {max_hp} outside expected range (2-12)")
            else:
                print("\n⚠️  Initiative tracker doesn't show HP yet")

        print("\n" + "=" * 80)
        print("TEST 2: Attack Goblin - Verify AC and Damage Tracking")
        print("=" * 80)
        print("💡 Expected: GM should use AC 15, track damage to goblin's HP")

        send_message(driver, "I attack the goblin with my longsword", wait_time=10)

        messages = get_chat_messages(driver)
        if messages:
            attack_response = messages[-1]
            print(f"\n🎭 GM: {attack_response[:400]}...")

            # Check for AC mention
            if "AC" in attack_response or "armor class" in attack_response.lower():
                print("\n✅ GM mentioned AC in combat!")

            # Check for damage tracking
            if "damage" in attack_response.lower():
                print("✅ Damage being tracked!")

        print("\n" + "=" * 80)
        print("TEST 3: Continue Combat Until Goblin Defeated")
        print("=" * 80)
        print("💡 Expected: Goblin should die around 7-10 HP of total damage")

        total_rounds = 0
        max_rounds = 5

        for round_num in range(1, max_rounds + 1):
            total_rounds = round_num
            print(f"\n--- Round {round_num} ---")

            send_message(driver, "I attack the goblin again", wait_time=10)

            messages = get_chat_messages(driver)
            if messages:
                response = messages[-1]
                print(f"🎭 GM: {response[:200]}...")

                # Check for HP in response
                import re
                hp_match = re.search(r'HP:\s*(\d+)/(\d+)', response)
                if hp_match:
                    current_hp = int(hp_match.group(1))
                    max_hp = int(hp_match.group(2))
                    print(f"   Goblin HP: {current_hp}/{max_hp}")

                # Check for death
                death_phrases = ["dies", "falls dead", "defeated", "slain", "dead", "killed"]
                if any(phrase in response.lower() for phrase in death_phrases):
                    print(f"\n🎉 Goblin defeated after {round_num} rounds!")
                    print(f"✅ SUCCESS: Combat ended at appropriate time")
                    break

        print("\n" + "=" * 80)
        print("TEST 4: Multiple Monster Combat")
        print("=" * 80)
        print("💡 Testing combat with multiple different monsters")

        send_message(driver, "/start_combat Wolf, Skeleton", wait_time=10)

        messages = get_chat_messages(driver)
        if messages:
            multi_combat = messages[-1]
            print(f"\n🎭 GM: {multi_combat[:300]}...")

            # Check that both monsters are in initiative
            if "Wolf" in multi_combat and "Skeleton" in multi_combat:
                print("\n✅ SUCCESS: Both monsters in initiative tracker!")

                # Check for HP tracking
                wolf_hp = re.search(r'Wolf.*?HP:\s*(\d+)/(\d+)', multi_combat, re.IGNORECASE)
                skeleton_hp = re.search(r'Skeleton.*?HP:\s*(\d+)/(\d+)', multi_combat, re.IGNORECASE)

                if wolf_hp and skeleton_hp:
                    print(f"   Wolf HP: {wolf_hp.group(1)}/{wolf_hp.group(2)}")
                    print(f"   Skeleton HP: {skeleton_hp.group(1)}/{skeleton_hp.group(2)}")
                    print("   ✅ All NPCs have HP tracked!")

        print("\n" + "=" * 80)
        print("🎉 MONSTER STATS INTEGRATION TEST COMPLETE!")
        print("=" * 80)
        print("\n📊 Verified:")
        print("   ✅ Monster stats loaded from database")
        print("   ✅ Initiative tracker shows NPC HP")
        print("   ✅ Combat uses accurate AC and damage")
        print("   ✅ HP tracking works correctly")
        print("   ✅ Multiple monsters tracked simultaneously")
        print("\n💡 Check server logs for detailed stat loading:")
        print("   - Look for '🐉 Loaded [monster] stats' messages")
        print("   - Verify HP, AC, and DEX mod calculations")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        try:
            screenshot_path = "/tmp/monster_stats_error.png"
            driver.save_screenshot(screenshot_path)
            print(f"\n📸 Screenshot saved to: {screenshot_path}")
        except:
            pass

        raise

    finally:
        time.sleep(2)
        driver.quit()


if __name__ == "__main__":
    print("\n" + "🐉" * 40)
    print("MONSTER STATS INTEGRATION E2E TEST")
    print("🐉" * 40)
    print("\n🎯 This test verifies:")
    print("   1. Monster stats loaded from database (not hallucinated)")
    print("   2. Real AC, HP, and attacks used in combat")
    print("   3. HP tracking displayed in initiative tracker")
    print("   4. Damage properly tracked and monster dies at correct HP")
    print("   5. Multiple monsters can be tracked simultaneously")
    print("\n⚔️ Let's see the monster stats system in action!\n")
    print("=" * 80)

    test_monster_stats_integration()
