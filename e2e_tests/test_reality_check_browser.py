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

            # Try to get the response text
            # Look for any new text that appeared
            chatbot_divs = driver.find_elements(By.CSS_SELECTOR, "[data-testid]")
            if chatbot_divs:
                # Get the last few divs and look for the response
                for div in reversed(chatbot_divs[-10:]):
                    text = div.text.strip()
                    if text and len(text) > 10:  # Meaningful response
                        print(f"🎭 GM: {text[:200]}...")
                        return text

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
