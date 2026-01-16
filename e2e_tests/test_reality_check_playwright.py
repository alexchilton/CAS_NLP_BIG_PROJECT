from playwright.sync_api import sync_playwright, expect
import time
from pathlib import Path
import sys
import os
import subprocess
import signal
import re

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from e2e_tests.playwright_helpers import (
    wait_for_gradio,
    load_character,
    send_message,
    get_last_bot_message,
    kill_port
)

def check_response_validity(response: str, should_reject: bool = False, keywords: list = []) -> bool:
    """
    Check if GM response is valid based on Reality Check expectations.
    Returns True if the response matches the expectation.
    """
    response_lower = response.lower()

    if should_reject:
        # Response should indicate rejection/failure without hallucinating the entity
        rejection_phrases = [
            "no", "don't", "can't", "isn't", "not", "empty",
            "nothing", "nowhere", "impossible", "not a wizard", "don't have"
        ]
        has_rejection = any(phrase in response_lower for phrase in rejection_phrases)

        # Check for hallucination (if the GM describes the non-existent thing as real)
        has_hallucination = any(keyword.lower() in response_lower for keyword in keywords)
        
        # If it should reject, it must have a rejection phrase AND NOT hallucinate the item/entity
        return has_rejection and not has_hallucination
    else:
        # Valid action - should proceed normally, no strong rejection
        has_rejection = any(phrase in response_lower for phrase in ["no", "don't", "can't", "isn't", "not", "impossible"])
        return not has_rejection

def test_reality_check_playwright():
    """
    Test: Reality Check System (Playwright)
    Verifies that the GM correctly handles valid and invalid actions.
    """
    print("\n" + "✅" * 40)
    print("TEST: Reality Check System (Playwright)")
    print("✅" * 40)
    
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
            
            # 1. Invalid Combat Target (Goblin Doesn't Exist)
            print("\n" + "=" * 80)
            print("TEST 1: Invalid Combat Target (Goblin Doesn't Exist)")
            print("=" * 80)
            
            send_message(page, "I attack the goblin with my longsword")
            response = get_last_bot_message(page)
            print(f"   GM: {response[:150]}...")
            
            assert check_response_validity(response, should_reject=True, keywords=["goblin"])
            print("✅ GM correctly rejected attack on non-existent goblin.")
            
            # 2. Invalid Item Use (Bow Not In Inventory)
            print("\n" + "=" * 80)
            print("TEST 2: Invalid Item Use (Bow Not In Inventory)")
            print("=" * 80)
            
            send_message(page, "I ready my bow and prepare to shoot")
            response = get_last_bot_message(page)
            print(f"   GM: {response[:150]}...")
            
            assert check_response_validity(response, should_reject=True, keywords=["bow", "arrow"])
            print("✅ GM correctly rejected using non-existent bow.")
            
            # 3. Valid Item Use (Longsword In Inventory)
            print("\n" + "=" * 80)
            print("TEST 3: Valid Item Use (Longsword In Inventory)")
            print("=" * 80)
            
            send_message(page, "I draw my longsword and hold it ready")
            response = get_last_bot_message(page)
            print(f"   GM: {response[:150]}...")
            
            assert check_response_validity(response, should_reject=False)
            print("✅ GM allowed using item from inventory.")
            
            # 4. Fighter Tries to Cast Spell (Invalid)
            print("\n" + "=" * 80)
            print("TEST 4: Fighter Tries to Cast Spell")
            print("=" * 80)
            
            send_message(page, "I cast Fireball at the dragon!")
            response = get_last_bot_message(page)
            print(f"   GM: {response[:150]}...")
            
            assert check_response_validity(response, should_reject=True, keywords=["fireball", "spell", "dragon"])
            print("✅ GM correctly rejected fighter casting spell.")
            
            print("\n✅ All Reality Check Tests Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="reality_check_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_reality_check_playwright()
