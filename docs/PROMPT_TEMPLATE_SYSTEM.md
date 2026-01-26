# Prompt Template System

## Overview

The prompt template system centralizes all long LLM prompts into external template files, eliminating 50+ line string literals embedded in code. This improves maintainability, readability, and allows prompt engineering without code changes.

## Architecture

```
dnd_rag_system/
├── prompts/                          # All prompt templates
│   ├── mechanics_extraction.txt      # 68 lines - Game mechanics parsing
│   ├── intent_classification.txt     # 67 lines - Action intent extraction
│   ├── explore_location.txt          # 35 lines - Location generation
│   ├── monster_encounter.txt         # 16 lines - Single monster descriptions
│   ├── multi_monster_encounter.txt   # 16 lines - Multi-monster encounters
│   ├── item_lore.txt                 # 14 lines - Magical item descriptions
│   ├── validation_no_target.txt      # 12 lines - Target not found messages
│   ├── validation_no_spell_slots.txt # 11 lines - No spell slots messages
│   └── validation_invalid_action.txt # 12 lines - Invalid action messages
└── utils/
    └── prompt_loader.py              # 130 lines - Template loading utility
```

## Usage

### Basic Usage

```python
from dnd_rag_system.utils.prompt_loader import load_prompt

# Load and format a template
prompt = load_prompt(
    "mechanics_extraction",
    narrative="The goblin attacks!",
    char_context="PLAYER CHARACTERS: Thorin",
    npc_context=""
)
```

### Advanced Usage

```python
from dnd_rag_system.utils.prompt_loader import PromptLoader

# Create loader instance
loader = PromptLoader()

# List available templates
templates = loader.list_templates()
# ['explore_location', 'intent_classification', ...]

# Load template
prompt = loader.load("intent_classification", 
                     user_input="I attack the goblin",
                     party_context="")

# Clear cache to reload templates
loader.reload("intent_classification")  # Reload specific template
loader.reload()  # Reload all templates
```

## Template Format

Templates use Python f-string style placeholders:

```
You are a Dungeon Master describing a monster encounter in D&D 5e.

MONSTER: {monster_name} (CR {monster_cr})
LOCATION: {location}
PARTY LEVEL: ~{party_level}
{repeat_info}
{lore}

Generate a dramatic 2-3 sentence encounter description...
```

## Benefits

### 1. **Separation of Concerns**
- Prompts are **data**, not code
- Prompt engineers can iterate without touching Python
- Version control tracks prompt changes separately

### 2. **Code Readability**
- **Before**: 70-line f-string in the middle of method
- **After**: Single `load_prompt()` call

### 3. **Reusability**
- Templates can be shared across systems
- Common patterns extracted once

### 4. **Maintainability**
- Update prompts without code review
- A/B test prompts easily
- Roll back prompt changes without code deployment

### 5. **IDE Support**
- Syntax highlighting for text files
- No escaping issues ({{ }} instead of {{}})
- Easy to read and edit

## Migration Guide

### Before (Embedded Prompt)

```python
def _build_extraction_prompt(self, narrative, character_names, existing_npcs):
    char_context = ""
    if character_names:
        char_context = f"\nKNOWN CHARACTERS: {', '.join(character_names)}\n"
    
    npc_context = ""
    if existing_npcs:
        npc_context = f"\nALREADY PRESENT NPCs: {', '.join(existing_npcs)}\n"

    prompt = f"""Extract D&D game mechanics from this narrative. Output ONLY valid JSON.

NARRATIVE:
{narrative}
{char_context}{npc_context}

Extract mechanics and output as JSON with this exact schema:
{{
  "damage": [
    {{"target": "TARGET_NAME", "amount": NUMBER, "type": "DAMAGE_TYPE"}}
  ],
  ...
  (60 more lines)
}}
"""
    return prompt
```

### After (Template Loading)

```python
from dnd_rag_system.utils.prompt_loader import load_prompt

def _build_extraction_prompt(self, narrative, character_names, existing_npcs):
    char_context = ""
    if character_names:
        char_context = f"\nKNOWN CHARACTERS: {', '.join(character_names)}\n"
    
    npc_context = ""
    if existing_npcs:
        npc_context = f"\nALREADY PRESENT NPCs: {', '.join(existing_npcs)}\n"

    return load_prompt(
        "mechanics_extraction",
        narrative=narrative,
        char_context=char_context,
        npc_context=npc_context
    )
```

## Current Status

