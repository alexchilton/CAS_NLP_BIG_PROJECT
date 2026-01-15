"""
Shared Selenium Helper Functions for E2E Tests

This module provides robust, reusable helper functions for Selenium-based E2E tests.
All tests should import and use these functions instead of implementing their own versions.

CRITICAL NOTES:
- Gradio dropdowns are NOT standard <select> elements!
- They are <input role="listbox"> with aria-label attributes
- Use input[aria-label="Choose Your Character"] to find the character dropdown
- This has been debugged multiple times - DO NOT try to find <select> tags!
"""

import time
from selenium.webdriver.common.by import By
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
    
    # Find the character dropdown by aria-label
    # Gradio renders dropdowns as <input role="listbox">
    try:
        char_dropdown = driver.find_element(
            By.CSS_SELECTOR, 
            'input[aria-label="Choose Your Character"]'
        )
        print(f"✅ Found character dropdown")
    except:
        print(f"❌ Could not find character dropdown")
        driver.save_screenshot('/tmp/dropdown_not_found.png')
        raise Exception("Character dropdown not found - check screenshot at /tmp/dropdown_not_found.png")
    
    # Click to open dropdown
    char_dropdown.click()
    time.sleep(3)  # Wait for dropdown animation and options to populate
    
    # Find and click the character option
    options = driver.find_elements(By.CSS_SELECTOR, '[role="option"]')
    print(f"   Found {len(options)} options")
    
    # Wait longer if options are empty - Gradio needs time to populate
    retry_count = 0
    while retry_count < 3 and (not options or not any(opt.text.strip() for opt in options)):
        print(f"   Waiting for options to populate (attempt {retry_count + 1})...")
        time.sleep(2)
        options = driver.find_elements(By.CSS_SELECTOR, '[role="option"]')
        retry_count += 1
    
    # Debug: print what's actually in the options
    for i, opt in enumerate(options):
        print(f"   Option {i}: text='{opt.text}' (visible={opt.is_displayed()})")
    
    found = False
    for opt in options:
        if char_name.lower() in opt.text.lower():
            print(f"   Selecting: {opt.text}")
            opt.click()
            time.sleep(1)
            found = True
            break
    
    if not found:
        available = [opt.text for opt in options]
        raise Exception(f"Character '{char_name}' not found. Available: {available}")
    
    # Click Load Character button
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if "Load Character" in btn.text:
            print(f"   Clicking Load Character button")
            btn.click()
            time.sleep(7)  # Wait for character to load
            break
    
    print(f"✅ Character loaded: {char_name}")


# Alias for backwards compatibility
load_character_robust = load_character


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

