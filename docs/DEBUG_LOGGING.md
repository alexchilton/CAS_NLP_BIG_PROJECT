# GM Debug Logging Guide

## Overview

The Game Master (GM) dialogue system includes comprehensive debug logging that shows exactly what prompts are being sent to the LLM (Ollama or Hugging Face API) and what responses are received.

## Enabling Debug Logging

There are two ways to enable debug logging:

### Method 1: Environment Variable (Recommended)

Set the `GM_DEBUG` environment variable to `true`:

```bash
# Linux/Mac
export GM_DEBUG=true
python3 web/app_gradio.py

# Windows
set GM_DEBUG=true
python web/app_gradio.py
```

### Method 2: Config File

Edit `dnd_rag_system/config/settings.py` and set:

```python
DEBUG_MODE = True
```

## What Gets Logged

When debug mode is enabled, you'll see:

1. **Startup Message**
   ```
   🔍 GM Debug mode enabled - will log all prompts sent to LLM
   ```

2. **Full Prompt Sent to LLM**
   ```
   ================================================================================
   PROMPT SENT TO OLLAMA:
   --------------------------------------------------------------------------------
   You are an experienced Dungeon Master running a D&D 5e game.

   CURRENT LOCATION: Dark Cave
   SCENE: You stand at the entrance of a dark cave...
   TIME: Day 1, morning
   NPCs/CREATURES PRESENT: Goblin

   PLAYER ACTION: I look around the cave
   ...
   ================================================================================
   ```

3. **Response from LLM**
   ```
   --------------------------------------------------------------------------------
   RESPONSE FROM OLLAMA:
   You enter the cave, the dim light from your torch...
   ================================================================================
   ```

## What Context is Included in Prompts

The logged prompts show the full context passed to the LLM:

- **Location**: Current location name and scene description
- **NPCs/Monsters**: List of creatures/NPCs present in the scene
- **Combat State**: If in combat, shows round number, initiative order, and whose turn it is
- **Active Quests**: Shows up to 2 active quests
- **Time**: In-game day and time of day
- **Recent Conversation**: Last 4 messages of conversation history
- **RAG Context**: Retrieved D&D rules if RAG search was performed
- **Player Action**: The current player input

## Disabling Debug Logging

```bash
# Linux/Mac
export GM_DEBUG=false

# Windows
set GM_DEBUG=false
```

Or set `DEBUG_MODE = False` in the config file.

## Example Output

See the test output above for a full example of what debug logging looks like. The logs clearly show:
- What information the AI has access to
- How the game state is formatted for the LLM
- What the AI generates in response

This is extremely useful for:
- Debugging unexpected AI behavior
- Understanding how context affects responses
- Verifying RAG retrieval is working
- Tuning prompts for better results
