#!/usr/bin/env python3
"""
E2E Test: Hallucination Bug from TODO.md

This test reproduces the bug described in TODO.md:
"So i start and try and cast magic missile at the goblin- there is no goblin 
but...then it goes into combat with a dragon who appears from nowhere"

Expected behavior:
1. Load Elara Moonwhisper character
2. Start in Adventurer's Guild Hall (no enemies present)
3. Player: "I cast Magic Missile at the goblin"
4. GM should REJECT this action (no goblin present)
5. NO combat should start
6. NO dragon should appear
7. NO other characters (like Thorin) should appear

Actual behavior (bug):
- GM hallucinates goblin death
- Dragon appears from nowhere
- Combat starts
- Thorin appears (wasn't loaded!)
"""

import sys
import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium_helpers import load_character, wait_for_gradio

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
GRADIO_URL = "http://localhost:7860"
HEADLESS = False
TIMEOUT = 30



# NOTE: This test file has been updated to import from selenium_helpers.py
# Local load_character() and wait_for_gradio() functions have been deprecated.
# The imported versions use the correct Gradio selectors (input[aria-label=...])
# See e2e_tests/README_SELENIUM.md for details.

def create_driver(headless=False):
    """Create Chrome WebDriver with options."""
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ Failed to create Chrome driver: {e}")
        print("\nPlease install chromedriver:")
        print("  macOS: brew install chromedriver")
        sys.exit(1)


# DEPRECATED: Use selenium_helpers.wait_for_gradio instead
# def wait_for_gradio(driver, timeout=30):
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
    max_wait = wait_time + 5
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
# def load_character(driver, char_name="Elara"):
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


def check_for_combat_ui(driver):
    """Check if combat UI is present."""
    # Look for combat indicators
    page_text = driver.find_element(By.TAG_NAME, "body").text
    
    combat_indicators = [
        "Initiative Tracker",
        "Combat Round",
        "Initiative Order:",
        "'s turn!"
    ]
    
    for indicator in combat_indicators:
        if indicator in page_text:
            return True
    
    return False


def check_for_entity(driver, entity_name):
    """Check if an entity name appears in the page."""
    page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    return entity_name.lower() in page_text


def main():
    """Run the hallucination bug test."""
    print("=" * 80)
    print("HALLUCINATION BUG TEST (from TODO.md)")
    print("=" * 80)
    print("\nThis test reproduces the bug where:")
    print("1. Player attacks non-existent goblin")
    print("2. GM hallucinates goblin death")
    print("3. Dragon appears from nowhere")
    print("4. Combat starts unexpectedly")
    print("5. Other characters appear (Thorin)")
    
    driver = create_driver(headless=HEADLESS)
    
    try:
        # Navigate to Gradio
        print(f"\n🌐 Navigating to {GRADIO_URL}")
        driver.get(GRADIO_URL)
        wait_for_gradio(driver)
        
        # Load Elara character
        load_character(driver, "Elara")
        
        # Get initial state
        messages_before = get_chat_messages(driver)
        print(f"\n📜 Initial messages count: {len(messages_before)}")
        
        # Verify starting location (should mention Guild Hall)
        page_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"\n🏛️ Starting location check:")
        if "Adventurer's Guild Hall" in page_text or "Guild" in page_text:
            print("   ✅ Started in Guild Hall")
        else:
            print("   ⚠️  Unknown starting location")
        
        # Check no combat initially
        print(f"\n⚔️ Pre-action combat state:")
        if not check_for_combat_ui(driver):
            print("   ✅ No combat active (expected)")
        else:
            print("   ❌ Combat already active (BUG!)")
        
        # THE BUG: Try to cast Magic Missile at non-existent goblin
        print("\n" + "=" * 80)
        print("🔴 TESTING THE BUG: Cast spell at non-existent goblin")
        print("=" * 80)
        send_message(driver, "I cast Magic Missile at the goblin", wait_time=10)
        
        # Get response
        messages_after = get_chat_messages(driver)
        new_messages = messages_after[len(messages_before):]
        
        print(f"\n📩 GM Response:")
        for msg in new_messages:
            print(f"   {msg[:200]}...")
        
        # Check for hallucination indicators
        print("\n🔍 Checking for hallucination bugs:")
        
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # Check 1: Did goblin appear/die?
        if "goblin" in page_text.lower() and ("falls" in page_text.lower() or "dead" in page_text.lower() or "dies" in page_text.lower()):
            print("   ❌ BUG: Goblin death hallucinated (goblin doesn't exist!)")
            bug_found = True
        else:
            print("   ✅ PASS: No goblin death hallucination")
            bug_found = False
        
        # Check 2: Did dragon appear?
        if check_for_entity(driver, "dragon"):
            print("   ❌ BUG: Dragon appeared from nowhere!")
            bug_found = True
        else:
            print("   ✅ PASS: No dragon hallucination")
        
        # Check 3: Did combat start?
        if check_for_combat_ui(driver):
            print("   ❌ BUG: Combat started unexpectedly!")
            bug_found = True
        else:
            print("   ✅ PASS: No unexpected combat")
        
        # Check 4: Did Thorin appear?
        if check_for_entity(driver, "thorin"):
            print("   ❌ BUG: Thorin appeared (wasn't loaded!)")
            bug_found = True
        else:
            print("   ✅ PASS: No Thorin hallucination")
        
        # Check 5: Was action properly rejected?
        rejection_phrases = [
            "no goblin",
            "not present",
            "don't see",
            "there isn't",
            "no such"
        ]
        
        response_text = " ".join(new_messages).lower()
        action_rejected = any(phrase in response_text for phrase in rejection_phrases)
        
        if action_rejected:
            print("   ✅ PASS: Action was properly rejected")
        else:
            print("   ❌ BUG: Action was NOT rejected (should have been invalid)")
            bug_found = True
        
        # Final verdict
        print("\n" + "=" * 80)
        if bug_found:
            print("❌ TEST FAILED: Hallucination bug reproduced!")
            print("=" * 80)
            print("\nThe Reality Check system failed to prevent:")
            print("  - Hallucinated entities (goblin, dragon, Thorin)")
            print("  - Invalid action acceptance")
            print("  - Unexpected combat start")
            return 1
        else:
            print("✅ TEST PASSED: No hallucinations detected!")
            print("=" * 80)
            print("\nThe Reality Check system correctly:")
            print("  - Rejected invalid action (no goblin present)")
            print("  - Prevented entity hallucination")
            print("  - Prevented unexpected combat")
            return 0
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print("\n🔚 Closing browser...")
        time.sleep(2)
        driver.quit()


if __name__ == "__main__":
    sys.exit(main())
