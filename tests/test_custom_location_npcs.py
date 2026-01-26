#!/usr/bin/env python3
"""
Demo: Custom Location + Custom NPCs via Environment Variables

Shows the flexibility of TEST_START_LOCATION and TEST_NPCS:
- Create ANY location on the fly
- Add ANY NPCs (or no NPCs)
- No forced location-based NPC mappings
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web.app_gradio import load_character_with_location
from web.session_state import create_session_state

print("\n" + "🎨" * 40)
print("CUSTOM LOCATION + CUSTOM NPC DEMO")
print("🎨" * 40)

# Test 1: Haunted Mansion with Ghost and Vampire
print("\n" + "=" * 80)
print("TEST 1: Custom Location with Custom NPCs")
print("=" * 80)

os.environ['TEST_START_LOCATION'] = 'Haunted Mansion'
os.environ['TEST_NPCS'] = 'Ghost, Vampire'

print(f"\n🧪 Environment Variables Set:")
print(f"   TEST_START_LOCATION = 'Haunted Mansion'")
print(f"   TEST_NPCS = 'Ghost, Vampire'")

try:
    # Create fresh session (initializes its own GM and DB)
    session = create_session_state()
    
    loc_name, loc_desc, char_name, updated_session = load_character_with_location("Thorin", session)
    print(f"\n✅ Loaded {char_name} at {loc_name}")
    print(f"📍 Description: {loc_desc[:100]}...")

    # Check NPCs from Session
    print(f"👻 NPCs Present: {updated_session.gm.session.npcs_present}")

    if "Ghost" in updated_session.gm.session.npcs_present and "Vampire" in updated_session.gm.session.npcs_present:
        print("\n✅ SUCCESS: Custom NPCs added!")
    else:
        print(f"\n❌ FAIL: Expected ['Ghost', 'Vampire'], got {updated_session.gm.session.npcs_present}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Peaceful Town with NO NPCs
print("\n" + "=" * 80)
print("TEST 2: Location with NO NPCs (no TEST_NPCS set)")
print("=" * 80)

os.environ['TEST_START_LOCATION'] = 'The Prancing Pony Inn'
if 'TEST_NPCS' in os.environ:
    del os.environ['TEST_NPCS']

print(f"\n🧪 Environment Variables Set:")
print(f"   TEST_START_LOCATION = 'The Prancing Pony Inn'")
print(f"   TEST_NPCS = (not set)")

try:
    # Create fresh session
    session = create_session_state()

    loc_name, loc_desc, char_name, updated_session = load_character_with_location("Thorin", session)
    print(f"\n✅ Loaded {char_name} at {loc_name}")
    print(f"📍 Description: {loc_desc[:100]}...")
    print(f"👤 NPCs Present: {updated_session.gm.session.npcs_present}")

    if not updated_session.gm.session.npcs_present:
        print("\n✅ SUCCESS: No NPCs added (as expected)!")
    else:
        print(f"\n❌ FAIL: Expected no NPCs, got {updated_session.gm.session.npcs_present}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 3: On-the-fly location creation with custom monsters
print("\n" + "=" * 80)
print("TEST 3: Create New Location On-The-Fly with Custom Monsters")
print("=" * 80)

os.environ['TEST_START_LOCATION'] = 'Underwater Temple'
os.environ['TEST_NPCS'] = 'Sahuagin, Sea Hag'

print(f"\n🧪 Environment Variables Set:")
print(f"   TEST_START_LOCATION = 'Underwater Temple'")
print(f"   TEST_NPCS = 'Sahuagin, Sea Hag'")

try:
    # Create fresh session
    session = create_session_state()

    loc_name, loc_desc, char_name, updated_session = load_character_with_location("Thorin", session)
    print(f"\n✅ Loaded {char_name}")
    print(f"📍 Location: {loc_name}")
    print(f"🌊 NPCs Present: {updated_session.gm.session.npcs_present}")

    if "Sahuagin" in updated_session.gm.session.npcs_present and "Sea Hag" in updated_session.gm.session.npcs_present:
        print("\n✅ SUCCESS: On-the-fly location + custom NPCs!")
    else:
        print(f"\n❌ FAIL: Expected ['Sahuagin', 'Sea Hag'], got {updated_session.gm.session.npcs_present}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ DEMO COMPLETE!")
print("=" * 80)
print("\n💡 Key Takeaways:")
print("   ✅ NPCs are OPTIONAL, not forced by location")
print("   ✅ Can create ANY location with ANY NPCs")
print("   ✅ Can set location without NPCs")
print("   ✅ Perfect for flexible E2E testing")
print("=" * 80 + "\n")
