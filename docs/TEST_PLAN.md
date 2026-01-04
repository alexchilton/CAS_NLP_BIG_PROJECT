# Test Plan for New Features

## Current Test Status

### ✅ Passing Tests (Verified)
- `test_game_state.py` - All 67 tests pass (GameSession, CharacterState, PartyState, CombatState)
- `test_mechanics_system.py` - All 5 tests pass (damage extraction, healing, conditions)

### ⚠️ Need to Verify
- `test_unconscious_state.py` - Created but needs Ollama mocking
- Other combat tests may need updates

## Required New Tests

### 1. Player Attack Calculation Tests
**File**: `tests/test_player_attack_calculation.py`

**Test Cases**:
```python
def test_basic_attack_hit():
    """Test successful attack against low AC"""
    # Thorin (STR 16, +2 prof) attacks Goblin (AC 12)
    # Roll 10: 10 + 3 + 2 = 15 vs AC 12 → HIT
    # Damage: 1d8+3 (longsword)
    
def test_basic_attack_miss():
    """Test missed attack against high AC"""
    # Roll 5: 5 + 3 + 2 = 10 vs AC 18 → MISS
    
def test_critical_hit():
    """Test natural 20 doubles damage"""
    # Roll 20: automatic hit
    # Damage: (1d8+3) * 2
    
def test_critical_miss():
    """Test natural 1 always misses"""
    # Roll 1: 1 + 5 = 6 vs AC 5 → still MISS
    
def test_weapon_detection():
    """Test finding weapon in equipment list"""
    # Equipment: ["Longsword", "Shield"] → longsword (1d8)
    # Equipment: ["Greatsword"] → greatsword (2d6)
    # Equipment: ["Backpack", "Rope"] → unarmed (1d4)
    
def test_no_base_character_stats():
    """Test graceful failure when character not loaded"""
    # base_character_stats empty → returns ""
    
def test_npc_not_in_combat():
    """Test default AC when NPC not loaded"""
    # Target not in combat manager → AC defaults to 12
    
def test_party_mode_attack():
    """Test attack works with multiple characters"""
    # Party: Thorin + Elara
    # Thorin attacks → uses Thorin's stats
    # Elara attacks → uses Elara's stats
```

**Priority**: HIGH - Core combat feature

### 2. Base Character Stats Storage Tests
**File**: `tests/test_base_character_stats.py`

**Test Cases**:
```python
def test_store_single_character():
    """Test solo mode character storage"""
    session = GameSession()
    session.base_character_stats[thorin.name] = thorin
    assert "Thorin Stormshield" in session.base_character_stats
    
def test_store_multiple_characters():
    """Test party mode character storage"""
    session = GameSession()
    session.base_character_stats[thorin.name] = thorin
    session.base_character_stats[elara.name] = elara
    assert len(session.base_character_stats) == 2
    
def test_character_lookup():
    """Test retrieving character stats by name"""
    session = GameSession()
    session.base_character_stats["Thorin"] = thorin
    char = session.base_character_stats["Thorin"]
    assert char.strength == 16
    
def test_missing_character():
    """Test graceful handling of missing character"""
    session = GameSession()
    char = session.base_character_stats.get("NonExistent")
    assert char is None
```

**Priority**: MEDIUM - Architectural change

### 3. Combat Integration Tests
**File**: `tests/test_combat_damage_integration.py`

**Test Cases**:
```python
def test_player_attacks_npc():
    """Test full flow: player attack → damage → NPC HP reduction"""
    # 1. Player attacks goblin
    # 2. Attack calculated (hit, 8 damage)
    # 3. GM narrates
    # 4. Mechanics extracted
    # 5. Damage applied to goblin
    # 6. Goblin HP: 15 → 7
    
def test_npc_attacks_player():
    """Test NPC attack flow still works"""
    # Existing functionality - regression test
    
def test_bidirectional_combat():
    """Test player and NPC exchange attacks"""
    # Turn 1: Player attacks goblin (8 dmg)
    # Turn 2: Goblin attacks player (5 dmg)
    # Verify both HP changes
    
def test_kill_npc():
    """Test NPC death when HP reaches 0"""
    # Goblin at 5 HP
    # Player hits for 8 damage
    # Goblin HP → 0, marked dead
    # Removed from combat
    
def test_player_unconscious_no_attack():
    """Test unconscious player can't calculate attacks"""
    # Player unconscious
    # Try to attack → blocked before calculation
```

