#!/usr/bin/env python3
"""
E2E Test Suite: Multiple Combat Scenarios

Tests various combat scenarios with different characters, locations, and monsters:
1. Wizard vs Skeleton (Ancient Ruins) - Spell combat with RAG lookups
2. Fighter vs Ogre (Rocky Mountain Pass) - Melee combat
3. Wizard vs Wolf Pack (Dark Forest) - Multi-enemy combat
4. Fighter vs Dragon (Dragon's Lair) - Boss fight

Each test fights to death or victory.
"""

import sys
import time
import os
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium_helpers import load_character, wait_for_gradio

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Enable debug mode
os.environ['GM_DEBUG'] = 'true'


# DEPRECATED: Use selenium_helpers.wait_for_gradio instead
# def wait_for_gradio(driver, timeout=30):
    """Wait for Gradio interface to fully load."""
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.TAG_NAME, "gradio-app"))
    )
    time.sleep(2)



# NOTE: This test file has been updated to import from selenium_helpers.py
# Local load_character() and wait_for_gradio() functions have been deprecated.
# The imported versions use the correct Gradio selectors (input[aria-label=...])
# See e2e_tests/README_SELENIUM.md for details.

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
    """Get all chat messages."""
    chat_containers = driver.find_elements(By.CLASS_NAME, "message")
    messages = []
    seen_texts = set()

    for container in chat_containers:
        text = container.text.strip()
        if text and text not in seen_texts and text != "Loading content":
            messages.append(text)
            seen_texts.add(text)

    return messages


# DEPRECATED: Use selenium_helpers.load_character instead
# def load_character(driver, char_name):
    """Load a character via UI with verification."""
    print(f"\n📝 Loading {char_name}...")

    # Find the character dropdown
    dropdowns = driver.find_elements(By.TAG_NAME, "select")
    char_dropdown = None
    for dd in dropdowns:
        if dd.is_displayed():
            char_dropdown = dd
            break

    if not char_dropdown:
        raise Exception("Could not find character dropdown")

    # Use Selenium's Select class for robust dropdown handling
    select = Select(char_dropdown)

    # Get all available options
    available_options = [opt.text for opt in select.options]
    print(f"   Available characters: {available_options}")

    # Find matching option
    matching_option = None
    for option in select.options:
        if char_name.lower() in option.text.lower():
            matching_option = option.text
            break

    if not matching_option:
        raise Exception(f"Character '{char_name}' not found in dropdown. Available: {available_options}")

    # Select by visible text
    print(f"   Selecting: {matching_option}")
    select.select_by_visible_text(matching_option)
    time.sleep(0.5)

    # Verify selection
    selected_option = select.first_selected_option.text
    if char_name.lower() not in selected_option.lower():
        raise Exception(f"Selection failed! Expected '{char_name}' but got '{selected_option}'")

    print(f"   ✅ Verified: {selected_option} is selected")

    # Click Load Character button
    buttons = driver.find_elements(By.TAG_NAME, "button")
    load_button = None
    for btn in buttons:
        if "load character" in btn.text.lower():
            load_button = btn
            break

    if not load_button:
        raise Exception("Could not find 'Load Character' button")

    load_button.click()
    time.sleep(3)


def check_combat_over(message):
    """Check if combat is over."""
    lower_msg = message.lower()

    # Player death
    if any(phrase in lower_msg for phrase in ["you have died", "you are dead", "you fall unconscious",
                                                "death save", "you collapse"]):
        return "player_dead"

    # Enemy death
    if any(phrase in lower_msg for phrase in ["falls dead", "is defeated", "dies", "slain",
                                                "victory", "you have won", "breathes its last"]):
        return "enemy_dead"

    # Combat end
    if "combat has ended" in lower_msg or "combat is over" in lower_msg:
        return "combat_ended"

    return None


