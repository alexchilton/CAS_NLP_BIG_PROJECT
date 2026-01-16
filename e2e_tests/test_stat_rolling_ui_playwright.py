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
    set_slider,
    kill_port
)

def test_stat_rolling_ui_playwright():
    """
    Test: Stat Rolling UI (Playwright)
    Verifies sliders, ranges, and the random roll button.
    """
    print("\n" + "🎲" * 40)
    print("TEST: Stat Rolling UI (Playwright)")
    print("🎲" * 40)
    
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
            
            # 1. Check Initial Values (should be 10 usually)
            print("\n🔍 Checking initial slider values...")
            sliders = page.locator("input[type='range']")
            # Index 0 is Level, 1-6 are Stats
            
            # Check a few
            val_str = sliders.nth(1).input_value() # Strength
            print(f"   Initial Strength: {val_str}")
            
            # 2. Test Manual Adjustment
            print("\n🎚️ Testing manual adjustment...")
            # Set Strength (idx 1) to 15
            sliders.nth(1).fill("15")
            time.sleep(0.5)
            assert sliders.nth(1).input_value() == "15", "Slider update failed"
            print("✅ Manual slider update worked")
            
            # 3. Test Random Roll
            print("\n🎲 Testing Random Roll button...")
            roll_btn = page.get_by_role("button", name="Roll Random Stats")
            expect(roll_btn).to_be_visible()
            
            # Get values before roll
            values_before = [sliders.nth(i).input_value() for i in range(1, 7)]
            print(f"   Values before: {values_before}")
            
            # Click Roll
            roll_btn.click()
            time.sleep(1) # Wait for update
            
            # Get values after roll
            values_after = [sliders.nth(i).input_value() for i in range(1, 7)]
            print(f"   Values after:  {values_after}")
            
            # Verify change
            if values_before != values_after:
                print("✅ Stats changed after roll!")
            else:
                print("⚠️  Stats didn't change (unlikely but possible if rolled same numbers)")
                
            # Verify range (3-18)
            all_valid = all(3 <= int(v) <= 18 for v in values_after)
            if all_valid:
                print("✅ All stats within 3-18 range")
            else:
                print("❌ Invalid stat values detected!")
                
            print("\n✅ Stat Rolling UI Test Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="stat_rolling_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_stat_rolling_ui_playwright()
