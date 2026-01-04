# Process Detection Bug Fix

## Problem

The scripts couldn't find running Gradio processes because:

**Original Pattern**: `grep "[p]ython.*app_gradio.py"`

**Actual Process**:
```
/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python web/app_gradio.py
```

The full path is `Python` (capital P) in `.app/Contents/MacOS/`, not `python` (lowercase).

## Root Cause

macOS Python.app wraps the interpreter in:
```
Python.app/Contents/MacOS/Python
```

So the process name is `Python` not `python`.

## Solution

### 1. Better grep Pattern
```bash
# Before (failed):
grep "[p]ython.*app_gradio.py"

# After (works):
grep -E "[P]ython.*app_gradio|[p]ython.*app_gradio"
```

Matches both:
- `Python` (macOS .app wrapper)
- `python` (direct interpreter)
- `python3` (version-specific)

### 2. Port-Based Fallback
If grep fails, check port 7860 directly:

```bash
# Find processes using port 7860
PORT_PIDS=$(lsof -ti:7860 2>/dev/null)

if [ -n "$PORT_PIDS" ]; then
    echo "⚠️  Found process(es) using port 7860"
    # Kill them
    for PID in $PORT_PIDS; do
        kill -9 $PID
    done
fi
```

## Updated Scripts

### `stop_gradio.sh`
```bash
# Find processes
PIDS=$(ps aux | grep -E "[P]ython.*app_gradio|[p]ython.*app_gradio" | awk '{print $2}')

# If none found, check port as fallback
if [ -z "$PIDS" ]; then
    PORT_PIDS=$(lsof -ti:7860 2>/dev/null)
    if [ -n "$PORT_PIDS" ]; then
        # Kill processes on port
    fi
fi
```

### `restart_gradio.sh`
```bash
# Same grep pattern
PIDS=$(ps aux | grep -E "[P]ython.*app_gradio|[p]ython.*app_gradio" | awk '{print $2}')

# Port fallback after killing
PORT_PIDS=$(lsof -ti:7860 2>/dev/null)
if [ -n "$PORT_PIDS" ]; then
    kill -9 $PORT_PIDS
fi
```

## Testing

### Before Fix
```bash
$ ./stop_gradio.sh
✓ No running Gradio server found

$ lsof -i:7860
# Shows process still running!
```

### After Fix
```bash
$ ./stop_gradio.sh
Found running Gradio server(s):
alexchilton 68650 ... Python web/app_gradio.py

🔪 Killing process 68650...
✓ All Gradio processes stopped

$ lsof -i:7860
# Port is free ✅
```

## Why This Matters

### Scenario 1: Port Already in Use
**Before**:
```bash
./start_gradio.sh
# Error: Address already in use
# Manual: ps aux | grep gradio, find PID, kill, retry
```

**After**:
```bash
./start_gradio.sh
# ✓ Finds and kills old process
# ✓ Frees port 7860
# ✓ Starts new server
```

### Scenario 2: Invisible Processes
**Before**: Script says "no server found" but port is blocked  
**After**: Fallback checks port and kills blocking process

## Platform Compatibility

### macOS
- ✅ Matches `Python.app/Contents/MacOS/Python`
- ✅ Fallback with `lsof -ti:7860`

### Linux
- ✅ Matches `/usr/bin/python3`
- ✅ Fallback with `lsof -ti:7860`

### Both
- ✅ Pattern matches case-insensitive Python variants
- ✅ Port-based detection as safety net

## Edge Cases Handled

1. **Multiple Python installations**: Matches any Python variant
2. **Zombie processes**: Port fallback catches them
3. **Process with different path**: Regex allows flexibility
4. **Port blocked by other process**: `lsof` reports and kills it

## Code Diff

```diff
- PIDS=$(ps aux | grep "[p]ython.*app_gradio.py" | awk '{print $2}')
+ PIDS=$(ps aux | grep -E "[P]ython.*app_gradio|[p]ython.*app_gradio" | awk '{print $2}')

  if [ -z "$PIDS" ]; then
-     echo "✓ No running Gradio server found"
-     exit 0
+     echo "✓ No running Gradio server found"
+     echo ""
+     echo "💡 Checking for processes using port 7860..."
+     PORT_PIDS=$(lsof -ti:7860 2>/dev/null)
+     if [ -n "$PORT_PIDS" ]; then
+         echo "⚠️  Found process(es) using port 7860"
+         # Kill them
+     fi
+     exit 0
  fi
```

## User Experience

### Before
```
User: "Port is in use but script says no server found"
Dev: "Try ps aux | grep gradio and kill manually"
```

### After
```
User: ./stop_gradio.sh
Script: ✓ Found and killed Gradio on port 7860
User: ✓ Works!
```

## Files Fixed
- ✅ `stop_gradio.sh` - Enhanced grep + port fallback
- ✅ `restart_gradio.sh` - Enhanced grep + port cleanup
- ✅ `start_gradio.sh` - Calls fixed `stop_gradio.sh`
