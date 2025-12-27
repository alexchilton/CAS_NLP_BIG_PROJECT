#!/usr/bin/env python3
"""
Manual Visible Browser Test - Watch Thorin Explore & Fight!

Run this directly: python3 run_visible_test.py

You'll see a Chrome window open and Thorin:
- Explore different locations
- Encounter random monsters
- Fight them
- Travel to new places
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    print("🎮 Starting D&D Adventure Test - VISIBLE BROWSER MODE")
    print("=" * 60)
    
    # Setup visible browser
    options = Options()
    options.add_argument('--start-maximized')
    # NO headless mode - we want to SEE it!
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print("\n📖 Opening game...")
        driver.get("http://localhost:7860")
        
        print("⏳ Waiting for page to load...")
        wait = WebDriverWait(driver, 20)
        
        # Wait for any input to appear (sign that page loaded)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
        time.sleep(3)  # Extra buffer for full render
        
        print("\n🎭 Loading Thorin Oakenshield...")
        # Find the dropdown input (Gradio uses listbox role)
        dropdown_inputs = driver.find_elements(By.CSS_SELECTOR, "input[role='listbox']")
        
        if not dropdown_inputs:
            print("   Trying combobox selector...")
            dropdown_inputs = driver.find_elements(By.CSS_SELECTOR, "input[role='combobox']")
        
        if not dropdown_inputs:
            print("   Trying alternative selector...")
            dropdown_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        
        if not dropdown_inputs:
            print("❌ Character dropdown not found!")
            print(f"   Page title: {driver.title}")
            all_inputs = driver.find_elements(By.TAG_NAME, 'input')
            print(f"   Found {len(all_inputs)} inputs total")
            
            # Debug: show first few inputs
            print("\n   First 5 inputs:")
            for i, inp in enumerate(all_inputs[:5]):
                print(f"     {i+1}. type={inp.get_attribute('type')}, role={inp.get_attribute('role')}, "
                      f"class={inp.get_attribute('class')[:50] if inp.get_attribute('class') else 'None'}")
            
            # Try to find character-related input
            print("\n   Looking for character-related inputs...")
            for i, inp in enumerate(all_inputs):
                placeholder = inp.get_attribute('placeholder') or ""
                if 'character' in placeholder.lower() or 'name' in placeholder.lower():
                    print(f"     Found at index {i}: placeholder='{placeholder}'")
                    dropdown_inputs = [inp]
                    break
            
            if not dropdown_inputs:
                time.sleep(10)  # Keep browser open so you can inspect
                return
        
        dropdown = dropdown_inputs[0]
        dropdown.click()
        time.sleep(0.5)
        
        # Type Thorin's name
        dropdown.clear()
        dropdown.send_keys("Thorin")
        time.sleep(0.5)
        dropdown.send_keys(Keys.RETURN)
        time.sleep(1)
        
        # Click Load Character button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        load_button = None
        for btn in buttons:
            if "Load" in btn.text:
                load_button = btn
                break
        
        if load_button:
            load_button.click()
            time.sleep(3)
        else:
            print("⚠️  Load button not found, character may auto-load")
        
        print("✅ Thorin loaded!")
        print("\n🗺️  Starting adventure...\n")
        
        # Helper function to send chat message
        def send_chat(message):
            print(f"💬 Player: {message}")
            textbox = driver.find_element(By.CSS_SELECTOR, 'textarea')
            textbox.clear()
            textbox.send_keys(message)
            textbox.send_keys(Keys.RETURN)
            time.sleep(8)  # Wait for GM response
            
            # Get last response
            messages = driver.find_elements(By.CSS_SELECTOR, '.message')
            if messages:
                last = messages[-1].text
                print(f"🎲 GM: {last[:200]}...")
                print()
        
        # Adventure sequence
        send_chat("I look around the tavern")
        time.sleep(2)
        
        send_chat("/explore")
        time.sleep(2)
        
        send_chat("I venture into the newly discovered area")
        time.sleep(3)
        
        send_chat("/explore")
        time.sleep(2)
        
        send_chat("I continue exploring deeper")
        time.sleep(3)
        
        send_chat("/explore")
        time.sleep(2)
        
        send_chat("I search for adventure")
        time.sleep(3)
        
        send_chat("/map")
        time.sleep(2)
        
        print("\n" + "=" * 60)
        print("🎮 Test complete! Browser will stay open for 30 seconds")
        print("   Check the browser to see the full conversation!")
        print("=" * 60)
        
        time.sleep(30)
        
    finally:
        print("\n👋 Closing browser...")
        driver.quit()
        print("✅ Done!")

if __name__ == "__main__":
    main()
