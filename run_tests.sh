#!/bin/bash
# Comprehensive Test Runner for D&D RAG System
# Usage: ./run_tests.sh [unit|e2e|playwright|all]

# Don't exit on error - we want to see all test results
set +e

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
    python3 -m pytest tests/ -v --tb=short --maxfail=999 2>&1 | tee logs/unit_tests_$(date +%Y%m%d_%H%M%S).log
    echo ""
}

# Function to run programmatic E2E tests (no UI)
run_e2e_programmatic() {
    echo -e "${YELLOW}Running Programmatic E2E Tests...${NC}"
    echo "---"

    # Find all test files in e2e_tests that are NOT Playwright/Selenium UI tests
    # Exclude files ending in _playwright.py, _selenium.py, and specific UI tests
    E2E_TESTS=(
        "e2e_tests/test_combat_mechanics_direct.py"
        "e2e_tests/test_combat_npc_extraction.py"
        "e2e_tests/test_combat_system.py"
        "e2e_tests/test_dragon_combat_mechanics.py"
        "e2e_tests/test_equipment_system_e2e.py"
        "e2e_tests/test_goblin_combat_npc_extraction.py"
        "e2e_tests/test_goblin_treasure_persistence.py"
        "e2e_tests/test_hallucination_bug.py"
        "e2e_tests/test_hp_tracking.py"
        "e2e_tests/test_magic_item_rag_e2e.py"
        "e2e_tests/test_monster_stats_integration.py"
        "e2e_tests/test_party_character_parsing.py"
        "e2e_tests/test_reality_check_e2e.py"
        "e2e_tests/test_steal_and_combat.py"
    )

    FAILED_TESTS=()
    for test in "${E2E_TESTS[@]}"; do
        if [ -f "$test" ]; then
            echo -e "\n${GREEN}▶${NC} Running: $test"
            if ! python3 "$test" 2>&1 | tee "logs/$(basename $test .py)_$(date +%Y%m%d_%H%M%S).log"; then
                FAILED_TESTS+=("$test")
            fi
        fi
    done
    
    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        echo -e "\n${RED}❌ Failed Programmatic E2E tests:${NC}"
        for failed in "${FAILED_TESTS[@]}"; do
            echo -e "  ${RED}✗${NC} $failed"
        done
    else
        echo -e "\n${GREEN}✅ All Programmatic E2E tests passed!${NC}"
    fi
    echo ""
}

# Function to run Playwright E2E tests (UI)
run_playwright_tests() {
    echo -e "${YELLOW}Running Playwright E2E Tests (Headless)...${NC}"
    echo "---"
    
    if [ -f "./run_playwright_tests.sh" ]; then
        ./run_playwright_tests.sh
    else
        echo -e "${RED}Error: run_playwright_tests.sh not found!${NC}"
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
    playwright)
        run_playwright_tests
        ;;
    selenium)
        echo -e "${YELLOW}Selenium tests have been deprecated. Running Playwright tests instead.${NC}"
        run_playwright_tests
        ;;
    all)
        run_unit_tests
        run_e2e_programmatic
        run_playwright_tests
        ;;
    *)
        echo -e "${RED}Invalid test type: $TEST_TYPE${NC}"
        echo "Usage: ./run_tests.sh [unit|e2e|playwright|all]"
        exit 1
        ;;
esac

echo "=========================================="
echo -e "${GREEN}Test run complete!${NC}"
echo "Logs saved to: logs/"
echo "=========================================="