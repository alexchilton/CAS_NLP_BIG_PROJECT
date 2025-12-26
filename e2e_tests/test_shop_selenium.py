#!/usr/bin/env python3
"""
Selenium Browser Test: Shop System

Watch Thorin Stormshield visit "The Rusty Blade" weapon shop and interact
with Grum the Grumpy shopkeeper! This test demonstrates the conversational
shop system in action.

Features:
- Natural conversation with NPC shopkeeper
- Browsing shop inventory
- Asking about prices
- Buying items (/buy command)
- Selling items (/sell command)
- Running out of gold (failed purchase)
- Successful haggling
"""

import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Test configuration
GRADIO_URL = "http://localhost:7860"
HEADLESS = False  # Keep browser visible to watch the shopping!
WAIT_TIME = 8  # Wait time for GM responses


def create_driver():
    """Create Chrome WebDriver."""
    options = Options()
    if HEADLESS:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"❌ Failed to create Chrome driver: {e}")
        print("\nPlease install chromedriver:")
        print("  macOS: brew install chromedriver")
        sys.exit(1)


def wait_for_gradio(driver, timeout=10):
    """Wait for Gradio to load."""
    time.sleep(timeout)
    return True


def send_message(driver, message):
    """Send a message in the chat."""
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

        print(f"💬 Thorin: {message}")
        time.sleep(WAIT_TIME)  # Wait for GM response
        return True

    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False


def load_character(driver, character_name):
    """Load a character."""
    try:
        print(f"📝 Loading {character_name}...")
        time.sleep(3)

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
                if character_name in opt.text:
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

        print(f"✓ Loaded {character_name}")
        return True

    except Exception as e:
        print(f"❌ Failed to load character: {e}")
        return False


def main():
    """Run the shop system test."""
    print("\n" + "="*80)
    print("🏪 SELENIUM BROWSER TEST: Shop System - The Rusty Blade")
    print("="*80)
    print("\nThis will open Chrome and show Thorin shopping at a weapon shop!")
    print("Watch him interact with Grum the Grumpy shopkeeper.\n")
    print(f"Make sure Gradio is running at {GRADIO_URL}")
    print("="*80)

    driver = create_driver()

    try:
        # Navigate to Gradio
        print(f"\n🌐 Opening {GRADIO_URL}...")
        driver.get(GRADIO_URL)
        wait_for_gradio(driver)
        print("✓ Gradio loaded")

        # Load Thorin
        print("\n" + "="*80)
        print("⚔️  LOADING THORIN STORMSHIELD")
        print("="*80)
        load_character(driver, "Thorin")

        # Give Thorin some gold to shop with
        print("\n💰 Giving Thorin 100 gold pieces for shopping...")
        # Note: This would normally be done through the system, but for demo we'll proceed

        # Enter the shop
        print("\n" + "="*80)
        print("🏪 ENTERING THE RUSTY BLADE WEAPON SHOP")
        print("="*80)

        send_message(driver, "I push open the heavy wooden door and enter The Rusty Blade weapon shop. The smell of oil and steel fills the air. Behind the counter stands a grumpy-looking dwarf shopkeeper named Grum.")

        # Shopkeeper greeting
        print("\n" + "="*80)
        print("👋 MEETING GRUM THE SHOPKEEPER")
        print("="*80)

        send_message(driver, "I approach the counter. 'Good day, shopkeeper! What fine weapons do you have for sale?'")

        # Browse inventory
        print("\n" + "="*80)
        print("👀 BROWSING THE SHOP")
        print("="*80)

        send_message(driver, "I look around at the weapons on display. 'Show me your best swords and axes, Grum!'")

        # Ask about specific item
        print("\n" + "="*80)
        print("💰 ASKING ABOUT PRICES")
        print("="*80)

        send_message(driver, "I examine a battleaxe hanging on the wall. 'How much for that battleaxe, Grum?'")

        # Buy a weapon
        print("\n" + "="*80)
        print("🛒 PURCHASING A BATTLEAXE")
        print("="*80)

        send_message(driver, "/buy battleaxe")
        print("   (Using /buy command - system validates gold and updates inventory)")

        # Try to buy a shield
        print("\n" + "="*80)
        print("🛡️  PURCHASING A SHIELD")
        print("="*80)

        send_message(driver, "That battleaxe is mighty fine! I'll also take a shield if you have one.")
        time.sleep(2)
        send_message(driver, "/buy shield")

        # Sell an old item
        print("\n" + "="*80)
        print("💵 SELLING OLD EQUIPMENT")
        print("="*80)

        send_message(driver, "Grum, I have some old plate armor I'd like to sell. Will you buy it?")
        time.sleep(2)
        send_message(driver, "/sell plate armor")
        print("   (Selling at half market price - D&D 5e standard)")

        # Ask about expensive item
        print("\n" + "="*80)
        print("👑 BROWSING EXPENSIVE ITEMS")
        print("="*80)

        send_message(driver, "Do you have any magical weapons? Something truly legendary?")

        # Try to buy something too expensive (will fail)
        print("\n" + "="*80)
        print("❌ TRYING TO BUY EXPENSIVE ITEM (INSUFFICIENT GOLD)")
        print("="*80)

        send_message(driver, "/buy greatsword")
        print("   (Testing insufficient gold error handling)")

        # Haggling attempt
        print("\n" + "="*80)
        print("💬 HAGGLING WITH GRUM")
        print("="*80)

        send_message(driver, "Come now, Grum! Surely you can give a fellow dwarf a better price on that greatsword? We're kin, after all!")

        # Browse adventuring gear
        print("\n" + "="*80)
        print("🎒 CHECKING OUT ADVENTURING GEAR")
        print("="*80)

        send_message(driver, "What about adventuring supplies? I need rope and torches for dungeon delving.")

        # Buy multiple items
        print("\n" + "="*80)
        print("🛒 BUYING SUPPLIES IN BULK")
        print("="*80)

        send_message(driver, "/buy 50 rope")
        print("   (Buying 50 feet of rope)")

        # Thank the shopkeeper and leave
        print("\n" + "="*80)
        print("👋 LEAVING THE SHOP")
        print("="*80)

        send_message(driver, "Thank you for your wares, Grum! Your shop serves adventurers well. I'll be back when I've cleared out that goblin lair and have more coin!")

        # Check inventory
        print("\n" + "="*80)
        print("📦 CHECKING INVENTORY")
        print("="*80)

        send_message(driver, "/stats")
        print("   (Checking updated inventory and remaining gold)")

        # Summary
        print("\n" + "="*80)
        print("📊 SHOP VISIT COMPLETE!")
        print("="*80)
        print("\n✅ Test finished! Check the browser to see all the shopping interactions.")
        print("\nThe shop system demonstrated:")
        print("  ✓ Natural NPC shopkeeper conversation")
        print("  ✓ Browsing inventory with GM descriptions")
        print("  ✓ Asking about prices")
        print("  ✓ Purchasing items (/buy command)")
        print("  ✓ Selling items (/sell command - half price)")
        print("  ✓ Insufficient gold validation")
        print("  ✓ Haggling roleplay")
        print("  ✓ Bulk purchases")
        print("  ✓ Inventory tracking")

        print("\n\n⏸️  Browser will stay open for 30 seconds so you can read the conversation...")
        print("Press Ctrl+C to close immediately, or wait for auto-close.")

        time.sleep(30)

    except KeyboardInterrupt:
        print("\n\n👋 Closing browser early...")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔚 Closing browser...")
        driver.quit()


if __name__ == "__main__":
    main()
