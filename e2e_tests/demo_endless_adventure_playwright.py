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
    select_dropdown_option(page, "Alignment", "Chaotic Good") # Everyone is chaotic good today
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
    
    # Wait for success message (or just a safe wait)
    time.sleep(2) 
    print(f"✅ Created {name}")

def assemble_party(page, characters):
    """Add all characters to the party."""
    print("\n🎭 Assembling Party...")
    click_tab(page, "🎭 Party Management")
    
    # Add each character
    # For multiselect, we select them one by one in the dropdown
    # Note: In Gradio multiselect, clicking an option adds it to the input.
    # We might need to open the dropdown for each one.
    
    for char_name in characters:
        full_name = f"{char_name['name']} ({char_name['race']} {char_name['class']})"
        print(f"   Adding {full_name}...")
        try:
            # We use partial match True because created name might format differently in dropdown
            select_dropdown_option(page, "Select Characters", char_name['name'])
        except Exception as e:
            print(f"   ⚠️ Could not select {char_name['name']}: {e}")
            
    time.sleep(1)
    page.get_by_role("button", name="➕ Add to Party").click()
    time.sleep(2)
    print("✅ Party Assembled!")

def get_party_status(page):
    """Get current status from GM response."""
    msg = get_last_bot_message(page)
    return msg

def extract_enemies(text):
    """Simple heuristic to find enemies in text."""
    enemies = []
    common_foes = ["Goblin", "Orc", "Skeleton", "Wolf", "Bandit", "Dragon", "Troll", "Spider", "Rat", "Zombie"]
    for foe in common_foes:
        if foe.lower() in text.lower():
            enemies.append(foe)
    return list(set(enemies))

def demo_endless_adventure():
    """
    DEMO: Endless Adventure with 5-Character Party
    """
    print("\n" + "🎬" * 40)
    print("DEMO: ENDLESS PARTY ADVENTURE")
    print("🎬" * 40)
    
    # 1. Setup Server
    kill_port(7860)
    print("\n🚀 Starting Gradio server...")
    gradio_process = subprocess.Popen(
        ['python3', 'web/app_gradio.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(12) # Wait for startup
    
    with sync_playwright() as p:
        # VISIBLE BROWSER FOR DEMO
        browser = p.chromium.launch(headless=False, slow_mo=50) 
        page = browser.new_page()
        page.set_viewport_size({"width": 1400, "height": 900})
        
        try:
            page.goto("http://localhost:7860")
            wait_for_gradio(page)
            
            # ---------------------------------------------------------
            # 2. Create Characters
            # ---------------------------------------------------------
            party_config = [
                {"name": "Sir Gideon", "race": "Human", "class": "Paladin", "level": 5, "stats": [16, 10, 14, 10, 14, 16]},
                {"name": "Lyra", "race": "Elf", "class": "Wizard", "level": 3, "stats": [8, 16, 12, 17, 13, 10]},
                {"name": "Garret", "race": "Halfling", "class": "Rogue", "level": 4, "stats": [10, 18, 12, 12, 10, 14]},
                {"name": "Thonk", "race": "Half-Orc", "class": "Barbarian", "level": 2, "stats": [18, 14, 16, 8, 10, 10]},
                {"name": "Seraphina", "race": "Tiefling", "class": "Cleric", "level": 1, "stats": [12, 10, 14, 10, 16, 14]}
            ]
            
            for char in party_config:
                create_character(page, char['name'], char['race'], char['class'], char['level'], char['stats'])
                
            # ---------------------------------------------------------
            # 3. Assemble Party
            # ---------------------------------------------------------
            assemble_party(page, party_config)
            
            # ---------------------------------------------------------
            # 4. Start Game
            # ---------------------------------------------------------
            print("\n🎮 Starting Game...")
            click_tab(page, "🎮 Play Game")
            
            # Select Party Mode
            # Finding the radio button for Party Mode
            # Gradio radio buttons are often labels.
            print("   Switching to Party Mode...")
            page.get_by_label("Party Mode").check()
            time.sleep(1)
            
            # Load Party
            print("   Loading Party...")
            page.get_by_role("button", name="Load Party").click()
            time.sleep(5)
            
            print("\n🗺️  THE ADVENTURE BEGINS! (Press Ctrl+C to stop)")
            
            turn = 0
            while True:
                turn += 1
                print(f"\n🔹 Turn {turn}")
                
                # Get Context
                last_response = get_last_bot_message(page)
                enemies = extract_enemies(last_response)
                
                action = ""
                
                # Decision Logic
                if "Initiative Order" in last_response or "COMBAT" in last_response or len(enemies) > 0:
                    # Combat Mode
                    print(f"⚔️  Combat detected! Enemies: {enemies}")
                    if not enemies: enemies = ["Enemy"]
                    target = enemies[0]
                    
                    combat_actions = [
                        f"The party focuses fire on the {target}!",
                        f"Sir Gideon smites the {target} with his longsword!",
                        f"Lyra casts Magic Missile at the {target}!",
                        f"Thonk rages and recklessly attacks the {target}!",
                        f"Garret attempts a sneak attack on the {target}!",
                        f"Seraphina casts Bless on the party!",
                        "The party coordinates a massive assault!"
                    ]
                    action = random.choice(combat_actions)
                    
                    # Occasionally verify kills
                    if "dead" in last_response.lower() or "defeated" in last_response.lower():
                        action = "/end_combat"
                        print("   Ending combat...")
                else:
                    # Exploration Mode
                    print("🌲 Exploration mode")
                    explore_actions = [
                        "/explore",
                        "We investigate the area for loot.",
                        "We travel to the nearest dungeon.",
                        "We look for trouble.",
                        "We search for monsters to fight.",
                        "The party sets up camp for a short rest.",
                        "We head towards the dark forest.",
                        "We ask around for rumors of dragons."
                    ]
                    
                    # 30% chance to start combat explicitly if boring
                    if random.random() < 0.3:
                        mob = random.choice(["Orcs", "Bandits", "Skeletons", "Trolls"])
                        action = f"/start_combat {mob}"
                    else:
                        action = random.choice(explore_actions)
                
                # Send Action
                print(f"👉 Action: {action}")
                send_message(page, action)
                
                # Wait for readability (longer for demo)
                time.sleep(8) 
                
        except KeyboardInterrupt:
            print("\n👋 Demo stopped by user.")
        except Exception as e:
            print(f"\n❌ Demo Error: {e}")
            page.screenshot(path="demo_failure.png")
        finally:
            browser.close()
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    demo_endless_adventure()
