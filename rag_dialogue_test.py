#!/usr/bin/env python3
"""
Test script simulating RAG + Dialogue Model pipeline
Tests how well the dialogue model applies retrieved D&D rules
"""

import subprocess
import time


class MockRAGSystem:
    """Simulates a RAG system with pre-defined D&D rule responses"""

    def __init__(self):
        # Mock D&D rules database
        self.rules_db = {
            "fireball": {
                "spell": "Fireball (3rd-level evocation)",
                "casting_time": "1 action",
                "range": "150 feet",
                "components": "V, S, M (a tiny ball of bat guano and sulfur)",
                "duration": "Instantaneous",
                "description": "Each creature in a 20-foot-radius sphere must make a Dexterity saving throw. A target takes 8d6 fire damage on a failed save, or half as much damage on a successful one.",
                "mechanics": "Roll 8d6 fire damage. Targets make DC 15 Dex save for half damage."
            },
            "magic missile": {
                "spell": "Magic Missile (1st-level evocation)",
                "casting_time": "1 action",
                "range": "120 feet",
                "description": "Three darts of magical force hit their target automatically. Each dart deals 1d4+1 force damage.",
                "mechanics": "Automatic hit. Roll 3 separate 1d4+1 for damage (or 1d4+1 per dart if upcast)."
            },
            "attack longsword": {
                "weapon": "Longsword",
                "damage": "1d8 slashing (one-handed) or 1d10 slashing (two-handed)",
                "mechanics": "Roll d20 + STR modifier + proficiency bonus to hit vs target AC. On hit, roll damage."
            },
            "goblin": {
                "creature": "Goblin",
                "ac": "15 (Leather Armor, Shield)",
                "hp": "7 (2d6)",
                "speed": "30 ft",
                "str": "8 (-1)", "dex": "14 (+2)", "con": "10 (+0)",
                "saves": "Dex +2",
                "mechanics": "Small humanoid, uses scimitar (+4 to hit, 1d6+2 damage) or shortbow."
            },
            "initiative": {
                "rule": "Initiative",
                "mechanics": "Each participant rolls 1d20 + Dex modifier. Act in descending order each round."
            },
            "search room": {
                "rule": "Investigation/Perception",
                "mechanics": "Roll Investigation (INT) to find hidden objects or clues. Roll Perception (WIS) to notice things. DC set by DM based on difficulty."
            },
            "pick lock": {
                "rule": "Thieves' Tools",
                "mechanics": "Roll Dexterity (Thieves' Tools). DC varies by lock complexity. Takes 1 minute. On failure by 5+, lock jams."
            }
        }

    def search(self, query):
        """Simulate RAG search for D&D rules"""
        query_lower = query.lower()
        results = []

        for key, rule in self.rules_db.items():
            if any(word in key for word in query_lower.split()):
                results.append(rule)

        return results


