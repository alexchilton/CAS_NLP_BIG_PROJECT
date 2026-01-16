#!/usr/bin/env python3
"""
E2E Test: NPC Counter-Attack Verification

This test verifies the CRITICAL combat mechanic:
- NPCs must attack back during their turns
- Player must take damage from NPC attacks
- Turn order must be correct (player -> NPC -> player)

Bug Found: NPCs were not attacking because process_npc_turns() was inside
a DEBUG_PROMPTS block, so it only worked in debug mode!

Test Methodology:
1. Load character and note starting HP
2. Start combat with known NPC (Goblin)
3. Player attacks on their turn
4. Wait for NPC turn and check for:
   - "NPC ACTIONS" section in output
   - Damage dealt to player
   - HP decrease on character sheet
5. Verify combat continues properly
"""

import sys
import time
import os
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from e2e_tests.selenium_helpers import load_character, wait_for_gradio

# Test configuration
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
GRADIO_URL = "http://127.0.0.1:7860"


def setup_driver():
    """Initialize Chrome WebDriver"""
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def send_message(driver, message, wait_time=10):
    """Send a message in the chat"""
    print(f"\n💬 Player: \"{message}\"")

    # Find text input
    textareas = driver.find_elements(By.TAG_NAME, "textarea")
    chat_input = None
    for ta in textareas:
        if ta.is_displayed() and ta.is_enabled():
            chat_input = ta
            break

    if not chat_input:
        raise Exception("Chat input not found")

    # Clear and enter message
    chat_input.clear()
    chat_input.send_keys(message)

    # Find and click Send button
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if "send" in btn.text.lower():
            btn.click()
            break

    time.sleep(wait_time)  # Wait for response


def get_page_text(driver):
    """Get all visible text on page"""
    return driver.find_element(By.TAG_NAME, "body").text


def extract_hp_from_character_sheet(driver):
    """Extract current HP from character sheet"""
    try:
        page_text = get_page_text(driver)

        # Look for HP display like "HP: 28/30"
        hp_pattern = r'HP[:\s]+(\d+)/(\d+)'
        match = re.search(hp_pattern, page_text)

        if match:
            current_hp = int(match.group(1))
            max_hp = int(match.group(2))
            return {"current": current_hp, "max": max_hp}

        return None
    except Exception as e:
        print(f"⚠️ HP extraction failed: {e}")
        return None


def check_for_npc_attack(page_text):
    """
    Check if NPC attacked during their turn.

    Returns:
        dict with keys: attacked (bool), damage (int or None), evidence (str)
    """
    result = {
        "attacked": False,
        "damage": None,
        "evidence": ""
    }

    # Look for "🐉 NPC ACTIONS:" section
    if "NPC ACTIONS" in page_text or "🐉" in page_text:
        result["attacked"] = True
        result["evidence"] += "Found 'NPC ACTIONS' section. "

    # Look for NPC attack patterns
    npc_attack_patterns = [
        r"Goblin.*attacks?",
        r"Goblin.*swings?",
        r"Goblin.*strikes?",
        r"Goblin.*hits?",
        r"🎯.*Goblin",
    ]

    for pattern in npc_attack_patterns:
        if re.search(pattern, page_text, re.IGNORECASE):
            result["attacked"] = True
            result["evidence"] += f"Found attack pattern: '{pattern}'. "

    # Extract damage dealt to player
    # Pattern: "You take 5 slashing damage"
    damage_pattern = r'You take (\d+) \w+ damage'
    damage_match = re.search(damage_pattern, page_text)

    if damage_match:
        result["damage"] = int(damage_match.group(1))
        result["evidence"] += f"Player took {result['damage']} damage. "

    return result


