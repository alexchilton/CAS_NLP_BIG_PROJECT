# Deploying to Hugging Face Spaces

This guide explains how to deploy your D&D RAG Game Master to Hugging Face Spaces.

## 🎯 Overview

The app **automatically detects** its environment and uses the optimal backend:
- **Local Mode** (auto-detected): Uses Ollama with `hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M` (quantized)
- **HF Spaces Mode** (auto-detected): Uses HF Inference API with `Chun121/Qwen3-4B-RPG-Roleplay-V2` (full model)

**Same RPG-optimized model in both modes!** The app detects HF Spaces by checking for `SPACE_ID`, `SPACE_AUTHOR_NAME`, or `HF_SPACE` environment variables.

## 📦 Step 1: Prepare Files

You'll need to upload these files to your HF Space:

### Required Files:
```
app.py                           # Main Gradio app (unified version)
requirements_spaces.txt          # Rename to requirements.txt for Spaces
chromadb/                        # Your ChromaDB database (85MB)
dnd_rag_system/                 # Entire package
├── core/
│   └── chroma_manager.py
├── config/
│   └── settings.py
└── systems/
    ├── character_creator.py
    └── gm_dialogue_unified.py   # Unified Ollama + HF support
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
   - Only needed if using private models
   - The RPG model (Chun121/Qwen3-4B-RPG-Roleplay-V2) is public

**Note:** No need to set `USE_HF_API` - it's detected automatically!

## 📁 Step 4: Upload Files

### Option A: Git Upload (Recommended)

```bash
# Clone your space
git clone https://huggingface.co/spaces/YOUR_USERNAME/dnd-rag-game-master
cd dnd-rag-game-master

# Copy files
cp ../CAS_NLP_BIG_PROJECT/app.py .
cp ../CAS_NLP_BIG_PROJECT/requirements_spaces.txt requirements.txt
cp -r ../CAS_NLP_BIG_PROJECT/dnd_rag_system .
cp -r ../CAS_NLP_BIG_PROJECT/chromadb .

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
   - `app.py`
   - `requirements.txt` (renamed from requirements_spaces.txt)
   - `dnd_rag_system/` folder
   - `chromadb/` folder

## 🧪 Step 5: Test Deployment

1. Wait for Space to build (2-3 minutes)
2. Check logs for:
   ```
   🎲 Initializing D&D RAG System...
   🤗 Using Hugging Face Inference API mode
      Model: Chun121/Qwen3-4B-RPG-Roleplay-V2
   ```
3. Test the interface:
   - Load a character
   - Type: "I look around"
   - Should get GM response!

## 🏠 Running Locally vs HF Spaces

### Local (Ollama) - Auto-detected:
```bash
# No environment variables needed
python3 app_gradio.py
# Automatically uses Ollama
```

### Local (Test HF Mode) - Manual override:
```bash
export USE_HF_API=true
export HF_TOKEN=your_token_here
python3 app_gradio.py
# Manually enables HF API mode for testing
```

### HF Spaces - Auto-detected:
- **Automatically** detects HF Spaces environment
- Uses HF Inference API without any configuration
- Skips Ollama installation in Docker (faster builds!)
- No manual env vars needed!

## 📊 Model Information

**Model Used:** `Chun121/Qwen3-4B-RPG-Roleplay-V2` (same model everywhere!)
- **Local Ollama**: `hf.co/Chun121/Qwen3-4B-RPG-Roleplay-V2:Q4_K_M` (quantized to Q4_K_M)
- **HF Spaces**: `Chun121/Qwen3-4B-RPG-Roleplay-V2` (full precision model)

**Benefits of using the same model:**
- **Consistent behavior** across local and cloud environments
- **RPG-optimized** - specifically fine-tuned for D&D roleplay and narrative
- **Better on HF Spaces** - full precision vs quantized version
- **Faster inference** via HF's optimized infrastructure

## 🐛 Troubleshooting

### Space won't build:
- Check `requirements.txt` exists (not `requirements_spaces.txt`)
- Verify all files uploaded
- Check build logs for errors

### "HF_TOKEN not found" error:
- Only needed for private models
- The RPG model (Chun121/Qwen3-4B-RPG-Roleplay-V2) should be public
- Check model visibility at: https://huggingface.co/Chun121/Qwen3-4B-RPG-Roleplay-V2
- If private, add `HF_TOKEN` to Space secrets

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
5. **Same RPG model everywhere**: Consistent D&D gameplay experience
6. **Better quality on HF Spaces**: Full precision vs quantized local version

## 📚 Resources

- [HF Spaces Documentation](https://huggingface.co/docs/hub/spaces)
- [Gradio on Spaces](https://huggingface.co/docs/hub/spaces-sdks-gradio)
- [HF Inference API](https://huggingface.co/docs/api-inference/index)
- [Model Page](https://huggingface.co/Chun121/Qwen3-4B-RPG-Roleplay-V2)

## 🎮 What Works on HF Spaces

✅ Character selection (Thorin, Elara)
✅ RAG retrieval (spells, monsters, classes)
✅ AI GM responses using Qwen3-4B-RPG model
✅ All commands (`/help`, `/stats`, `/context`, `/rag`)
✅ Conversation history
✅ Character stats display

## ⚠️ Limitations on Free Tier

- Inference may be slower than local Ollama
- Rate limits on HF Inference API
- Space sleeps after inactivity (wakes on visit)
- CPU-only (but works fine for this model size)

---

**Ready to deploy?** Follow Steps 1-5 above! 🚀
