"""
Test GM to Combat Integration
Tests if the GM properly triggers combat when describing encounters
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def send_chat(driver, message):
    """Send a chat message"""
    try:
        # Find visible textarea
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        chat_input = None
        for ta in textareas:
            if ta.is_displayed() and ta.is_enabled():
                chat_input = ta
                break
        
        if not chat_input:
            print(f"⚠️  No chat input found")
            return False
        
        chat_input.clear()
        chat_input.send_keys(message)
        
        # Find and click Send button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Send" in btn.text and btn.is_displayed():
                btn.click()
                break
        
        print(f"💬 Player: {message}")
        print(f"⏳ Waiting 10 seconds for GM response...")
        time.sleep(10)  # Longer wait for GM response
        return True
    
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False


def test_gm_combat_flow():
    """Test that GM can trigger combat through narrative"""
    
    print("\n" + "="*60)
    print("🎮 Testing GM -> Combat Integration")
    print("="*60)
    
    # Setup Chrome
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Comment out to see browser
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Open the game
        print("\n📖 Opening game...")
        driver.get("http://localhost:7860")
        
        # Wait for Gradio to load (simple sleep like shop test)
        print("⏳ Waiting for Gradio to load...")
        time.sleep(10)
        
        # Select character using dropdowns
        print("🎭 Loading Thorin Oakenshield...")
        
        # Find all dropdowns
        dropdowns = driver.find_elements(By.TAG_NAME, "select")
        if dropdowns:
            char_dropdown = dropdowns[0]
            char_dropdown.click()
            time.sleep(0.5)
            
            # Find Thorin option
            options = char_dropdown.find_elements(By.TAG_NAME, "option")
            for opt in options:
                if "Thorin" in opt.text:
                    opt.click()
                    break
            time.sleep(0.5)
        
        # Click Load Character button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Load Character" in btn.text:
                btn.click()
                break
        
        time.sleep(3)
        
        print("✅ Character loaded!\n")
        print("⏳ Waiting 5 seconds for initial load...")
        time.sleep(5)
        
        # Test 1: Ask GM to create an encounter
        print("="*60)
        print("TEST 1: Asking GM for a dangerous encounter")
        print("="*60)
        
        send_chat(driver, "I want to explore a dangerous cave looking for treasure. What do I find?")
        
        # Check if combat started
        print("\n🔍 Checking for combat...")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        for ta in textareas:
            if "combat" in ta.get_attribute("value").lower() or ta.get_attribute("placeholder"):
                print(f"Combat area text: {ta.get_attribute('value')[:200]}")
        
        time.sleep(2)
        
        # Test 2: Explicitly ask for a goblin fight
        print("\n" + "="*60)
        print("TEST 2: Explicitly requesting combat")
        print("="*60)
        
        send_chat(driver, "A goblin jumps out and attacks me with a rusty sword!")
        
        print("\n🔍 Checking for combat...")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        for i, ta in enumerate(textareas):
            val = ta.get_attribute("value")
            if val and len(val) > 20:
                print(f"Textarea {i}: {val[:200]}")
        
        time.sleep(2)
        
        # Test 3: Try attacking
        print("\n" + "="*60)
        print("TEST 3: Trying to attack the goblin")
        print("="*60)
        
        send_chat(driver, "I swing my longsword at the goblin!")
        
        print("\n🔍 Checking for combat log...")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        for i, ta in enumerate(textareas):
            val = ta.get_attribute("value")
            if val and len(val) > 20:
                print(f"Textarea {i}: {val[:200]}")
        
        time.sleep(3)
        
        print("\n" + "="*60)
        print("Test complete - keeping browser open for 60 seconds...")
        print("PLEASE OBSERVE THE BROWSER TO SEE:")
        print("  1. Did the GM respond to messages?")
        print("  2. Did combat ever trigger?")
        print("  3. What's in the chat history?")
        print("="*60)
        time.sleep(60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n👋 Closing browser...")
        driver.quit()
        print("✅ Done!")


if __name__ == "__main__":
    test_gm_combat_flow()
