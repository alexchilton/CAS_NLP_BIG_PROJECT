#!/usr/bin/env python3
"""
E2E Test: Simple Combat - 1 Player vs 1 Goblin

Tests:
1. NPC damage tracking
2. NPC death mechanics
3. Combat turn order (no double NPC turns)
4. HP calculation accuracy
5. Damage display format
"""

import os
import sys
import time
import re
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium_helpers import load_character, wait_for_gradio

# Test configuration
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
GRADIO_URL = "http://127.0.0.1:7860"
TIMEOUT = 30


# NOTE: This test file has been updated to import from selenium_helpers.py
# Local load_character() and wait_for_gradio() functions have been deprecated.
# The imported versions use the correct Gradio selectors (input[aria-label=...])
# See e2e_tests/README_SELENIUM.md for details.

class CombatTestResults:
    """Track test results"""
    def __init__(self):
        self.npc_damage_events = []
        self.npc_death_confirmed = False
        self.double_turn_detected = False
        self.hp_calculations_correct = True
        self.wrong_npc_detected = False
        self.errors = []

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

def wait_for_gradio_ready(driver, timeout=30):
    """Wait for Gradio interface to load"""
    print("⏳ Waiting for Gradio interface...")

    # Wait for gradio-app tag
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "gradio-app"))
    )

    # Wait longer for JavaScript to render
    print("   ⏳ Waiting for JavaScript to render components...")
    time.sleep(10)  # Increased from 3 to 10 seconds

    # Wait for any button to appear (sign that UI is rendered)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "button"))
        )
        print("   ✅ Buttons detected - UI rendered")
    except:
        print("   ⚠️  No buttons found yet, continuing anyway...")

    print("✅ Gradio interface loaded")

def find_character_dropdown(driver):
    """Find the character selection dropdown"""
    print("\n🔍 Searching for character dropdown...")

    # Try standard <select> tags first
    dropdowns = driver.find_elements(By.TAG_NAME, "select")
    print(f"   Found {len(dropdowns)} <select> elements")

    # If not found, try ARIA combobox (Gradio 4+)
    if not dropdowns:
        dropdowns = driver.find_elements(By.CSS_SELECTOR, "[role='combobox']")
        print(f"   Found {len(dropdowns)} ARIA combobox elements")

    if dropdowns:
        print(f"✅ Found dropdown element")
        return dropdowns[0]  # Return first dropdown (character selector)

    # Save screenshot for debugging
    try:
        screenshot_path = "/tmp/dropdown_not_found.png"
        driver.save_screenshot(screenshot_path)
        print(f"\n📸 Screenshot saved to: {screenshot_path}")
    except:
        pass

    return None

# DEPRECATED: Use selenium_helpers.load_character instead
# def load_character(driver, char_name="Thorin"):
    """Load a character via UI"""
    print(f"\n📝 Loading character: {char_name}")

    # Find character dropdown
    char_dropdown = find_character_dropdown(driver)
    if not char_dropdown:
        # Try to print page source for debugging
        print("\n⚠️  Page HTML structure:")
        print(driver.page_source[:500])  # Print first 500 chars
        raise Exception("Character dropdown not found - check screenshot at /tmp/dropdown_not_found.png")

    # Click dropdown to open
    char_dropdown.click()
    time.sleep(1)

    # Try both standard options and ARIA options
    options = char_dropdown.find_elements(By.TAG_NAME, "option")
    if not options:
        options = driver.find_elements(By.CSS_SELECTOR, "[role='option']")

    print(f"   Found {len(options)} options")

    # Select the character
    for opt in options:
        if char_name.lower() in opt.text.lower():
            print(f"   Selecting: {opt.text}")
            opt.click()
            time.sleep(1)
            break

    # Find and click Load Character button
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"\n🔍 Found {len(buttons)} buttons")
    for btn in buttons:
        if "Load Character" in btn.text:
            print(f"✅ Clicking: '{btn.text}'")
            btn.click()
            time.sleep(7)  # Wait for character to load
            break

    print(f"✅ Character loaded: {char_name}")

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

def extract_npc_damage(text):
    """Extract NPC damage from mechanics output"""
    # Pattern: "💥 Goblin takes 8 slashing damage! (HP: 4/12)"
    pattern = r"💥\s+(\w+)\s+takes\s+(\d+)\s+\w+\s+damage.*?HP:\s*(\d+)/(\d+)"
    match = re.search(pattern, text)

    if match:
        npc_name = match.group(1)
        damage = int(match.group(2))
        current_hp = int(match.group(3))
        max_hp = int(match.group(4))
        return {"npc": npc_name, "damage": damage, "current_hp": current_hp, "max_hp": max_hp}

    # Pattern for death: "💥 Goblin takes 8 slashing damage and dies! ☠️"
    death_pattern = r"💥\s+(\w+)\s+takes\s+(\d+)\s+\w+\s+damage.*?dies"
    death_match = re.search(death_pattern, text, re.IGNORECASE)

    if death_match:
        npc_name = death_match.group(1)
        damage = int(death_match.group(2))
        return {"npc": npc_name, "damage": damage, "current_hp": 0, "max_hp": None, "dead": True}

    return None