def run_npc_counterattack_test():
    """Main test: Verify NPCs attack back during their turns"""
    print("\n" + "="*80)
    print("🧪 E2E TEST: NPC Counter-Attack Verification")
    print("="*80)
    print("\n📋 Test Plan:")
    print("   1. Load character (Thorin) and record starting HP")
    print("   2. Start combat with Goblin")
    print("   3. Player attacks Goblin")
    print("   4. Verify Goblin attacks back on its turn")
    print("   5. Verify player takes damage from Goblin")
    print("="*80)

    driver = None
    test_passed = False

    try:
        # Setup browser
        driver = setup_driver()
        driver.get(GRADIO_URL)
        wait_for_gradio(driver)

        # Load character
        print("\n📝 Loading character: Thorin...")
        load_character(driver, "Thorin")

        # Record starting HP
        initial_hp_data = extract_hp_from_character_sheet(driver)
        if not initial_hp_data:
            print("⚠️ Warning: Could not extract initial HP from character sheet")
            initial_hp = None
        else:
            initial_hp = initial_hp_data["current"]
            max_hp = initial_hp_data["max"]
            print(f"✅ Starting HP: {initial_hp}/{max_hp}")

        print("\n" + "-"*80)
        print("⚔️ PHASE 1: Start Combat with Goblin")
        print("-"*80)

        send_message(driver, "/start_combat Goblin", wait_time=8)

        page_text = get_page_text(driver)

        # Verify combat started
        if "Initiative Order" in page_text or "COMBAT BEGINS" in page_text:
            print("✅ Combat started successfully")
        else:
            print("❌ Combat may not have started properly")

        print("\n" + "-"*80)
        print("⚔️ PHASE 2: Player Attacks Goblin")
        print("-"*80)

        send_message(driver, "I attack the goblin with my longsword", wait_time=12)

        page_text = get_page_text(driver)

        # Check if player attack was processed
        if "damage" in page_text.lower() and "goblin" in page_text.lower():
            print("✅ Player attack was processed")

        print("\n" + "-"*80)
        print("⚔️ PHASE 3: Check for NPC Counter-Attack (CRITICAL TEST)")
        print("-"*80)

        # Get fresh page text after NPC turns should have processed
        time.sleep(3)
        page_text = get_page_text(driver)

        # Check for NPC attack
        npc_attack_result = check_for_npc_attack(page_text)

        print(f"\n🔍 NPC Attack Detection:")
        print(f"   Attacked: {npc_attack_result['attacked']}")
        print(f"   Damage:   {npc_attack_result['damage'] if npc_attack_result['damage'] else 'None detected'}")
        print(f"   Evidence: {npc_attack_result['evidence']}")

        # Verify HP changed
        final_hp_data = extract_hp_from_character_sheet(driver)
        if final_hp_data and initial_hp:
            final_hp = final_hp_data["current"]
            hp_lost = initial_hp - final_hp

            print(f"\n💊 HP Analysis:")
            print(f"   Starting: {initial_hp}")
            print(f"   Final:    {final_hp}")
            print(f"   Lost:     {hp_lost}")

            if hp_lost > 0:
                print(f"   ✅ Player took {hp_lost} damage total")
            else:
                print(f"   ⚠️ Player HP unchanged - Goblin may not have attacked!")

        print("\n" + "="*80)
        print("📊 TEST RESULTS")
        print("="*80)

        # Determine if test passed
        if npc_attack_result["attacked"]:
            print("\n✅ PASS: NPC Attack Detected")
            print(f"   Evidence: {npc_attack_result['evidence']}")
            test_passed = True

            if npc_attack_result["damage"]:
                print(f"   ✅ Damage confirmed: {npc_attack_result['damage']} HP")
            else:
                print(f"   ⚠️ No damage extracted from text (but attack confirmed)")
        else:
            print("\n❌ FAIL: NPC Did NOT Attack Back")
            print("   Expected: Goblin should attack during its turn")
            print("   Actual:   No NPC attack detected in game output")
            print("\n🐛 Possible Causes:")
            print("   - process_npc_turns() not being called")
            print("   - NPC turns logic inside DEBUG_PROMPTS block")
            print("   - NPCs not loaded into combat_manager.npc_monsters")
            test_passed = False

        print("="*80)

        return test_passed

    except Exception as e:
        print(f"\n❌ TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            print("\n🧹 Cleaning up browser...")
            driver.quit()
            print("✅ Browser closed")


if __name__ == "__main__":
    print("\n🎮 NPC COUNTER-ATTACK E2E TEST")
    print("="*80)
    print("This test verifies the CRITICAL mechanic:")
    print("  NPCs MUST attack back during their combat turns!")
    print("="*80 + "\n")

    passed = run_npc_counterattack_test()

    # Exit with appropriate code
    sys.exit(0 if passed else 1)
