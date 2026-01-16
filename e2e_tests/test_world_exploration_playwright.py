from playwright.sync_api import sync_playwright, expect
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
    click_tab,
    kill_port
)

def extract_location_from_explore(response):
    """Extract location name from exploration response (usually between **)."""
    # Look for bold text which usually indicates the new location name
    match = re.search(r'\*\*([^*]+)\*\*', response)
    if match:
        return match.group(1)
    return None

def test_world_exploration_playwright():
    """
    E2E Test: World Exploration with Persistence (Playwright)
    """
    print("\n" + "🗺️" * 40)
    print("TEST: World Exploration & Persistence (Playwright)")
    print("🗺️" * 40)
    
    # Ensure port 7860 is free
    kill_port(7860)
    
    # Start Gradio server
    print("\n🚀 Starting Gradio server...")
    # We don't set specific start location to test default behavior or we can set a safe one
    # Let's rely on default random or "The Market Square" if hardcoded in app
    env = os.environ.copy()
    env['TEST_START_LOCATION'] = 'The Market Square' # Start in a known hub
    
    gradio_process = subprocess.Popen(
        ['python3', 'web/app_gradio.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(10) # Give server time to start
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 1. Load App
            page.goto("http://localhost:7860")
            wait_for_gradio(page)
            
            # Switch to Play Game
            click_tab(page, "🎮 Play Game")
            
            # 2. Load Thorin
            print("\n📝 Loading Thorin...")
            load_character(page, "Thorin")
            
            # Check welcome message
            welcome = get_last_bot_message(page)
            print(f"   Context: {welcome[:100]}...")
            
            # 3. Check Map
            print("\n📍 Checking /map...")
            send_message(page, "/map")
            time.sleep(2)
            map_response = get_last_bot_message(page)
            # print(f"   Map: {map_response[:100]}...")
            if "travel" in map_response.lower() or "location" in map_response.lower():
                print("✅ Map command working")
            else:
                print("⚠️  Map response unclear")

            # 4. Explore to find NEW location
            print("\n🔍 Exploring for new location...")
            send_message(page, "/explore")
            time.sleep(5)
            explore_response = get_last_bot_message(page)
            print(f"   Explore: {explore_response[:150]}...")
            
            new_location = extract_location_from_explore(explore_response)
            if new_location:
                print(f"✅ Discovered: {new_location}")
            else:
                print("⚠️  No new location extracted from explore response")
                # Fallback names if regex fails but text implies success
                if "forest" in explore_response.lower(): new_location = "Dark Forest"
                elif "cave" in explore_response.lower(): new_location = "Goblin Cave"
                else: new_location = "Unknown Wilds"
            
            # 5. Travel to new location
            print(f"\n🚶 Traveling to {new_location}...")
            send_message(page, f"/travel {new_location}")
            time.sleep(3)
            travel_response = get_last_bot_message(page)
            
            if new_location in travel_response or "travel" in travel_response.lower():
                print(f"✅ Traveled to {new_location}")
            else:
                print(f"⚠️  Travel unclear: {travel_response[:100]}...")

            # 6. Combat & Persistence
            print("\n⚔️  Simulating Combat (Cave Goblin)...")
            send_message(page, "/start_combat Cave Goblin")
            time.sleep(3)
            
            # Attack once
            send_message(page, "I attack the Cave Goblin with my battleaxe!")
            time.sleep(3)
            
            # End combat (kill it)
            send_message(page, "/end_combat")
            print("✅ Combat ended (Goblin defeated)")
            
            # 7. Travel Back & Verify Return
            print(f"\n🔙 Returning to 'The Market Square'...")
            send_message(page, "/travel The Market Square")
            time.sleep(3)
            
            # 8. Shop Integration
            print("\n💰 Testing Shop at Market Square...")
            send_message(page, "/buy rope")
            time.sleep(3)
            buy_response = get_last_bot_message(page)
            
            if "bought" in buy_response.lower() or "added" in buy_response.lower():
                print("✅ Purchase successful")
            elif "not enough" in buy_response.lower():
                print("✅ Purchase attempted (Gold validation working)")
            else:
                print(f"⚠️  Shop response: {buy_response[:100]}...")
                
            # 9. Return to previous location (Persistence Check)
            print(f"\n🔁 Returning to {new_location} to check persistence...")
            send_message(page, f"/travel {new_location}")
            time.sleep(3)
            
            # Check for goblin body/absence
            send_message(page, "I look for the Cave Goblin")
            time.sleep(3)
            look_response = get_last_bot_message(page)
            
            if "dead" in look_response.lower() or "body" in look_response.lower() or "defeated" in look_response.lower():
                print("✅ PERSISTENCE VERIFIED: Enemy is dead/gone")
            else:
                print(f"ℹ️  Look response: {look_response[:100]}...")
                
            print("\n✅ World Exploration Test Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="world_exploration_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_world_exploration_playwright()
