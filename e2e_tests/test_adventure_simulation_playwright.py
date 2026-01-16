from playwright.sync_api import sync_playwright, expect, Page
import time
import random
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
    click_tab,
    kill_port, # Import kill_port
    get_hp_from_sheet, # Import get_hp_from_sheet
    extract_creatures, # Import extract_creatures
    get_last_bot_message
)

def test_adventure_simulation_playwright():
    """
    Automated Adventure Simulation - Random Travel & Combat Until Death (Playwright)
    """
    print("=" * 80)
    print("🎮 AUTOMATED ADVENTURE SIMULATION (Playwright)")
    print("=" * 80)
    
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
        # Use headless for automation, set to False to watch
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 720}) # Set a reasonable viewport
        
        try:
            # Navigate to app
            print("\n📱 Opening browser...")
            page.goto("http://localhost:7860")
            wait_for_gradio(page)
            
            # Click "Play Game" tab
            click_tab(page, "🎮 Play Game")
            
            # Load character
            print("⚔️  Loading Thorin Stormshield...")
            load_character(page, "Thorin Stormshield")
            
            print("✅ Character loaded!\n")
            
            # Start adventure
            print("=" * 80)
            print("🗺️  ADVENTURE BEGINS!")
            print("=" * 80)
            
            turn = 0
            max_turns = 20  # Safety limit
            in_combat = False
            current_enemy = None
            
            while turn < max_turns:
                turn += 1
                
                # Check HP
                hp = get_hp_from_sheet(page)
                print(f"\n💚 Turn {turn} - HP: {hp if hp is not None else '???'}")
                
                if hp is not None and hp <= 0:
                    print("\n" + "=" * 80)
                    print("💀 GAME OVER - CHARACTER DIED!")
                    print("=" * 80)
                    break
                
                # Decide action
                if not in_combat:
                    # Exploration mode - Ask GM what we see/encounter
                    action_roll = random.random()
                    
                    if action_roll < 0.3:
                        # Venture into wilderness/danger
                        actions = [
                            "I venture deeper into the wilderness, looking for adventure",
                            "I follow the path ahead, seeking what dangers or treasures await",
                            "I explore the area thoroughly, searching for anything unusual",
                            "I venture into the darker parts of this place",
                            "I head toward the sounds of potential danger",
                            "I search for signs of monsters or bandits in the area"
                        ]
                        action = random.choice(actions)
                        print(f"\n🔍 Turn {turn}: {action}")
                        send_message(page, action)
                        response = get_last_bot_message(page)
                        print(f"GM: {response[:300]}...")
                        
                        # Check for creatures
                        creatures = extract_creatures(response)
                        if creatures:
                            print(f"⚠️  CREATURE SPOTTED: {creatures[0]}!")
                            current_enemy = creatures[0]
                            in_combat = True
                    
                    elif action_roll < 0.6:
                        # Ask GM about surroundings
                        actions = [
                            "I look around carefully. What do I see?",
                            "I listen for any sounds nearby. What do I hear?",
                            "What dangers might be lurking here?",
                            "I investigate the area. Is there anything interesting?",
                            "Are there any creatures or people nearby?"
                        ]
                        action = random.choice(actions)
                        print(f"\n👀 Turn {turn}: {action}")
                        send_message(page, action)
                        response = get_last_bot_message(page)
                        print(f"GM: {response[:300]}...")
                        
                        creatures = extract_creatures(response)
                        if creatures:
                            print(f"⚠️  CREATURE SPOTTED: {creatures[0]}!")
                            current_enemy = creatures[0]
                            in_combat = True
                    
                    else:
                        # Move to a new area (use travel or natural language)
                        destinations = ['Dark Forest', 'Mountain Road', 'Old Ruins', 
                                      'Temple District', 'Market Square', 'Forest Path',
                                      'Town Gates', 'Town Square']
                        dest = random.choice(destinations)
                        
                        print(f"\n🚶 Turn {turn}: Traveling to {dest}...")
                        send_message(page, f"I travel to {dest}")
                        response = get_last_bot_message(page)
                        
                        print(f"GM: {response[:300]}...")
                        
                        # Check for creatures
                        creatures = extract_creatures(response)
                        if creatures:
                            print(f"⚠️  CREATURE SPOTTED: {creatures[0]}!")
                            current_enemy = creatures[0]
                            in_combat = True
                
                else:
                    # Combat mode - attack until someone dies
                    print(f"\n⚔️  Turn {turn}: COMBAT - Attacking {current_enemy}!")
                    
                    # Start combat if not already in it
                    # Check if previous response indicated combat start
                    last_msg = get_last_bot_message(page)
                    if 'initiative' not in last_msg.lower():
                        send_message(page, f"/start_combat {current_enemy}")
                        time.sleep(2) # Give a moment for combat to init
                        response = get_last_bot_message(page)
                        print(f"Combat started: {response[:200]}...")
                    
                    # Attack
                    attack_variations = [
                        f"I attack the {current_enemy} with my battleaxe",
                        f"I swing at the {current_enemy}",
                        f"I strike the {current_enemy}",
                        f"I attack {current_enemy}"
                    ]
                    attack = random.choice(attack_variations)
                    
                    send_message(page, attack)
                    response = get_last_bot_message(page)
                    print(f"Attack: {response[:250]}...")
                    
                    # Check if enemy died
                    if 'dead' in response.lower() or 'dies' in response.lower() or 'falls' in response.lower():
                        print(f"✅ {current_enemy} defeated!")
                        in_combat = False
                        current_enemy = None
                        
                        # End combat
                        send_message(page, "/end_combat")
                    
                    # Check our HP
                    hp = get_hp_from_sheet(page)
                    if hp is not None and hp <= 0:
                        print(f"\n💀 Thorin has fallen in battle against {current_enemy}!")
                        break
                
                # Pause between turns
                time.sleep(1) # Keep it running slower to better observe interactions if headless=False
            
            if turn >= max_turns:
                print("\n⏱️  Adventure ended - max turns reached")
            
            print("\n" + "=" * 80)
            print("🏁 ADVENTURE COMPLETE")
            print("=" * 80)
            print(f"\nTotal turns: {turn}")
            print(f"Final HP: {get_hp_from_sheet(page)}")
            
            # Keep browser open on error for inspection
            if "PYTEST_CURRENT_TEST" not in os.environ: # Only if run directly, not by pytest
                print("\n👀 Browser will stay open for 10 seconds...")
                time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="adventure_failure.png")
            raise e
        
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_adventure_simulation_playwright()
