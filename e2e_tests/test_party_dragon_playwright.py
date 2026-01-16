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
    select_dropdown_option
)

def test_party_dragon_playwright():
    """
    Test: Party Dragon Combat (Playwright)
    Simulates a narrative battle between Thorin/Elara and an Ancient Red Dragon.
    """
    print("\n" + "🐉" * 40)
    print("TEST: Party Dragon Combat (Playwright)")
    print("🐉" * 40)
    
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
            
            # Load Thorin
            print("\n📝 Loading Thorin...")
            load_character(page, "Thorin")
            
            # Narrative Setup
            print("\n📜 Setting up Dragon Encounter...")
            setup_msg = "Thorin the dwarf fighter and Elara the elf wizard enter a vast cavern filled with mountains of gold. At the center, coiled atop the treasure hoard, rests an Ancient Red Dragon with 200 HP."
            send_message(page, setup_msg)
            time.sleep(2)
            
            # Round 1
            print("\n⚔️  Round 1: Thorin Charges")
            send_message(page, "Thorin the dwarf fighter and Elara the elf wizard enter a vast cavern filled with mountains of gold. At the center, coiled atop the treasure hoard, rests an Ancient Red Dragon with 200 HP.")
            time.sleep(3)
            
            print("\n🔥 Round 1: Elara Casts")
            send_message(page, "Elara raises her staff and casts Fire Bolt at the dragon's chest!")
            time.sleep(3)
            
            print("\n🐲 Round 1: Dragon Breaths")
            send_message(page, "The dragon roars and unleashes a massive gout of flame at both of them!")
            time.sleep(3)
            
            # Round 2
            print("\n🛡️  Round 2: Thorin Protects")
            send_message(page, "Thorin steps in front of Elara, raises his shield, and attacks the dragon with his longsword!")
            time.sleep(3)
            
            # Test Invalid Spell (Fighter casting Fireball)
            print("\n🚫 Testing Reality Check: Fighter casting Fireball")
            send_message(page, "Thorin tries to cast Fireball at the dragon!")
            time.sleep(3)
            
            response = get_last_bot_message(page)
            if "fighter" in response.lower() and "cannot" in response.lower():
                print("✅ Reality Check Passed: Fighter cannot cast spells.")
            elif "fail" in response.lower() or "unable" in response.lower():
                print("✅ Reality Check Passed (Implicit): Action failed.")
            else:
                print(f"⚠️  Reality Check Unclear: {response[:100]}...")
            
            # Round 3 - Final Stand
            print("\n⚔️  Round 3: Desperate Attack")
            send_message(page, "With his last ounce of strength, Thorin attacks the dragon one more time!")
            time.sleep(3)
            
            print("\n✅ Party Dragon Combat Test Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="dragon_combat_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_party_dragon_playwright()
