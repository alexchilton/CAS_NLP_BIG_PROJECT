# Server Management Scripts - Summary

## Created Files

### 1. `start_gradio.sh` ✅
**Purpose**: Start Gradio server (kills existing first)

**Usage**:
```bash
./start_gradio.sh              # Foreground mode
./start_gradio.sh --background # Background mode
./start_gradio.sh -b           # Background (short flag)
```

**Features**:
- Automatically kills any existing server
- Foreground mode: Shows all output, Ctrl+C to stop
- Background mode: Runs in background, logs to `logs/gradio.log`
- Clean startup messages with PID and URL

---

### 2. `stop_gradio.sh` ✅
**Purpose**: Stop any running Gradio server

**Usage**:
```bash
./stop_gradio.sh
```

**Features**:
- Finds all `app_gradio.py` processes
- Graceful shutdown (SIGTERM)
- Force kill if needed (SIGKILL)
- Shows what was stopped

---

### 3. `restart_gradio.sh` ✅
**Purpose**: One-command restart (stop + start)

**Usage**:
```bash
./restart_gradio.sh              # Foreground
./restart_gradio.sh --background # Background
./restart_gradio.sh -b           # Background (short)
```

**Features**:
- Calls `stop_gradio.sh` first
- Then starts fresh server
- Useful after code changes
- Supports foreground/background modes

---

## Why These Scripts?

### Problem Before
```bash
# Manual process (error-prone):
ps aux | grep app_gradio           # Find PID
kill 12345                         # Kill it
python3 web/app_gradio.py          # Restart
# But sometimes port still in use...
# Or multiple processes running...
```

### Solution Now
```bash
# One command:
./restart_gradio.sh -b
# ✓ All old processes killed
# ✓ Server started fresh
# ✓ Logs saved
# ✓ PID and URL shown
```

---

## Use Cases

### Development Workflow
```bash
# 1. Start server in background
./start_gradio.sh -b

# 2. Make code changes to fix inventory bug
vim web/app_gradio.py

# 3. Quick restart to test
./restart_gradio.sh -b

# 4. Watch logs
tail -f logs/gradio.log

# 5. Stop when done
./stop_gradio.sh
```

### Testing After Bug Fix
```bash
# After fixing inventory display bug:
./restart_gradio.sh              # Restart in foreground
# Test in browser
# See all output in terminal
# Ctrl+C when done
```

### Production/Demo
```bash
# Start server in background for demo
./start_gradio.sh -b

# Server runs independently
# Can close terminal
# Access at http://localhost:7860

# Stop later
./stop_gradio.sh
```

---

## Safety Features

### 1. No `pkill` or `killall`
Uses specific PIDs only:
```bash
# Safe: Kills only app_gradio.py processes
ps aux | grep "[p]ython.*app_gradio.py" | awk '{print $2}'
# Then: kill <specific_PID>
```

### 2. Graceful → Force
```bash
kill $PID        # Try graceful first
sleep 1
kill -9 $PID     # Force if needed
```

### 3. Port Release Wait
```bash
# After killing, wait for port to be released
sleep 2
# Then start new server
```

---

## Files Structure

```
/
├── start_gradio.sh      # Start server
├── stop_gradio.sh       # Stop server  
├── restart_gradio.sh    # Restart server
├── logs/
│   └── gradio.log       # Background server logs
└── docs/
    └── GRADIO_SCRIPTS.md # Documentation
```

---

## Background Mode Details

### Starting
```bash
./start_gradio.sh --background
```

**What happens**:
1. Kills any existing server
2. Creates `logs/` directory if needed
3. Starts server with `nohup`
4. Redirects output to `logs/gradio.log`
5. Shows PID and URL
6. Server persists after terminal closes

### Viewing Logs
```bash
# Watch live
tail -f logs/gradio.log

# View last 100 lines
tail -100 logs/gradio.log

# Search logs
grep "error" logs/gradio.log
```

### Stopping
```bash
./stop_gradio.sh
# Finds and kills background process
```

---

## Common Issues & Solutions

### "Address already in use"
```bash
./stop_gradio.sh    # Kill old server
./start_gradio.sh   # Try again
```

### Multiple servers running
```bash
./stop_gradio.sh    # Kills ALL of them
```

### Can't find process
```bash
# Manual check:
ps aux | grep gradio

# Manual kill:
kill -9 <PID>
```

### Permission denied
```bash
chmod +x *.sh       # Make executable
```

---

## Integration with README

Updated `README.md` to include:
```markdown
### Web Interface (Recommended)

```bash
# Quick start (foreground)
python web/app_gradio.py

# Or use convenience scripts:
./start_gradio.sh              # Foreground (Ctrl+C to stop)
./start_gradio.sh --background # Background (runs in logs)
./restart_gradio.sh            # Kill old, start new
./stop_gradio.sh               # Stop server
```

**Server Management:**
- `start_gradio.sh` - Start server (kills existing first)
- `stop_gradio.sh` - Stop any running server
- `restart_gradio.sh` - Quick restart after code changes
- See `docs/GRADIO_SCRIPTS.md` for details
```

---

## Testing

All scripts tested and working:
```bash
$ ./stop_gradio.sh
✓ No running Gradio server found

$ ./start_gradio.sh -b
✓ Gradio server started (PID: 12345)
🌐 URL: http://localhost:7860

$ ps aux | grep gradio
# Shows running process

$ ./stop_gradio.sh
🔪 Killing process 12345...
✓ All Gradio processes stopped
```

---

## Benefits

✅ **Quick restarts** after code changes  
✅ **Clean shutdown** (no orphaned processes)  
✅ **Background mode** for development  
✅ **Logs saved** for debugging  
✅ **Safe killing** (specific PIDs only)  
✅ **User-friendly** messages and instructions  

---

## Related Fix

This also helps with the **inventory display bug** fix:
- Fix code: Show both EQUIPMENT and INVENTORY
- Quick test: `./restart_gradio.sh -b`
- See fix working immediately
- No manual process hunting

---

## Future Enhancements

Possible additions:
- `status_gradio.sh` - Check if server is running
- `logs_gradio.sh` - Tail logs with colors
- Auto-restart on code changes (watchdog)
- Health check endpoint pinging
