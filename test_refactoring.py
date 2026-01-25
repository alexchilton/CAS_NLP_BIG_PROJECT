#!/usr/bin/env python3
"""
Integration test for refactored environment detection.

Tests that all affected systems still work correctly after centralizing
environment detection logic.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*70)
print("REFACTORING INTEGRATION TESTS")
print("="*70)
print()

# Test 1: Import all affected modules
print("✅ Test 1: Importing all affected modules...")
try:
    from dnd_rag_system.config import is_huggingface_space, HuggingFaceConfig
    from dnd_rag_system.systems.gm_dialogue_unified import GameMaster
    from dnd_rag_system.systems.action_validator import ActionValidator
    from dnd_rag_system.systems.mechanics_extractor import MechanicsExtractor
    print("   ✅ All imports successful\n")
except Exception as e:
    print(f"   ❌ Import failed: {e}\n")
    sys.exit(1)

# Test 2: Environment detection consistency
print("✅ Test 2: Environment detection consistency...")
try:
    env_detected = is_huggingface_space()
    print(f"   Environment: {'HuggingFace Spaces' if env_detected else 'Local'}")
    print(f"   is_huggingface_space() = {env_detected}")
    print("   ✅ Environment detection works\n")
except Exception as e:
    print(f"   ❌ Environment detection failed: {e}\n")
    sys.exit(1)

# Test 3: HuggingFaceConfig accessibility
print("✅ Test 3: HuggingFaceConfig accessibility...")
try:
    model = HuggingFaceConfig.INFERENCE_MODEL
    endpoint = HuggingFaceConfig.ROUTER_ENDPOINT
    print(f"   Model: {model}")
    print(f"   Endpoint: {endpoint}")
    assert model == "meta-llama/Llama-3.1-8B-Instruct"
    assert endpoint == "https://router.huggingface.co"
    print("   ✅ Config accessible and correct\n")
except Exception as e:
    print(f"   ❌ Config access failed: {e}\n")
    sys.exit(1)

# Test 4: GameMaster initialization
print("✅ Test 4: GameMaster initialization...")
try:
    from dnd_rag_system.core.chroma_manager import ChromaDBManager
    db = ChromaDBManager()
    gm = GameMaster(db)
    print(f"   Model: {gm.model_name}")
    print(f"   Use HF API: {gm.use_hf_api}")
    print("   ✅ GameMaster initializes correctly\n")
except Exception as e:
    print(f"   ❌ GameMaster init failed: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: ActionValidator initialization
print("✅ Test 5: ActionValidator initialization...")
try:
    validator = ActionValidator()
    print(f"   Use HF API: {validator.use_hf_api}")
    print(f"   LLM Model: {validator.llm_model}")
    print("   ✅ ActionValidator initializes correctly\n")
except Exception as e:
    print(f"   ❌ ActionValidator init failed: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: MechanicsExtractor initialization
print("✅ Test 6: MechanicsExtractor initialization...")
try:
    extractor = MechanicsExtractor()
    print(f"   Use HF API: {extractor.use_hf_api}")
    print(f"   Model: {extractor.model_name}")
    print("   ✅ MechanicsExtractor initializes correctly\n")
except Exception as e:
    print(f"   ❌ MechanicsExtractor init failed: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*70)
print("✅ ALL INTEGRATION TESTS PASSED!")
print("="*70)
print()
print("Refactoring is safe to commit.")
