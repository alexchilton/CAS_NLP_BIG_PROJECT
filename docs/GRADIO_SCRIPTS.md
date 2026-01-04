# Gradio Server Management Scripts

Quick scripts to manage the Gradio web interface server.

## Scripts

### 🚀 `start_gradio.sh`
Start the Gradio server.

```bash
# Start in foreground (Ctrl+C to stop)
./start_gradio.sh

# Start in background
./start_gradio.sh --background
./start_gradio.sh -b
```

**Background mode**:
- Server runs in background
- Logs saved to `logs/gradio.log`
- View logs: `tail -f logs/gradio.log`
- Stop with: `./stop_gradio.sh`

---

### 🛑 `stop_gradio.sh`
Stop any running Gradio server.

```bash
./stop_gradio.sh
```

Kills all `app_gradio.py` processes safely.

---

### 🔄 `restart_gradio.sh`
Stop and restart the Gradio server (one command).

```bash
# Restart in foreground
./restart_gradio.sh

# Restart in background
./restart_gradio.sh --background
./restart_gradio.sh -b
```

**Use this when**:
- You made code changes
- Server is unresponsive
- Testing new features

---

## Quick Reference

```bash
# Common workflow
./restart_gradio.sh -b     # Start in background for development
tail -f logs/gradio.log    # Watch logs
./stop_gradio.sh           # Stop when done

# Manual server (see all output)
./start_gradio.sh          # Ctrl+C to stop
```

## Port

Default: `http://localhost:7860`

## Troubleshooting

**"Address already in use"**:
```bash
./stop_gradio.sh           # Kill old server
./start_gradio.sh          # Try again
```

**Server won't stop**:
```bash
ps aux | grep app_gradio   # Find PID
kill -9 <PID>              # Force kill
```

**Check if running**:
```bash
ps aux | grep app_gradio
```

---

## Files

- `start_gradio.sh` - Start server (kills old one first)
- `stop_gradio.sh` - Stop server
- `restart_gradio.sh` - Stop + Start in one command
- `logs/gradio.log` - Background server logs
