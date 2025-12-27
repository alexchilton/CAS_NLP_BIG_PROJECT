#!/usr/bin/env python3
"""
Master Selenium Test Runner - Run All Tests Sequentially with Visible Browser

This script runs all important selenium tests one after another so you can watch them:
1. Character Loading (Thorin & Elara)
2. World Exploration (lazy generation, items, travel)
3. Hallucination Bug Test (non-existent goblin)
4. Shop System
5. Combat System
6. Party Mode

Each test runs in a visible browser with pauses between tests.
"""

import subprocess
import time
import sys

# ANSI colors
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header(text):
    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}{text:^70}{NC}")
    print(f"{BLUE}{'=' * 70}{NC}\n")

def run_test(test_name, test_file, description):
    """Run a single pytest test with visible browser."""
    print_header(f"TEST: {test_name}")
    print(f"{YELLOW}📝 Description: {description}{NC}")
    print(f"{YELLOW}📂 File: {test_file}{NC}\n")
    
    # Run pytest with visible browser markers
    cmd = [
        'python3', '-m', 'pytest',
        f'e2e_tests/{test_file}',
        '-v',
        '-s',  # Show print statements
        '--tb=short',  # Short traceback
        '--capture=no'  # Don't capture output
    ]
    
    try:
        result = subprocess.run(cmd, cwd='/Users/alexchilton/DataspellProjects/CAS_NLP_BIG_PROJECT')
        
        if result.returncode == 0:
            print(f"\n{GREEN}✅ {test_name} PASSED{NC}")
        else:
            print(f"\n{RED}❌ {test_name} FAILED{NC}")
            response = input(f"\n{YELLOW}Continue to next test? (y/n): {NC}")
            if response.lower() != 'y':
                print(f"{RED}Tests stopped by user{NC}")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n{RED}Tests interrupted by user{NC}")
        sys.exit(1)
    
    # Pause between tests
    print(f"\n{YELLOW}⏸️  Pausing 3 seconds before next test...{NC}")
    time.sleep(3)

def main():
    print_header("🎮 D&D RAG SELENIUM TEST SUITE 🎮")
    print(f"{YELLOW}This will run all selenium tests sequentially with visible browsers{NC}")
    print(f"{YELLOW}You can watch each test execute in Chrome{NC}\n")
    
    # Check if app is running
    import urllib.request
    try:
        urllib.request.urlopen('http://localhost:7860', timeout=2)
        print(f"{GREEN}✅ App is running at http://localhost:7860{NC}\n")
    except:
        print(f"{RED}❌ App is NOT running at http://localhost:7860{NC}")
        print(f"{YELLOW}Please start it first: python3 app.py{NC}\n")
        sys.exit(1)
    
    input(f"{YELLOW}Press ENTER to start tests...{NC}")
    
    # Test Suite
    tests = [
        ("Character Loading", "test_character_loading.py", 
         "Load Thorin and Elara, verify their stats appear correctly"),
        
        ("World Exploration", "test_world_exploration.py",
         "Test lazy location generation, item persistence, travel back/forth"),
        
        ("Hallucination Bug", "test_hallucination_bug.py",
         "Attack non-existent goblin, verify GM doesn't hallucinate dragon"),
        
        ("Shop System", "test_shop_selenium.py",
         "Visit shop, browse items, buy/sell, verify inventory updates"),
        
        ("Combat System", "test_combat_system.py",
         "Full combat test - attack, damage, turns, death"),
        
        ("Party Mode", "test_party_dragon_selenium.py",
         "Multiple characters fighting together against dragon"),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_file, description in tests:
        try:
            run_test(test_name, test_file, description)
            passed += 1
        except Exception as e:
            print(f"{RED}Error running {test_name}: {e}{NC}")
            failed += 1
    
    # Final summary
    print_header("📊 TEST SUMMARY")
    print(f"{GREEN}✅ Passed: {passed}{NC}")
    print(f"{RED}❌ Failed: {failed}{NC}")
    print(f"{BLUE}📝 Total:  {passed + failed}{NC}\n")
    
    if failed == 0:
        print(f"{GREEN}🎉 ALL TESTS PASSED! 🎉{NC}\n")
    else:
        print(f"{YELLOW}⚠️  Some tests failed - check output above{NC}\n")

if __name__ == "__main__":
    main()