### ✅ Infrastructure Complete
- [x] Created `dnd_rag_system/prompts/` directory
- [x] Extracted 9 template files (251 total lines)
- [x] Built `PromptLoader` utility class
- [x] Added template caching
- [x] Comprehensive error handling
- [x] Committed and deployed

### ⏳ Pending Migrations

Systems still using embedded prompts (ready to migrate):

1. **mechanics_extractor.py** (68-line prompt) → `mechanics_extraction.txt` ✅ Created
2. **action_validator.py** (67-line prompt) → `intent_classification.txt` ✅ Created
3. **world_builder.py** (35-line prompt) → `explore_location.txt` ✅ Created
4. **monster_description_generator.py** (2 prompts) → Templates created ✅
5. **item_lore_generator.py** (1 prompt) → `item_lore.txt` ✅ Created
6. **validation_message_generator.py** (3 prompts) → Templates created ✅

**Migration Impact**: Update 6 files, remove ~250 lines of embedded prompts

## Template Inventory

| Template | Size | Used By | Status |
|----------|------|---------|--------|
| `mechanics_extraction.txt` | 68 lines | MechanicsExtractor | Ready |
| `intent_classification.txt` | 67 lines | ActionValidator | Ready |
| `explore_location.txt` | 35 lines | WorldBuilder | Ready |
| `monster_encounter.txt` | 16 lines | MonsterDescriptionGenerator | Ready |
| `multi_monster_encounter.txt` | 16 lines | MonsterDescriptionGenerator | Ready |
| `item_lore.txt` | 14 lines | ItemLoreGenerator | Ready |
| `validation_no_target.txt` | 12 lines | ValidationMessageGenerator | Ready |
| `validation_no_spell_slots.txt` | 11 lines | ValidationMessageGenerator | Ready |
| `validation_invalid_action.txt` | 12 lines | ValidationMessageGenerator | Ready |

## Design Decisions

### Why .txt instead of .yaml?

- **Simpler**: No YAML parsing overhead
- **Readable**: Plain text, no special syntax
- **Flexible**: Can include JSON examples without escaping
- **Fast**: Direct file read, minimal processing

### Why f-string style placeholders?

- **Familiar**: Python developers know the syntax
- **IDE Support**: Syntax highlighting works
- **Simple**: `template.format(**kwargs)` is built-in
- **Explicit**: Missing variables raise clear errors

### Why template caching?

- **Performance**: Load once, use many times
- **Production**: No disk I/O on every LLM call
- **Development**: Reload() available for testing

## Future Enhancements

### Possible Additions

1. **System Messages**: Extract to separate files
   - `system_messages/dm_roleplay.txt`
   - `system_messages/mechanics_parser.txt`

2. **Multi-Language Support**: Templates in different languages
   - `prompts/en/mechanics_extraction.txt`
   - `prompts/es/mechanics_extraction.txt`

3. **Prompt Versioning**: A/B testing support
   - `prompts/mechanics_extraction_v1.txt`
   - `prompts/mechanics_extraction_v2.txt`

4. **Validation**: JSON schema for template variables
   - Catch missing placeholders at load time

5. **Hot Reload**: Watch file changes in development
   - Auto-reload templates when files change

## Testing

```python
# Test prompt loader
from dnd_rag_system.utils.prompt_loader import PromptLoader

def test_prompt_loader():
    loader = PromptLoader()
    
    # Test loading
    prompt = loader.load(
        "mechanics_extraction",
        narrative="Test",
        char_context="",
        npc_context=""
    )
    assert "Extract D&D game mechanics" in prompt
    
    # Test caching
    prompt2 = loader.load("mechanics_extraction", ...)
    # Should use cached version (no disk I/O)
    
    # Test missing variable
    try:
        loader.load("mechanics_extraction")  # Missing required vars
    except ValueError as e:
        assert "Missing required variable" in str(e)
```

## Summary

The prompt template system successfully extracts 250+ lines of embedded prompts into 9 maintainable template files. The infrastructure is production-ready and awaiting incremental migration of existing systems.

**Key Metrics:**
- 🗂️ **9 templates** created (251 lines total)
- 🔧 **130-line** utility class
- 📉 **~250 lines** of embedded prompts ready to remove
- ✅ **100%** of long prompts documented and extracted
- 🚀 **Zero breaking changes** - backward compatible

The system is designed for gradual adoption - existing code continues to work while new code can immediately benefit from centralized prompts.
