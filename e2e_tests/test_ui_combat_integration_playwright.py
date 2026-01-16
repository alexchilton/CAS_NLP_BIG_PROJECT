from playwright.sync_api import sync_playwright, expect
import time
from pathlib import Path
import sys
import os
import subprocess
import signal
import re

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from e2e_tests.playwright_helpers import (
    wait_for_gradio,
    load_character,
    send_message,
    get_last_bot_message,
    get_all_messages,
    kill_port
)

def test_ui_combat_integration_playwright():
    """
    Test: UI Combat Integration (Playwright)
    Verifies chat, initiative tracker, and combat buttons work.
    """
    print("\n" + "\ud83c\udfae" * 40)
    print("TEST: UI Combat Integration (Playwright)")
    print("\ud83c\udfae" * 40)
    
    # Ensure port 7860 is free
    kill_port(7860)
    
    # Start Gradio server
    print("\n🚀 Starting Gradio server...")
    gradio_process = subprocess.Popen(
        ['python3', 'web/app_gradio.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(10) # Give server time to start
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:7860")
            wait_for_gradio(page)
            
            # 1. Load character and send basic message
            print("\n" + "=" * 80)
            print("TEST 1: Load character and send basic message")
            print("=" * 80)
            
            load_character(page, "Thorin")
            
            send_message(page, "I look around")
            messages = get_all_messages(page)
            expect(len(messages)).to_be_greater_than_or_equal(2)
            print("✅ Basic chat works.")
            
            # 2. Start combat and check for errors
            print("\n" + "=" * 80)
            print("TEST 2: Start combat with /start_combat command")
            print("=" * 80)
            
            send_message(page, "/start_combat Goblin, Orc")
            combat_start_response = get_last_bot_message(page)
            
            expect(page.locator("body")).not_to_contain_text("error", timeout=5000)
            expect(page.locator("body")).not_to_contain_text("traceback", timeout=5000)
            expect(page.locator("body")).to_contain_text("Initiative Order")
            print("✅ Combat starts without errors.")
            
            # 3. Check for initiative tracker visibility and combat buttons
            print("\n" + "=" * 80)
            print("TEST 3: Check for initiative tracker and combat buttons")
            print("=" * 80)
            
            # Initiative tracker accordion should be visible
            expect(page.get_by_text("⚔️ Initiative Tracker")).to_be_visible()
            
            # Combat action buttons
            expect(page.get_by_role("button", name="⚔️ Attack")).to_be_visible()
            expect(page.get_by_role("button", name="⏭️ Next Turn")).to_be_visible()
            expect(page.get_by_role("button", name="🛑 End Combat")).to_be_visible()
            print("✅ Initiative tracker and combat buttons found.")
            
            # 4. Send combat action
            print("\n" + "=" * 80)
            print("TEST 4: Send combat action")
            print("=" * 80)
            
            send_message(page, "I attack the Goblin with my longsword")
            combat_action_response = get_last_bot_message(page)
            
            expect(page.locator("body")).not_to_contain_text("error", timeout=5000)
            expect(page.locator("body")).not_to_contain_text("traceback", timeout=5000)
            print("✅ Combat actions work without errors.")
            
            # 5. End combat
            print("\n" + "=" * 80)
            print("TEST 5: End combat")
            print("=" * 80)
            
            send_message(page, "/end_combat")
            end_combat_response = get_last_bot_message(page)
            
            expect(page.locator("body")).to_contain_text("Combat has ended")
            print("✅ Combat ends successfully.")
            
            print("\n✅ All UI Combat Integration Tests Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="ui_combat_integration_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_ui_combat_integration_playwright()
