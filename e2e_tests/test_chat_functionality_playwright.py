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
    get_all_messages,
    kill_port
)

def test_chat_functionality_playwright():
    """
    Test: Chat Functionality (Playwright)
    """
    print("\n" + "💬" * 40)
    print("TEST: Chat Functionality (Playwright)")
    print("💬" * 40)
    
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
            print("\n📝 Loading Thorin for chat tests...")
            load_character(page, "Thorin")
            
            # 1. Test Chat Input Exists
            print("\n" + "=" * 80)
            print("TEST 1: Chat Input Exists")
            print("=" * 80)
            expect(page.get_by_placeholder("Type your action")).to_be_visible()
            print("✅ Chat input exists.")
            
            # 2. Test Send Button Exists
            print("\n" + "=" * 80)
            print("TEST 2: Send Button Exists")
            print("=" * 80)
            expect(page.get_by_role("button", name="Send")).to_be_visible()
            print("✅ Send button exists.")
            
            # 3. Test Clear History Button Exists
            print("\n" + "=" * 80)
            print("TEST 3: Clear History Button Exists")
            print("=" * 80)
            expect(page.get_by_role("button", name="Clear History")).to_be_visible()
            print("✅ Clear History button exists.")
            
            # 4. Test Send Simple Message
            print("\n" + "=" * 80)
            print("TEST 4: Send Simple Message")
            print("=" * 80)
            test_message = "I look around the tavern."
            send_message(page, test_message)
            
            # Verify user message appears in chat history
            expect(page.locator(".message").filter(has_text=test_message)).to_be_visible()
            gm_response = get_last_bot_message(page)
            print(f"   GM response preview: {gm_response[:100]}...")
            if "tavern" in gm_response.lower() or "look around" in gm_response.lower():
                print("✅ GM responded to simple message.")
            else:
                print("⚠️  GM response unclear.")
            
            # 5. Test /help Command
            print("\n" + "=" * 80)
            print("TEST 5: /help Command")
            print("=" * 80)
            send_message(page, "/help")
            help_response = get_last_bot_message(page)
            expect(page.locator("body")).to_contain_text("Available Commands")
            print("✅ /help command response verified.")
            
            # 6. Test /stats Command
            print("\n" + "=" * 80)
            print("TEST 6: /stats Command")
            print("=" * 80)
            send_message(page, "/stats")
            stats_response = get_last_bot_message(page)
            expect(page.locator("body")).to_contain_text("Thorin Stormshield")
            expect(page.locator("body")).to_contain_text("HP:")
            print("✅ /stats command response verified.")
            
            # 7. Test /context Command
            print("\n" + "=" * 80)
            print("TEST 7: /context Command")
            print("=" * 80)
            send_message(page, "/context")
            context_response = get_last_bot_message(page)
            expect(page.locator("body")).to_contain_text("Current Context:")
            print("✅ /context command response verified.")
            
            # 8. Test /rag Command
            print("\n" + "=" * 80)
            print("TEST 8: /rag Command")
            print("=" * 80)
            send_message(page, "/rag Fireball")
            rag_response = get_last_bot_message(page)
            expect(page.locator("body")).to_contain_text("RAG Search Results:")
            expect(page.locator("body")).to_contain_text("fireball")
            print("✅ /rag command response verified.")
            
            # 9. Test Clear Chat History
            print("\n" + "=" * 80)
            print("TEST 9: Clear Chat History")
            print("=" * 80)
            # Send one more message to ensure history has content
            send_message(page, "another message")
            expect(page.locator(".message").count()).to_be_greater_than(1) # At least two messages
            
            page.get_by_role("button", name="Clear History").click()
            time.sleep(1) # Allow UI to update
            
            # Chatbot should be empty or just initial greeting
            all_chat_messages = get_all_messages(page) # Get all visible messages
            expect(len(all_chat_messages)).to_be_less_than_or_equal(1) # Initial greeting usually remains
            print("✅ Chat history cleared.")
            
            # 10. Test Chat Input Clears After Send
            print("\n" + "=" * 80)
            print("TEST 10: Chat Input Clears")
            print("=" * 80)
            chat_input = page.get_by_placeholder("Type your action")
            send_message(page, "One final message.")
            expect(chat_input).to_have_value("") # Input should be empty
            print("✅ Chat input clears after send.")
            
            print("\n✅ All Chat Functionality Tests Completed!")
            
        except Exception as e:
            print(f"\n❌ Test Failed: {e}")
            page.screenshot(path="chat_failure.png")
            raise e
        finally:
            browser.close()
            print("🛑 Stopping Gradio...")
            gradio_process.terminate()
            gradio_process.wait()

if __name__ == "__main__":
    test_chat_functionality_playwright()
