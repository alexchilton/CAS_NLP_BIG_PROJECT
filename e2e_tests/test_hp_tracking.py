#!/usr/bin/env python3
"""
Diagnostic Test: Track Skeleton HP During Spell Combat

This test monitors the skeleton's actual HP to see if damage is being applied.
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
    print(f"\n💬 Player: {message}")
    
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


def extract_skeleton_hp(response):
    """Extract skeleton HP from GM response."""
    # Look for patterns like "HP: 7/13" or "Skeleton (7/13 HP)"
    patterns = [
        r'Skeleton.*?(\d+)/(\d+)\s*HP',
        r'HP:\s*(\d+)/(\d+)',
        r'\((\d+)/(\d+)\s*HP\)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            current = int(match.group(1))
            max_hp = int(match.group(2))
            return current, max_hp
    
    return None, None


def test_hp_tracking():
    """Test that tracks skeleton HP after each spell."""
    print("\n" + "🔬" * 40)
    print("DIAGNOSTIC: Skeleton HP Tracking During Spell Combat")
    print("🔬" * 40)
    
    driver = setup_chrome_driver()
    
    try:
        driver.get("http://localhost:7860")
        wait_for_gradio(driver)
        
        load_character(driver, "Elara")
        
        print("\n" + "=" * 80)
        print("Starting combat and checking initial skeleton HP")
        print("=" * 80)
        
        response = send_message(driver, "/start_combat Skeleton", wait_time=8)
        
        # Try to get initial skeleton HP
        current_hp, max_hp = extract_skeleton_hp(response)
        if max_hp:
            print(f"🐉 Skeleton initial HP: {current_hp}/{max_hp}")
        else:
            print("⚠️  Could not extract skeleton HP from combat start")
            print(f"Response: {response[:300]}")
        
        # Track HP changes across spell casts
        spells = [
            ("Magic Missile", "I cast Magic Missile at the skeleton"),
            ("Fire Bolt", "I cast Fire Bolt at the skeleton"),
            ("Magic Missile", "I cast Magic Missile at the skeleton"),
            ("Fire Bolt", "I cast Fire Bolt at the skeleton"),
        ]
        
        hp_history = []
        if max_hp:
            hp_history.append(("Start", current_hp, max_hp, 0))
        
        for i, (spell_name, spell_action) in enumerate(spells, 1):
            print(f"\n{'=' * 80}")
            print(f"Round {i}: Casting {spell_name}")
            print(f"{'=' * 80}")
            
            response = send_message(driver, spell_action, wait_time=10)
            
            # Extract HP from response
            new_hp, new_max = extract_skeleton_hp(response)
            
            # Check for damage mentions
            damage_match = re.search(r'(\d+)\s+(?:fire|force|damage)', response, re.IGNORECASE)
            mentioned_damage = int(damage_match.group(1)) if damage_match else None
            
            # Check for mechanics output
            has_mechanics = "⚙️ MECHANICS:" in response
            
            # Check if skeleton died
            is_dead = "dies" in response.lower() or "defeated" in response.lower()
            
            print(f"\n📊 Analysis:")
            print(f"   Spell: {spell_name}")
            
            if new_hp is not None:
                damage_dealt = (current_hp - new_hp) if current_hp else 0
                print(f"   HP: {new_hp}/{new_max} (was {current_hp}/{max_hp})")
                print(f"   Damage applied: {damage_dealt}")
                hp_history.append((spell_name, new_hp, new_max, damage_dealt))
                current_hp = new_hp
            else:
                print(f"   HP: NOT FOUND in response")
                print(f"   (Could not track HP change)")
            
            if mentioned_damage:
                print(f"   Damage mentioned: {mentioned_damage}")
            
            print(f"   Mechanics section: {'YES' if has_mechanics else 'NO'}")
            
            if is_dead:
                print(f"\n💀 Skeleton defeated!")
                break
            
            # Show snippet of response
            print(f"\n   Response snippet:")
            print(f"   {response[:200]}...")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 HP TRACKING SUMMARY")
        print("=" * 80)
        
        if hp_history:
            print(f"\n{'Event':<20} {'HP':<10} {'Damage':<10}")
            print("-" * 40)
            for event, hp, max_hp, damage in hp_history:
                print(f"{event:<20} {hp}/{max_hp:<10} {damage if damage else '-':<10}")
        else:
            print("⚠️  No HP data was tracked - HP extraction failed")
        
        # Check for pattern
        damages = [d for _, _, _, d in hp_history if d > 0]
        if damages:
            print(f"\n✅ Damage was applied {len(damages)} times")
            print(f"   Average damage: {sum(damages)/len(damages):.1f}")
        else:
            print(f"\n❌ No damage was tracked across {len(spells)} spell casts")
            print(f"   This suggests damage isn't being applied or HP isn't being shown")
        
        send_message(driver, "/end_combat", wait_time=3)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()


if __name__ == "__main__":
    test_hp_tracking()
