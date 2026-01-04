# Running Tests and Gradio

## Starting Gradio

### Basic Start
```bash
python3 web/app_gradio.py
```

**Gradio will be available at:** http://localhost:7860

### With Environment Variables (Testing Setup)
```bash
# Start Gradio with specific location and NPCs
TEST_START_LOCATION="Goblin Cave" \
TEST_NPCS="Goblin, Orc" \
python3 web/app_gradio.py
```

### Kill Existing Gradio Processes
```bash
# Find and kill any running Gradio processes
pkill -f "python3 web/app_gradio.py"

# Or more forceful
ps aux | grep "python3 web/app_gradio.py" | grep -v grep | awk '{print $2}' | xargs kill -9
```

## Running Selenium Tests

### Visible Mode (See Browser)
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

### Headless Mode (No Browser UI)
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

## Running Multiple Tests

### All E2E Tests
```bash
# Headless mode
HEADLESS=true pytest e2e_tests/ -v

# Visible mode (watch all tests)
pytest e2e_tests/ -v
```

### All Unit Tests
```bash
pytest tests/ -v
```

## Test with Custom Environment

### Goblin Cave with Treasure
```bash
# 1. Start Gradio with test environment
TEST_START_LOCATION="Goblin Cave" \
TEST_NPCS="Goblin" \
TEST_ITEMS="Hidden Chest:Magic Ring of Protection" \
python3 web/app_gradio.py &

# 2. Wait for Gradio to start
sleep 5

# 3. Run test (visible mode to watch)
python3 e2e_tests/test_goblin_treasure_persistence.py
```

### Dragon Fight
```bash
# Start Gradio with dragon
TEST_START_LOCATION="Dragon's Lair" \
TEST_NPCS="Ancient Red Dragon" \
python3 web/app_gradio.py &

# Run test
sleep 5
python3 e2e_tests/test_dragon_combat.py
```

## Demo Scripts

### NPC Spawning Demo
```bash
# Shows all NPC spawning modes
python3 tests/demo_npc_spawning.py
```

### Custom Location Demo
```bash
# Shows custom location creation
python3 tests/test_custom_location_npcs.py
```

## Debugging Tests

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

## Common Test Patterns

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

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `HEADLESS` | Run browser without UI | `HEADLESS=true` |
| `GM_DEBUG` | Enable debug logging | `GM_DEBUG=true` |
| `TEST_START_LOCATION` | Set starting location | `TEST_START_LOCATION="Goblin Cave"` |
| `TEST_NPCS` | Deterministic NPCs | `TEST_NPCS="Goblin, Orc"` |
| `TEST_ITEMS` | Items in location | `TEST_ITEMS="Hidden Chest:Magic Ring"` |
| `TEST_LOCATION_DESC` | Custom location description | `TEST_LOCATION_DESC="A dark cave..."` |

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
