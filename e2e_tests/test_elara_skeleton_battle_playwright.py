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
    analyze_response,
    kill_port
)

def test_elara_skeleton_battle_playwright():
    """
    Test: Elara (Wizard) vs Skeletons - Spell Combat (Playwright)
    """
    print("\n" + "🔮" * 40)
    print("TEST: Elara vs Skeletons (Playwright)")
    print("🔮" * 40)
    
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
            
            # Load Elara
            print("\n📝 Loading Elara...")
            load_character(page, "Elara")
            
            # Start combat
            print("\n" + "=" * 80)
            print("⚔️  STARTING COMBAT WITH SKELETON")
            print("=" * 80)
            
            send_message(page, "/start_combat Skeleton")
            time.sleep(3)
            
            combat_start_response = get_last_bot_message(page)
            expect(page.locator("body")).to_contain_text("Initiative Order")
            print("✅ Combat started.")
            
            # Combat loop
            spells = [
                "I cast Magic Missile at the skeleton",
                "I cast Fire Bolt at the skeleton",
                "I attack the skeleton with my quarterstaff"
            ]
            
            round_num = 1
            max_rounds = 15
            combat_over = False
            
            print("\n🔮 Elara begins casting spells!")
            
            while round_num <= max_rounds and not combat_over:
                print(f"\n{'=' * 80}")
                print(f"⚔️  ROUND {round_num}")
                print(f"{'=' * 80}")
                
                action = spells[(round_num - 1) % len(spells)]
                send_message(page, action)
                time.sleep(5) # Wait for response
                
                response = get_last_bot_message(page)
                
                # Analyze response using analyze_response helper
                dead = analyze_response(response, action)
                
                if dead:
                    print(f"\n✅ Skeleton defeated in round {round_num}!")
                    combat_over = True
                    break
                
                # Check for player death explicitly
                if "you have died" in response.lower() or "you are dead" in response.lower() or "elara has fallen" in response.lower():
                    print(f"\n💀 Elara has fallen in combat in round {round_num}!")
                    combat_over = True
                    break
                
                round_num += 1
                
            if combat_over:
                print("\n✅ Combat concluded!")
                send_message(page, "/end_combat")
            else:
                print(f"\n⚠️  Combat reached maximum rounds ({max_rounds}).")
                send_message(page, "/end_combat") # Ensure combat ends
                
            print("\n✅ Elara vs Skeletons Test Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="elara_skeleton_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_elara_skeleton_battle_playwright()
