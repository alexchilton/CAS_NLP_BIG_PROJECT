#!/bin/bash
# E2E Test Runner Script
#
# Runs Selenium tests for the Gradio D&D RAG app

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 D&D RAG E2E Test Runner${NC}"
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📦 Installing test dependencies...${NC}"
pip install -q -r requirements.txt

# Check if Gradio app is running
echo -e "${YELLOW}🔍 Checking if Gradio app is running...${NC}"
if curl -s --fail http://localhost:7860 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Gradio app is running${NC}"
else
    echo -e "${RED}❌ Gradio app is NOT running at http://localhost:7860${NC}"
    echo -e "${YELLOW}Please start the app first:${NC}"
    echo "    cd .."
    echo "    python web/app_gradio.py"
    exit 1
fi

# Parse arguments
TEST_ARGS="$@"

# Default: run all tests with verbose output
if [ -z "$TEST_ARGS" ]; then
    TEST_ARGS="-v"
fi

# Run tests
echo -e "${GREEN}🚀 Running tests...${NC}"
echo "================================"

pytest $TEST_ARGS

# Capture exit code
EXIT_CODE=$?

# Summary
echo ""
echo "================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
fi

echo ""
echo "📸 Screenshots: $(pwd)/screenshots/"
echo "📊 HTML Report: Use --html=report.html to generate"

exit $EXIT_CODE
