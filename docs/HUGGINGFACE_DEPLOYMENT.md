# Deploying to Hugging Face Spaces

This guide explains how to deploy your D&D RAG Game Master to Hugging Face Spaces.

## 🎯 Overview

The app **automatically detects** its environment and uses the optimal backend:
- **Local Mode** (auto-detected): Uses Ollama with `hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M` (RPG-optimized)
- **HF Spaces Mode** (auto-detected): Uses HF Inference API with `Qwen/Qwen2.5-7B-Instruct` (larger, public model)

**Different but compatible models:** Local uses RPG-specific model, HF Spaces uses a larger general model that's excellent for roleplay. The app detects HF Spaces by checking for `SPACE_ID`, `SPACE_AUTHOR_NAME`, or `HF_SPACE` environment variables.

## 📦 Step 1: Prepare Files

You'll need to upload these files to your HF Space:

### Required Files:
```
web/app_gradio.py                # Main Gradio app with character creation
characters/                      # Character JSON files
├── thorin_stormshield.json
└── elara_moonwhisper.json
chromadb/                        # Your ChromaDB database (85MB)
dnd_rag_system/                 # Entire package
├── core/
│   └── chroma_manager.py
├── config/
│   └── settings.py
└── systems/
    ├── character_creator.py
    └── gm_dialogue_unified.py   # Unified Ollama + HF support
requirements.txt                 # Python dependencies
```

## 🚀 Step 2: Create HF Space

1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"**
3. Fill in:
   - **Name**: `dnd-rag-game-master` (or your choice)
   - **License**: MIT
   - **Space SDK**: Gradio
   - **Space hardware**: CPU basic (free tier works!)
   - **Visibility**: Public or Private

## ⚙️ Step 3: Configure Environment Variables (Optional)

The app **auto-detects** HF Spaces, so you only need to set:

1. **`HF_TOKEN`** (Optional) = Your HF token
   - Get from: https://huggingface.co/settings/tokens
   - Qwen/Qwen2.5-7B-Instruct is public and doesn't require a token
   - Only set if using a private model

**Note:** No need to set `USE_HF_API` - it's detected automatically!

## 📁 Step 4: Upload Files

### Option A: Git Upload (Recommended)

```bash
# Clone your space
git clone https://huggingface.co/spaces/YOUR_USERNAME/dnd-rag-game-master
cd dnd-rag-game-master

# Copy files
cp ../CAS_NLP_BIG_PROJECT/web/app_gradio.py app.py
cp ../CAS_NLP_BIG_PROJECT/requirements.txt .
cp -r ../CAS_NLP_BIG_PROJECT/dnd_rag_system .
cp -r ../CAS_NLP_BIG_PROJECT/chromadb .
cp -r ../CAS_NLP_BIG_PROJECT/characters .

# Add and commit
git lfs install  # For large files
git lfs track "chromadb/**/*"
git add .
git commit -m "Initial deployment of D&D RAG Game Master"
git push
```

### Option B: Web Upload

1. Go to your Space's "Files" tab
2. Upload each file/folder:
   - `app.py` (copy from web/app_gradio.py)
   - `requirements.txt`
   - `characters/` folder (with JSON files)
   - `dnd_rag_system/` folder
   - `chromadb/` folder

## 🧪 Step 5: Test Deployment

1. Wait for Space to build (2-3 minutes)
2. Check logs for:
   ```
   🎲 Initializing D&D RAG System...
   🤗 Using Hugging Face Inference API mode
      Model: Qwen/Qwen2.5-7B-Instruct
      Note: Using Inference API compatible model (local uses RPG-specific model)
   ```
3. Test the interface:
   - Load a character
   - Type: "I look around"
   - Should get GM response!

## 🏠 Running Locally vs HF Spaces

### Local (Ollama) - Auto-detected:
```bash
# No environment variables needed
python3 web/app_gradio.py
# Automatically uses Ollama
```

### Local (Test HF Mode) - Manual override:
```bash
export USE_HF_API=true
export HF_TOKEN=your_token_here
python3 web/app_gradio.py
# Manually enables HF API mode for testing
```

### HF Spaces - Auto-detected:
- **Automatically** detects HF Spaces environment
- Uses HF Inference API without any configuration
- Skips Ollama installation in Docker (faster builds!)
- No manual env vars needed!

## 📊 Model Information

**Models Used (auto-selected):**
- **Local Ollama**: `hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M` (4B params, RPG-optimized)
- **HF Spaces**: `Qwen/Qwen2.5-7B-Instruct` (7B params, general model excellent for roleplay)

**Why different models:**
- **Local RPG model** not available via HF Inference API (download-only)
- **Qwen2.5-7B-Instruct** is larger (7B vs 4B) = better quality
- **Public and free** via HF Inference API
- **Excellent for roleplay** - Qwen2.5 series is known for great instruction-following and narrative

## 🐛 Troubleshooting

### Space won't build:
- Check `requirements.txt` exists (not `requirements_spaces.txt`)
- Verify all files uploaded
- Check build logs for errors

### Model errors / "HF_TOKEN not found":
- Qwen/Qwen2.5-7B-Instruct is public and doesn't need a token
- If you get Inference API errors, the model might be rate-limited
- Check HF Inference API status: https://status.huggingface.co/
- Free tier has rate limits - upgrade for higher throughput

### ChromaDB errors:
- Ensure entire `chromadb/` folder is uploaded
- Check `chroma.sqlite3` file is present
- Verify vector data files uploaded

### Model errors:
- Verify your HF token has access to the model
- Model should be public: https://huggingface.co/Chun121/Qwen3-4B-RPG-Roleplay-V2
- Check HF Inference API status

### RAG not working:
- Test with `/rag Magic Missile` command
- Check ChromaDB loaded correctly in logs
- Verify collections exist

## 💡 Tips

1. **Free tier works!** CPU basic is enough for this app
2. **Keep ChromaDB small**: Current 85MB is fine
3. **Monitor usage**: HF Inference API has rate limits on free tier
4. **Auto-detection**: No need to configure env vars - it just works!
5. **Better model on HF Spaces**: 7B model vs 4B locally = higher quality
6. **No token needed**: Qwen2.5-7B-Instruct is public

## 📚 Resources

- [HF Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Gradio on Spaces](https://huggingface.co/docs/hub/spaces-sdks-gradio)
- [HF Inference API](https://huggingface.co/docs/api-inference/index)
- [Model Page](https://huggingface.co/Chun121/Qwen3-4B-RPG-Roleplay-V2)

## 🎮 What Works on HF Spaces

✅ **Pre-made Characters**: Play as Thorin Stormshield or Elara Moonwhisper
✅ **Character Creation**: Full interactive character creator in the UI
✅ **Custom Characters**: Create and save your own characters
✅ **Character Portraits**: Placeholder for future GAN-generated images
✅ **RAG Retrieval**: Spells, monsters, classes, and races
✅ **AI GM Responses**: Using Qwen2.5-7B-Instruct model
✅ **All Commands**: `/help`, `/stats`, `/context`, `/rag`
✅ **Conversation History**: Full chat history tracking
✅ **Character Stats Display**: Live character sheet in sidebar

## ⚠️ Limitations on Free Tier

- Inference may be slower than local Ollama
- Rate limits on HF Inference API
- Space sleeps after inactivity (wakes on visit)
- CPU-only (but works fine for this model size)

---

**Ready to deploy?** Follow Steps 1-5 above! 🚀
