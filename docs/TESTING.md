# Testing Guide

## Quick Start

```bash
# Run all unit tests (fast)
./run_tests.sh unit

# Run programmatic E2E tests (medium speed)
./run_tests.sh e2e

# Run Selenium browser tests (slow, requires Chrome)
./run_tests.sh selenium

# Run unit + programmatic E2E tests
./run_tests.sh all
```

## Test Categories

### 1. Unit Tests (`tests/`)
**Fast** ⚡ | **Isolated** | **No external dependencies**

Located in `tests/` directory. Run with pytest:

```bash
python3 -m pytest tests/ -v
```

**Key Tests**:
- `test_monster_combat_integration.py` - Monster stats from database ✅
- `test_shop_system.py` - Shop transactions (7 tests) ✅
- `test_rag_search.py` - Semantic search (5 tests) ✅
- `test_reality_check.py` - Action validation ✅
- `test_spell_management.py` - Spell slot tracking ✅
- `test_combat_npc.py` - NPC combat AI ✅
- `test_game_state.py` - Game state management (70 tests) ✅
- `test_world_system.py` - World persistence (11 tests) ✅
- `test_equipment_integration.py` - Equipment system ✅

### 2. Programmatic E2E Tests (`e2e_tests/`)
**Medium** 🕐 | **Integrated** | **Calls GM API directly**

These tests call the GameMaster API directly (no browser):

```bash
# Run individual test
python3 e2e_tests/test_combat_system.py

# Or use the runner
./run_tests.sh e2e
```

**Key Tests**:
- `test_combat_system.py` - Turn-based combat (9 tests) ✅
- `test_adventure_simulation.py` - Full gameplay simulation ✅
- `test_party_mode_logging.py` - Party logging ✅
- `test_dragon_combat_mechanics.py` - Dragon combat with mechanics extraction ✅

### 3. Selenium E2E Tests (`e2e_tests/`)
**Slow** 🐌 | **Full Stack** | **Browser automation**

Tests the complete UI via Selenium WebDriver:

```bash
# Requires Chrome + ChromeDriver
HEADLESS=true python3 e2e_tests/test_goblin_cave_combat.py

# Or use the runner
./run_tests.sh selenium
```

**Key Tests**:
- `test_goblin_cave_combat.py` - Combat with reality checks ✅
- `test_wizard_spell_combat.py` - Spell casting in combat ✅
- `test_ui_loading.py` - UI loads correctly ✅
- `test_character_creation.py` - Character creation flow ✅
- `test_stat_rolling_ui.py` - Stat rolling interface ✅

**Note**: Selenium tests require:
- Chrome/Chromium browser
- ChromeDriver matching your Chrome version
- Gradio server to start/stop cleanly

---

## Running Tests

### Starting Gradio

#### Basic Start
```bash
python3 web/app_gradio.py
```

**Gradio will be available at:** http://localhost:7860

#### With Environment Variables (Testing Setup)
```bash
# Start Gradio with specific location and NPCs
TEST_START_LOCATION="Goblin Cave" \
TEST_NPCS="Goblin, Orc" \
python3 web/app_gradio.py
```

#### Kill Existing Gradio Processes
```bash
# Find and kill any running Gradio processes
pkill -f "python3 web/app_gradio.py"

# Or more forceful
ps aux | grep "python3 web/app_gradio.py" | grep -v grep | awk '{print $2}' | xargs kill -9
```

### Running Selenium Tests

#### Visible Mode (See Browser)
**Recommended for debugging and watching tests run**

```bash
# Run specific test (visible browser)
python3 e2e_tests/test_goblin_cave_combat.py

# Run treasure persistence test (visible)
python3 e2e_tests/test_goblin_treasure_persistence.py
```

**What you'll see:**
- Chrome browser opens automatically
- Test navigates Gradio UI
- Combat interactions visible
- Chat messages appear in real-time
- Browser stays open on errors for debugging

#### Headless Mode (No Browser UI)
**Recommended for CI/CD and automated testing**

```bash
# Run specific test (headless)
HEADLESS=true python3 e2e_tests/test_goblin_cave_combat.py

# Run treasure persistence test (headless)
HEADLESS=true python3 e2e_tests/test_goblin_treasure_persistence.py
```

**What happens:**
- Browser runs in background (no window)
- Faster execution
- Screenshots saved on errors: `/tmp/*.png`

### Individual Test Execution

#### Run specific unit test
```bash
python3 -m pytest tests/test_shop_system.py::test_purchase_transactions -v
```

#### Run specific E2E test
```bash
python3 e2e_tests/test_combat_system.py
```

#### Run with debugging
```bash
GM_DEBUG=true python3 e2e_tests/test_combat_system.py
```

---

## Test Patterns

### Pattern 1: Manual Testing
```bash
# Start Gradio manually
python3 web/app_gradio.py

# Open browser to http://localhost:7860
# Load character, test manually
# Ctrl+C to stop Gradio when done
```

### Pattern 2: Automated E2E Test
```bash
# Test starts Gradio, runs test, stops Gradio
HEADLESS=true python3 e2e_tests/test_goblin_cave_combat.py
```

