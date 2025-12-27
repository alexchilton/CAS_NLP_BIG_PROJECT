"""
Test wandering adventure starting at Mürren with random encounters
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def send_message(driver, message):
    """Send a message in the chat"""
    try:
        # Find visible textarea
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        chat_input = None
        for ta in textareas:
            if ta.is_displayed() and ta.is_enabled():
                chat_input = ta
                break

        if not chat_input:
            print(f"⚠️  No chat input found for: {message}")
            return False

        chat_input.clear()
        chat_input.send_keys(message)

        # Find and click Send button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Send" in btn.text and btn.is_displayed():
                btn.click()
                break

        time.sleep(3)  # Wait for GM response
        return True

    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False


def wait_for_gm_response(driver, timeout=10):
    """Wait for GM to respond"""
    time.sleep(timeout)


def get_latest_gm_message(driver):
    """Get the latest GM message text"""
    try:
        # Look for chat messages in Gradio
        time.sleep(1)
        # Try to find messages - adjust selector based on actual Gradio structure
        messages = driver.find_elements(By.CSS_SELECTOR, ".message")
        if messages:
            return messages[-1].text
        return ""
    except:
        return ""


def check_for_combat(driver):
    """Check if we're in combat by looking for combat UI elements"""
    try:
        driver.find_element(By.ID, "combat-section")
        return True
    except:
        return False


def main():
    print("🎮 Starting Mürren Mountain Adventure Test")
    print("=" * 60)
    
    # Setup Chrome options for visible browser
    chrome_options = Options()
    # No headless mode - we want to see it!
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1400, 1000)
    
    try:
        # Open the game
        print("\n📖 Opening game...")
        driver.get("http://localhost:7860")
        
        # Wait for page to load
        print("⏳ Waiting for page to load...")
        time.sleep(10)
        
        # Select character
        print("🎭 Loading Thorin Oakenshield...")
        
        # Find dropdown
        dropdowns = driver.find_elements(By.TAG_NAME, "select")
        if not dropdowns:
            dropdowns = driver.find_elements(By.CSS_SELECTOR, "[role='combobox']")

        if dropdowns:
            dropdown = dropdowns[0]
            dropdown.click()
            time.sleep(1)

            # Find character option
            options = driver.find_elements(By.CSS_SELECTOR, "[role='option']")
            for opt in options:
                if "Thorin" in opt.text:
                    opt.click()
                    time.sleep(1)
                    break

        # Click Load Character button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Load Character" in btn.text:
                btn.click()
                time.sleep(7)  # Wait for character to load
                break
        
        print("✅ Character loaded!")
        
        # Navigate to Mürren step by step
        print("\n🗺️ Navigating to Mürren...")
        
        print("  → Checking current location...")
        send_message(driver, "/map")
        time.sleep(3)
        
        print("  → Going to Town Square...")
        send_message(driver, "/travel Town Square")
        time.sleep(3)
        
        print("  → Going to Town Gates...")
        send_message(driver, "/travel Town Gates")
        time.sleep(3)
        
        print("  → Going to Mountain Road...")
        send_message(driver, "/travel Mountain Road")
        time.sleep(3)
        
        print("  → Finally arriving at Mürren!")
        send_message(driver, "/travel Mürren")
        time.sleep(4)
        
        print("✅ Arrived at Mürren!")
        
        # Start exploring
        exploration_count = 0
        max_explorations = 10
        
        print("\n🚶 Beginning adventure...")
        print("-" * 60)
        
        while exploration_count < max_explorations:
            exploration_count += 1
            
            # Look around
            print(f"\n🔍 Exploration #{exploration_count}")
            send_message(driver, "I look around carefully")
            
            gm_response = get_latest_gm_message(driver)
            print(f"GM: {gm_response[:200]}...")
            
            # Check if combat started
            if check_for_combat(driver):
                print("\n⚔️ COMBAT STARTED!")
                
                # Fight until combat ends
                combat_round = 0
                while check_for_combat(driver):
                    combat_round += 1
                    print(f"\n⚔️ Combat Round {combat_round}")
                    
                    send_message(driver, "I attack with my weapon!")
                    time.sleep(3)
                    
                    gm_response = get_latest_gm_message(driver)
                    print(f"GM: {gm_response[:200]}...")
                    
                    # Check if we died
                    if "unconscious" in gm_response.lower() or "died" in gm_response.lower() or "death" in gm_response.lower():
                        print("\n💀 CHARACTER DIED!")
                        print("-" * 60)
                        print("🎮 GAME OVER")
                        time.sleep(5)
                        return
                    
                    if combat_round > 20:
                        print("\n⚠️ Combat taking too long, breaking...")
                        break
                
                print("\n✅ Combat ended!")
            
            # Move to a random direction
            import random
            directions = ["north", "south", "east", "west", "up the mountain path", "down the valley"]
            direction = random.choice(directions)
            
            print(f"\n🚶 Moving {direction}...")
            send_message(driver, f"I go {direction}")
            time.sleep(2)
            
            gm_response = get_latest_gm_message(driver)
            print(f"GM: {gm_response[:150]}...")
        
        print("\n✅ Adventure test completed!")
        print("=" * 60)
        
        # Keep browser open
        print("\n👀 Browser will stay open for 30 seconds...")
        time.sleep(30)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(10)
    finally:
        print("\n👋 Closing browser...")
        driver.quit()
        print("✅ Done!")


if __name__ == "__main__":
    main()
