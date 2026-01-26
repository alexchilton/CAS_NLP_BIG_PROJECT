"""
E2E Test Configuration

Configuration settings for Selenium tests of the Gradio D&D RAG app.
"""

import os
from pathlib import Path

# Base URL for the Gradio app
BASE_URL = os.getenv("GRADIO_URL", "http://localhost:7860")

# Timeouts (in seconds)
PAGE_LOAD_TIMEOUT = 30
IMPLICIT_WAIT = 10
EXPLICIT_WAIT = 20

# Browser settings
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
BROWSER = os.getenv("BROWSER", "chrome").lower()  # chrome or firefox

# Test data
TEST_CHARACTER_NAME = "Test Hero"
TEST_CHARACTER_RACE = "Human"
TEST_CHARACTER_CLASS = "Fighter"
TEST_CHARACTER_BACKGROUND = "Soldier"
TEST_CHARACTER_ALIGNMENT = "Lawful Good"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CHARACTERS_DIR = PROJECT_ROOT / "characters"
SCREENSHOTS_DIR = PROJECT_ROOT / "e2e_tests" / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Test settings
SAVE_SCREENSHOTS_ON_FAILURE = True
SAVE_SCREENSHOTS_ON_SUCCESS = False

# Selectors (Gradio-specific)
SELECTORS = {
    # Tabs
    "play_game_tab": "button[id*='play-game']",
    "create_character_tab": "button[id*='create-character']",

    # Character selection (Play Game tab)
    "character_dropdown": "input[type='text']",  # Gradio dropdown
    "load_button": "button:has-text('Load Character')",
    "character_sheet": "div.markdown",

    # Chat interface
    "chat_input": "textarea[placeholder*='action']",
    "send_button": "button:has-text('Send')",
    "chatbot": "div[class*='chatbot']",
    "clear_button": "button:has-text('Clear History')",

    # Character creation form
    "name_input": "input[placeholder*='name']",
    "race_dropdown": "select",  # or dropdown component
    "class_dropdown": "select",
    "background_input": "input[placeholder*='Background']",
    "alignment_input": "input[placeholder*='Alignment']",
    "create_button": "button:has-text('Create Character')",

    # Ability score sliders
    "str_slider": "input[type='range']",
}
