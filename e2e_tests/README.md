# E2E Tests for D&D RAG Gradio App

End-to-end Selenium tests for testing the Gradio web interface.

## 🎯 What's Tested

### UI Loading (`test_ui_loading.py`)
- App loads successfully
- Main title and tabs are present
- Character dropdown and buttons exist
- Chat interface is present
- Character sheet area exists
- No critical JavaScript errors

### Character Loading (`test_character_loading.py`)
- Load Thorin Stormshield character
- Load Elara Moonwhisper character
- Character stats are displayed (STR, DEX, CON, etc.)
- Character equipment is shown
- Wizard spells are displayed (for Elara)
- Switch between characters
- Character portrait placeholder exists

### Character Creation (`test_character_creation.py`)
- Navigate to Create Character tab
- Enter character name
- Select race and class
- Adjust ability score sliders
- Enter background and alignment
- Create Character button exists
- Full character creation flow

### Chat Functionality (`test_chat_functionality.py`)
- Chat input and Send button exist
- Send simple chat messages
- Test commands: `/help`, `/stats`, `/context`, `/rag`
- Clear chat history
- Multiple messages in sequence
- Wait for LLM responses (slow test)

## 🚀 Quick Start

### Prerequisites

1. **Gradio app must be running:**
   ```bash
   cd ..
   python web/app_gradio.py
   ```

2. **Chrome or Firefox browser** installed on your system

### Installation

```bash
cd e2e_tests

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Tests

**Option 1: Use the test runner script (recommended)**
```bash
./run_tests.sh
```

**Option 2: Run pytest directly**
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest test_ui_loading.py

# Run specific test
pytest test_ui_loading.py::TestUILoading::test_app_loads

# Run tests by marker
pytest -m ui          # Only UI tests
pytest -m character   # Only character tests
pytest -m chat        # Only chat tests
pytest -m "not slow"  # Exclude slow tests

# Generate HTML report
pytest --html=report.html --self-contained-html
```

### Running in Headless Mode

```bash
# Set environment variable
export HEADLESS=true
pytest

# Or inline
HEADLESS=true pytest
```

### Using Firefox Instead of Chrome

```bash
export BROWSER=firefox
pytest
```

## 📊 Test Reports

### Screenshots

Failed tests automatically save screenshots to `screenshots/` directory:
```
screenshots/
├── test_load_thorin_1234567890_FAILED.png
└── test_send_message_1234567891_FAILED.png
```

### HTML Report

Generate a detailed HTML report:
```bash
pytest --html=report.html --self-contained-html
open report.html  # macOS
```

### Logs

Test execution logs are saved to `test_run.log`

## ⚙️ Configuration

### Environment Variables

```bash
# Gradio app URL (default: http://localhost:7860)
export GRADIO_URL=http://localhost:7860

# Browser (default: chrome)
export BROWSER=chrome  # or firefox

# Headless mode (default: false)
export HEADLESS=true

# Screenshots on success (default: false)
export SAVE_SCREENSHOTS_ON_SUCCESS=true
```

### Config File

Edit `config.py` to change:
- Timeouts (page load, implicit wait, explicit wait)
- Test data (character names, race, class, etc.)
- Selectors (CSS selectors for UI elements)
- Screenshot settings

## 🧪 Writing New Tests

### Test File Template

```python
import pytest
from selenium.webdriver.common.by import By
import time
from config import BASE_URL

@pytest.mark.your_marker
class TestYourFeature:
    """Test suite for your feature."""

    def test_something(self, driver):
        """Test description."""
        driver.get(BASE_URL)
        time.sleep(2)

        # Your test code here
        element = driver.find_element(By.ID, "some-id")
        assert element.is_displayed()

        print("✅ Test passed")
```

### Best Practices

1. **Use descriptive test names**: `test_load_thorin` not `test_1`
2. **Add print statements**: Help debug when tests fail
3. **Use appropriate waits**: `time.sleep()` for Gradio, `WebDriverWait` for elements
4. **Mark slow tests**: Use `@pytest.mark.slow` for tests that take >10 seconds
5. **Clean up**: Tests should be independent and not affect each other
6. **Use markers**: Categorize tests with `@pytest.mark.ui`, etc.

## 🐛 Troubleshooting

### App Not Running
```
❌ Cannot connect to Gradio app at http://localhost:7860
```
**Solution:** Start the Gradio app first:
```bash
cd ..
python web/app_gradio.py
```

### WebDriver Errors
```
selenium.common.exceptions.WebDriverException: Chrome not found
```
**Solution:** Install Chrome or use Firefox:
```bash
export BROWSER=firefox
pytest
```

### Element Not Found
```
NoSuchElementException: Unable to locate element
```
**Solution:**
- Check if Gradio app loaded properly
- Increase wait time in `config.py`
- Inspect element selectors (Gradio generates dynamic IDs)

### Tests Pass But Functionality Doesn't Work
**Solution:**
- Check screenshots in `screenshots/` directory
- Review `test_run.log` for detailed logs
- Run tests without headless mode to watch them execute:
  ```bash
  HEADLESS=false pytest
  ```

## 📚 Documentation

- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Gradio Documentation](https://gradio.app/docs/)

## 🎨 Advanced Usage

### Parallel Execution (requires pytest-xdist)

```bash
pip install pytest-xdist
pytest -n 4  # Run with 4 workers
```

### Coverage Report (requires pytest-cov)

```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
```

### Watch Mode (requires pytest-watch)

```bash
pip install pytest-watch
ptw  # Re-runs tests on file changes
```

## 📝 Test Checklist

Before merging code changes, ensure:

- [ ] All UI loading tests pass
- [ ] Both characters (Thorin, Elara) load correctly
- [ ] Character creation form works
- [ ] All chat commands (`/help`, `/stats`, `/context`, `/rag`) work
- [ ] No critical errors in browser console
- [ ] Screenshots saved for any failures

## 🚦 CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r e2e_tests/requirements.txt

      - name: Start Gradio app
        run: python web/app_gradio.py &

      - name: Wait for app
        run: sleep 10

      - name: Run E2E tests
        run: cd e2e_tests && pytest -v --html=report.html
        env:
          HEADLESS: true

      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: screenshots
          path: e2e_tests/screenshots/
```

---

**Happy Testing!** 🧪✨
