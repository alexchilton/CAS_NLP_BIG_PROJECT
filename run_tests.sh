#!/bin/bash
# Comprehensive Test Runner for D&D RAG System
# Usage: ./run_tests.sh [unit|e2e|selenium|all]

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "D&D RAG System - Test Runner"
echo "=========================================="
echo ""

# Default to all tests
TEST_TYPE="${1:-all}"

# Function to run unit tests
run_unit_tests() {
    echo -e "${YELLOW}Running Unit Tests...${NC}"
    echo "---"
    python3 -m pytest tests/ -v --tb=short -x 2>&1 | tee logs/unit_tests_$(date +%Y%m%d_%H%M%S).log
    echo ""
}

# Function to run programmatic E2E tests (no Selenium)
run_e2e_programmatic() {
    echo -e "${YELLOW}Running Programmatic E2E Tests...${NC}"
    echo "---"

    PROGRAMMATIC_TESTS=(
        "e2e_tests/test_combat_system.py"
        "e2e_tests/test_adventure_simulation.py"
        "e2e_tests/test_party_mode_logging.py"
    )

    for test in "${PROGRAMMATIC_TESTS[@]}"; do
        if [ -f "$test" ]; then
            echo -e "\n${GREEN}▶${NC} Running: $test"
            python3 "$test" 2>&1 | tee "logs/$(basename $test .py)_$(date +%Y%m%d_%H%M%S).log"
        fi
    done
    echo ""
}

# Function to run Selenium E2E tests
run_selenium_tests() {
    echo -e "${YELLOW}Running Selenium E2E Tests (HEADLESS mode)...${NC}"
    echo "---"
    echo -e "${RED}⚠️  These tests are slow and may require Chrome/ChromeDriver${NC}"
    echo ""

    SELENIUM_TESTS=(
        "e2e_tests/test_goblin_cave_combat.py"
        "e2e_tests/test_wizard_spell_combat.py"
        "e2e_tests/test_ui_loading.py"
        "e2e_tests/test_character_creation.py"
        "e2e_tests/test_stat_rolling_ui.py"
    )

    for test in "${SELENIUM_TESTS[@]}"; do
        if [ -f "$test" ]; then
            echo -e "\n${GREEN}▶${NC} Running: $test"
            HEADLESS=true python3 "$test" 2>&1 | tee "logs/$(basename $test .py)_$(date +%Y%m%d_%H%M%S).log"
        fi
    done
    echo ""
}

# Create logs directory if it doesn't exist
mkdir -p logs

# Run selected tests
case "$TEST_TYPE" in
    unit)
        run_unit_tests
        ;;
    e2e)
        run_e2e_programmatic
        ;;
    selenium)
        run_selenium_tests
        ;;
    all)
        run_unit_tests
        run_e2e_programmatic
        echo -e "${YELLOW}Skipping Selenium tests (run with: ./run_tests.sh selenium)${NC}"
        ;;
    *)
        echo -e "${RED}Invalid test type: $TEST_TYPE${NC}"
        echo "Usage: ./run_tests.sh [unit|e2e|selenium|all]"
        exit 1
        ;;
esac

echo "=========================================="
echo -e "${GREEN}Test run complete!${NC}"
echo "Logs saved to: logs/"
echo "=========================================="
