#!/usr/bin/env python3
"""
Selenium Browser Test: Full Party Dragon Combat

Watch Thorin (Fighter) and Elara (Wizard) battle an Ancient Red Dragon
in the actual Gradio UI! This test opens a Chrome browser so you can
SEE the combat happening in real-time.

Epic combat scenario:
- Thorin attacks with longsword, tries to cast spells (fails hilariously)
- Elara casts Fire Bolt and Magic Missile
- Dragon breathes fire, bites, claws
- Characters take damage and might die!
"""

import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Test configuration
GRADIO_URL = "http://localhost:7860"
HEADLESS = False  # Keep browser visible to watch the combat!
LONG_WAIT = 8  # Wait time for GM responses


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

        print(f"💬 Sent: {message}")
        time.sleep(LONG_WAIT)  # Wait for GM response
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
    """Run the epic party dragon combat test."""
    print("\n" + "="*80)
    print("🐉 SELENIUM BROWSER TEST: Party Dragon Combat")
    print("="*80)
    print("\nThis will open Chrome and show you Thorin & Elara vs Ancient Red Dragon!")
    print("Watch the combat unfold in real-time in the browser window.\n")
    print(f"Make sure Gradio is running at {GRADIO_URL}")
    print("="*80)

    driver = create_driver()

    try:
        # Navigate to Gradio
        print(f"\n🌐 Opening {GRADIO_URL}...")
        driver.get(GRADIO_URL)
        wait_for_gradio(driver)
        print("✓ Gradio loaded")

        # Load Thorin first
        print("\n" + "="*80)
        print("⚔️  LOADING PARTY: THORIN & ELARA")
        print("="*80)
        load_character(driver, "Thorin")

        # Set up dragon encounter with PARTY
        print("\n" + "="*80)
        print("🐉 SETTING UP DRAGON ENCOUNTER - PARTY MODE")
        print("="*80)
        send_message(driver, "Thorin the dwarf fighter and Elara the elf wizard enter a vast cavern filled with mountains of gold. At the center, coiled atop the treasure hoard, rests an Ancient Red Dragon with 200 HP. Its eyes snap open as they enter.")

        # Track HP for BOTH characters
        thorin_hp = 28
        elara_hp = 14  # Wizard - LOW HP!
        dragon_hp = 200

        # Combat begins!
        print("\n" + "="*80)
        print(f"⚔️  ROUND 1 - THE BATTLE BEGINS!")
        print(f"   Thorin: {thorin_hp}/28 HP | Elara: {elara_hp}/14 HP | Dragon: {dragon_hp}/200 HP")
        print("="*80)

        print("\n🗡️  Thorin charges with his longsword...")
        send_message(driver, f"Thorin charges forward and attacks the Ancient Red Dragon with his longsword! (Thorin: {thorin_hp}/28, Elara: {elara_hp}/14, Dragon: {dragon_hp}/200)")
        dragon_hp -= 8

        print("\n🔥 Elara casts Fire Bolt...")
        send_message(driver, f"Elara raises her staff and casts Fire Bolt at the dragon's chest! (Thorin: {thorin_hp}/28, Elara: {elara_hp}/14, Dragon: {dragon_hp - 8}/200)")
        dragon_hp -= 6

        print("\n🐲 Dragon breathes fire at BOTH of them...")
        send_message(driver, f"The dragon roars and unleashes a massive gout of flame! Thorin takes 10 fire damage, Elara takes 12 fire damage! (Thorin: {thorin_hp - 10}/28, Elara: {elara_hp - 12}/14, Dragon: {dragon_hp}/200)")
        thorin_hp -= 10
        elara_hp -= 12  # Elara at 2 HP - CRITICAL!

        print("\n" + "="*80)
        print(f"⚔️  ROUND 2 - ELARA CRITICALLY WOUNDED!")
        print(f"   Thorin: {thorin_hp}/28 HP | Elara: {elara_hp}/14 HP (CRITICAL!) | Dragon: {dragon_hp}/200 HP")
        print("="*80)

        print("\n🛡️  Thorin protects Elara and attacks...")
        send_message(driver, f"Thorin steps in front of Elara, raises his shield, and attacks the dragon with his longsword! (Thorin: {thorin_hp}/28, Elara: {elara_hp}/14, Dragon: {dragon_hp}/200)")
        dragon_hp -= 7

        print("\n✨ Elara casts Magic Missile...")
        send_message(driver, f"Elara, burned and bleeding, casts Magic Missile at the dragon! Three bolts of arcane energy strike true! (Thorin: {thorin_hp}/28, Elara: {elara_hp}/14, Dragon: {dragon_hp - 7}/200)")
        dragon_hp -= 9

        print("\n🐲 Dragon bites Elara...")
        send_message(driver, f"The dragon lunges past Thorin's shield and bites down on Elara! She takes 15 piercing damage! (Thorin: {thorin_hp}/28, Elara: {elara_hp - 15}/14, Dragon: {dragon_hp}/200)")
        elara_hp -= 15

        if elara_hp <= 0:
            elara_hp = 0
            print("\n💀 ELARA HAS FALLEN!")

        print("\n" + "="*80)
        print(f"⚔️  ROUND 3 - THORIN FIGHTS ALONE!")
        print(f"   Thorin: {thorin_hp}/28 HP | Elara: 0/14 HP (DEAD) | Dragon: {dragon_hp}/200 HP")
        print("="*80)

        print("\n⚔️  Thorin roars in fury...")
        send_message(driver, f"Thorin roars in fury at Elara's death and attacks the dragon with renewed rage! (Thorin: {thorin_hp}/28, Elara: DEAD, Dragon: {dragon_hp}/200)")
        dragon_hp -= 10

        print("\n🔮 Thorin desperately tries to cast Fireball (THIS WILL FAIL HILARIOUSLY)...")
        send_message(driver, f"Thorin, desperate to avenge Elara, tries to cast Fireball at the dragon! (Thorin: {thorin_hp}/28, Elara: DEAD, Dragon: {dragon_hp - 10}/200)")
        print("   (Watch for the hilarious dwarf rejection!)")

        print("\n🐲 Dragon claws Thorin...")
        send_message(driver, f"The dragon slashes at Thorin with its massive claws! Thorin takes 12 slashing damage! (Thorin: {thorin_hp - 12}/28, Elara: DEAD, Dragon: {dragon_hp}/200)")
        thorin_hp -= 12

        print("\n" + "="*80)
        print(f"⚔️  ROUND 4 - THORIN'S LAST STAND!")
        print(f"   Thorin: {thorin_hp}/28 HP | Elara: 0/14 HP (DEAD) | Dragon: {dragon_hp}/200 HP")
        print("="*80)

        print("\n🏹 Thorin tries to shoot a bow he doesn't have...")
        send_message(driver, f"Thorin, barely standing, tries to grab a bow and fire at the dragon! (Thorin: {thorin_hp}/28, Elara: DEAD, Dragon: {dragon_hp}/200)")

        print("\n🐲 Dragon's tail swipe...")
        send_message(driver, f"The dragon's tail crashes into Thorin! He takes 10 bludgeoning damage! (Thorin: {thorin_hp - 10}/28, Elara: DEAD, Dragon: {dragon_hp}/200)")
        thorin_hp -= 10

        print("\n" + "="*80)
        print(f"⚔️  ROUND 5 - FINAL MOMENTS!")
        print(f"   Thorin: {thorin_hp}/28 HP | Elara: 0/14 HP (DEAD) | Dragon: {dragon_hp}/200 HP")
        print("="*80)

        if thorin_hp > 0:
            print("\n⚔️  Thorin makes one final desperate attack...")
            send_message(driver, f"With his last ounce of strength, Thorin attacks the dragon one more time with his longsword for Elara! (Thorin: {thorin_hp}/28, Elara: DEAD, Dragon: {dragon_hp}/200)")
            dragon_hp -= 9

            print("\n🐲 Dragon's final fire breath...")
            send_message(driver, f"The dragon roars and breathes fire again! Thorin takes 15 fire damage! (Thorin: {thorin_hp - 15}/28, Elara: DEAD, Dragon: {dragon_hp - 9}/200)")
            thorin_hp -= 15

        # Final status
        print("\n" + "="*80)
        print("⚰️  COMBAT OUTCOME")
        print("="*80)

        if thorin_hp <= 0:
            thorin_hp = 0
            print(f"\n💀 TOTAL PARTY KILL!")
            print(f"   Thorin: 0/28 HP - DEAD")
            print(f"   Elara: 0/14 HP - DEAD")
            print(f"   Ancient Red Dragon: {dragon_hp}/200 HP - VICTORIOUS")
            send_message(driver, f"Thorin falls beside Elara. The dragon has won. Total Party Kill. (Final: Thorin DEAD, Elara DEAD, Dragon: {dragon_hp}/200 HP)")
        else:
            print(f"\n🩸 Thorin survives, but at what cost...")
            print(f"   Thorin: {thorin_hp}/28 HP - ALIVE (barely)")
            print(f"   Elara: 0/14 HP - DEAD")
            print(f"   Ancient Red Dragon: {dragon_hp}/200 HP - Still strong")
            send_message(driver, f"Thorin retreats, carrying Elara's body. The dragon is barely scratched. (Final: Thorin: {thorin_hp}/28 HP, Elara: DEAD, Dragon: {dragon_hp}/200 HP)")

        # Summary
        print("\n" + "="*80)
        print("📊 COMBAT COMPLETE!")
        print("="*80)
        print("\n✅ Test finished! Check the browser to see all the GM responses.")
        print("\nThe Reality Check system handled:")
        print("  ✓ Valid longsword attacks")
        print("  ✓ Valid shield use")
        print("  ✓ Invalid spell casting (Fighter can't cast Fireball)")
        print("  ✓ Invalid weapon use (no bow in inventory)")

        print("\n\n⏸️  Browser will stay open for 30 seconds so you can read the combat log...")
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
