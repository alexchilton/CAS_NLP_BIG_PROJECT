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

**Categories**:
- `test_monster_combat_integration.py` - Monster stats from database ✅
- `test_shop_system.py` - Shop transactions (7 tests) ✅
- `test_rag_search.py` - Semantic search (5 tests) ✅
- `test_reality_check.py` - Action validation ✅
- `test_spell_management.py` - Spell slot tracking
- `test_combat_npc.py` - NPC combat AI
- And more...

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
- `test_adventure_simulation.py` - Full gameplay simulation
- `test_party_mode_logging.py` - Party logging

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
- `test_ui_loading.py` - UI loads correctly
- `test_character_creation.py` - Character creation flow
- `test_stat_rolling_ui.py` - Stat rolling interface

**Note**: Selenium tests are slow and can be flaky. They require:
- Chrome/Chromium browser
- ChromeDriver matching your Chrome version
- Gradio server to start/stop cleanly

## Individual Test Execution

### Run specific unit test
```bash
python3 -m pytest tests/test_shop_system.py::test_purchase_transactions -v
```

### Run specific E2E test
```bash
python3 e2e_tests/test_combat_system.py
```

### Run with debugging
```bash
GM_DEBUG=true python3 e2e_tests/test_combat_system.py
```

## Test Status (2026-01-04)

### ✅ Passing Tests
- **Unit Tests**: Monster combat, shop system, RAG search
- **E2E Programmatic**: Combat system (9/9 tests)
- **E2E Selenium**: Goblin cave combat, wizard spell combat (with reality checks)

### ⚠️ Not Fully Verified
- **27 other E2E tests**: Not systematically run yet
- Some may be slow, flaky, or need updates

### 🐛 Known Issues
- Some Selenium tests timeout
- Full unit test suite times out after 2 minutes
- Some tests may need Chrome/ChromeDriver configuration

## Test Logs

All test runs save logs to `logs/` directory:
```
logs/
├── unit_tests_20260104_123456.log
├── test_combat_system_20260104_123457.log
└── test_goblin_cave_combat_20260104_123458.log
```

## Continuous Integration

To set up CI, add to your workflow:

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run unit tests
        run: ./run_tests.sh unit
      - name: Run programmatic E2E tests
        run: ./run_tests.sh e2e
```

(Selenium tests not recommended for CI due to flakiness)

## Debugging Failed Tests

### Unit Tests
1. Run with verbose output: `-v`
2. Stop on first failure: `-x`
3. Show full tracebacks: `--tb=long`

```bash
python3 -m pytest tests/ -v -x --tb=long
```

### E2E Tests
1. Enable debug mode: `GM_DEBUG=true`
2. Run without headless: Remove `HEADLESS=true`
3. Save screenshots on failure (Selenium tests do this automatically)

```bash
GM_DEBUG=true python3 e2e_tests/test_combat_system.py
```

### Selenium Tests
1. Check Chrome/ChromeDriver versions match
2. View screenshots in `/tmp/*.png` on failure
3. Check Gradio logs for server issues

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

## Best Practices

1. **Unit tests**: Fast, isolated, no external dependencies
2. **Use fixtures**: Pytest fixtures for common setup
3. **Descriptive names**: `test_combat_starts_with_initiative_order`
4. **Arrange-Act-Assert**: Clear test structure
5. **Reality checks**: Selenium tests should mirror real gameplay
6. **Single source of truth**: One property per data point
7. **Proper assertions**: Use `assert`, not `return True/False`

## Recent Fixes (2026-01-04)

See `TEST_FIXES_SUMMARY.md` for detailed information about:
- Monster combat test warnings fixed
- Shop system gold refactoring
- RAG search pytest fixture added
- E2E Selenium reality check pattern

---

**Questions?** Check `TEST_FIXES_SUMMARY.md` for detailed explanations of recent test improvements.
