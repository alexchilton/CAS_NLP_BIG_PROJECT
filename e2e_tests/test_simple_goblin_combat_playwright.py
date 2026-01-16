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
    kill_port,
    analyze_response # This helper includes damage/death analysis
)

class CombatTestResults:
    """Track test results (similar to original Selenium test)."""
    def __init__(self):
        self.npc_damage_events = []
        self.npc_death_confirmed = False
        self.double_turn_detected = False
        self.hp_calculations_correct = True # Not directly tested here
        self.wrong_npc_detected = False # Not directly tested here
        self.errors = []

def extract_npc_damage_and_hp(response_text):
    """
    Extract NPC damage, current HP, and max HP from a combat response.
    Returns a dict or None.
    """
    # Pattern: "💥 Goblin takes 8 slashing damage! (HP: 4/12)"
    pattern = r"💥\s+(?P<npc>\w+)\s+takes\s+(?P<damage>\d+)\s+\w+\s+damage!.*?HP:\s*(?P<current_hp>\d+)/(?P<max_hp>\d+)"
    match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)

    if match:
        return {
            "npc": match.group("npc"),
            "damage": int(match.group("damage")),
            "current_hp": int(match.group("current_hp")),
            "max_hp": int(match.group("max_hp")),
            "dead": False
        }

    # Pattern for death: "💥 Goblin takes 8 slashing damage and dies! ☠️"
    death_pattern = r"💥\s+(?P<npc>\w+)\s+takes\s+(?P<damage>\d+)\s+\w+\s+damage\s+and\s+dies!"
    death_match = re.search(death_pattern, response_text, re.IGNORECASE | re.DOTALL)

    if death_match:
        return {
            "npc": death_match.group("npc"),
            "damage": int(death_match.group("damage")),
            "current_hp": 0,
            "max_hp": None, # Max HP might not be present in death message
            "dead": True
        }
    return None

def test_simple_goblin_combat_playwright():
    """
    Test: Simple Combat - 1 Player vs 1 Goblin (Playwright)
    """
    print("\n" + "🗡️" * 40)
    print("TEST: Simple Combat (Playwright)")
    print("🗡️" * 40)
    
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
            
            # Start combat explicitly
            print("\n" + "=" * 80)
            print("⚔️  STARTING COMBAT WITH GOBLIN")
            print("=" * 80)
            
            send_message(page, "/start_combat Goblin")
            time.sleep(3)
            
            combat_start_response = get_last_bot_message(page)
            expect(page.locator("body")).to_contain_text("Initiative Order")
            print("✅ Combat started.")
            
            # Combat loop
            results = CombatTestResults()
            max_attacks = 15 # Max attacks to ensure death or timeout
            
            print("\n🗡️ Thorin attacks the Goblin!")
            
            for attack_num in range(1, max_attacks + 1):
                print(f"\n--- Attack #{attack_num} ---")
                
                send_message(page, "I attack the goblin with my longsword")
                time.sleep(5) # Wait for response
                
                response = get_last_bot_message(page)
                print(f"   GM: {response[:200]}...")
                
                # Analyze response for damage/death
                combat_event = extract_npc_damage_and_hp(response)
                if combat_event:
                    results.npc_damage_events.append(combat_event)
                    if combat_event["dead"]:
                        results.npc_death_confirmed = True
                        break # Goblin is dead
                
                # Check for double NPC turns (simplified - just look for repeated initiative)
                if "goblin's turn" in response.lower() and re.findall(r"goblin's turn", response.lower()).count > 1:
                     results.double_turn_detected = True
                     results.errors.append("Double turn detected in response.")
                
            expect(results.npc_death_confirmed).to_be_true()
            print("✅ Goblin confirmed dead!")
            
            if results.double_turn_detected:
                print("❌ Double turn bug detected!")
            
            send_message(page, "/end_combat")
            print("✅ Combat ended.")
            
            print("\n✅ Simple Combat Test Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="simple_goblin_combat_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_simple_goblin_combat_playwright()
