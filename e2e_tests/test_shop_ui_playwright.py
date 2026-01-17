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
    get_character_sheet_text
)

def extract_gold_and_inventory(sheet_text: str):
    """Extract gold and inventory items from character sheet text."""
    gold_match = re.search(r'Gold:\s*(\d+)\s*GP', sheet_text, re.IGNORECASE)
    gold = int(gold_match.group(1)) if gold_match else 0

    inventory_match = re.search(r'### 🎒 Inventory\n(.*?)(?=\n###|\Z)', sheet_text, re.DOTALL | re.IGNORECASE)
    inventory_items = []
    if inventory_match:
        inventory_block = inventory_match.group(1).strip()
        if inventory_block and inventory_block != "*Empty*":
            inventory_items = [line.strip().replace('- ', '') for line in inventory_block.split('\n')]
    return gold, inventory_items

def test_shop_ui_playwright():
    """
    Test: Shop System UI Integration (Playwright)
    Verifies /buy and /sell commands, and character sheet updates.
    """
    print("\n" + "🛒" * 40)
    print("TEST: Shop System UI Integration (Playwright)")
    print("🛒" * 40)
    
    # Ensure port 7860 is free
    kill_port(7860)
    
    # Start Gradio server in a shop-friendly location
    print("\n🚀 Starting Gradio server (Location: The Market Square)...")
    env = os.environ.copy()
    env['TEST_START_LOCATION'] = 'The Market Square'
    gradio_process = subprocess.Popen(
        ['python3', 'web/app_gradio.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(10) # Give server time to start
    
    with sync_playwright() as p:
        # Allow HEADLESS env var to show GUI: HEADLESS=false python3 test.py
        headless_mode = os.getenv('HEADLESS', 'true').lower() != 'false'
        browser = p.chromium.launch(headless=headless_mode)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:7860")
            wait_for_gradio(page)
            
            # Load Thorin
            print("\n📝 Loading Thorin...")
            load_character(page, "Thorin")

            # Send /stats to ensure character sheet is fully populated
            send_message(page, "/stats")
            time.sleep(3)  # Give UI time to fully update and render stats

            # Get initial stats from the response
            initial_response = get_last_bot_message(page)
            initial_gold, initial_inventory = extract_gold_and_inventory(initial_response)

            print(f"DEBUG: Stats response length: {len(initial_response)}")
            print(f"DEBUG: Stats response preview:\n{initial_response[:800]}")
            print(f"DEBUG: Extracted - Gold={initial_gold}, Inventory={initial_inventory}")
            
            # 1. Buy an item (Rope, cost 1 GP)
            print("\n" + "=" * 80)
            print("TEST 1: Buy 'rope'")
            print("=" * 80)
            
            send_message(page, "/buy rope")
            buy_response = get_last_bot_message(page)
            print(f"   GM: {buy_response[:100]}...")
            
            # Verify success response
            expect(page.locator("body")).to_contain_text("Purchase successful!")
            expect(page.locator("body")).to_contain_text("rope")
            print("✅ Buy command successful response.")
            
            # Check inventory and gold after purchase
            send_message(page, "/stats")
            stats_response = get_last_bot_message(page)
            current_gold, current_inventory = extract_gold_and_inventory(stats_response)

            # Use Python assertions for integer/boolean comparisons
            assert current_gold == initial_gold - 1, f"Expected gold={initial_gold - 1}, got {current_gold}"
            assert any("rope" in item.lower() for item in current_inventory), f"Rope not found in inventory: {current_inventory}"
            print("✅ Inventory and gold updated after purchase.")
            
            # 2. Sell an item (Longsword, initially equipped)
            print("\n" + "=" * 80)
            print("TEST 2: Sell 'longsword'")
            print("=" * 80)
            
            # Find a longsword in inventory, if not, try another item or skip
            # For simplicity, assume longsword is equipped and we want to sell it.
            # Longsword in Thorin's initial equipment, assume it's also in inventory
            
            send_message(page, "/sell longsword")
            sell_response = get_last_bot_message(page)
            print(f"   GM: {sell_response[:100]}...")
            
            # Verify success response
            expect(page.locator("body")).to_contain_text("Sold 1x Longsword")
            print("✅ Sell command successful response.")
            
            # Check inventory and gold after sale
            send_message(page, "/stats")
            stats_response_after_sell = get_last_bot_message(page)
            final_gold, final_inventory = extract_gold_and_inventory(stats_response_after_sell)

            # Use Python assertions for integer/boolean comparisons
            assert final_gold > current_gold, f"Expected gold to increase from {current_gold}, got {final_gold}"
            assert not any("longsword" in item.lower() for item in final_inventory), f"Longsword should be sold, but found in: {final_inventory}"
            print("✅ Inventory and gold updated after sale.")
            
            print("\n✅ All Shop UI Integration Tests Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="shop_ui_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_shop_ui_playwright()