**Priority**: HIGH - Critical combat flow

### 4. Encounter System Tests
**File**: `tests/test_encounter_cooldown.py`

**Test Cases**:
```python
def test_encounter_cooldown():
    """Test 5-turn cooldown prevents spam"""
    # Turn 1: Encounter spawns
    # Turns 2-5: No encounters
    # Turn 6: Encounter can spawn again
    
def test_location_change_resets():
    """Test changing location allows new encounter"""
    # Turn 1: Encounter at Forest
    # Turn 2: Travel to Cave
    # Turn 3: Encounter can spawn (location changed)
    
def test_combat_doesnt_trigger_encounter():
    """Test no random encounters during combat"""
    # In combat: turns pass
    # No random encounters spawn
```

**Priority**: MEDIUM - Already implemented, needs coverage

### 5. Item Persistence Tests  
**File**: `tests/test_item_persistence.py`

**Test Cases**:
```python
def test_item_pickup_removes_from_location():
    """Test picking up item removes it from location"""
    # Location has ["Rope", "Torch"]
    # Player picks up Rope
    # Location now has ["Torch"]
    
def test_item_no_respawn():
    """Test item doesn't reappear on revisit"""
    # Player picks up Rope at Cave
    # Player leaves Cave
    # Player returns to Cave
    # Rope still gone
    
def test_multiple_items():
    """Test picking up multiple items"""
    # Pick up Rope, Torch, Chest
    # All removed from location
    # All in player inventory
```

**Priority**: MEDIUM - Already implemented, needs coverage

## Test Infrastructure Needs

### Mocking Strategy
Many tests require Ollama LLM calls. Options:

1. **Mock Ollama responses** (RECOMMENDED):
```python
@pytest.fixture
def mock_ollama(monkeypatch):
    def mock_query(prompt):
        return '{"damage": [{"target": "goblin", "amount": 8}]}'
    monkeypatch.setattr("gm._query_ollama", mock_query)
```

2. **Use test fixtures** (pre-recorded responses)
3. **Skip LLM tests in CI** (only run locally with Ollama)

### Test Data Fixtures
Need consistent test data:

```python
@pytest.fixture
def thorin_character():
    """Thorin Stormshield - Fighter, STR 16, Longsword"""
    return Character(
        name="Thorin Stormshield",
        character_class="Fighter",
        strength=16,
        proficiency_bonus=2,
        equipment=["Longsword", "Shield"],
        # ...
    )

@pytest.fixture
def goblin_npc():
    """Standard goblin - AC 15, HP 15"""
    return MonsterInstance(
        name="Goblin",
        ac=15,
        max_hp=15,
        current_hp=15,
        # ...
    )
```

## Running Tests

### Quick Unit Tests (No LLM)
```bash
pytest tests/test_player_attack_calculation.py -v
pytest tests/test_base_character_stats.py -v
pytest tests/test_item_persistence.py -v
```

### Integration Tests (Requires Ollama)
```bash
pytest tests/test_combat_damage_integration.py -v --ollama
pytest tests/test_encounter_cooldown.py -v --ollama
```

### All Tests
```bash
pytest tests/ -v
```

## Priority Order

1. **HIGH**: Player attack calculation tests
2. **HIGH**: Combat damage integration tests  
3. **MEDIUM**: Base character stats storage tests
4. **MEDIUM**: Encounter cooldown tests
5. **MEDIUM**: Item persistence tests
6. **LOW**: Update existing combat tests for new architecture

## Estimated Effort

- Player attack tests: 2-3 hours
- Combat integration tests: 3-4 hours (mocking complexity)
- Base stats tests: 1 hour
- Encounter tests: 2 hours
- Item persistence tests: 1-2 hours

**Total**: ~10-12 hours for comprehensive test coverage

## Notes

- Existing `test_game_state.py` (67 tests) still passes ✅
- Existing `test_mechanics_system.py` (5 tests) still passes ✅
- Focus on NEW functionality first, then update old tests
- Mock Ollama for speed and CI compatibility