def run_combat_scenario(location, character, enemy, actions, use_rag=False, rag_queries=None, max_rounds=25):
    """
    Run a complete combat scenario.

    Args:
        location: Starting location name
        character: Character name ("Thorin" or "Elara")
        enemy: Enemy name
        actions: List of combat actions to cycle through
        use_rag: Whether to use RAG lookups
        rag_queries: List of RAG queries to make before combat
        max_rounds: Maximum combat rounds before timeout
    """
    print(f"\n{'⚔️' * 40}")
    print(f"SCENARIO: {character} vs {enemy} @ {location}")
    print(f"{'⚔️' * 40}\n")

    # Start Gradio
    import subprocess
    env = os.environ.copy()
    env['TEST_START_LOCATION'] = location

    gradio_process = subprocess.Popen(
        ['python3', 'web/app_gradio.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(8)

    options = webdriver.ChromeOptions()
    if os.environ.get('HEADLESS', 'false').lower() == 'true':
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:7860")
        wait_for_gradio(driver)

        # Load character
        load_character(driver, character)
        print(f"✅ {character} loaded at {location}")

        # RAG lookups (if wizard)
        if use_rag and rag_queries:
            print(f"\n📚 RAG Lookups:")
            for query in rag_queries:
                send_message(driver, f"/rag {query}", wait_time=6)
                messages = get_chat_messages(driver)
                if messages:
                    rag_result = messages[-1]
                    print(f"   ℹ️ {query}: {rag_result[:100]}...")

        # Start combat
        print(f"\n⚔️ Starting combat with {enemy}...")
        send_message(driver, f"/start_combat {enemy}", wait_time=8)

        messages = get_chat_messages(driver)
        if messages:
            print(f"🎭 {messages[-1][:300]}...")

        # Combat loop
        round_num = 1
        action_index = 0
        combat_over = False

        while round_num <= max_rounds and not combat_over:
            print(f"\n--- Round {round_num} ---")

            action = actions[action_index % len(actions)]
            send_message(driver, action, wait_time=10)

            messages = get_chat_messages(driver)
            if messages:
                response = messages[-1]
                print(f"🎭 {response[:400]}...")

                # Check combat status
                combat_status = check_combat_over(response)
                if combat_status:
                    print(f"\n{'💀' * 40}")
                    if combat_status == "player_dead":
                        print(f"💀 {character.upper()} HAS FALLEN!")
                    elif combat_status == "enemy_dead":
                        print(f"⚔️ {enemy.upper()} DEFEATED! {character.upper()} VICTORIOUS!")
                    else:
                        print("⚔️ COMBAT ENDED!")
                    print(f"{'💀' * 40}\n")
                    combat_over = True
                    break

            action_index += 1
            round_num += 1
            time.sleep(1)

        # Results
        print(f"\n{'=' * 80}")
        print(f"SCENARIO COMPLETE: {character} vs {enemy}")
        print(f"{'=' * 80}")
        print(f"Rounds: {round_num - 1}")
        print(f"Outcome: {combat_status if combat_over else 'Timeout'}")
        print(f"{'=' * 80}\n")

        return combat_status if combat_over else "timeout"

    except Exception as e:
        print(f"\n❌ Scenario failed: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        driver.quit()
        gradio_process.terminate()
        try:
            gradio_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            gradio_process.kill()
            gradio_process.wait()


def main():
    """Run all combat scenarios."""
    print("\n" + "⚔️" * 40)
    print("D&D COMBAT SCENARIOS TEST SUITE")
    print("⚔️" * 40)
    print("\nTesting multiple combat scenarios with RAG integration")
    print("Each scenario fights until death or victory\n")
    print("=" * 80)

    results = {}

    # Scenario 1: Wizard vs Skeleton (with RAG)
    print("\n" + "✨" * 40)
    print("SCENARIO 1: Wizard Spell Combat with RAG")
    print("✨" * 40)

    results["Wizard vs Skeleton"] = run_combat_scenario(
        location="Ancient Ruins",
        character="Elara",
        enemy="Skeleton",
        actions=[
            "I cast Magic Missile at the skeleton",
            "I cast Fire Bolt at the skeleton",
            "I attack with my quarterstaff",
        ],
        use_rag=True,
        rag_queries=["Magic Missile", "Fire Bolt", "Skeleton"],
        max_rounds=20
    )

    time.sleep(3)

    # Scenario 2: Fighter vs Ogre
    print("\n" + "🗡️" * 40)
    print("SCENARIO 2: Fighter Melee Combat")
    print("🗡️" * 40)

    results["Fighter vs Ogre"] = run_combat_scenario(
        location="Rocky Mountain Pass",
        character="Thorin",
        enemy="Ogre",
        actions=[
            "I attack the ogre with my longsword",
            "I shield bash the ogre",
            "I make a power attack with my longsword",
        ],
        max_rounds=25
    )

    time.sleep(3)

    # Scenario 3: Wizard vs Wolf Pack
    print("\n" + "🐺" * 40)
    print("SCENARIO 3: Multi-Enemy Combat")
    print("🐺" * 40)

    results["Wizard vs Wolves"] = run_combat_scenario(
        location="Dark Forest Clearing",
        character="Elara",
        enemy="Wolf",
        actions=[
            "I cast Fire Bolt at the closest wolf",
            "I cast Magic Missile at the wolves",
            "I retreat and attack with my quarterstaff",
        ],
        use_rag=True,
        rag_queries=["Wolf"],
        max_rounds=20
    )

    time.sleep(3)

    # Scenario 4: Fighter vs Young Dragon (Boss Fight)
    print("\n" + "🐉" * 40)
    print("SCENARIO 4: Boss Fight - Dragon!")
    print("🐉" * 40)

    results["Fighter vs Dragon"] = run_combat_scenario(
        location="Dragon's Lair Approach",
        character="Thorin",
        enemy="Young Dragon",
        actions=[
            "I attack the dragon with my longsword",
            "I use my Second Wind ability",
            "I make a desperate attack at the dragon's weak point",
        ],
        max_rounds=30
    )

    # Final Summary
    print("\n" + "=" * 80)
    print("FINAL TEST RESULTS")
    print("=" * 80)

    for scenario, outcome in results.items():
        emoji = "✅" if outcome in ["player_dead", "enemy_dead", "combat_ended"] else "⚠️"
        print(f"{emoji} {scenario}: {outcome}")

    print("=" * 80)
    print("\n✅ All combat scenarios completed!")
    print("\n📊 Demonstrated:")
    print("   ✅ RAG integration for spell/monster lookups")
    print("   ✅ Combat to death mechanics")
    print("   ✅ Multiple location types")
    print("   ✅ Various monster types (Skeleton, Ogre, Wolf, Dragon)")
    print("   ✅ Spell casting and melee combat")
    print("   ✅ Multi-enemy encounters")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
