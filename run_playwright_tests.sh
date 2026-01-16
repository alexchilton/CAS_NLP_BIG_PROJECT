#!/bin/bash
# Run all Playwright E2E tests

# Colors
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}🎭 Running Playwright E2E Tests...${NC}"
echo "=========================================="

# 1. Weapon vs Spell (Basic Chat & Combat)
echo -e "\n${GREEN}▶ Running: test_weapon_vs_spell_playwright.py${NC}"
python3 e2e_tests/test_weapon_vs_spell_playwright.py

# 2. Character Creation (UI, Sliders, Dropdowns)
echo -e "\n${GREEN}▶ Running: test_character_creation_playwright.py${NC}"
python3 e2e_tests/test_character_creation_playwright.py

# 3. Goblin Cave (Context, Env Vars, Combat)
echo -e "\n${GREEN}▶ Running: test_goblin_cave_combat_playwright.py${NC}"
python3 e2e_tests/test_goblin_cave_combat_playwright.py

# 4. Shop System (Location, Transactions)
echo -e "\n${GREEN}▶ Running: test_shop_playwright.py${NC}"
python3 e2e_tests/test_shop_playwright.py

# 5. Adventure Simulation (Random Playthrough)
echo -e "\n${GREEN}▶ Running: test_adventure_simulation_playwright.py${NC}"
python3 e2e_tests/test_adventure_simulation_playwright.py

# 6. Wizard Spell Combat (Casting mechanics)
echo -e "\n${GREEN}▶ Running: test_wizard_spell_combat_playwright.py${NC}"
python3 e2e_tests/test_wizard_spell_combat_playwright.py

# 7. Party Dragon Combat (Narrative scenario)
echo -e "\n${GREEN}▶ Running: test_party_dragon_playwright.py${NC}"
python3 e2e_tests/test_party_dragon_playwright.py

# 8. World Exploration (Map, Travel, Persistence)
echo -e "\n${GREEN}▶ Running: test_world_exploration_playwright.py${NC}"
python3 e2e_tests/test_world_exploration_playwright.py

# 9. Stat Rolling UI (Sliders, Random Roll)
echo -e "\n${GREEN}▶ Running: test_stat_rolling_ui_playwright.py${NC}"
python3 e2e_tests/test_stat_rolling_ui_playwright.py

# 10. UI Loading (Basic Elements)
echo -e "\n${GREEN}▶ Running: test_ui_loading_playwright.py${NC}"
python3 e2e_tests/test_ui_loading_playwright.py

# 11. Character Loading (Verify character sheets)
echo -e "\n${GREEN}▶ Running: test_character_loading_playwright.py${NC}"
python3 e2e_tests/test_character_loading_playwright.py

# 12. Chat Functionality (Messages, Commands, History)
echo -e "\n${GREEN}▶ Running: test_chat_functionality_playwright.py${NC}"
python3 e2e_tests/test_chat_functionality_playwright.py

# 13. Elara vs Skeletons Combat (Wizard Spell Combat)
echo -e "\n${GREEN}▶ Running: test_elara_skeleton_battle_playwright.py${NC}"
python3 e2e_tests/test_elara_skeleton_battle_playwright.py

# 14. Reality Check System (Valid/Invalid actions)
echo -e "\n${GREEN}▶ Running: test_reality_check_playwright.py${NC}"
python3 e2e_tests/test_reality_check_playwright.py

# 15. Shop UI Integration (Buy/Sell, Inventory/Gold)
echo -e "\n${GREEN}▶ Running: test_shop_ui_playwright.py${NC}"
python3 e2e_tests/test_shop_ui_playwright.py

# 16. Simple Goblin Combat (NPC Damage/Death, No Double Turns)
echo -e "\n${GREEN}▶ Running: test_simple_goblin_combat_playwright.py${NC}"
python3 e2e_tests/test_simple_goblin_combat_playwright.py

# 17. UI Combat Integration (Chat, Initiative, Buttons)
echo -e "\n${GREEN}▶ Running: test_ui_combat_integration_playwright.py${NC}"
python3 e2e_tests/test_ui_combat_integration_playwright.py

echo -e "\n${GREEN}✅ All Playwright tests completed.${NC}"
