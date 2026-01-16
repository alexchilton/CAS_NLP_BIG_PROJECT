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
    kill_port,
    click_tab # Import click_tab
)

def test_ui_loading_playwright():
    """
    Test: UI Loading & Elements (Playwright)
    Verifies title, tabs, and essential UI components are present.
    """
    print("\n" + "\u26f0\ufe0f" * 40)
    print("TEST: UI Loading (Playwright)")
    print("\u26f0\ufe0f" * 40)
    
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
            
            # 1. Check Title
            print("\n\U0001f50d Checking Title...")
            expect(page).to_have_title(re.compile("D&D|Gradio"))
            print("✅ Title verified")
            
            # 2. Check Tabs
            print("\n🔍 Checking Tabs...")
            # Gradio tabs might have role="tab" or just be buttons
            # Get all text from things that look like tabs/buttons
            buttons = page.get_by_role("button").all_inner_texts()
            tabs = page.get_by_role("tab").all_inner_texts()
            all_texts = buttons + tabs
            # print(f"   Found interactables: {all_texts}")
            
            # Check if any element contains the text
            play_tab = any("Play Game" in t for t in all_texts)
            create_tab = any("Create Character" in t for t in all_texts)
            
            if play_tab and create_tab:
                print("✅ Main tabs found")
            else:
                # Last resort: generic text search (Gradio sometimes uses simple spans for tabs)
                print("   ⚠️  Roles not found, checking generic text...")
                play_visible = page.get_by_text("Play Game").first.is_visible()
                create_visible = page.get_by_text("Create Character").first.is_visible()
                
                if play_visible and create_visible:
                     print("✅ Main tabs found (via text match)")
                else:
                     print(f"❌ Tabs not found. Visible text: {all_texts}")
                     raise Exception("Tabs missing")
            
            # 3. Check Play Game Elements
            print("\n\U0001f50d Checking Play Game Elements...")
            # Dropdown
            expect(page.get_by_label("Choose Your Character")).to_be_visible()
            # Load Button
            expect(page.get_by_role("button", name="Load Character")).to_be_visible()
            # Chat Input
            expect(page.get_by_placeholder("Type your action")).to_be_visible()
            print("✅ Play Game elements found")
            
            # 4. Check Create Character Elements
            print("\n🔍 Checking Create Character Elements...")
            # Switch tab using helper
            click_tab(page, "✨ Create Character")
            
            # Inputs
            expect(page.get_by_label("Character Name")).to_be_visible()
            expect(page.get_by_label("Race")).to_be_visible()
            expect(page.get_by_label("Class")).to_be_visible()
            # Create Button
            expect(page.get_by_role("button", name="Create Character")).to_be_visible()
            print("✅ Create Character elements found")
            
            print("\n✅ UI Loading Test Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="ui_loading_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    import re # Needed for title regex
    test_ui_loading_playwright()
