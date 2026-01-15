#!/bin/bash
# Comprehensive Test Runner for D&D RAG System
# Usage: ./run_tests.sh [unit|e2e|selenium|all]

# Don't exit on error - we want to see all test results
# set -e removed to allow tests to continue after failures

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
    # Removed -x flag to continue after failures
    # Added --tb=short to keep output concise
    python3 -m pytest tests/ -v --tb=short --maxfail=999 2>&1 | tee logs/unit_tests_$(date +%Y%m%d_%H%M%S).log
    echo ""
}

# Function to run programmatic E2E tests (no Selenium)
run_e2e_programmatic() {
    echo -e "${YELLOW}Running Programmatic E2E Tests...${NC}"
    echo "---"

    # Find all test files in e2e_tests that don't require Selenium
    # Exclude Selenium tests (those will be run separately)
    SELENIUM_EXCLUDE=(
        "test_goblin_cave_combat.py"
        "test_wizard_spell_combat.py"
        "test_ui_loading.py"
        "test_character_creation.py"
        "test_stat_rolling_ui.py"
        "test_shop_selenium.py"
        "test_party_dragon_selenium.py"
        "test_reality_check_browser.py"
        "test_shop_ui.py"
        "test_adventure_simulation.py"  # Interactive - requires manual start
        "test_party_mode_logging.py"    # Interactive - infinite loop for manual inspection
    )
    
    # Get all test files
    PROGRAMMATIC_TESTS=()
    for test in e2e_tests/test_*.py; do
        basename_test=$(basename "$test")
        # Check if it's not in the exclude list
        if [[ ! " ${SELENIUM_EXCLUDE[@]} " =~ " ${basename_test} " ]]; then
            PROGRAMMATIC_TESTS+=("$test")
        fi
    done

    # Track failures but continue running all tests
    FAILED_TESTS=()
    for test in "${PROGRAMMATIC_TESTS[@]}"; do
        if [ -f "$test" ]; then
            echo -e "\n${GREEN}▶${NC} Running: $test"
            if ! python3 "$test" 2>&1 | tee "logs/$(basename $test .py)_$(date +%Y%m%d_%H%M%S).log"; then
                FAILED_TESTS+=("$test")
            fi
        fi
    done
    
    # Report failures at the end
    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        echo -e "\n${RED}❌ Failed E2E tests:${NC}"
        for failed in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}✗${NC} $failed"
        done
    else
        echo -e "\n${GREEN}✅ All E2E tests passed!${NC}"
    fi
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

    FAILED_TESTS=()
    for test in "${SELENIUM_TESTS[@]}"; do
        if [ -f "$test" ]; then
            echo -e "\n${GREEN}▶${NC} Running: $test"
            if ! HEADLESS=true python3 "$test" 2>&1 | tee "logs/$(basename $test .py)_$(date +%Y%m%d_%H%M%S).log"; then
                FAILED_TESTS+=("$test")
            fi
        fi
    done
    
    # Report failures at the end
    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        echo -e "\n${RED}❌ Failed Selenium tests:${NC}"
        for failed in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}✗${NC} $failed"
        done
    else
        echo -e "\n${GREEN}✅ All Selenium tests passed!${NC}"
    fi
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
