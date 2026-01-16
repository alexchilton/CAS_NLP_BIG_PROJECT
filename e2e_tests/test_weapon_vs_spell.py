#!/usr/bin/env python3
"""
Test: Compare Weapon Attack vs Spell Damage Tracking

Tests if HP tracking works differently for:
1. Weapon attacks (e.g., "I attack with my longsword")
2. Spell attacks (e.g., "I cast Fire Bolt")
"""

import sys
import time
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium_helpers import (
    load_character,
    wait_for_gradio,
    find_chat_input,
    find_send_button,
    setup_chrome_driver
)
from selenium.webdriver.common.by import By


def send_message(driver, message, wait_time=10):
    """Send message and return response."""
    print(f"\n💬 {message}")
    
    chat_input = find_chat_input(driver)
    chat_input.clear()
    chat_input.send_keys(message)
    
    send_btn = find_send_button(driver)
    send_btn.click()
    
    time.sleep(wait_time)
    
    messages = driver.find_elements(By.CSS_SELECTOR, "[data-testid='bot'], .message")
    if messages:
        return messages[-1].text
    return ""


def analyze_response(response, action_type):
    """Analyze GM response for damage tracking."""
    print(f"\n📊 {action_type} Analysis:")
    
    # Check for damage mentions
    damage_pattern = re.search(r'(\d+)\s+(?:damage|fire|slashing|piercing|force)', response, re.IGNORECASE)
    if damage_pattern:
        print(f"   ✅ Damage mentioned: {damage_pattern.group(1)}")
    else:
        print(f"   ❌ No damage mentioned")
    
    # Check for HP tracking
    hp_pattern = re.search(r'(?:HP|health).*?(\d+)/(\d+)', response, re.IGNORECASE)
    if hp_pattern:
        print(f"   ✅ HP shown: {hp_pattern.group(1)}/{hp_pattern.group(2)}")
    else:
        print(f"   ❌ No HP shown")
    
    # Check for mechanics section
    has_mechanics = "⚙️ MECHANICS:" in response
    print(f"   Mechanics section: {'✅ YES' if has_mechanics else '❌ NO'}")
    
    # Check for death
    is_dead = "dies" in response.lower() or "defeated" in response.lower() or "falls" in response.lower()
    if is_dead:
        print(f"   💀 Enemy defeated!")
    
    print(f"\n   Response preview:")
    print(f"   {response[:250]}...")
    
    return is_dead


def test_weapon_vs_spell_tracking():
    """Compare tracking between weapon and spell attacks."""
    print("\n" + "⚔️" * 40)
    print("TEST: Weapon Attack vs Spell Damage Tracking")
    print("⚔️" * 40)
    
    driver = setup_chrome_driver()
    
    try:
        driver.get("http://localhost:7860")
        wait_for_gradio(driver)
        
        # Test 1: Thorin with weapon attacks
        print("\n" + "=" * 80)
        print("TEST 1: THORIN (Fighter) - Weapon Attacks")
        print("=" * 80)
        
        load_character(driver, "Thorin")
        
        response = send_message(driver, "/start_combat Goblin", wait_time=8)
        print(f"\nCombat started!")
        
        # Weapon attack 1
        print(f"\n--- Weapon Attack 1: Longsword ---")
        response = send_message(driver, "I attack the goblin with my longsword", wait_time=10)
        dead = analyze_response(response, "Weapon Attack")
        
        if not dead:
            # Weapon attack 2
            print(f"\n--- Weapon Attack 2: Longsword ---")
            response = send_message(driver, "I attack the goblin with my longsword", wait_time=10)
            dead = analyze_response(response, "Weapon Attack")
        
        send_message(driver, "/end_combat", wait_time=3)
        
        # Test 2: Elara with spell attacks
        print("\n\n" + "=" * 80)
        print("TEST 2: ELARA (Wizard) - Spell Attacks")
        print("=" * 80)
        
        # Refresh page to ensure clean state for dropdown
        print("🔄 Refreshing page to reset UI state...")
        driver.refresh()
        wait_for_gradio(driver)
        
        load_character(driver, "Elara")
        
        response = send_message(driver, "/start_combat Goblin", wait_time=8)
        print(f"\nCombat started!")
        
        # Spell attack 1: Magic Missile
        print(f"\n--- Spell Attack 1: Magic Missile ---")
        response = send_message(driver, "I cast Magic Missile at the goblin", wait_time=10)
        dead = analyze_response(response, "Magic Missile")
        
        if not dead:
            # Spell attack 2: Fire Bolt
            print(f"\n--- Spell Attack 2: Fire Bolt ---")
            response = send_message(driver, "I cast Fire Bolt at the goblin", wait_time=10)
            dead = analyze_response(response, "Fire Bolt")
        
        if not dead:
            # Spell attack 3: Magic Missile again
            print(f"\n--- Spell Attack 3: Magic Missile ---")
            response = send_message(driver, "I cast Magic Missile at the goblin", wait_time=10)
            dead = analyze_response(response, "Magic Missile")
        
        send_message(driver, "/end_combat", wait_time=3)
        
        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print("\nConclusion:")
        print("- Check if weapon attacks show HP/damage mechanics")
        print("- Check if spell attacks show HP/damage mechanics")
        print("- If weapon attacks work but spells don't, it's a spell-specific bug")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()


if __name__ == "__main__":
    test_weapon_vs_spell_tracking()
