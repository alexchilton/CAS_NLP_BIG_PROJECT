"""
Shared Playwright Helper Functions for E2E Tests.

Replaces selenium_helpers.py with more robust Playwright equivalents.
"""

import time # ADDED
import re
from playwright.sync_api import Page, expect
import os
import subprocess
import signal

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

def wait_for_gradio(page: Page, timeout: int = 30000):
    """
    Wait for Gradio interface to fully load.
    
    Args:
        page: Playwright Page object
        timeout: Timeout in milliseconds
    """
    print("⏳ Waiting for Gradio interface...")
    
    # Wait for the main app container
    page.wait_for_selector("gradio-app", timeout=timeout)
    
    # Wait specifically for the chat interface or buttons to be ready
    # Gradio often has a loading state
    expect(page.get_by_role("button", name="Send")).to_be_visible(timeout=timeout)
    
    print("✅ Gradio interface loaded")

def select_dropdown_option(page: Page, label: str, option_text: str):
    """
    Select an option from a Gradio dropdown using its label.
    
    Args:
        page: Playwright Page object
        label: The label of the dropdown (e.g., "Choose Your Character")
        option_text: The text of the option to select
    """
    print(f"\n🎯 Selecting '{option_text}' from dropdown '{label}'")
    
    # Locate the dropdown input by its label
    # Gradio dropdowns are inputs with aria-label or associated labels
    dropdown_input = page.get_by_label(label)
    
    # Ensure it's visible and enabled
    expect(dropdown_input).to_be_visible()
    
    # Click to open the dropdown
    dropdown_input.click()
    
    # Wait for the options list to appear
    # Gradio options usually have role="option"
    # We use a loose match because sometimes text has extra whitespace or icons
    page.get_by_role("option").filter(has_text=option_text).first.click()
    
    # Optional: Click outside or hit Escape if it doesn't close automatically (Gradio usually does)
    # But usually clicking the option closes it.
    
    print(f"✅ Selected: {option_text}")

def load_character(page: Page, char_name: str = "Thorin"):
    """
    Load a character using the dropdown and button.
    """
    print(f"\n📝 Loading character: {char_name}")
    
    select_dropdown_option(page, "Choose Your Character", char_name)
    
    # Click the "Load Character" button
    # Using exact text match for the button
    page.get_by_role("button", name="Load Character").click()
    
    # Wait for loading to complete. 
    # A good heuristic for Gradio is waiting for the chat history to reflect the welcome message
    # or waiting for a specific element that appears after loading.
    # For now, we'll wait for the character sheet or chat update.
    # Let's wait for a reasonable amount of time or for a specific text update.
    time.sleep(2) # Short sleep to let the request start
    
    # Wait for network idle to ensure character data is fetched
    page.wait_for_load_state("networkidle")
    
    print(f"✅ Character loaded: {char_name}")

def send_message(page: Page, message: str):
    """
    Send a message via the chat input.
    """
    print(f"📤 {message}")
    
    # Find the textbox. Gradio often labels it "Your Action" or by placeholder
    chat_input = page.get_by_placeholder("Type your action")
    
    # Fill and press enter
    chat_input.fill(message)
    chat_input.press("Enter")
    
    # Wait for response
    # We can wait for the 'Send' button to become interactive again or for new messages
    # Gradio usually disables the input or send button while processing
    time.sleep(1) # Debounce
    
    # Wait until "Loading..." indicator is gone if present, or just wait for network idle
    page.wait_for_load_state("networkidle")

def wait_for_text_stability(locator, timeout=15000, stability_interval=500):
    """
    Wait for the text content of a locator to stop changing (for streaming responses).
    Ignores temporary loading states.
    """
    start_time = time.time() * 1000
    last_text = ""
    stable_start = 0
    
    while (time.time() * 1000) - start_time < timeout:
        try:
            current_text = locator.inner_text().strip()
        except:
            current_text = ""
            
        # Ignore loading messages
        if "loading" in current_text.lower() or not current_text:
            time.sleep(0.2)
            continue
            
        if current_text == last_text:
            if stable_start and (time.time() * 1000) - stable_start > stability_interval:
                return current_text
        else:
            stable_start = time.time() * 1000
            last_text = current_text
            
        time.sleep(0.1)
    
    return last_text

