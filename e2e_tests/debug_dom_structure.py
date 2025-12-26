#!/usr/bin/env python3
"""
Debug script to inspect Gradio DOM structure for HP display.
Helps fix the HP extraction in Selenium tests.
"""

import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def inspect_character_sheet_dom():
    """Inspect the DOM structure of the character sheet."""
    print("\n" + "=" * 80)
    print("DOM STRUCTURE INSPECTOR - Finding HP Display")
    print("=" * 80)

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)

    try:
        print("\n📍 Opening Gradio at http://localhost:7860")
        driver.get("http://localhost:7860")

        # Wait for Gradio to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "gradio-app"))
        )
        time.sleep(2)

        # Load a character
        print("📝 Loading Thorin...")
        dropdowns = driver.find_elements(By.TAG_NAME, "select")
        if dropdowns:
            dropdowns[0].click()
            time.sleep(0.5)
            options_list = dropdowns[0].find_elements(By.TAG_NAME, "option")
            for opt in options_list:
                if "thorin" in opt.text.lower():
                    opt.click()
                    break

        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if "load character" in btn.text.lower():
                btn.click()
                time.sleep(3)
                break

        print("✅ Character loaded\n")

        # Now inspect all elements that might contain HP
        print("=" * 80)
        print("SEARCHING FOR HP IN DOM...")
        print("=" * 80)

        # 1. Search all divs with "HP" text
        print("\n1️⃣  Divs containing 'HP:'")
        divs_with_hp = driver.find_elements(By.XPATH, "//*[contains(text(), 'HP')]")
        for i, elem in enumerate(divs_with_hp[:5]):  # Limit to first 5
            print(f"   Element {i+1}:")
            print(f"      Tag: {elem.tag_name}")
            print(f"      Text: {elem.text[:100]}")
            print(f"      Classes: {elem.get_attribute('class')}")
            print()

        # 2. Check markdown components
        print("\n2️⃣  Markdown components (likely location)")
        markdown_divs = driver.find_elements(By.CSS_SELECTOR, ".markdown, [class*='markdown']")
        for i, elem in enumerate(markdown_divs[:3]):
            text = elem.text
            if "HP" in text:
                print(f"   Markdown {i+1} (CONTAINS HP!):")
                print(f"      Text:\n{text[:200]}")
                print(f"      Classes: {elem.get_attribute('class')}")
                print()

        # 3. Check for specific patterns
        print("\n3️⃣  Elements with 'HP:' pattern")
        hp_pattern_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'HP:')]")
        for elem in hp_pattern_elements[:3]:
            print(f"   Tag: {elem.tag_name}")
            print(f"   Text: {elem.text[:100]}")
            print(f"   Parent: {elem.find_element(By.XPATH, '..').tag_name}")
            print()

        # 4. Save page source for manual inspection
        page_source_path = "/tmp/gradio_page_source.html"
        with open(page_source_path, "w") as f:
            f.write(driver.page_source)
        print(f"\n💾 Full page source saved to: {page_source_path}")

        print("\n" + "=" * 80)
        print("✅ INSPECTION COMPLETE")
        print("=" * 80)

    finally:
        driver.quit()


if __name__ == "__main__":
    inspect_character_sheet_dom()
