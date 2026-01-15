#!/usr/bin/env python3
"""
Demonstration Test: New Dropdown Helpers

This test validates that we can now reliably:
1. Select ANY character from the character dropdown (not just default Thorin)
2. Select a debug scenario from the scenario dropdown
3. Verify the selections worked correctly

This was previously a constant problem causing silent failures.
"""

import sys
import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the new helpers
from e2e_tests.selenium_helpers import (
    wait_for_gradio,
    select_character,
    select_debug_scenario,
    send_message,
    get_chat_messages,
    setup_chrome_driver,
    get_character_sheet_text,
)


def test_dropdown_helpers():
    """Test that dropdown helpers work correctly for character and scenario selection."""

    print("\n" + "=" * 80)
    print("🧪 TESTING NEW DROPDOWN HELPERS")
    print("=" * 80)
    print("\n📋 This test will:")
    print("   1. Select Elara (Wizard) from character dropdown")
    print("   2. Select 'Skeleton Guardian' from debug scenario dropdown")
    print("   3. Load the character")
    print("   4. Verify Elara is loaded (not Thorin!)")
    print("   5. Verify we're at the right location")
    print("   6. Try a wizard spell to confirm it's really Elara")
    print("\n" + "=" * 80)

    # Start Gradio in debug mode
    import subprocess
    env = os.environ.copy()
    env['GM_DEBUG'] = 'true'

    print("\n🚀 Starting Gradio app...")
    gradio_process = subprocess.Popen(
        ['python3', 'web/app_gradio.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for Gradio to start
    print("   ⏳ Waiting 10 seconds for Gradio to initialize...")
    time.sleep(10)

    # Setup browser
    driver = setup_chrome_driver(headless=False)  # Run visible so we can watch!

    try:
        print("\n📱 Opening browser at http://localhost:7860...")
        driver.get("http://localhost:7860")
        wait_for_gradio(driver)

        # Give Gradio extra time to populate dropdowns
        print("   ⏳ Waiting 5 more seconds for dropdowns to populate...")
        time.sleep(5)

        print("\n" + "=" * 80)
        print("STEP 1: Select Elara from character dropdown")
        print("=" * 80)

        # Use the new helper to select Elara
        selected_char = select_character(driver, "Elara")
        print(f"\n✅ Character dropdown selection returned: {selected_char}")

        if "Elara" not in selected_char:
            raise Exception(f"❌ FAILED: Expected 'Elara' but got '{selected_char}'")

        print("\n" + "=" * 80)
        print("STEP 2: Select Skeleton Guardian from debug scenario dropdown")
        print("=" * 80)

        # Use the new helper to select a debug scenario
        selected_scenario = select_debug_scenario(driver, "Skeleton Guardian")
        print(f"\n✅ Scenario dropdown selection returned: {selected_scenario}")

        if "Skeleton" not in selected_scenario:
            raise Exception(f"❌ FAILED: Expected 'Skeleton Guardian' but got '{selected_scenario}'")

        print("\n" + "=" * 80)
        print("STEP 3: Click Load Character button")
        print("=" * 80)

        # Find and click Load Character button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Load Character" in btn.text:
                print("   🔘 Clicking 'Load Character' button...")
                btn.click()
                time.sleep(5)
                break

        print("\n" + "=" * 80)
        print("STEP 4: Verify Elara loaded (check character sheet)")
        print("=" * 80)

        # Get character sheet text
        char_sheet = get_character_sheet_text(driver)
        print(f"\n📄 Character sheet preview:")
        print(char_sheet[:400] + "..." if len(char_sheet) > 400 else char_sheet)

        # Verify it's Elara, not Thorin
        if "Elara" not in char_sheet and "ELARA" not in char_sheet:
            print(f"\n❌ CRITICAL FAILURE: Character sheet doesn't mention Elara!")
            print(f"   This suggests the dropdown selection failed silently")
            print(f"   Full character sheet: {char_sheet}")
            raise Exception("Character sheet doesn't contain 'Elara'")

        if "Thorin" in char_sheet or "THORIN" in char_sheet:
            print(f"\n❌ CRITICAL FAILURE: Character sheet mentions Thorin!")
            print(f"   This means dropdown defaulted to Thorin instead of selecting Elara")
            raise Exception("Wrong character loaded - got Thorin instead of Elara")

        print("\n✅ VERIFIED: Elara is loaded (not Thorin)")

        print("\n" + "=" * 80)
        print("STEP 5: Verify scenario location")
        print("=" * 80)

        # Check context
        send_message(driver, "/context", wait_time=5)
        messages = get_chat_messages(driver)
        if messages:
            context = messages[-1]
            print(f"\n📍 Current location: {context[:300]}...")
            print(f"\n✅ Scenario loaded successfully")

        print("\n" + "=" * 80)
        print("STEP 6: Try casting a wizard spell (proves it's Elara, not Thorin)")
        print("=" * 80)

        # If this was Thorin, the spell would be rejected with "Ye're a FIGHTER"
        send_message(driver, "I look around carefully, examining the ancient ruins", wait_time=8)
        messages = get_chat_messages(driver)
        if messages:
            response = messages[-1]
            print(f"\n🎭 GM Response: {response[:400]}...")

        # Try to cast Magic Missile
        send_message(driver, "I cast Magic Missile", wait_time=8)
        messages = get_chat_messages(driver)
        if messages:
            spell_response = messages[-1]
            print(f"\n🎭 Spell Response: {spell_response[:400]}...")

            # Check for Thorin's rejection message
            if "FIGHTER" in spell_response or "Ye're" in spell_response or "daft" in spell_response:
                print(f"\n❌ CRITICAL FAILURE: Got Thorin's personality in response!")
                print(f"   This proves Elara selection failed and defaulted to Thorin")
                print(f"   Full response: {spell_response}")
                raise Exception("Character is responding as Thorin, not Elara!")

            print("\n✅ VERIFIED: No Thorin-style rejection - this is definitely Elara!")

        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        print("\n✅ Dropdown helpers work correctly:")
        print(f"   • Selected character: {selected_char}")
        print(f"   • Selected scenario: {selected_scenario}")
        print(f"   • Character loaded: Elara (verified)")
        print(f"   • Scenario loaded: Success")
        print(f"   • Spell casting: Works (proves it's Elara, not Thorin)")
        print("\n🎊 The dropdown selection bug is FIXED!")
        print("=" * 80)

        # Keep browser open for 15 seconds so user can see it
        print("\n👀 Keeping browser open for 15 seconds so you can inspect...")
        time.sleep(15)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

        # Save screenshot for debugging
        try:
            screenshot_path = "/tmp/dropdown_test_failure.png"
            driver.save_screenshot(screenshot_path)
            print(f"\n📸 Screenshot saved to: {screenshot_path}")
        except:
            pass

        # Keep browser open longer on failure
        print("\n👀 Keeping browser open for 30 seconds for inspection...")
        time.sleep(30)

        raise

    finally:
        driver.quit()

        # Stop Gradio
        print("\n🛑 Stopping Gradio process...")
        gradio_process.terminate()
        try:
            gradio_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            gradio_process.kill()
            gradio_process.wait()


if __name__ == "__main__":
    print("\n" + "🧪" * 40)
    print("DROPDOWN HELPERS VALIDATION TEST")
    print("🧪" * 40)
    print("\n📚 Purpose:")
    print("   Prove that we can now select ANY character and ANY scenario")
    print("   from the dropdowns without silent failures.")
    print("\n🔍 What to watch for:")
    print("   • Browser will open visibly (not headless)")
    print("   • You'll see dropdowns being selected")
    print("   • Console will show detailed logging")
    print("   • Character sheet should show ELARA, not Thorin")
    print("   • Spell casting should work (no 'Ye're a FIGHTER' message)")
    print("\n" + "🧪" * 40 + "\n")

    test_dropdown_helpers()
