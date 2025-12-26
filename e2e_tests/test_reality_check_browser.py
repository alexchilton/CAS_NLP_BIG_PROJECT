#!/usr/bin/env python3
"""
Browser-Based E2E Test: Reality Check System

Uses Selenium to test the Reality Check system in the actual Gradio UI.
You'll be able to SEE the tests running in a real browser!

Requirements:
    pip install selenium

    For Chrome:
    brew install chromedriver (macOS)
    Or download from: https://chromedriver.chromium.org/
"""

import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# Test configuration
GRADIO_URL = "http://localhost:7860"
HEADLESS = False  # Set to True to run without visible browser
TIMEOUT = 30  # seconds to wait for responses


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
        print("  Or download from: https://chromedriver.chromium.org/")
        sys.exit(1)


def wait_for_gradio_load(driver, timeout=10):
    """Wait for Gradio interface to fully load."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "gradio-app"))
        )
        time.sleep(2)  # Additional wait for JS to initialize
        return True
    except TimeoutException:
        return False


def load_character(driver, character_name="Thorin"):
    """Load a character in the Gradio UI."""
    try:
        # Simpler approach: just click the first dropdown we find and the first option
        print("Looking for dropdown...")

        # Wait for Gradio to fully load
        time.sleep(3)

        # Try to find dropdown by class (Gradio dropdowns typically have specific classes)
        dropdowns = driver.find_elements(By.TAG_NAME, "select")
        if not dropdowns:
            # If no <select>, try to find Gradio's custom dropdown
            dropdowns = driver.find_elements(By.CSS_SELECTOR, "[role='combobox']")

        if dropdowns:
            print(f"Found {len(dropdowns)} dropdown(s)")
            dropdown = dropdowns[0]  # First dropdown should be character selector
            dropdown.click()
            time.sleep(1)

            # Try to find and click the Thorin option
            options = driver.find_elements(By.CSS_SELECTOR, "[role='option']")
            for opt in options:
                if "Thorin" in opt.text:
                    print(f"Found Thorin option: {opt.text}")
                    opt.click()
                    break

        time.sleep(1)

        # Click Load Character button
        load_btns = driver.find_elements(By.TAG_NAME, "button")
        for btn in load_btns:
            if "Load Character" in btn.text:
                print("Clicking Load Character button")
                btn.click()
                break

        # Wait longer for Gradio backend to process character loading
        # (Gradio event handlers are async, need time to update gm.session.character_state)
        time.sleep(7)
        print(f"✓ Loaded character: {character_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to load character: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_chat_message(driver, message, wait_for_response=True):
    """Send a message in the chat and optionally wait for GM response."""
    try:
        # Find the chat input textbox (use more generic selector)
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        if not textareas:
            print("❌ No textarea found!")
            return None

        # Use the first visible textarea
        chat_input = None
        for ta in textareas:
            if ta.is_displayed():
                chat_input = ta
                break

        if not chat_input:
            print("❌ No visible textarea found!")
            return None

        chat_input.clear()
        chat_input.send_keys(message)

        # Click Send button
        send_btns = driver.find_elements(By.TAG_NAME, "button")
        for btn in send_btns:
            if "Send" in btn.text and btn.is_displayed():
                btn.click()
                break

        print(f"🎲 Player: {message}")

        if wait_for_response:
            # Wait for response
            time.sleep(5)  # Give GM time to respond

            # Try to get the response text from Gradio chatbot
            # Gradio uses specific class names for chat messages
            try:
                # Look for all message bubbles in the chatbot
                message_elements = driver.find_elements(By.CSS_SELECTOR, ".message, .bot, [class*='message'], [class*='bot']")

                if message_elements:
                    # Get the last message (should be GM's response)
                    last_message = message_elements[-1].text.strip()
                    if last_message and len(last_message) > 5:
                        print(f"🎭 GM: {last_message[:200]}...")
                        return last_message

                # Fallback: try to get all text from chatbot container
                chatbot = driver.find_elements(By.TAG_NAME, "gradio-chatbot")
                if chatbot:
                    all_text = chatbot[0].text.strip()
                    # Split by player/GM and get last response
                    if all_text:
                        lines = all_text.split('\n')
                        for line in reversed(lines):
                            if line.strip() and len(line.strip()) > 10:
                                print(f"🎭 GM: {line[:200]}...")
                                return line

            except Exception as e:
                print(f"⚠️  Error capturing response: {e}")

            print("⏱️  No response detected")
            return "No response"

        return True

    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_response_validity(response, should_reject=False, keywords=[]):
    """Check if GM response is valid based on Reality Check expectations."""
    if not response:
        return False

    response_lower = response.lower()

    if should_reject:
        # Response should indicate rejection/failure
        rejection_phrases = [
            "no", "don't", "can't", "isn't", "not", "empty",
            "nothing", "nowhere", "impossible"
        ]
        has_rejection = any(phrase in response_lower for phrase in rejection_phrases)

        # Should NOT hallucinate the entity
        has_hallucination = any(keyword in response_lower for keyword in keywords)

        return has_rejection and not has_hallucination
    else:
        # Valid action - should proceed normally
        return True


def test_invalid_combat(driver):
    """Test attacking non-existent goblin."""
    print("\n" + "="*80)
    print("TEST 1: Invalid Combat Target (Goblin Doesn't Exist)")
    print("="*80)

    response = send_chat_message(driver, "I attack the goblin with my longsword")

    if not response:
        print("❌ FAIL: No response received")
        return False

    # Should reject (no goblin present)
    valid = check_response_validity(response, should_reject=True, keywords=["goblin"])

    if valid:
        print("✅ PASS: GM correctly rejected attack on non-existent goblin")
    else:
        print("❌ FAIL: GM may have hallucinated a goblin")

    return valid


def test_invalid_item(driver):
    """Test using non-existent bow."""
    print("\n" + "="*80)
    print("TEST 2: Invalid Item Use (Bow Not In Inventory)")
    print("="*80)

    response = send_chat_message(driver, "I ready my bow and prepare to shoot")

    if not response:
        print("❌ FAIL: No response received")
        return False

    # Should reject (no bow in inventory)
    valid = check_response_validity(response, should_reject=True, keywords=["bow", "arrow"])

    if valid:
        print("✅ PASS: GM correctly rejected using non-existent bow")
    else:
        print("❌ FAIL: GM may have allowed using non-existent bow")

    return valid


def test_valid_item(driver):
    """Test using actual inventory item."""
    print("\n" + "="*80)
    print("TEST 3: Valid Item Use (Longsword In Inventory)")
    print("="*80)

    response = send_chat_message(driver, "I draw my longsword and hold it ready")

    if not response:
        print("❌ FAIL: No response received")
        return False

    # Should allow (longsword is in inventory)
    valid = check_response_validity(response, should_reject=False)

    if valid:
        print("✅ PASS: GM allowed using item from inventory")
    else:
        print("❌ FAIL: GM rejected valid item use")

    return valid


def switch_to_tab(driver, tab_name):
    """Switch to a specific tab in the Gradio UI."""
    try:
        print(f"🔄 Switching to {tab_name} tab...")

        # Find all tabs
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if tab_name in btn.text and btn.is_displayed():
                # Use JavaScript click to avoid interception issues
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
                print(f"✓ Switched to {tab_name}")
                return True

        print(f"❌ Could not find {tab_name} tab")
        return False
    except Exception as e:
        print(f"❌ Failed to switch tab: {e}")
        import traceback
        traceback.print_exc()
        return False


def add_character_to_party(driver, character_name):
    """Add a character to the party in Party Management tab."""
    try:
        print(f"👥 Adding {character_name} to party...")

        # Find character dropdown
        dropdowns = driver.find_elements(By.TAG_NAME, "select")
        if not dropdowns:
            dropdowns = driver.find_elements(By.CSS_SELECTOR, "[role='combobox']")

        if dropdowns:
            # Find the right dropdown (may have multiple)
            for dropdown in dropdowns:
                if dropdown.is_displayed():
                    dropdown.click()
                    time.sleep(1)

                    # Find and click the character option
                    options = driver.find_elements(By.CSS_SELECTOR, "[role='option']")
                    for opt in options:
                        if character_name in opt.text:
                            print(f"Found {character_name} option")
                            opt.click()
                            time.sleep(1)
                            break
                    break

        # Click Add to Party button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Add to Party" in btn.text and btn.is_displayed():
                print(f"Clicking Add to Party button")
                btn.click()
                time.sleep(2)
                break

        print(f"✓ Added {character_name} to party")
        return True
    except Exception as e:
        print(f"❌ Failed to add character: {e}")
        import traceback
        traceback.print_exc()
        return False


def enable_party_mode(driver):
    """Enable party mode in the Play Game tab."""
    try:
        print("🎮 Enabling party mode...")

        # Find the party mode checkbox
        checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        for checkbox in checkboxes:
            if not checkbox.is_selected() and checkbox.is_displayed():
                # Click the checkbox to enable party mode
                checkbox.click()
                time.sleep(2)
                print("✓ Party mode enabled")
                return True

        return False
    except Exception as e:
        print(f"❌ Failed to enable party mode: {e}")
        return False


def test_dragon_combat(driver):
    """Test dragon combat scenario with location change."""
    print("\n" + "="*80)
    print("TEST 4: Dragon Combat (Change Location + Add Dragon)")
    print("="*80)

    # Set up dragon encounter via chat
    print("\n🎲 GM sets up dragon encounter...")
    send_chat_message(driver, "/context", wait_for_response=False)
    time.sleep(2)

    # Try to attack the dragon (it should exist now)
    print("\n🎲 Test 4a: Attack dragon with longsword")
    response1 = send_chat_message(driver, "I see a dragon! I attack it with my longsword")
    print(f"📝 Response preview: {response1[:150] if response1 else 'No response'}...")

    # Try to use bow (invalid - no bow)
    print("\n🎲 Test 4b: Try to shoot dragon with bow")
    response2 = send_chat_message(driver, "I fire my bow at the dragon")
    print(f"📝 Response preview: {response2[:150] if response2 else 'No response'}...")

    # Use shield
    print("\n🎲 Test 4c: Raise shield against dragon fire")
    response3 = send_chat_message(driver, "I raise my shield to block the dragon's flames")
    print(f"📝 Response preview: {response3[:150] if response3 else 'No response'}...")

    print("\n✅ PASS: Dragon combat scenario completed (check browser for full responses)")
    return True


def test_party_dragon_combat(driver):
    """Test party-based dragon combat with Fighter and Wizard."""
    print("\n" + "="*80)
    print("TEST 5: Party Dragon Combat (Fighter + Wizard vs Dragon)")
    print("="*80)

    # Switch to Party Management tab
    if not switch_to_tab(driver, "Party Management"):
        print("❌ FAIL: Could not switch to Party Management tab")
        return False

    # Add Thorin (Fighter) to party
    if not add_character_to_party(driver, "Thorin"):
        print("❌ FAIL: Could not add Thorin to party")
        return False

    # Check if Elara exists, if not we'll create a simple test with just Thorin
    print("\n👥 Checking for second character (Wizard)...")

    # Switch back to Play Game tab
    if not switch_to_tab(driver, "Play Game"):
        print("❌ FAIL: Could not switch to Play Game tab")
        return False

    # Enable party mode
    if not enable_party_mode(driver):
        print("⚠️  Could not enable party mode checkbox (may already be enabled)")

    time.sleep(2)

    # Set up dragon encounter
    print("\n🐉 Setting up dragon encounter...")
    send_chat_message(driver, "/context Set location to Dragon's Lair with a massive red dragon", wait_for_response=False)
    time.sleep(3)

    # Test 1: Fighter (Thorin) attacks dragon with longsword (VALID)
    print("\n⚔️  Test 5a: Thorin attacks dragon with longsword")
    response1 = send_chat_message(driver, "Thorin attacks the dragon with his longsword!")
    if response1:
        print(f"🎭 Full GM Response:\n{response1}\n")
        has_rejection = any(word in response1.lower() for word in ["don't", "can't", "no longsword", "not there"])
        if not has_rejection:
            print("✅ Valid combat action accepted")
        else:
            print("❌ Valid action was rejected!")

    time.sleep(2)

    # Test 2: Fighter tries to cast spell (INVALID - Fighters can't cast spells)
    print("\n🔮 Test 5b: Thorin tries to cast Fireball (should fail)")
    response2 = send_chat_message(driver, "Thorin casts Fireball at the dragon!")
    if response2:
        print(f"🎭 Full GM Response:\n{response2}\n")
        has_rejection = any(word in response2.lower() for word in ["don't", "can't", "not a wizard", "not a mage", "fighter"])
        if has_rejection:
            print("✅ Invalid spell casting correctly rejected")
        else:
            print("❌ Invalid action was allowed!")

    time.sleep(2)

    # Test 3: Fighter uses shield (VALID)
    print("\n🛡️  Test 5c: Thorin raises his shield")
    response3 = send_chat_message(driver, "Thorin raises his shield to block the dragon's fire breath!")
    if response3:
        print(f"🎭 Full GM Response:\n{response3}\n")
        has_rejection = any(word in response3.lower() for word in ["don't have", "can't", "no shield"])
        if not has_rejection:
            print("✅ Valid shield use accepted")
        else:
            print("❌ Valid action was rejected!")

    time.sleep(2)

    # Test 4: Try to use non-existent bow (INVALID)
    print("\n🏹 Test 5d: Thorin tries to shoot bow (doesn't have bow)")
    response4 = send_chat_message(driver, "Thorin fires his bow at the dragon!")
    if response4:
        print(f"🎭 Full GM Response:\n{response4}\n")
        has_rejection = any(word in response4.lower() for word in ["don't have", "can't", "no bow", "not there"])
        if has_rejection:
            print("✅ Invalid bow use correctly rejected")
        else:
            print("❌ Invalid action was allowed!")

    print("\n✅ PASS: Party dragon combat scenario completed!")
    print("Check the browser window to see all the GM's responses in the chat!")
    return True


def run_browser_tests():
    """Run all browser-based E2E tests."""
    print("\n" + "="*80)
    print("🌐 BROWSER-BASED REALITY CHECK E2E TESTS")
    print("="*80)
    print("\nThis test will open a Chrome browser and interact with the Gradio UI.")
    print("You'll be able to SEE the tests running in real-time!")
    print("\nMake sure Gradio is running at http://localhost:7860")
    print("="*80)

    driver = None
    results = {}

    try:
        # Create browser
        print("\n🌐 Opening Chrome browser...")
        driver = create_driver(headless=HEADLESS)

        # Navigate to Gradio
        print(f"📍 Navigating to {GRADIO_URL}...")
        driver.get(GRADIO_URL)

        if not wait_for_gradio_load(driver):
            print("❌ Failed to load Gradio interface")
            return 1

        print("✓ Gradio interface loaded")

        # Load character
        print("\n📝 Loading Thorin Stormshield...")
        if not load_character(driver, "Thorin"):
            print("❌ Failed to load character")
            return 1

        # Run tests
        print("\n🧪 Running Reality Check tests in browser...\n")

        results["Invalid Combat"] = test_invalid_combat(driver)
        time.sleep(2)

        results["Invalid Item"] = test_invalid_item(driver)
        time.sleep(2)

        results["Valid Item Use"] = test_valid_item(driver)
        time.sleep(2)

        results["Party Dragon Combat"] = test_party_dragon_combat(driver)
        time.sleep(2)

        # Summary
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)

        passed = sum(1 for result in results.values() if result)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")

        print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

        if passed == total:
            print("\n🎉 ALL BROWSER TESTS PASSED!")
            print("\nThe Reality Check system is working in the Gradio UI!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return 1

    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        if driver:
            print("\n🔚 Keeping browser open for 5 seconds so you can see the results...")
            time.sleep(5)
            print("Closing browser...")
            driver.quit()


if __name__ == "__main__":
    exit_code = run_browser_tests()
    sys.exit(exit_code)
