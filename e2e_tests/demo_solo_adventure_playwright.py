from playwright.sync_api import sync_playwright, expect
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
    click_tab,
    fill_input,
    set_slider,
    select_dropdown_option,
    kill_port,
    send_message,
    get_last_bot_message,
    get_character_sheet_text
)

def create_character(page, name, race, char_class, level, stats):
    """Helper to create a single character."""
    print(f"\n✨ Creating {name} ({race} {char_class} Lvl {level})...")
    
    # Ensure we are on the Create tab
    click_tab(page, "✨ Create Character")
    
    # Fill details
    fill_input(page, "Character Name", name)
    select_dropdown_option(page, "Race", race)
    select_dropdown_option(page, "Class", char_class)
    select_dropdown_option(page, "Alignment", "Chaotic Good")
    fill_input(page, "Background", "Adventurer")
    
    # Set Level (Slider index 0)
    sliders = page.locator("input[type='range']")
    sliders.nth(0).fill(str(level))
    
    # Set Stats (Indices 1-6)
    # Stats array order: Str, Dex, Con, Int, Wis, Cha
    for i, val in enumerate(stats):
        sliders.nth(i+1).fill(str(val))
        
    # Create
    page.get_by_role("button", name="Create Character").click()
    time.sleep(2)
    print(f"   ✅ {name} created!")

def get_class_based_action(char_class, turn):
    """Generate smart exploration actions based on character class."""
    
    wizard_actions = [
        "I examine the arcane symbols on the walls",
        "I study the magical auras in this place",
        "I consult my spellbook for relevant knowledge",
        "I try to identify any magical items nearby"
    ]
    
    rogue_actions = [
        "I search for hidden doors and secret passages",
        "I check the area for traps",
        "I listen carefully for sounds of danger",
        "I examine the shadows for hiding spots"
    ]
    
    cleric_actions = [
        "I pray for divine guidance",
        "I sense for any evil presence nearby",
        "I bless our path forward",
        "I check for any undead presence"
    ]
    
    fighter_actions = [
        "I survey the area for tactical advantages",
        "I check our defensive positions",
        "I keep watch for threats",
        "I examine the architecture for structural weaknesses"
    ]
    
    barbarian_actions = [
        "I sniff the air for danger",
        "I test the strength of the structures around me",
        "I look for signs of recent battle",
        "I search for tracks or signs of passage"
    ]
    
    # Map classes to actions
    class_actions = {
        "Wizard": wizard_actions,
        "Rogue": rogue_actions,
        "Cleric": cleric_actions,
        "Fighter": fighter_actions,
        "Paladin": fighter_actions,
        "Barbarian": barbarian_actions,
    }
    
    actions = class_actions.get(char_class, [
        "I explore the area",
        "I look around carefully",
        "I move forward cautiously"
    ])
    
    return random.choice(actions)

def is_in_combat(response):
    """Check if the response indicates combat."""
    combat_keywords = ['combat', 'initiative', 'roll initiative', 'attacks you', 'draws weapon']
    return any(keyword in response.lower() for keyword in combat_keywords)

def is_enemy_dead(response):
    """Check if enemy was defeated."""
    death_keywords = ['defeated', 'killed', 'dies', 'falls dead', 'slain', 'destroyed', 'no more enemies', 'combat ends']
    return any(keyword in response.lower() for keyword in death_keywords)

