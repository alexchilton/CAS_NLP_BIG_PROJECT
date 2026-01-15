#!/usr/bin/env python3
"""
E2E Test: Elara (Wizard) vs Skeletons - Spell Combat

Simple, direct test:
1. Load Elara (Wizard)
2. Start combat with Skeleton (explicit)
3. Use wizard spells to defeat it
4. Track combat rounds and outcome
"""

import sys
import time
from pathlib import Path

# Add project to path
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
    """Send a message and wait for response."""
    print(f"\n💬 Player: {message}")
    
    chat_input = find_chat_input(driver)
    chat_input.clear()
    chat_input.send_keys(message)
    
    send_btn = find_send_button(driver)
    send_btn.click()
    
    time.sleep(wait_time)
    
    # Get last GM response
    messages = driver.find_elements(By.CSS_SELECTOR, "[data-testid='bot'], .message")
    if messages:
        last_msg = messages[-1].text
        print(f"🎭 GM: {last_msg[:300]}...")
        return last_msg
    return ""


def test_elara_skeleton_battle():
    """Elara fights skeletons using wizard spells."""
    print("\n" + "🔮" * 40)
    print("ELARA VS SKELETONS - WIZARD SPELL COMBAT TEST")
    print("🔮" * 40)
    print("\n⚠️  NOTE: Connects to running Gradio at http://localhost:7860")
    print("🔮" * 40)
    
    driver = setup_chrome_driver()
    
    try:
        # Setup
        print("\n📍 Opening Gradio...")
        driver.get("http://localhost:7860")
        wait_for_gradio(driver)
        
        # Load Elara
        load_character(driver, "Elara")
        
        # Start combat explicitly
        print("\n" + "=" * 80)
        print("⚔️  STARTING COMBAT WITH SKELETON")
        print("=" * 80)
        
        send_message(driver, "/start_combat Skeleton", wait_time=8)
        
        # Combat loop
        round_num = 1
        max_rounds = 15
        
        # Wizard spell rotation
        spells = [
            "I cast Magic Missile at the skeleton",
            "I cast Fire Bolt at the skeleton",
            "I attack the skeleton with my quarterstaff"
        ]
        
        print("\n🔮 Elara begins casting spells!")
        
        while round_num <= max_rounds:
            print(f"\n{'=' * 80}")
            print(f"⚔️  ROUND {round_num}")
            print(f"{'=' * 80}")
            
            # Cast spell
            spell = spells[(round_num - 1) % len(spells)]
            response = send_message(driver, spell, wait_time=10)
            
            # Check if combat ended
            response_lower = response.lower()
            
            if "dies" in response_lower or "defeated" in response_lower or "falls" in response_lower:
                print(f"\n{'✨' * 40}")
                print("⚔️  SKELETON DEFEATED!")
                print(f"✨ Elara won in {round_num} rounds using wizard spells!")
                print(f"{'✨' * 40}\n")
                break
            
            if "you die" in response_lower or "you have fallen" in response_lower or "game over" in response_lower:
                print(f"\n{'💀' * 40}")
                print("💀 ELARA HAS FALLEN IN COMBAT!")
                print(f"{'💀' * 40}\n")
                break
            
            round_num += 1
            time.sleep(2)
        
        if round_num > max_rounds:
            print(f"\n⏱️  Combat reached maximum rounds ({max_rounds})")
        
        # End combat
        send_message(driver, "/end_combat", wait_time=3)
        
        print("\n" + "=" * 80)
        print("✅ WIZARD SPELL COMBAT TEST COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Combat Summary:")
        print(f"   Character: Elara (Wizard)")
        print(f"   Enemy: Skeleton")
        print(f"   Rounds: {round_num}")
        print(f"   Spells Used: Magic Missile, Fire Bolt, Quarterstaff")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            driver.save_screenshot('/tmp/elara_skeleton_error.png')
            print("\n📸 Screenshot saved to: /tmp/elara_skeleton_error.png")
        except:
            pass
        
        raise
    
    finally:
        driver.quit()
        print("\n✅ Browser closed")


if __name__ == "__main__":
    test_elara_skeleton_battle()
