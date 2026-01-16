import os
import time
import subprocess
import signal
from playwright.sync_api import sync_playwright, expect
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from e2e_tests.playwright_helpers import (
    wait_for_gradio,
    load_character,
    send_message,
    get_last_bot_message,
    get_all_messages,
    click_tab
)

def kill_port(port):
    """Kill process listening on a specific port."""
    try:
        cmd = f"lsof -ti:{port}"
        pid = subprocess.check_output(cmd, shell=True).decode().strip()
        if pid:
            print(f"🛑 Killing existing process on port {port} (PID {pid})...")
            os.kill(int(pid), signal.SIGTERM)
            time.sleep(2)
    except:
        pass

def test_goblin_cave_combat_playwright():
    """
    Test: Goblin Cave Combat with Monster Stats (Playwright)
    """
    print("\n" + "🗡️" * 40)
    print("TEST: Goblin Cave Combat (Playwright)")
    print("🗡️" * 40)
    
    # Kill existing
    kill_port(7860)
    
    # Start Gradio with specific environment variables
    env = os.environ.copy()
    env['TEST_START_LOCATION'] = 'Goblin Cave'
    env['TEST_NPCS'] = 'Goblin'
    
    print(f"\n🚀 Starting Gradio with env vars...")
    gradio_process = subprocess.Popen(
        ['python3', 'web/app_gradio.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give it time to start
    time.sleep(10)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("📍 Opening http://localhost:7860")
            page.goto("http://localhost:7860")
            wait_for_gradio(page)
            
            # Load Character
            load_character(page, "Thorin")
            
            # Verify Location via /context
            send_message(page, "/context")
            time.sleep(2)
            
            context = get_last_bot_message(page)
            print(f"\n🗺️  Context check: {context[:100]}...")
            
            if "Goblin Cave" in context or "cave" in context.lower():
                print("✅ Location verified: Goblin Cave")
            else:
                print(f"⚠️  Location mismatch? Context: {context}")
                
            # Verify NPC
            if "Goblin" in context:
                print("✅ NPC verified: Goblin")
            else:
                print("⚠️  Goblin not found in context")
                
            # Start Combat
            print("\n⚔️  Starting Combat...")
            send_message(page, "/start_combat Goblin")
            time.sleep(3)
            
            response = get_last_bot_message(page)
            if "Initiative Order" in response:
                print("✅ Combat started with initiative!")
            else:
                print(f"⚠️  Combat start unclear: {response[:100]}")
                
            # Attack
            print("\n⚔️  Attacking...")
            send_message(page, "I attack the goblin with my longsword")
            time.sleep(5) # Wait for response
            
            attack_response = get_last_bot_message(page)
            print(f"📄 Response: {attack_response[:100]}...")
            
            if "damage" in attack_response.lower() or "miss" in attack_response.lower():
                print("✅ Attack resolved (hit/miss/damage tracked)")
            else:
                print("⚠️  Attack response unclear")
                
            print("\n✅ Test Completed Successfully!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="goblin_combat_failure.png")
            raise e
        finally:
            browser.close()
            # Kill Gradio
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_goblin_cave_combat_playwright()