def demo_solo_endless_adventure():
    """
    Automated endless adventure demo for SINGLE CHARACTER.
    
    Similar to party demo but for solo play - lets us compare performance.
    Uses whatever character is already available (no creation needed).
    
    Features:
    - Solo character mode (any existing character)
    - Generic combat/exploration actions
    - Natural combat encounters
    - Context window stress testing
    - Stuck detection and recovery
    """
    print("\n" + "🎬" * 40)
    print("DEMO: ENDLESS SOLO ADVENTURE (Zephyr)")
    print("🎬" * 40)
    
    # 1. Setup Server
    kill_port(7860)
    print("\n🚀 Starting Gradio server...")
    import sys
    gradio_process = subprocess.Popen(
        ['python3', 'web/app_gradio.py'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for server to be ready by polling the port
    import socket
    max_wait = 30
    start = time.time()
    while time.time() - start < max_wait:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 7860))
            sock.close()
            if result == 0:
                print("✅ Gradio server started and ready!")
                time.sleep(2)  # Extra buffer for full init
                break
        except:
            pass
        time.sleep(1)
    else:
        print("❌ Gradio server failed to start in time!")
        sys.exit(1)
    
    print("🌐 Launching browser...")
    with sync_playwright() as p:
        # VISIBLE BROWSER FOR DEMO
        browser = p.chromium.launch(headless=False, slow_mo=50)
        print("✅ Browser launched") 
        page = browser.new_page()
        page.set_viewport_size({"width": 1400, "height": 900})
        
        try:
            print("\n🌐 Loading Gradio UI...")
            page.goto("http://localhost:7860")
            print("✅ Page navigated")
            wait_for_gradio(page)
            print("✅ Gradio loaded")
            
            # ---------------------------------------------------------
            # 2. Start Game with First Available Character
            # ---------------------------------------------------------
            print("\n🎮 Starting Game with first available character...")
            click_tab(page, "🎮 Play Game")
            
            # Select Character Mode (default)
            print("   Mode: Single Character ✅")
            time.sleep(1)
            
            # First character should be auto-selected
            print("   Using first available character...")
            time.sleep(1)
            
            # Load Character
            print("   Loading Character...")
            page.get_by_role("button", name="Load Character").click()
            time.sleep(5)
            
            print("\n🗺️  THE ADVENTURE BEGINS! (Press Ctrl+C to stop)")
            print(f"   Mode: Solo Character")
            
            turn = 0
            combat_turns = 0  # Track how long we've been in combat
            last_response_text = ""
            stuck_count = 0
            
            # ---------------------------------------------------------
            # 4. Endless Adventure Loop
            # ---------------------------------------------------------
            while True:
                turn += 1
                print(f"\n🔹 Turn {turn}")
                
                # Get current response to track changes
                current_response = get_last_bot_message(page)
                print(f"   🔎 Captured response length: {len(current_response)}")
                
                # Determine if in combat
                combat_mode = is_in_combat(current_response)
                
                if combat_mode:
                    combat_turns += 1
                    print(f"⚔️  Combat active (round {combat_turns})!")
                    
                    # Stuck combat detection - force end after 20 rounds
                    if combat_turns > 20:
                        print(f"   ⚠️  Combat stuck (20+ rounds)! Force ending...")
                        action = "/end_combat"
                        combat_turns = 0
                    # Check if enemy died
                    elif is_enemy_dead(current_response):
                        print(f"   💀 Enemy defeated! Combat should end.")
                        combat_turns = 0
                        # Generic exploration action after combat
                        action = random.choice([
                            "I search the area for treasure.",
                            "I check the body for loot.",
                            "I look around carefully.",
                            "I investigate the surroundings."
                        ])
                    else:
                        # Generic combat actions
                        action = random.choice([
                            "I attack the enemy!",
                            "I strike with my weapon!",
                            "I defend and counterattack!",
                            "I aim for a vital spot!",
                            "I charge at the enemy!",
                            "I feint and attack!"
                        ])
                
                else:
                    combat_turns = 0
                    print("🌲 Exploration mode")
                    
                    # Lower chance to force combat (5%)
                    if random.random() < 0.05:
                        mob = random.choice(["Orc", "Bandit", "Skeleton", "Kobold", "Giant Spider"])
                        print(f"😈 Random encounter spawned: {mob}")
                        action = f"/start_combat {mob}"
                    else:
                        # Use generic exploration
                        exploration_actions = [
                            "I explore the area carefully",
                            "I look around for anything interesting",
                            "I search for clues",
                            "I move forward cautiously"
                        ]
                        action = random.choice(exploration_actions)
                
                # Send Action with timeout
                print(f"👉 Action: {action}")
                print(f"   📊 Turn {turn} stats: Solo mode")
                
                action_start = time.time()
                success = send_message(page, action, max_wait=180)
                action_time = time.time() - action_start
                
                if not success:
                    print(f"   🚨 TIMEOUT DETECTED!")
                    print(f"   ├─ Total time: {action_time:.1f}s")
                    print(f"   ├─ Last successful response: Turn {turn-1 if turn > 1 else 0}")
                    print(f"   └─ Attempting recovery...")
                    
                    print(f"   ⏳ Waiting 30s to see if UI recovers...")
                    time.sleep(30)
                    
                    # Check if recovered
                    test_response = get_last_bot_message(page)
                    if test_response == last_response_text:
                        print(f"   🛑 UI is definitely stuck (same message).")
                        print(f"      Forcing page reload...")
                        page.reload()
                        time.sleep(5)
                        print(f"      ✅ Page reloaded. Demo will continue...")
                    else:
                        print(f"   ✅ UI recovered! Response appeared.")
                
                # Get and analyze response
                current_response = get_last_bot_message(page)
                response_length = len(current_response)
                print(f"   📝 Response: {response_length} chars")
                
                # Detect if response changed
                if current_response == last_response_text:
                    stuck_count += 1
                    print(f"   ⚠️  WARNING: Same response as last turn (stuck count: {stuck_count}/3)")
                    if stuck_count >= 3:
                        print(f"   🚨 STUCK DETECTED (3 identical responses)!")
                        print(f"      This indicates a serious problem.")
                        print(f"      Attempting recovery...")
                        
                        # Force end combat and refresh
                        send_message(page, "/end_combat", max_wait=10)
                        time.sleep(2)
                        send_message(page, "/help", max_wait=10)
                        time.sleep(2)
                        stuck_count = 0
                        print(f"      Recovery attempted. Continuing...")
                else:
                    stuck_count = 0
                
                last_response_text = current_response
                
                # Wait for readability
                # Longer wait every 10 turns to check context window
                if turn % 10 == 0:
                    print(f"   ⏸️  Extended pause (turn {turn}) - checking system health...")
                    print(f"      ├─ Average response time: ~{action_time:.1f}s")
                    print(f"      ├─ Checking for context window issues...")
                    print(f"      └─ Pausing 12s for observation...")
                    time.sleep(12)
                else:
                    time.sleep(6)
                
        except KeyboardInterrupt:
            print("\n👋 Demo stopped by user.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()
            gradio_process.terminate()
            gradio_process.wait()
    
    print("\n✅ Demo complete!")

if __name__ == "__main__":
    demo_solo_endless_adventure()