class RAGDialogueTestSystem:
    def __init__(self):
        print("Setting up RAG + Dialogue Model test system...")

        self.model_name = "hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M"
        self.rag = MockRAGSystem()

        # Check if ollama is working
        try:
            result = subprocess.run(['ollama', '--version'], capture_output=True, check=True)
            print(f"✅ Ollama ready")
        except:
            raise Exception("Ollama not found. Please ensure it's installed and the model is available.")

        print("✅ Mock RAG system ready")
        print("-" * 60)

    def generate_rag_enhanced_response(self, player_input, context=""):
        """Generate response using RAG-enhanced prompts"""

        # 1. Determine which enhanced prompt to use based on player input
        player_lower = player_input.lower()

        if "fireball" in player_lower:
            enhanced_prompt = f"""You are an experienced D&D 5e Dungeon Master. 

RETRIEVED RULES (Apply these exactly):
RULE: Fireball (3rd-level evocation)
MECHANICS: Roll 8d6 fire damage. Targets make DC 15 Dex save for half damage.
DETAILS: Each creature in a 20-foot-radius sphere must make a Dexterity saving throw. A target takes 8d6 fire damage on a failed save, or half as much damage on a successful one.

RULE: Goblin Stats
MECHANICS: AC 15, HP 7, Dex +2 modifier, Dex save +2
DETAILS: Small humanoid, typically wields scimitar and shield

RULE: Saving Throws
MECHANICS: Roll 1d20 + ability modifier vs spell save DC
DETAILS: Success = half damage (rounded down), failure = full damage

CURRENT SITUATION: {context}

PLAYER ACTION: {player_input}

INSTRUCTIONS: 
1. Apply the retrieved rules precisely
2. Ask for or simulate appropriate dice rolls
3. Be concise and focused on the mechanical outcome
4. Maintain engaging GM narration style

GM RESPONSE:"""

        elif "magic missile" in player_lower:
            enhanced_prompt = f"""You are an experienced D&D 5e Dungeon Master. 

RETRIEVED RULES (Apply these exactly):
RULE: Magic Missile (1st-level evocation)
MECHANICS: Automatic hit. Roll 3 separate 1d4+1 for damage (or 1d4+1 per dart if upcast).
DETAILS: Three darts of magical force hit their target automatically. Each dart deals 1d4+1 force damage. Cannot be blocked or dodged.

RULE: Bandit Captain Stats
MECHANICS: AC 15, HP 58, no damage resistances to force
DETAILS: Medium humanoid, human bandit leader

RULE: Force Damage
MECHANICS: Magical energy damage, rarely resisted
DETAILS: Pure magical force, bypasses most defenses

CURRENT SITUATION: {context}

PLAYER ACTION: {player_input}

INSTRUCTIONS: 
1. Apply the retrieved rules precisely
2. Ask for or simulate appropriate dice rolls
3. Be concise and focused on the mechanical outcome
4. Maintain engaging GM narration style

GM RESPONSE:"""

        elif "attack" in player_lower and "longsword" in player_lower:
            enhanced_prompt = f"""You are an experienced D&D 5e Dungeon Master. 

RETRIEVED RULES (Apply these exactly):
RULE: Longsword Attack
MECHANICS: Roll d20 + STR modifier + proficiency bonus to hit vs target AC. On hit, roll 1d8 + STR modifier slashing damage (1d10 if two-handed).
DETAILS: Versatile weapon, can be wielded one or two-handed

RULE: Orc Warrior Stats
MECHANICS: AC 13 (Hide Armor), HP 15, no special defenses
DETAILS: Medium humanoid, aggressive melee fighter

RULE: Attack Rolls
MECHANICS: d20 + attack bonus vs Armor Class. Natural 20 = critical hit (double damage dice)
DETAILS: Roll to hit first, then damage on success

CURRENT SITUATION: {context}

PLAYER ACTION: {player_input}

INSTRUCTIONS: 
1. Apply the retrieved rules precisely
2. Ask for or simulate appropriate dice rolls
3. Be concise and focused on the mechanical outcome
4. Maintain engaging GM narration style

GM RESPONSE:"""

        elif "initiative" in player_lower:
            enhanced_prompt = f"""You are an experienced D&D 5e Dungeon Master. 

RETRIEVED RULES (Apply these exactly):
RULE: Initiative
MECHANICS: Each participant rolls 1d20 + Dex modifier. Act in descending order each round.
DETAILS: Roll once at start of combat, maintain same order throughout

RULE: Combat Order
MECHANICS: Highest initiative goes first, then descending order
DETAILS: Ties decided by highest Dex modifier, then by player choice

RULE: Bandit Stats
MECHANICS: Bandits have +1 Dex modifier for initiative
DETAILS: Human bandits, typically act as a group

CURRENT SITUATION: {context}

PLAYER ACTION: {player_input}

INSTRUCTIONS: 
1. Apply the retrieved rules precisely
2. Ask for or simulate appropriate dice rolls
3. Be concise and focused on the mechanical outcome
4. Maintain engaging GM narration style

GM RESPONSE:"""

        elif "pick" in player_lower and ("lock" in player_lower or "thieves" in player_lower):
            enhanced_prompt = f"""You are an experienced D&D 5e Dungeon Master. 

RETRIEVED RULES (Apply these exactly):
RULE: Thieves' Tools (Lock Picking)
MECHANICS: Roll Dexterity (Thieves' Tools) vs DC set by lock complexity. Standard lock DC 15. Takes 1 minute.
DETAILS: On failure by 5 or more, lock mechanism jams and becomes unpickable

RULE: Chest Lock Difficulty
MECHANICS: Sturdy wooden chest with iron lock = DC 15
DETAILS: Well-made but not magical, standard difficulty

RULE: Tool Proficiency
MECHANICS: Add proficiency bonus if proficient with thieves' tools
DETAILS: Without proficiency, can still attempt but no bonus

CURRENT SITUATION: {context}

PLAYER ACTION: {player_input}

INSTRUCTIONS: 
1. Apply the retrieved rules precisely
2. Ask for or simulate appropriate dice rolls
3. Be concise and focused on the mechanical outcome
4. Maintain engaging GM narration style

GM RESPONSE:"""

        else:
            # Fallback for other actions
            enhanced_prompt = f"""You are an experienced D&D 5e Dungeon Master.

CURRENT SITUATION: {context}
PLAYER ACTION: {player_input}

Respond as a GM would, asking for dice rolls as appropriate and applying D&D 5e rules.

GM RESPONSE:"""

        # Display what we're sending to the model
        print("\n📝 Enhanced Prompt:")
        print("-" * 40)
        print(enhanced_prompt[:300] + "..." if len(enhanced_prompt) > 300 else enhanced_prompt)
        print("-" * 40)

        # Send to dialogue model
        try:
            result = subprocess.run(
                ['ollama', 'run', self.model_name, enhanced_prompt],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return f"Error: {result.stderr}"

            response = result.stdout.strip()

            # Clean up response
            if "GM RESPONSE:" in response:
                response = response.split("GM RESPONSE:")[-1].strip()

            return response if response else "No response generated"

        except subprocess.TimeoutExpired:
            return "Error: Response timed out"
        except Exception as e:
            return f"Error: {str(e)}"

    def run_rag_comparison_tests(self):
        """Test scenarios comparing RAG-enhanced vs standard prompts"""

        test_scenarios = [
            {
                "name": "Fireball Spell",
                "context": "Three goblins stand 30 feet away in a forest clearing",
                "player_input": "I cast fireball centered between the goblins",
                "expected_mechanics": ["8d6", "dex save", "fire damage", "half"]
            },
            {
                "name": "Magic Missile",
                "context": "A bandit captain with 25 HP faces you across a tavern",
                "player_input": "I cast magic missile at the bandit captain",
                "expected_mechanics": ["1d4+1", "automatic hit", "force damage"]
            },
            {
                "name": "Sword Attack",
                "context": "An orc warrior (AC 13) charges at you with an axe",
                "player_input": "I attack the orc with my longsword",
                "expected_mechanics": ["d20", "attack roll", "1d8", "slashing"]
            },
            {
                "name": "Initiative Roll",
                "context": "Bandits leap out from behind trees to ambush your party",
                "player_input": "I roll initiative",
                "expected_mechanics": ["1d20", "dex modifier", "initiative"]
            },
            {
                "name": "Lock Picking",
                "context": "You find a sturdy wooden chest with an iron lock",
                "player_input": "I try to pick the lock with my thieves' tools",
                "expected_mechanics": ["dexterity", "thieves' tools", "DC"]
            }
        ]

        results = []

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{'=' * 70}")
            print(f"TEST {i}: {scenario['name']}")
            print(f"{'=' * 70}")
            print(f"Context: {scenario['context']}")
            print(f"Player: {scenario['player_input']}")

            start_time = time.time()
            response = self.generate_rag_enhanced_response(
                scenario['player_input'],
                scenario['context']
            )
            generation_time = time.time() - start_time

            print(f"\n🎭 GM Response:")
            print(f"'{response}'")
            print(f"\n⏱️  Generation time: {generation_time:.1f}s")

            # Check if expected mechanics are mentioned
            response_lower = response.lower()
            found_mechanics = [
                mech for mech in scenario['expected_mechanics']
                if mech.lower() in response_lower
            ]

            print(f"🎲 Expected mechanics: {scenario['expected_mechanics']}")
            print(f"✅ Found mechanics: {found_mechanics}")
            print(f"📊 Mechanics score: {len(found_mechanics)}/{len(scenario['expected_mechanics'])}")

            results.append({
                'scenario': scenario['name'],
                'response': response,
                'mechanics_score': len(found_mechanics) / len(scenario['expected_mechanics']),
                'generation_time': generation_time
            })

        return results

    def interactive_rag_test(self):
        """Interactive mode to test RAG-enhanced responses"""
        print(f"\n{'=' * 60}")
        print("INTERACTIVE RAG + DIALOGUE TEST")
        print("Enter D&D actions. Type 'quit' to exit, 'context: <text>' to set scene")
        print(f"{'=' * 60}")

        context = "You are adventuring in a standard D&D dungeon"

        while True:
            user_input = input(f"\n🎲 Player: ").strip()

            if user_input.lower() == 'quit':
                break
            elif user_input.lower().startswith('context:'):
                context = user_input[8:].strip()
                print(f"📍 Scene set: {context}")
                continue

            response = self.generate_rag_enhanced_response(user_input, context)
            print(f"🎭 GM: {response}")


def main():
    try:
        system = RAGDialogueTestSystem()

        print("RAG + Dialogue Model Test Options:")
        print("1. Quick RAG comparison tests")
        print("2. Interactive RAG testing")

        choice = input("\nChoose option (1-2): ").strip()

        if choice == "1":
            print("\n🧪 Running RAG-enhanced dialogue tests...")
            results = system.run_rag_comparison_tests()

            # Summary
            avg_mechanics = sum(r['mechanics_score'] for r in results) / len(results)
            avg_time = sum(r['generation_time'] for r in results) / len(results)

            print(f"\n{'=' * 60}")
            print("📊 SUMMARY")
            print(f"{'=' * 60}")
            print(f"Average mechanics accuracy: {avg_mechanics:.1%}")
            print(f"Average response time: {avg_time:.1f}s")
            print(f"Total tests: {len(results)}")

        elif choice == "2":
            system.interactive_rag_test()
        else:
            print("Invalid choice!")

    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()