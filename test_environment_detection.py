#!/usr/bin/env python3
"""
Test script for environment detection utility.

Tests that is_huggingface_space() works correctly in different scenarios.
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.config.environment import is_huggingface_space, get_environment_name


def test_local_detection():
    """Test that local environment is correctly detected (no HF env vars)."""
    # Clear any HF env vars
    for var in ["SPACE_ID", "SPACE_AUTHOR_NAME", "HF_SPACE", "USE_HF_API"]:
        os.environ.pop(var, None)

    result = is_huggingface_space()
    env_name = get_environment_name()

    print(f"✅ Test 1: Local detection")
    print(f"   is_huggingface_space() = {result}")
    print(f"   get_environment_name() = {env_name}")

    assert result == False, "Should detect local environment when no HF vars set"
    assert env_name == "local", "Environment name should be 'local'"
    print("   ✅ PASSED\n")


def test_space_id_detection():
    """Test HF Spaces detection via SPACE_ID."""
    os.environ["SPACE_ID"] = "test-space"

    result = is_huggingface_space()
    env_name = get_environment_name()

    print(f"✅ Test 2: HF Spaces detection (SPACE_ID)")
    print(f"   SPACE_ID = {os.getenv('SPACE_ID')}")
    print(f"   is_huggingface_space() = {result}")
    print(f"   get_environment_name() = {env_name}")

    assert result == True, "Should detect HF Spaces when SPACE_ID is set"
    assert env_name == "huggingface", "Environment name should be 'huggingface'"
    print("   ✅ PASSED\n")

    # Clean up
    os.environ.pop("SPACE_ID", None)


def test_author_name_detection():
    """Test HF Spaces detection via SPACE_AUTHOR_NAME."""
    os.environ["SPACE_AUTHOR_NAME"] = "test-author"

    result = is_huggingface_space()

    print(f"✅ Test 3: HF Spaces detection (SPACE_AUTHOR_NAME)")
    print(f"   SPACE_AUTHOR_NAME = {os.getenv('SPACE_AUTHOR_NAME')}")
    print(f"   is_huggingface_space() = {result}")

    assert result == True, "Should detect HF Spaces when SPACE_AUTHOR_NAME is set"
    print("   ✅ PASSED\n")

    # Clean up
    os.environ.pop("SPACE_AUTHOR_NAME", None)


def test_manual_override():
    """Test manual USE_HF_API override."""
    os.environ["USE_HF_API"] = "true"

    result = is_huggingface_space()

    print(f"✅ Test 4: Manual override (USE_HF_API=true)")
    print(f"   USE_HF_API = {os.getenv('USE_HF_API')}")
    print(f"   is_huggingface_space() = {result}")

    assert result == True, "Should detect HF mode when USE_HF_API=true"
    print("   ✅ PASSED\n")

    # Clean up
    os.environ.pop("USE_HF_API", None)


def test_manual_override_false():
    """Test that USE_HF_API=false doesn't trigger HF mode."""
    os.environ["USE_HF_API"] = "false"

    result = is_huggingface_space()

    print(f"✅ Test 5: Manual override false (USE_HF_API=false)")
    print(f"   USE_HF_API = {os.getenv('USE_HF_API')}")
    print(f"   is_huggingface_space() = {result}")

    assert result == False, "Should NOT detect HF mode when USE_HF_API=false"
    print("   ✅ PASSED\n")

    # Clean up
    os.environ.pop("USE_HF_API", None)


if __name__ == "__main__":
    print("="*70)
    print("ENVIRONMENT DETECTION TESTS")
    print("="*70)
    print()

    try:
        test_local_detection()
        test_space_id_detection()
        test_author_name_detection()
        test_manual_override()
        test_manual_override_false()

        print("="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        sys.exit(0)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("="*70)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*70)
        sys.exit(1)
