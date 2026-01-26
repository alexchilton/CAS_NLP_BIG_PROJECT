"""
Pytest configuration for E2E tests

Sets up fixtures and hooks for Selenium testing.
"""

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from pathlib import Path
import time

from e2e_config import (
    BASE_URL,
    BROWSER,
    HEADLESS,
    PAGE_LOAD_TIMEOUT,
    IMPLICIT_WAIT,
    SCREENSHOTS_DIR,
    SAVE_SCREENSHOTS_ON_FAILURE,
    SAVE_SCREENSHOTS_ON_SUCCESS
)


@pytest.fixture(scope="function")
def driver(request):
    """
    Create a WebDriver instance for each test.

    Automatically handles browser setup and teardown.
    """
    # Set up browser
    if BROWSER == "firefox":
        options = webdriver.FirefoxOptions()
        if HEADLESS:
            options.add_argument("--headless")
        driver = webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install()),
            options=options
        )
    else:  # default to Chrome
        options = webdriver.ChromeOptions()
        if HEADLESS:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )

    # Set timeouts
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(IMPLICIT_WAIT)
    driver.maximize_window()

    yield driver

    # Teardown: save screenshot if test failed
    if request.node.rep_call.failed and SAVE_SCREENSHOTS_ON_FAILURE:
        screenshot_name = f"{request.node.name}_{int(time.time())}_FAILED.png"
        screenshot_path = SCREENSHOTS_DIR / screenshot_name
        driver.save_screenshot(str(screenshot_path))
        print(f"\n📸 Screenshot saved: {screenshot_path}")

    # Teardown: save screenshot if test passed (optional)
    elif request.node.rep_call.passed and SAVE_SCREENSHOTS_ON_SUCCESS:
        screenshot_name = f"{request.node.name}_{int(time.time())}_PASSED.png"
        screenshot_path = SCREENSHOTS_DIR / screenshot_name
        driver.save_screenshot(str(screenshot_path))

    driver.quit()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to make test result available in fixture.

    Allows us to check if test failed for screenshot capture.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="session", autouse=True)
def check_app_running():
    """
    Verify the Gradio app is running before tests start.
    """
    import requests

    print(f"\n🔍 Checking if Gradio app is running at {BASE_URL}...")

    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ Gradio app is running at {BASE_URL}")
        else:
            pytest.exit(f"❌ Gradio app returned status code {response.status_code}", returncode=1)
    except requests.exceptions.RequestException as e:
        pytest.exit(
            f"❌ Cannot connect to Gradio app at {BASE_URL}\n"
            f"Make sure the app is running: python web/app_gradio.py\n"
            f"Error: {e}",
            returncode=1
        )


def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests"
    )
    config.addinivalue_line(
        "markers", "character: marks tests related to character functionality"
    )
    config.addinivalue_line(
        "markers", "chat: marks tests related to chat functionality"
    )

def pytest_collection_modifyitems(items):
    """
    Called after test collection is complete.
    Apply custom markers to tests based on their filenames.
    """
    for item in items:
        # item.fspath is a legacy LocalPath object, use basename for filename
        filename = item.fspath.basename
        
        # Apply markers based on filename patterns
        if "playwright" in filename:
            item.add_marker(pytest.mark.playwright)
        elif "selenium" in filename:
            item.add_marker(pytest.mark.selenium)
        # Check if test is in e2e_tests directory
        # We convert to string to safely check path components
        elif "e2e_tests" in str(item.fspath):
            # Ensure it's not already explicitly marked as playwright or selenium
            existing_markers = [marker.name for marker in item.iter_markers()]
            if not any(m in existing_markers for m in ["playwright", "selenium"]):
                item.add_marker(pytest.mark.e2e_programmatic)