def get_last_bot_message(page: Page) -> str:
    """
    Retrieve the text of the last message from the bot, waiting for it to complete.
    """
    # Select all messages. Gradio structure varies, but usually .message-bot or data-testid='bot'
    # We'll look for the bot message container
    bot_messages = page.locator(".message.bot, [data-testid='bot']")
    
    if bot_messages.count() > 0:
        last_msg = bot_messages.last
        # Wait for the text to stabilize (streaming complete)
        text = wait_for_text_stability(last_msg)
        print(f"   🔎 Captured response length: {len(text)}")
        # print(f"   🔎 Preview: {text[:100]}...") 
        return text
    return ""

def get_all_messages(page: Page) -> list[str]:
    """Get all chat messages."""
    return page.locator(".message").all_inner_texts()

def click_tab(page: Page, tab_name: str):
    """
    Click a Gradio tab by name.
    """
    print(f"👉 Clicking tab: {tab_name}")
    # Try finding by role 'tab' first (standard Gradio)
    try:
        page.get_by_role("tab", name=tab_name).click(timeout=2000)
    except:
        # Fallback to button role
        try:
             page.get_by_role("button", name=tab_name).click(timeout=2000)
        except:
             # Last resort: text match (some Gradio versions use simple divs/spans)
             page.get_by_text(tab_name).click()
             
    # Wait for tab content to likely appear
    time.sleep(1)

def fill_input(page: Page, label: str, value: str):
    """
    Fill a text input by label or placeholder.
    """
    print(f"✍️  Filling input '{label}' with '{value}'")
    # Try by label first
    try:
        page.get_by_label(label).fill(value)
    except:
        # Try by placeholder
        page.get_by_placeholder(label).fill(value)

def set_slider(page: Page, label: str, value: int):
    """
    Set a slider value. 
    """
    print(f"🎚️  Setting slider '{label}' to {value}")
    
    # Strategy 1: exact label match (if <label> is properly associated)
    try:
        page.get_by_label(label, exact=True).fill(str(value))
        return
    except:
        pass
        
    # Strategy 2: Find a container with the text, then the slider
    # Gradio blocks often contain the label and the input
    
    # Try to find a generic container that has the text and a range input
    # We use a specific filter to avoid finding the whole body
    # We look for a div that directly contains the text (or close to it) and the input
    try:
        # Locate the text first
        text_locator = page.get_by_text(label, exact=True)
        if text_locator.count() == 0:
             text_locator = page.get_by_text(label)
             
        if text_locator.count() > 0:
            # Go up to a common ancestor that holds both label and input
            # Usually a div with class 'block' or 'form'
            # We can try to find the input relative to the text
            # This is a bit heuristic: find the slider in the same 'group'
            
            # This locator finds a div that contains the label text AND has a range input descendant
            # We sort by count to find the smallest container (hopefully)
            # Actually, just filtering for text and input is usually enough for Gradio
            slider = page.locator("div").filter(has_text=label).filter(has=page.locator("input[type='range']")).last
            
            if slider.count() > 0:
                input_el = slider.locator("input[type='range']").first
                input_el.fill(str(value))
                return
    except Exception as e:
        # print(f"Strategy 2 failed: {e}")
        pass
            
    # Strategy 3: "range" role matching name (if aria-label matches)
    try:
        slider = page.get_by_role("slider", name=label)
        if slider.count() > 0:
            slider.fill(str(value))
            return
    except:
        pass
        
    print(f"   ⚠️ Could not find slider for '{label}'")

