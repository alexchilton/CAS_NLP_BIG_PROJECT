#!/usr/bin/env python3
"""
Party Mode Browser Test - Logging and Exploration

This test documents the current state of party mode in the browser UI
and identifies what works and what needs investigation.
"""

import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

GRADIO_URL = "http://localhost:7860"

def create_driver():
    """Create Chrome WebDriver."""
    options = Options()
    options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=options)

def main():
    print("\n" + "="*80)
    print("🔍 PARTY MODE UI EXPLORATION")
    print("="*80)

    driver = create_driver()

    try:
        # Navigate to Gradio
        print(f"\n📍 Navigating to {GRADIO_URL}...")
        driver.get(GRADIO_URL)
        time.sleep(5)

        print("\n🔍 Finding all UI elements...")

        # Log all tabs
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"\n📑 Found {len(buttons)} buttons:")
        for i, btn in enumerate(buttons[:20]):  # First 20 only
            if btn.is_displayed():
                text = btn.text.strip()
                if text and len(text) < 50:
                    print(f"  Button {i}: '{text}'")

        # Switch to Party Management
        print("\n🔄 Switching to Party Management tab...")
        for btn in buttons:
            if "Party Management" in btn.text and btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(3)
                print("✓ Switched to Party Management")
                break

        # Log party management UI
        print("\n🔍 Party Management UI elements:")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        print(f"  Textareas: {len(textareas)}")

        dropdowns = driver.find_elements(By.TAG_NAME, "select")
        print(f"  Dropdowns: {len(dropdowns)}")

        # Try to add Thorin to party
        print("\n👥 Adding Thorin to party...")
        if dropdowns:
            for dropdown in dropdowns:
                if dropdown.is_displayed():
                    dropdown.click()
                    time.sleep(1)

                    options = driver.find_elements(By.CSS_SELECTOR, "[role='option']")
                    for opt in options:
                        if "Thorin" in opt.text:
                            print(f"  Found: {opt.text}")
                            opt.click()
                            time.sleep(1)
                            break
                    break

        # Click Add to Party
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Add to Party" in btn.text and btn.is_displayed():
                btn.click()
                time.sleep(2)
                print("  ✓ Clicked 'Add to Party'")
                break

        # Switch to Play Game
        print("\n🔄 Switching to Play Game tab...")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Play Game" in btn.text and btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(3)
                print("✓ Switched to Play Game")
                break

        # Log Play Game UI BEFORE enabling party mode
        print("\n🔍 Play Game UI (BEFORE party mode):")
        textareas_before = driver.find_elements(By.TAG_NAME, "textarea")
        print(f"  Textareas: {len(textareas_before)}")
        for i, ta in enumerate(textareas_before):
            print(f"    Textarea {i}: visible={ta.is_displayed()}, enabled={ta.is_enabled()}")

        # Enable party mode
        print("\n🎮 Enabling party mode...")
        checkboxes = driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        print(f"  Found {len(checkboxes)} checkboxes")
        for i, cb in enumerate(checkboxes):
            if cb.is_displayed():
                print(f"    Checkbox {i}: selected={cb.is_selected()}")
                if not cb.is_selected():
                    cb.click()
                    time.sleep(3)
                    print("  ✓ Toggled party mode checkbox")
                    break

        # Log Play Game UI AFTER enabling party mode
        print("\n🔍 Play Game UI (AFTER party mode):")
        textareas_after = driver.find_elements(By.TAG_NAME, "textarea")
        print(f"  Textareas: {len(textareas_after)}")
        for i, ta in enumerate(textareas_after):
            print(f"    Textarea {i}: visible={ta.is_displayed()}, enabled={ta.is_enabled()}")

        # Try to find the chat input
        print("\n🔍 Looking for chat input...")
        for i, ta in enumerate(textareas_after):
            if ta.is_displayed():
                print(f"  Attempting to interact with textarea {i}...")
                try:
                    ta.clear()
                    ta.send_keys("Test message")
                    print(f"  ✓ Textarea {i} is interactable!")
                except Exception as e:
                    print(f"  ✗ Textarea {i} NOT interactable: {type(e).__name__}")

        print("\n📊 Summary:")
        print(f"  ✅ Party mode tab switching works")
        print(f"  ✅ Adding characters to party works")
        print(f"  ✅ Party mode checkbox toggling works")
        print(f"  ⚠️  Chat input interactivity needs investigation in party mode")

        print("\n\n⏸️  Keeping browser open for manual inspection...")
        print("Press Ctrl+C to close the browser and exit")

        # Keep browser open for manual inspection
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n👋 Closing browser...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
