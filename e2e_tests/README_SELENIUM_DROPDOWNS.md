# Selenium Dropdown Selection Guide

## ⚠️ CRITICAL: This Has Been a Constant Problem

This document exists because **Gradio dropdown selection has failed repeatedly** across multiple test files, causing silent failures and wasted debugging time.

## The Problem

**Gradio dropdowns are NOT standard HTML `<select>` elements.**

### What Gradio Actually Renders

```html
<!-- Gradio renders THIS: -->
<input role="listbox" aria-label="Choose Your Character" />

<!-- NOT this: -->
<select>
  <option>Character 1</option>
  <option>Character 2</option>
</select>
```

### Why This Causes Silent Failures

When you use standard Selenium dropdown selectors:

```python
# ❌ WRONG - This finds NOTHING
dropdowns = driver.find_elements(By.TAG_NAME, "select")
# Returns empty list, but code continues...

# ❌ WRONG - This also doesn't work
select = Select(some_element)  # Only works with <select> tags
```

**What happens:**
1. Dropdown search finds nothing or wrong element
2. Click fails silently or clicks wrong element
3. **UI defaults to first option** (e.g., Thorin instead of Elara)
4. Test continues with wrong value
5. Later assertions fail with confusing error messages

## The Solution

### Always Use selenium_helpers.py

**DO NOT** implement dropdown logic in individual test files.
**ALWAYS** import and use the helpers:

```python
from selenium_helpers import (
    select_dropdown_option,  # Universal dropdown helper
    select_character,         # Specific helpers
    select_race,
    select_class,
    select_alignment,
)

# Use them like this:
select_character(driver, "Elara")
select_race(driver, "Elf")
select_class(driver, "Wizard")

# Or use the universal helper:
select_dropdown_option(driver, "Choose Your Character", "Elara")
```

### Correct CSS Selector

```python
# ✅ CORRECT
driver.find_element(
    By.CSS_SELECTOR,
    'input[aria-label="Choose Your Character"]'
)
```

## All Available Dropdowns

| Dropdown Purpose | aria-label | Helper Function |
|-----------------|------------|----------------|
| Load character | `"Choose Your Character"` | `select_character(driver, name)` |
| Character race | `"Race"` | `select_race(driver, race)` |
| Character class | `"Class"` | `select_class(driver, cls)` |
| Alignment | `"Alignment"` | `select_alignment(driver, alignment)` |
| Debug scenario | `"🧪 Debug Scenario (Optional)"` | `select_debug_scenario(driver, scenario)` |
| Party members | `"Select Characters"` | `select_party_characters(driver, names)` |
| Remove character | `"Select Character to Remove"` | `select_dropdown_option(driver, label, name)` |

## Common Mistakes

### ❌ Mistake 1: Using find_elements with "select"
```python
# WRONG
dropdowns = driver.find_elements(By.TAG_NAME, "select")
for dd in dropdowns:
    if dd.is_displayed():
        dd.click()  # This never finds Gradio dropdowns!
```

### ❌ Mistake 2: Using Selenium's Select class
```python
# WRONG
from selenium.webdriver.support.ui import Select
select = Select(dropdown_element)
select.select_by_visible_text("Elara")  # Raises exception - not a <select>!
```

### ❌ Mistake 3: Assuming selection worked
```python
# WRONG - No verification
dropdown.click()
option.click()
# Did it actually work? You don't know!
```

### ✅ Correct Approach
```python
# RIGHT
from selenium_helpers import select_character

selected = select_character(driver, "Elara")
# Includes logging, verification, and error handling
# Returns the actual selected value
# Raises exception if selection fails
```

## Debugging Failed Dropdowns

If a dropdown selection fails:

1. **Check the screenshot**: Helpers save to `/tmp/dropdown_*.png`
2. **Check the console output**: Helpers print available options
3. **Verify aria-label**: Use browser DevTools to inspect the dropdown
4. **Check timing**: Gradio needs time to populate options after page load

## History

This issue has been debugged and fixed multiple times:

1. **Initial issue**: Tests defaulting to Thorin instead of Elara
2. **Root cause**: Using `find_elements(By.TAG_NAME, "select")`
3. **Fix attempt 1**: Manual click on options - still failed silently
4. **Fix attempt 2**: Use Select() class - raised exceptions
5. **Final fix**: Created `selenium_helpers.py` with correct CSS selectors
6. **This document**: Created to prevent future regressions

## Rules for Future Development

1. **NEVER** implement dropdown selection in individual test files
2. **ALWAYS** use helpers from `selenium_helpers.py`
3. **If you need a new dropdown helper**, add it to `selenium_helpers.py`, don't create it locally
4. **Read this file** before touching any Selenium dropdown code
5. **Update this file** if Gradio version changes affect dropdowns

## Testing Your Changes

Before committing changes to dropdown handling:

```bash
# Test character loading specifically
HEADLESS=true python3 e2e_tests/test_wizard_spell_combat.py

# Verify Elara loads (not Thorin)
# Check console output for "✅ Verified: Elara Moonwhisper (Elf Wizard) is selected"
```

---

**Remember: Gradio dropdowns are special. Use the helpers. Always.**