def analyze_response(response: str, action_type: str) -> bool:
    """
    Analyze GM response for damage tracking (mirrors the logic in the original test).
    Returns True if the enemy is dead.
    """
    print(f"\n📊 {action_type} Analysis:")
    
    # Check for damage mentions
    damage_pattern = re.search(r'(\d+)\s+(?:damage|fire|slashing|piercing|force)', response, re.IGNORECASE)
    if damage_pattern:
        print(f"   ✅ Damage mentioned: {damage_pattern.group(1)}")
    else:
        print(f"   ❌ No damage mentioned")
    
    # Check for HP tracking
    hp_pattern = re.search(r'(?:HP|health).*?(\d+)/(\d+)', response, re.IGNORECASE)
    if hp_pattern:
        print(f"   ✅ HP shown: {hp_pattern.group(1)}/{hp_pattern.group(2)}")
    else:
        print(f"   ❌ No HP shown")
    
    # Check for mechanics section
    has_mechanics = "⚙️ MECHANICS:" in response
    print(f"   Mechanics section: {'✅ YES' if has_mechanics else '❌ NO'}")
    
    # Check for death
    is_dead = "dies" in response.lower() or "defeated" in response.lower() or "falls" in response.lower()
    if is_dead:
        print(f"   💀 Enemy defeated!")
    
    # print(f"\n   Response preview:")
    # print(f"   {response[:250]}...")
    
    return is_dead

def get_hp_from_sheet(page: Page):
    """Extract HP from character sheet (parsed from markdown)."""
    full_sheet_text = get_character_sheet_text(page) # This refers to a helper function within playwright_helpers
    if not full_sheet_text:
        return None
        
    match = re.search(r'HP[:\s]+(\d+)/(\d+)', full_sheet_text, re.IGNORECASE)
    if match:
        current_hp = int(match.group(1))
        return current_hp
    return None

def extract_creatures(response: str):
    """Try to find creature names in GM response."""
    creatures = []
    keywords = ['goblin', 'dragon', 'wolf', 'orc', 'skeleton', 'zombie', 
                'bandit', 'troll', 'spider', 'rat', 'bear', 'snake']
    
    response_lower = response.lower()
    for keyword in keywords:
        if keyword in response_lower:
            creatures.append(keyword.title())
    
    return creatures

def get_character_sheet_text(page: Page) -> str:
    """
    Retrieves the main character sheet markdown text.
    It looks for the 'Character Sheet' section and returns its inner text.
    """
    try:
        # Locate the overall 'Character Sheet' section
        # Assuming the character sheet is contained within a div with an h2/h3 'Character Sheet' or similar.
        # Gradio usually renders gr.Markdown components as div.markdown-html.
        # In the app, char_col1, char_col2, char_col3 are gr.Markdown components.
        # Let's target the parent element of those three columns, and get its inner text.
        
        # This is a robust way to find the main character sheet content area in the 'Play Game' tab.
        # Navigate to the 'Play Game' tab's content area
        play_tab_content = page.locator("div.gradio-tab-item[data-tab-name='🎮 Play Game']")
        
        # Within the 'Play Game' tab, find the section that contains the character sheet output.
        # This is typically beneath the "Character Sheet" heading.
        # The actual markdown content is in a 'div.markdown-html'
        
        # We target the specific markdown output elements (char_col1, char_col2, char_col3)
        # and concatenate their text.
        
        # The easiest way to get the *entire* character sheet content is to find the parent container
        # that holds col1, col2, col3, then get its text.
        
        # Based on web/components/play_tab.py, char_col1 is under the second gr.Row() in that tab
        # with "Character Sheet" above it.
        
        # This locator tries to get the entire text of the character sheet display area.
        # Let's find the container that holds the 3 columns (gr.Row) and get its text.
        # The 'Character Sheet' heading is followed by a gr.Row with 3 gr.Column inside.
        
        # Find the 'Character Sheet' heading, then the immediate sibling div (gr.Row)
        char_sheet_heading_locator = page.get_by_text("Character Sheet", exact=True).first
        if char_sheet_heading_locator.count() > 0:
            char_sheet_row_container = char_sheet_heading_locator.locator("xpath=./following-sibling::div").first
            if char_sheet_row_container.count() > 0:
                # This should contain the markdown outputs from col1, col2, col3
                return char_sheet_row_container.inner_text()
        
    except Exception as e:
        print(f"Error getting character sheet text: {e}")
        return ""
    
    return ""
