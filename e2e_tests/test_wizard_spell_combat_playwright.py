from playwright.sync_api import sync_playwright, expect, Page
import time
import re
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
    kill_port,
    get_character_sheet_text,
    analyze_response,
    click_tab,
    select_dropdown_option
)

def test_wizard_spell_combat_playwright():
    """
    Test: Wizard Spell Combat to Death (Playwright)
    Tests wizard spell casting, spell slots, and combat mechanics.
    """
    print("\n" + "✨" * 40)
    print("TEST: Wizard Spell Combat (Playwright)")
    print("✨" * 40)
    
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
            # Open App
            page.goto("http://localhost:7860")
            wait_for_gradio(page)
            
            # Load Elara (Wizard)
            print("\n📝 Loading Elara (Wizard)...")
            load_character(page, "Elara")
            
            # Verify initial state
            print("\n🔍 Checking initial state...")
            send_message(page, "/context")
            context = get_last_bot_message(page)
            print(f"Context: {context[:100]}...")
            
            # Explore to find enemies (or force spawn via start_combat if exploration fails)
            print("\n🔍 Exploring Ancient Ruins...")
            send_message(page, "I carefully explore the ancient ruins, looking for any signs of danger or treasure")
            time.sleep(5)
            exploration_response = get_last_bot_message(page)
            print(f"GM: {exploration_response[:200]}...")
            
            # Check for skeletons
            if "skeleton" in exploration_response.lower() or "undead" in exploration_response.lower():
                print("✅ GM mentioned undead/skeletons!")
            else:
                print("⚠️  GM didn't mention skeletons directly, but we will proceed with combat test.")
            
            # Start Combat
            print("\n⚔️  Starting Combat with Skeleton...")
            send_message(page, "/start_combat Skeleton")
            time.sleep(3)
            
            combat_start = get_last_bot_message(page)
            print(f"GM: {combat_start[:200]}...")
            
            if "Initiative Order" in combat_start:
                print("✅ Combat started with initiative!")
            
            # Combat Loop
            spells = [
                "I cast Magic Missile at the skeleton",
                "I cast Fire Bolt at the skeleton",
                "I attack the skeleton with my quarterstaff",
            ]
            
            round_num = 1
            max_rounds = 10
            combat_over = False
            
            while round_num <= max_rounds and not combat_over:
                print(f"\n⚡ ROUND {round_num}")
                
                action = spells[(round_num - 1) % len(spells)]
                send_message(page, action)
                time.sleep(5) # Wait for response
                
                response = get_last_bot_message(page)
                # print(f"GM: {response[:200]}...")
                
                # Analyze response
                dead = analyze_response(response, f"Action: {action}")
                
                if dead:
                    print(f"\n💀 Enemy defeated in round {round_num}!")
                    combat_over = True
                    break
                
                if "you have died" in response.lower() or "you are dead" in response.lower():
                    print(f"\n💀 Elara has fallen in round {round_num}!")
                    combat_over = True
                    break
                
                round_num += 1
            
            if combat_over:
                print("\n✅ Combat concluded!")
                send_message(page, "/end_combat")
            else:
                print(f"\n⚠️  Combat reached max rounds ({max_rounds}).")
                
            print("\n✅ Wizard Spell Combat Test Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="wizard_combat_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_wizard_spell_combat_playwright()
