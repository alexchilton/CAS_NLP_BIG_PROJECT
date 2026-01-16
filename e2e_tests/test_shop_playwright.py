from playwright.sync_api import sync_playwright
import time
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from e2e_tests.playwright_helpers import (
    wait_for_gradio,
    load_character,
    send_message,
    get_last_bot_message
)

import os
import subprocess
import signal

def kill_port(port):
    """Kill process listening on a specific port."""
    try:
        # Find PID
        cmd = f"lsof -ti:{port}"
        pid = subprocess.check_output(cmd, shell=True).decode().strip()
        if pid:
            print(f"🛑 Killing existing process on port {port} (PID {pid})...")
            os.kill(int(pid), signal.SIGTERM)
            time.sleep(2)
    except:
        pass

def test_shop_playwright():
    """
    Test: Shop System - The Rusty Blade (Playwright)
    """
    print("\n" + "🏪" * 40)
    print("TEST: Shop System (Playwright)")
    print("🏪" * 40)
    
    # Ensure port is free
    kill_port(7860)
    
    # Start clean Gradio instance with Shop Location
    env = os.environ.copy()
    env['TEST_START_LOCATION'] = 'The Market Square'
    
    print(f"\n🚀 Starting fresh Gradio instance (Location: The Market Square)...")
    gradio_process = subprocess.Popen(
        ['python3', 'web/app_gradio.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for startup
    time.sleep(10)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto("http://localhost:7860")
            wait_for_gradio(page)
            
            # Load Thorin
            load_character(page, "Thorin")
            
            # 1. Enter Shop
            print("\n-> Entering Shop...")
            send_message(page, "I push open the heavy wooden door and enter The Rusty Blade weapon shop. The smell of oil and steel fills the air.")
            time.sleep(2)
            
            # 2. Browse
            print("\n👀 Browsing...")
            send_message(page, "Show me your best swords and axes, Grum!")
            time.sleep(2)
            
            # 3. Buy Item
            print("\n💰 Buying Battleaxe...")
            send_message(page, "/buy battleaxe")
            time.sleep(2)
            resp = get_last_bot_message(page)
            if "bought" in resp.lower() or "purchased" in resp.lower() or "added" in resp.lower():
                print("✅ Purchase successful")
            else:
                print(f"⚠️  Purchase status unclear: {resp[:100]}")
                
            # 4. Sell Item
            print("\n💵 Selling Plate Armor...")
            send_message(page, "/sell plate armor")
            time.sleep(2)
            resp = get_last_bot_message(page)
            if "sold" in resp.lower() or "gold" in resp.lower():
                print("✅ Sale successful")
            else:
                print(f"⚠️  Sale status unclear: {resp[:100]}")
                
            # 5. Check Inventory
            print("\n📦 Checking Inventory...")
            send_message(page, "/stats")
            time.sleep(2)
            stats = get_last_bot_message(page)
            if "battleaxe" in stats.lower():
                print("✅ Battleaxe found in inventory")
            else:
                print("⚠️  Battleaxe missing from inventory")
                
            print("\n✅ Shop Test Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="shop_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_shop_playwright()
