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
    load_character, # This is the helper for loading characters
    click_tab,
    kill_port,
    get_character_sheet_text
)

def test_character_loading_playwright():
    """
    Test: Character Loading and Verification (Playwright)
    """
    print("\n" + "\u2714" * 40)
    print("TEST: Character Loading (Playwright)")
    print("\u2714" * 40)
    
    # Ensure port 7860 is free
    kill_port(7860)
    
    # Start Gradio server
    print("\n\U0001f680 Starting Gradio server...")
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
            
            # 1. Load Thorin and verify
            print("\n" + "=" * 80)
            print("TEST 1: Load Thorin Stormshield")
            print("=" * 80)
            
            load_character(page, "Thorin") # Using the playwright_helpers.load_character
            full_sheet = get_character_sheet_text(page)
            print(f"   Sheet preview: {full_sheet[:200]}...")
            
            expect(page.locator("body")).to_contain_text("Thorin") # Check overall body for character name
            expect(page.locator("body")).to_contain_text("Dwarf")
            expect(page.locator("body")).to_contain_text("Fighter")
            print("✅ Thorin loaded and verified.")
            
            # 2. Load Elara and verify
            print("\n" + "=" * 80)
            print("TEST 2: Load Elara Moonwhisper")
            print("=" * 80)
            
            # Reload page for clean state before loading new character
            page.reload()
            wait_for_gradio(page)
            load_character(page, "Elara")
            full_sheet = get_character_sheet_text(page)
            
            expect(page.locator("body")).to_contain_text("Elara")
            expect(page.locator("body")).to_contain_text("Elf")
            expect(page.locator("body")).to_contain_text("Wizard")
            print("✅ Elara loaded and verified.")
            
            # 3. Verify Character Stats Displayed
            print("\n" + "=" * 80)
            print("TEST 3: Character Stats Displayed")
            print("=" * 80)
            
            # Assume Thorin is loaded from Test 1
            page.reload()
            wait_for_gradio(page)
            load_character(page, "Thorin")
            full_sheet = get_character_sheet_text(page)
            
            stat_abbreviations = ["STR", "DEX", "CON", "INT", "WIS", "CHA", "HP:", "AC:"]
            for stat in stat_abbreviations:
                expect(page.locator("body")).to_contain_text(stat)
            print("✅ All key stats (STR, HP, AC, etc.) displayed.")
            
            # 4. Verify Equipment Displayed
            print("\n" + "=" * 80)
            print("TEST 4: Equipment Displayed")
            print("=" * 80)
            
            # Still Thorin
            expect(page.locator("body")).to_contain_text("Equipment")
            expect(page.locator("body")).to_contain_text("Longsword")
            expect(page.locator("body")).to_contain_text("Shield")
            print("✅ Equipment (Longsword, Shield) displayed.")
            
            # 5. Verify Wizard Spells Displayed
            print("\n" + "=" * 80)
            print("TEST 5: Wizard Spells Displayed")
            print("=" * 80)
            
            load_character(page, "Elara") # Load Elara again
            
            expect(page.locator("body")).to_contain_text("Spells")
            expect(page.locator("body")).to_contain_text("Magic Missile")
            expect(page.locator("body")).to_contain_text("Fire Bolt")
            print("✅ Wizard spells (Magic Missile, Fire Bolt) displayed.")
            
            # 6. Test Switch Between Characters
            print("\n" + "=" * 80)
            print("TEST 6: Switch Between Characters")
            print("=" * 80)
            
            load_character(page, "Thorin")
            expect(page.locator("body")).to_contain_text("Thorin")
            expect(page.locator("body")).not_to_contain_text("Elara")
            
            load_character(page, "Elara")
            expect(page.locator("body")).to_contain_text("Elara")
            expect(page.locator("body")).not_to_contain_text("Thorin")
            print("✅ Successfully switched between characters.")
            
            # 7. Character Portrait Placeholder (Optional, check for image tag presence)
            print("\n" + "=" * 80)
            print("TEST 7: Character Portrait Placeholder")
            print("=" * 80)
            
            # Expecting an image element somewhere for the portrait
            expect(page.locator("img[alt='Character Portrait']").first).to_be_visible()
            print("✅ Character portrait area exists.")
            
            print("\n✅ All Character Loading Tests Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="character_loading_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_character_loading_playwright()