### Pattern 3: Watch Test Run
```bash
# See browser automation in action (no HEADLESS)
python3 e2e_tests/test_goblin_cave_combat.py
```

### Pattern 4: Custom Scenario
```bash
# Set up custom scenario and test
TEST_START_LOCATION="Haunted Mansion" \
TEST_NPCS="Ghost, Vampire" \
TEST_ITEMS="Cursed Chest:Ancient Artifact" \
python3 e2e_tests/test_custom_scenario.py
```

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `HEADLESS` | Run browser without UI | `HEADLESS=true` |
| `GM_DEBUG` | Enable debug logging | `GM_DEBUG=true` |
| `TEST_START_LOCATION` | Set starting location | `TEST_START_LOCATION="Goblin Cave"` |
| `TEST_NPCS` | Deterministic NPCs | `TEST_NPCS="Goblin, Orc"` |
| `TEST_ITEMS` | Items in location | `TEST_ITEMS="Hidden Chest:Magic Ring"` |
| `TEST_LOCATION_DESC` | Custom location description | `TEST_LOCATION_DESC="A dark cave..."` |

---

## Debugging

### Enable Debug Logging
```bash
# See GM prompts and responses
GM_DEBUG=true python3 e2e_tests/test_goblin_cave_combat.py
```

### Visible + Debug Logging
```bash
# Best for debugging: watch browser + see logs
GM_DEBUG=true python3 e2e_tests/test_goblin_cave_combat.py
```

### Check Screenshots on Failure
```bash
# Tests save screenshots to /tmp/ on failure
ls -lt /tmp/*.png | head -5

# View screenshot
open /tmp/goblin_cave_error.png  # macOS
xdg-open /tmp/goblin_cave_error.png  # Linux
```

### Unit Test Debugging
```bash
# Run with verbose output
python3 -m pytest tests/ -v -x --tb=long

# Stop on first failure
python3 -m pytest tests/ -x

# Show full tracebacks
python3 -m pytest tests/ --tb=long
```

---

## Troubleshooting

### Port Already in Use
```bash
# Kill processes using port 7860
lsof -ti:7860 | xargs kill -9
```

### Selenium WebDriver Issues
```bash
# Update ChromeDriver
# Download from: https://chromedriver.chromium.org/
```

### Test Hangs or Times Out
```bash
# Run in visible mode to see what's happening
python3 e2e_tests/test_goblin_cave_combat.py

# Increase timeout in test file:
# send_message(driver, "...", wait_time=20)  # Increase from 10 to 20
```

### Gradio Won't Start
```bash
# Check if port is available
lsof -i:7860

# Check for errors
python3 web/app_gradio.py  # Run in foreground to see errors
```

---

## Writing New Tests

### Unit Test Template
```python
def test_my_feature():
    """Test description."""
    # Arrange
    char = CharacterState(character_name="Test", max_hp=30)

    # Act
    result = some_function(char)

    # Assert
    assert result == expected_value
```

### E2E Programmatic Test Template
```python
def test_my_e2e_feature():
    """E2E test description."""
    db = ChromaDBManager()
    gm = GameMaster(db)

    # Setup
    gm.set_location("Test Location", "Description")

    # Test
    response = gm.generate_response("player action")

    # Verify
    assert "expected text" in response.lower()
```

### Selenium Test Pattern
```python
def test_my_selenium_feature():
    # Start Gradio
    gradio_process = start_gradio_server()
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("http://localhost:7860")
        # Test UI interactions
        send_message(driver, "test message")
        response = get_chat_messages(driver)
        assert len(response) > 0
    finally:
        driver.quit()
        stop_gradio_server(gradio_process)
```

---

## Best Practices

1. **Unit tests**: Fast, isolated, no external dependencies
2. **Use fixtures**: Pytest fixtures for common setup
3. **Descriptive names**: `test_combat_starts_with_initiative_order`
4. **Arrange-Act-Assert**: Clear test structure
5. **Reality checks**: Selenium tests should mirror real gameplay
6. **Single source of truth**: One property per data point
7. **Proper assertions**: Use `assert`, not `return True/False`

---

## Test Status

### ✅ Passing Tests
- **Unit Tests**: 124+ tests passing
- **E2E Programmatic**: Combat system, adventure simulation, party mode
- **E2E Selenium**: Goblin cave combat, wizard spell combat, UI loading

### Test Coverage
- Game state management: 70 tests ✅
- Combat system: 20+ tests ✅
- Shop system: 7 tests ✅
- World system: 11 tests ✅
- Equipment system: 35 tests ✅
- Reality checking: 15+ tests ✅

---

## Quick Reference

```bash
# Start Gradio
python3 web/app_gradio.py

# Run visible Selenium test
python3 e2e_tests/test_goblin_cave_combat.py

# Run headless Selenium test
HEADLESS=true python3 e2e_tests/test_goblin_cave_combat.py

# Run with debug logging
GM_DEBUG=true python3 e2e_tests/test_goblin_cave_combat.py

# Kill Gradio
pkill -f "python3 web/app_gradio.py"

# Run all tests
pytest tests/ e2e_tests/ -v
```
