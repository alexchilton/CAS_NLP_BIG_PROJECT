#!/usr/bin/env python3
"""
Debug script to find correct Gradio chat message selectors.
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    print("🔍 Finding Gradio 6.x chat message selectors...")

    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:7860")

        # Wait for Gradio to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "gradio-app"))
        )
        time.sleep(3)

        # Load a character to initialize chat
        print("\n📝 Loading character to initialize chat...")
        dropdowns = driver.find_elements(By.TAG_NAME, "select")
        if dropdowns:
            for dropdown in dropdowns:
                if dropdown.is_displayed():
                    dropdown.click()
                    time.sleep(0.5)
                    options = dropdown.find_elements(By.TAG_NAME, "option")
                    if len(options) > 1:
                        options[1].click()  # Select first non-empty option
                        break
            time.sleep(1)

        # Click Load Character button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "load character" in btn.text.lower():
                print(f"  Clicking: {btn.text}")
                btn.click()
                time.sleep(3)  # Wait for character to load and welcome message
                break

        print("\n📋 Testing various selectors for chat messages:")

        selectors = [
            ("CLASS_NAME: message", By.CLASS_NAME, "message"),
            ("CLASS_NAME: message-row", By.CLASS_NAME, "message-row"),
            ("CLASS_NAME: bot", By.CLASS_NAME, "bot"),
            ("CLASS_NAME: user", By.CLASS_NAME, "user"),
            ("CSS: .message", By.CSS_SELECTOR, ".message"),
            ("CSS: .message-row", By.CSS_SELECTOR, ".message-row"),
            ("CSS: [data-testid='bot']", By.CSS_SELECTOR, "[data-testid='bot']"),
            ("CSS: [data-testid='user']", By.CSS_SELECTOR, "[data-testid='user']"),
            ("CSS: .chatbot .message", By.CSS_SELECTOR, ".chatbot .message"),
            ("CSS: div[data-testid]", By.CSS_SELECTOR, "div[data-testid]"),
            ("TAG: p", By.TAG_NAME, "p"),
        ]

        for name, by, selector in selectors:
            try:
                elements = driver.find_elements(by, selector)
                print(f"\n{name}: Found {len(elements)} elements")

                if elements:
                    # Show first few elements' text
                    for i, elem in enumerate(elements[:3]):
                        text = elem.text.strip()
                        if text:
                            print(f"  [{i}] {text[:100]}")
                        else:
                            # Try getting innerHTML if text is empty
                            html = elem.get_attribute('innerHTML')
                            if html:
                                print(f"  [{i}] (HTML) {html[:100]}")
            except Exception as e:
                print(f"{name}: Error - {e}")

        print("\n" + "="*80)
        print("💡 RECOMMENDATION:")
        print("="*80)

        # Try to find any text that looks like the welcome message
        body = driver.find_element(By.TAG_NAME, "body")
        body_text = body.text

        if "Welcome" in body_text or "Prancing Pony" in body_text:
            print("✅ Welcome message IS visible in the page!")
            print("The chat is working, we just need the right selector.")
        else:
            print("❌ No welcome message found - chat may not be initialized")

        # Look for all p tags with substantial text
        print("\n📝 All <p> tags with text content:")
        p_tags = driver.find_elements(By.TAG_NAME, "p")
        for i, p in enumerate(p_tags[:10]):
            text = p.text.strip()
            if len(text) > 10:
                print(f"  p[{i}]: {text[:150]}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
