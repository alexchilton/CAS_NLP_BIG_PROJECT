from playwright.sync_api import sync_playwright, expect
import time
from pathlib import Path
import sys
import os
import subprocess
import signal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from e2e_tests.playwright_helpers import (
    wait_for_gradio,
    load_character,
    send_message,
    get_last_bot_message,
    analyze_response,
    kill_port # Import kill_port
)

def test_weapon_vs_spell_tracking_playwright():
    """
    Test: Compare Weapon Attack vs Spell Damage Tracking (Playwright Version)
    """
    print("\n" + "⚔️" * 40)
    print("TEST: Weapon Attack vs Spell Damage Tracking (Playwright)")
    print("⚔️" * 40)
    
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
        # Launch browser
        browser = p.chromium.launch(headless=True) # Run headless for speed, set False to watch
        page = browser.new_page()
        
        try:
            # Open App
            page.goto("http://localhost:7860")
            wait_for_gradio(page)
            
            # ----------------------------------------------------------------
            # Test 1: Thorin with weapon attacks
            # ----------------------------------------------------------------
            print("\n" + "=" * 80)
            print("TEST 1: THORIN (Fighter) - Weapon Attacks")
            print("=" * 80)
            
            load_character(page, "Thorin")
            
            # Start combat
            send_message(page, "/start_combat Goblin")
            time.sleep(2) # Wait for GM response
            print(f"\nCombat started!")
            
            # Attack 1
            print(f"\n--- Weapon Attack 1: Longsword ---")
            send_message(page, "I attack the goblin with my longsword")
            # Wait for response text to appear/change
            time.sleep(5) 
            response = get_last_bot_message(page)
            dead = analyze_response(response, "Weapon Attack")
            
            if not dead:
                # Attack 2
                print(f"\n--- Weapon Attack 2: Longsword ---")
                send_message(page, "I attack the goblin with my longsword")
                time.sleep(5)
                response = get_last_bot_message(page)
                dead = analyze_response(response, "Weapon Attack")
            
            send_message(page, "/end_combat")
            time.sleep(1)
            
            # ----------------------------------------------------------------
            # Test 2: Elara with spell attacks
            # ----------------------------------------------------------------
            print("\n\n" + "=" * 80)
            print("TEST 2: ELARA (Wizard) - Spell Attacks")
            print("=" * 80)
            
            # Reload page to ensure clean state
            print("🔄 Refreshing page...")
            page.reload()
            wait_for_gradio(page)
            
            load_character(page, "Elara")
            
            send_message(page, "/start_combat Goblin")
            time.sleep(2)
            print(f"\nCombat started!")
            
            # Spell 1
            print(f"\n--- Spell Attack 1: Magic Missile ---")
            send_message(page, "I cast Magic Missile at the goblin")
            time.sleep(5)
            response = get_last_bot_message(page)
            dead = analyze_response(response, "Magic Missile")
            
            if not dead:
                # Spell 2
                print(f"\n--- Spell Attack 2: Fire Bolt ---")
                send_message(page, "I cast Fire Bolt at the goblin")
                time.sleep(5)
                response = get_last_bot_message(page)
                dead = analyze_response(response, "Fire Bolt")

            send_message(page, "/end_combat")
            
            print("\n" + "=" * 80)
            print("📊 SUMMARY: Test Completed Successfully")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            # Take screenshot on failure
            page.screenshot(path="playwright_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_weapon_vs_spell_tracking_playwright()