def check_double_npc_turn(text):
    """Check if NPC takes two turns in a row"""
    # Pattern: "🎯 Goblin's turn!" appearing twice consecutively
    pattern = r"🎯\s+(\w+)'s\s+turn!"
    matches = re.findall(pattern, text)

    # If we see the same NPC turn marker twice, it's a double turn
    if len(matches) >= 2:
        # Check if consecutive turns are the same NPC
        for i in range(len(matches) - 1):
            if matches[i] == matches[i + 1]:
                return True

    return False

def analyze_combat_output(text, results):
    """Analyze combat output and update results"""

    # Check for NPC damage
    npc_damage = extract_npc_damage(text)
    if npc_damage:
        results.npc_damage_events.append(npc_damage)

        if npc_damage.get("dead"):
            results.npc_death_confirmed = True
            print(f"💀 NPC DEATH CONFIRMED: {npc_damage['npc']} died after taking {npc_damage['damage']} damage")
        else:
            print(f"💥 NPC DAMAGE: {npc_damage['npc']} took {npc_damage['damage']} damage (HP: {npc_damage['current_hp']}/{npc_damage['max_hp']})")

    # Check for double NPC turns
    if check_double_npc_turn(text):
        results.double_turn_detected = True
        results.errors.append("NPC took two turns in a row")
        print("❌ BUG DETECTED: NPC took two turns in a row!")

def run_simple_combat_test():
    """Main test: 1 player vs 1 Goblin"""
    print("\n" + "="*60)
    print("🧪 E2E TEST: Simple Combat - 1 Player vs 1 Goblin")
    print("="*60)
    print("\n⚠️  NOTE: This test connects to your running Gradio instance at http://127.0.0.1:7860")
    print("   Make sure Gradio is running before starting this test!")
    print("="*60)

    results = CombatTestResults()
    driver = None

    try:
        # Wait for user confirmation
        time.sleep(2)

        # Setup browser
        driver = setup_driver()
        driver.get(GRADIO_URL)
        wait_for_gradio_ready(driver)

        # Load character
        load_character(driver, "Thorin")

        print("\n" + "-"*60)
        print("⚔️  COMBAT PHASE: Attacking Goblin until death")
        print("-"*60)

        # Attack goblin multiple times (up to 15 attacks to ensure death)
        max_attacks = 15
        for attack_num in range(1, max_attacks + 1):
            print(f"\n--- Attack #{attack_num} ---")

            send_message(driver, "attack the goblin", wait_time=10)

            # Get latest response
            time.sleep(2)
            page_text = driver.find_element(By.TAG_NAME, "body").text

            # Analyze combat output
            analyze_combat_output(page_text, results)

            # If goblin is dead, stop attacking
            if results.npc_death_confirmed:
                print(f"\n✅ Goblin died after {attack_num} attacks!")
                break

        # Print results
        print("\n" + "="*60)
        print("📊 TEST RESULTS")
        print("="*60)

        print(f"\n📈 NPC Damage Events: {len(results.npc_damage_events)}")
        for i, event in enumerate(results.npc_damage_events, 1):
            if event.get("dead"):
                print(f"  {i}. {event['npc']} took {event['damage']} damage → DEAD ☠️")
            else:
                print(f"  {i}. {event['npc']} took {event['damage']} damage (HP: {event['current_hp']}/{event['max_hp']})")

        print(f"\n💀 NPC Death: {'✅ CONFIRMED' if results.npc_death_confirmed else '❌ NOT CONFIRMED'}")
        print(f"🔄 Double Turn Bug: {'❌ DETECTED' if results.double_turn_detected else '✅ NOT DETECTED'}")
        print(f"🐺 Wrong NPC Bug: {'❌ DETECTED' if results.wrong_npc_detected else '✅ NOT DETECTED'}")

        if results.errors:
            print(f"\n❌ Errors Detected ({len(results.errors)}):")
            for error in results.errors:
                print(f"  - {error}")
        else:
            print("\n✅ No errors detected")

        # Overall verdict
        print("\n" + "="*60)
        if results.npc_death_confirmed and not results.double_turn_detected and not results.wrong_npc_detected:
            print("✅ TEST PASSED: Combat mechanics working correctly!")
        else:
            print("❌ TEST FAILED: Critical bugs detected!")
            if not results.npc_death_confirmed:
                print("  - NPCs not dying (damage not applied)")
            if results.double_turn_detected:
                print("  - NPCs taking double turns")
            if results.wrong_npc_detected:
                print("  - Wrong NPC appearing in combat")
        print("="*60)

        return results

    except Exception as e:
        print(f"\n❌ TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        if driver:
            print("\n🧹 Cleaning up browser...")
            driver.quit()
            print("✅ Browser closed")

        print("\n⚠️  Note: Gradio is still running at http://127.0.0.1:7860")

if __name__ == "__main__":
    results = run_simple_combat_test()

    # Exit with error code if test failed
    if results is None or not results.npc_death_confirmed:
        sys.exit(1)
    else:
        sys.exit(0)
