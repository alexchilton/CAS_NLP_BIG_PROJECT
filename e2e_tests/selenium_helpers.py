"""
Shared Selenium Helper Functions for E2E Tests

This module provides robust, reusable helper functions for Selenium-based E2E tests.
All tests should import and use these functions instead of implementing their own versions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  CRITICAL: GRADIO DROPDOWN SELECTOR ISSUE ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THIS HAS BEEN A CONSTANT PROBLEM - READ CAREFULLY:

Gradio dropdowns are NOT standard HTML <select> elements!
They are <input role="listbox"> with aria-label attributes.

❌ WRONG - DO NOT USE:
   driver.find_elements(By.TAG_NAME, "select")
   driver.find_elements(By.CSS_SELECTOR, "select")
   Select(dropdown_element)  # from selenium.webdriver.support.ui

✅ CORRECT - USE THIS:
   driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Exact Label Text"]')

When dropdown selection fails silently, the UI defaults to the first option,
causing tests to use the wrong character/value without raising an error.

ALWAYS use the helper functions in this module for ALL dropdown interactions.
DO NOT implement your own dropdown logic in individual test files.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def wait_for_gradio(driver, timeout=30):
    """
    Wait for Gradio interface to fully load.
    
    Args:
        driver: Selenium WebDriver instance
        timeout: Maximum wait time in seconds
    """
    print("⏳ Waiting for Gradio interface...")

    # Wait for gradio-app tag
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "gradio-app"))
    )

    # Wait longer for JavaScript to render components
    print("   ⏳ Waiting for JavaScript to render components...")
    time.sleep(10)  # Gradio needs time to render after DOM loads

    # Wait for any button to appear (sign that UI is rendered)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "button"))
        )
        print("   ✅ Buttons detected - UI rendered")
    except:
        print("   ⚠️  No buttons found yet, continuing anyway...")

    print("✅ Gradio interface loaded")


def load_character(driver, char_name="Thorin"):
    """
    Load a character via the Gradio UI dropdown.
    
    CRITICAL: Gradio dropdowns are NOT standard <select> elements!
    They are <input role="listbox"> with aria-label="Choose Your Character".
    
    This has been debugged multiple times. DO NOT try to use:
    - driver.find_elements(By.TAG_NAME, "select")  # WRONG!
    - driver.find_elements(By.CSS_SELECTOR, "[role='combobox']")  # WRONG!
    
    Use: input[aria-label="Choose Your Character"]  # CORRECT!
    
    Args:
        driver: Selenium WebDriver instance
        char_name: Name of character to load (case-insensitive, partial match OK)
    
    Raises:
        Exception: If dropdown or character not found
    """
    print(f"\n📝 Loading character: {char_name}")
    
    # Use the universal helper for selection
    select_dropdown_option(driver, "Choose Your Character", char_name)
    
    # Click Load Character button
    # Wait for the button to be clickable
    try:
        load_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Load Character')]"))
        )
        print(f"   Clicking Load Character button")
        load_btn.click()
        time.sleep(7)  # Wait for character to load
    except Exception as e:
        print(f"   ❌ Could not find/click Load Character button: {e}")
        # Fallback to finding by text iteration
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "Load Character" in btn.text:
                print(f"   Clicking Load Character button (fallback)")
                btn.click()
                time.sleep(7)
                return
        raise Exception("Load Character button not found")
    
    print(f"✅ Character loaded: {char_name}")


# Alias for backwards compatibility
load_character_robust = load_character


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UNIVERSAL DROPDOWN HELPER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def select_dropdown_option(driver, aria_label, option_text, partial_match=True):
    """
    Universal helper to select an option from ANY Gradio dropdown.

    This is the ONLY way to interact with Gradio dropdowns reliably.
    Use this function for all dropdown interactions in all E2E tests.

    Args:
        driver: Selenium WebDriver instance
        aria_label: Exact aria-label of the dropdown (e.g., "Choose Your Character")
        option_text: Text of option to select (e.g., "Elara", "Fighter")
        partial_match: If True, match if option_text appears in option (default: True)
                      If False, require exact match

    Returns:
        str: The text of the selected option

    Raises:
        Exception: If dropdown or option not found

    Example:
        # Load a character
        select_dropdown_option(driver, "Choose Your Character", "Elara")

        # Select a race
        select_dropdown_option(driver, "Race", "Elf")

        # Select a class
        select_dropdown_option(driver, "Class", "Wizard")
    """
    print(f"\n🎯 Selecting '{option_text}' from dropdown '{aria_label}'")

    # Find dropdown by aria-label
    try:
        dropdown = driver.find_element(
            By.CSS_SELECTOR,
            f'input[aria-label="{aria_label}"]'
        )
        print(f"   ✅ Found dropdown")
    except:
        print(f"   ❌ Could not find dropdown with aria-label='{aria_label}'")
        driver.save_screenshot(f'/tmp/dropdown_{aria_label.replace(" ", "_")}_not_found.png')
        raise Exception(f"Dropdown '{aria_label}' not found - check screenshot")

    # Click to open dropdown
    try:
        dropdown.click()
    except Exception as e:
        print(f"   ⚠️ Standard click failed: {e}. Trying JS click...")
        driver.execute_script("arguments[0].click();", dropdown)
        
    time.sleep(4)  # Initial wait for animation

    # Robust search loop
    found_opt = None
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries:
        options = driver.find_elements(By.CSS_SELECTOR, '[role="option"]')
        
        # Check for visibility
        visible_options = [opt for opt in options if opt.is_displayed()]
        
        # Also check for text content (sometimes elements are visible but text renders late)
        valid_options = [opt for opt in visible_options if opt.text.strip()]
        
        if valid_options:
            print(f"   Checking {len(valid_options)} visible options (Attempt {retry_count + 1}/{max_retries})...")
            
            for opt in valid_options:
                opt_text = opt.text.strip()
                match = False
                
                if partial_match:
                    if option_text.lower() in opt_text.lower():
                        match = True
                else:
                    if option_text.lower() == opt_text.lower():
                        match = True
                
                if match:
                    print(f"   ✅ Found match: '{opt_text}'")
                    try:
                        opt.click()
                        time.sleep(1)
                        
                        # Verify selection took effect
                        current_val = dropdown.get_attribute("value")
                        if current_val and ((partial_match and option_text.lower() in current_val.lower()) or 
                                          (not partial_match and option_text.lower() == current_val.lower())):
                             return opt_text
                        else:
                             print(f"   ⚠️ Selection failed? Input value is '{current_val}'. Retrying...")
                             
                    except Exception as e:
                        print(f"   ⚠️ Found but failed to click: {e}. Retrying...")
                        break 
            
            print(f"   ❌ Option '{option_text}' not found in current visible list. Retrying...")
            
        else:
            # Fallback: Check hidden options and force click if found
            print(f"   ⚠️ No visible options. Checking hidden options...")
            # Selenium .text is empty for hidden elements, must use textContent/innerText
            all_options = [opt for opt in options if opt.get_attribute("textContent").strip()]
            
            for opt in all_options:
                opt_text = opt.get_attribute("textContent").strip()
                
                if (partial_match and option_text.lower() in opt_text.lower()) or \
                   (not partial_match and option_text.lower() == opt_text.lower()):
                    print(f"   ✅ Found HIDDEN match: '{opt_text}'. Force clicking via JS...")
                    driver.execute_script("arguments[0].click();", opt)
                    time.sleep(1)
                    
                    # Verify selection took effect
                    current_val = dropdown.get_attribute("value")
                    if current_val and ((partial_match and option_text.lower() in current_val.lower()) or 
                                      (not partial_match and option_text.lower() == current_val.lower())):
                         return opt_text
                    else:
                         print(f"   ⚠️ Selection failed? Input value is '{current_val}'. Trying 'Type and Enter' strategy...")
                         
                         # Try typing the value and hitting Enter
                         try:
                             # Clear input (standard clear might not work on some custom inputs)
                             dropdown.send_keys(Keys.CONTROL + "a")
                             dropdown.send_keys(Keys.DELETE)
                             time.sleep(0.5)
                             
                             # Type and Enter
                             dropdown.send_keys(option_text)
                             time.sleep(1)
                             dropdown.send_keys(Keys.ENTER)
                             time.sleep(1)
                         except Exception as e:
                             print(f"   ⚠️ 'Type and Enter' failed: {e}")
                         
                         # Re-verify
                         current_val = dropdown.get_attribute("value")
                         if current_val and ((partial_match and option_text.lower() in current_val.lower()) or 
                                           (not partial_match and option_text.lower() == current_val.lower())):
                             print(f"   ✅ 'Type and Enter' success!")
                             return opt_text
                         else:
                             print(f"   ❌ 'Type and Enter' failed. Value is still '{current_val}'")
                    
                    # Continue loop to retry if verification failed
                    break

            # Diagnosis
            is_expanded = dropdown.get_attribute("aria-expanded")
            print(f"   Waiting for options... (Attempt {retry_count + 1}). Stats: Total={len(options)}, Visible={len(visible_options)}, Expanded={is_expanded}")
            
            # Recovery logic
            if len(visible_options) == 0:
                # Dropdown likely closed or options hidden
                # Rotate through different interaction methods
                method = retry_count % 3
                
                if method == 0:
                    print("   ♻️  Retry strategy 1: Standard Click...")
                    try:
                        dropdown.click()
                    except:
                        pass
                elif method == 1:
                    print("   ♻️  Retry strategy 2: JavaScript Click...")
                    driver.execute_script("arguments[0].click();", dropdown)
                else:
                    print("   ♻️  Retry strategy 3: Keyboard (Arrow Down)...")
                    dropdown.send_keys(Keys.ARROW_DOWN)
            
        time.sleep(3)
        retry_count += 1

    # Final check - failure
    options = driver.find_elements(By.CSS_SELECTOR, '[role="option"]')
    available = [opt.text.strip() for opt in options if opt.text.strip()]
    
    driver.save_screenshot(f'/tmp/dropdown_{aria_label.replace(" ", "_")}_failed.png')
    
    raise Exception(
        f"Option '{option_text}' not found in dropdown '{aria_label}' after {max_retries} retries. "
        f"Available: {available[:10]}..." 
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SPECIFIC DROPDOWN HELPERS (use these for convenience)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def select_character(driver, character_name):
    """
    Select a character from the 'Choose Your Character' dropdown.

    Args:
        driver: Selenium WebDriver instance
        character_name: Name of character (e.g., "Elara", "Thorin")
    """
    return select_dropdown_option(driver, "Choose Your Character", character_name)


def select_race(driver, race):
    """
    Select a race from the character creation 'Race' dropdown.

    Args:
        driver: Selenium WebDriver instance
        race: Race name (e.g., "Elf", "Dwarf", "Human")
    """
    return select_dropdown_option(driver, "Race", race)


def select_class(driver, character_class):
    """
    Select a class from the character creation 'Class' dropdown.

    Args:
        driver: Selenium WebDriver instance
        character_class: Class name (e.g., "Fighter", "Wizard", "Rogue")
    """
    return select_dropdown_option(driver, "Class", character_class)


def select_alignment(driver, alignment):
    """
    Select an alignment from the character creation alignment dropdown.

    Args:
        driver: Selenium WebDriver instance
        alignment: Alignment (e.g., "Lawful Good", "Chaotic Neutral")
    """
    return select_dropdown_option(driver, "Alignment", alignment)


def select_debug_scenario(driver, scenario_name):
    """
    Select a debug scenario from the '🧪 Debug Scenario (Optional)' dropdown.

    Args:
        driver: Selenium WebDriver instance
        scenario_name: Scenario name (e.g., "Goblin Cave", "Ancient Ruins")
    """
    return select_dropdown_option(driver, "🧪 Debug Scenario (Optional)", scenario_name)


def select_party_characters(driver, character_names):
    """
    Select characters for party mode (multi-select dropdown).

    Note: Multi-select dropdowns may behave differently. This function
    clicks each character option in sequence.

    Args:
        driver: Selenium WebDriver instance
        character_names: List of character names to select
    """
    print(f"\n👥 Selecting party members: {character_names}")

    for char_name in character_names:
        try:
            select_dropdown_option(driver, "Select Characters", char_name)
        except Exception as e:
            print(f"   ⚠️  Warning: Could not select {char_name}: {e}")

    print(f"✅ Party selection complete")


def find_chat_input(driver):
    """Find the chat input textarea."""
    textareas = driver.find_elements(By.TAG_NAME, "textarea")
    for ta in textareas:
        placeholder = ta.get_attribute("placeholder")
        if placeholder and "your action" in placeholder.lower():
            return ta
    for ta in textareas:
        if ta.is_displayed() and ta.is_enabled():
            return ta
    raise Exception("Could not find chat input textarea")


def find_send_button(driver):
    """Find the Send button."""
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if btn.text.strip().lower() == "send":
            return btn
    raise Exception("Could not find Send button")


def send_message(driver, message, wait_time=8):
    """Send a message in the chat."""
    print(f"📤 {message}")

    chat_input = find_chat_input(driver)
    chat_input.clear()
    chat_input.send_keys(message)

    send_btn = find_send_button(driver)
    send_btn.click()

    time.sleep(wait_time)

    # Wait for "Loading content" to clear
    max_wait = wait_time + 3
    start_time = time.time()
    while time.time() - start_time < max_wait:
        messages = get_chat_messages(driver)
        if messages and messages[-1] != "Loading content":
            break
        time.sleep(0.5)


def get_chat_messages(driver):
    """
    Get all chat messages from the Gradio chatbot.
    
    Returns:
        list: List of message text strings
    """
    try:
        # Gradio chat messages can be in various containers
        # Try multiple selectors
        chat_containers = driver.find_elements(
            By.CSS_SELECTOR, 
            "[data-testid='user'], [data-testid='bot'], .message"
        )
        
        messages = []
        seen_texts = set()
        
        for container in chat_containers:
            text = container.text.strip()
            if text and text not in seen_texts and text != "Loading content":
                messages.append(text)
                seen_texts.add(text)
        
        return messages
    except Exception as e:
        print(f"Warning: Could not get messages: {e}")
        return []


def switch_to_tab(driver, tab_name):
    """
    Switch to a specific Gradio tab.
    
    Args:
        driver: Selenium WebDriver instance
        tab_name: Name of tab to switch to (e.g., "Play Game", "Create Character")
        
    Returns:
        bool: True if tab found and clicked, False otherwise
    """
    print(f"\n🎲 Switching to {tab_name} tab...")
    tabs = driver.find_elements(By.CSS_SELECTOR, 'button.tab-nav, button[role="tab"]')
    
    for tab in tabs:
        if tab_name in tab.text:
            tab.click()
            time.sleep(1)
            print(f"✅ Switched to {tab_name}")
            return True
    
    print(f"⚠️  Tab '{tab_name}' not found")
    return False


def get_character_sheet_text(driver):
    """
    Get the character sheet text content.
    
    Returns:
        str: Character sheet markdown text
    """
    try:
        # Character sheet is typically in a markdown component
        markdown_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='markdown']")
        
        for elem in markdown_elements:
            text = elem.text
            if "HP:" in text or "PLAYER CHARACTER" in text:
                return text
        
        return ""
    except Exception as e:
        print(f"Warning: Could not get character sheet: {e}")
        return ""


def setup_chrome_driver(headless=False):
    """
    Create a Chrome WebDriver with standard options.
    
    Args:
        headless: Whether to run in headless mode (default: False)
        
    Returns:
        WebDriver: Configured Chrome WebDriver instance
    """
    from selenium import webdriver
    import os
    
    options = webdriver.ChromeOptions()
    
    # Check environment variable override
    if os.environ.get('HEADLESS', 'false').lower() == 'true':
        headless = True
    
    if headless:
        options.add_argument('--headless')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    return webdriver.Chrome(options=options)


# Test configuration constants
GRADIO_URL = "http://localhost:7860"
DEFAULT_WAIT_TIME = 10
CHARACTER_LOAD_WAIT = 7

