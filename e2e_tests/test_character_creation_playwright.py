from playwright.sync_api import sync_playwright, expect
import time
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
    kill_port # Import kill_port
)

def test_character_creation_playwright():
    """
    Test: Character Creation Flow (Playwright)
    """
    print("\n" + "🛠️" * 40)
    print("TEST: Character Creation (Playwright)")
    print("🛠️" * 40)
    
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
            
            # Navigate to Create Tab
            click_tab(page, "✨ Create Character")
            
            print("\n📝 Filling Character Details...")
            
            # Name
            fill_input(page, "Character Name", "Playwright Hero")
            
            # Dropdowns
            select_dropdown_option(page, "Race", "Human")
            select_dropdown_option(page, "Class", "Fighter")
            select_dropdown_option(page, "Alignment", "Neutral Good")
            
            # Background
            fill_input(page, "Background", "Former Guard")
            
            # Sliders
            # Note: Gradio slider labels are hard to match. We'll use index based on known UI order.
            # Order: Level (0), Str (1), Dex (2), Con (3), Int (4), Wis (5), Cha (6)
            print("\n🎚️ Setting Stats (via index)...")
            sliders = page.locator("input[type='range']")
            print(f"   Found {sliders.count()} sliders.")
            
            # Set Level (Index 0) to 5
            sliders.nth(0).fill("5")
            
            # Set Stats
            stats_values = [16, 14, 14, 10, 12, 10]
            for i, val in enumerate(stats_values):
                # +1 because index 0 is Level
                sliders.nth(i+1).fill(str(val))
            
            # Click Create
            print("\n🚀 Clicking Create Button...")
            page.get_by_role("button", name="Create Character").click()
            
            # Verify Success
            # We expect a success message in the output text box
            print("⏳ Waiting for creation...")
            
            try:
                # Use a locator that looks for the success text anywhere
                expect(page.locator("body")).to_contain_text("Character Created Successfully", timeout=5000)
                print("✅ Status message confirmed.")
            except:
                print("⚠️  Status message not found or timed out. Checking dropdown for confirmation...")
            
            # Verify it appears in the dropdown
            print("👉 Switching to Play Game tab...")
            click_tab(page, "🎮 Play Game")
            
            # Check dropdown
            # We need to open it to check options
            dropdown = page.get_by_label("Choose Your Character")
            dropdown.click()
            
            # Wait for option
            # The dropdown label format is "Name (Race Class)"
            expected_option = "Playwright Hero (Human Fighter)"
            print(f"🔎 Looking for option: '{expected_option}'")
            
            # Wait specifically for this option
            try:
                expect(page.get_by_role("option").filter(has_text=expected_option)).to_be_visible(timeout=10000)
                print("✅ New character found in dropdown! Test Passed.")
            except:
                print("❌ Character not found in dropdown.")
                # Print available options
                opts = page.get_by_role("option").all_inner_texts()
                print(f"Available options: {opts}")
                raise Exception("Character creation failed - not in dropdown")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="char_creation_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_character_creation_playwright()
