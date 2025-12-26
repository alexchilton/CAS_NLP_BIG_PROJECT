#!/usr/bin/env python3
"""
Automated Adventure Simulation - Random Travel & Combat Until Death

This test simulates a full adventure:
1. Load character (Thorin)
2. Explore and travel randomly
3. Fight any creatures encountered
4. Continue until character dies (game over)
5. Show everything in Selenium browser
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def setup_browser():
    """Setup Chrome with visible window."""
    options = Options()
    options.add_argument('--start-maximized')
    # Don't run headless - we want to SEE it!
    driver = webdriver.Chrome(options=options)
    return driver

def wait_for_response(driver, previous_count, timeout=30):
    """Wait for new GM response."""
    start = time.time()
    while time.time() - start < timeout:
        messages = driver.find_elements(By.CSS_SELECTOR, '.message')
        current_count = len(messages)
        if current_count > previous_count:
            # Skip "Loading..." messages
            last_msg = messages[-1].text if messages else ""
            if "Loading" not in last_msg and len(last_msg) > 10:
                return current_count
        time.sleep(0.5)
    return previous_count

def get_chat_messages(driver):
    """Get all chat messages."""
    messages = driver.find_elements(By.CSS_SELECTOR, '.message')
    return [msg.text for msg in messages if msg.text and "Loading" not in msg.text]

def send_message(driver, text):
    """Send a message and wait for response."""
    # Get current message count
    messages_before = len(get_chat_messages(driver))
    
    # Find and fill input
    textarea = driver.find_element(By.CSS_SELECTOR, 'textarea[placeholder*="Type"]')
    textarea.clear()
    textarea.send_keys(text)
    
    # Click submit
    submit_btn = driver.find_element(By.CSS_SELECTOR, 'button.primary')
    submit_btn.click()
    
    # Wait for response
    time.sleep(2)
    messages_after = wait_for_response(driver, messages_before, timeout=30)
    
    # Get latest response
    all_messages = get_chat_messages(driver)
    return all_messages[-1] if all_messages else ""

def get_hp_from_sheet(driver):
    """Extract HP from character sheet."""
    try:
        # Look for HP in character sheet
        sheet = driver.find_element(By.CSS_SELECTOR, 'textarea[label="Character Sheet"]')
        text = sheet.get_attribute('value')
        
        # Parse HP: "HP: 28/28" or "HP: 0/28 💀"
        for line in text.split('\n'):
            if 'HP:' in line:
                hp_part = line.split('HP:')[1].strip()
                current = hp_part.split('/')[0].strip()
                # Remove emoji and extra text
                current = ''.join(c for c in current if c.isdigit() or c == '-')
                return int(current) if current else 0
    except Exception as e:
        print(f"⚠️  Could not parse HP: {e}")
    return None

def extract_creatures(response):
    """Try to find creature names in GM response."""
    creatures = []
    keywords = ['goblin', 'dragon', 'wolf', 'orc', 'skeleton', 'zombie', 
                'bandit', 'troll', 'spider', 'rat', 'bear', 'snake']
    
    response_lower = response.lower()
    for keyword in keywords:
        if keyword in response_lower:
            creatures.append(keyword.title())
    
    return creatures

def main():
    print("=" * 80)
    print("🎮 AUTOMATED ADVENTURE SIMULATION")
    print("=" * 80)
    print("\nStarting Gradio app...")
    print("Make sure you run: python web/app_gradio.py")
    print("\nPress Enter when app is running...")
    input()
    
    driver = setup_browser()
    
    try:
        # Navigate to app
        print("\n📱 Opening browser...")
        driver.get("http://localhost:7860")
        time.sleep(3)
        
        # Click "Play Game" tab
        print("🎲 Switching to Play Game tab...")
        tabs = driver.find_elements(By.CSS_SELECTOR, 'button.tab-nav')
        for tab in tabs:
            if 'Play Game' in tab.text:
                tab.click()
                time.sleep(1)
                break
        
        # Load character - just type the load command directly
        print("⚔️  Loading Thorin Stormshield...")
        time.sleep(2)
        
        # Send load command directly via chat
        response = send_message(driver, "/load_char Thorin Stormshield")
        print(f"Load response: {response[:200]}...")
        time.sleep(2)
        
        print("✅ Character loaded!\n")
        
        # Start adventure
        print("=" * 80)
        print("🗺️  ADVENTURE BEGINS!")
        print("=" * 80)
        
        turn = 0
        max_turns = 50  # Safety limit
        in_combat = False
        current_enemy = None
        
        while turn < max_turns:
            turn += 1
            
            # Check HP
            hp = get_hp_from_sheet(driver)
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
                    response = send_message(driver, action)
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
                    response = send_message(driver, action)
                    print(f"GM: {response[:300]}...")
                    
                    creatures = extract_creatures(response)
                    if creatures:
                        print(f"⚠️  CREATURE SPOTTED: {creatures[0]}!")
                        current_enemy = creatures[0]
                        in_combat = True
                
                else:
                    # Move to a new area (use travel or natural language)
                    if random.random() < 0.5:
                        destinations = ['Dark Forest', 'Mountain Road', 'Old Ruins', 
                                      'Temple District', 'Market Square', 'Forest Path',
                                      'Town Gates', 'Town Square']
                        dest = random.choice(destinations)
                        print(f"\n🚶 Turn {turn}: Traveling to {dest}...")
                        response = send_message(driver, f"I travel to {dest}")
                    else:
                        directions = [
                            "I head north down the path",
                            "I venture east into the forest",
                            "I travel south along the road",
                            "I go west toward the mountains",
                            "I follow the road ahead",
                            "I leave this place and continue my journey"
                        ]
                        direction = random.choice(directions)
                        print(f"\n🚶 Turn {turn}: {direction}")
                        response = send_message(driver, direction)
                    
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
                if 'combat' not in response.lower() and 'initiative' not in response.lower():
                    response = send_message(driver, f"/start_combat {current_enemy}")
                    print(f"Combat started: {response[:200]}...")
                
                # Attack
                attack_variations = [
                    f"I attack the {current_enemy} with my battleaxe",
                    f"I swing at the {current_enemy}",
                    f"I strike the {current_enemy}",
                    f"I attack {current_enemy}"
                ]
                attack = random.choice(attack_variations)
                
                response = send_message(driver, attack)
                print(f"Attack: {response[:250]}...")
                
                # Check if enemy died
                if 'dead' in response.lower() or 'dies' in response.lower() or 'falls' in response.lower():
                    print(f"✅ {current_enemy} defeated!")
                    in_combat = False
                    current_enemy = None
                    
                    # End combat
                    time.sleep(2)
                    send_message(driver, "/end_combat")
                
                # Check our HP
                time.sleep(1)
                hp = get_hp_from_sheet(driver)
                if hp is not None and hp <= 0:
                    print(f"\n💀 Thorin has fallen in battle against {current_enemy}!")
                    break
            
            # Pause between turns
            time.sleep(3)
        
        if turn >= max_turns:
            print("\n⏱️  Adventure ended - max turns reached")
        
        print("\n" + "=" * 80)
        print("🏁 ADVENTURE COMPLETE")
        print("=" * 80)
        print(f"\nTotal turns: {turn}")
        print(f"Final HP: {get_hp_from_sheet(driver)}")
        
        # Keep browser open
        print("\n👀 Browser will stay open for 30 seconds...")
        time.sleep(30)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Keep browser open on error
        print("\n👀 Error occurred - browser staying open for inspection...")
        time.sleep(60)
    
    finally:
        driver.quit()
        print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
