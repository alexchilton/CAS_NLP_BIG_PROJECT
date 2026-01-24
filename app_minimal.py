#!/usr/bin/env python3
"""
Minimal Gradio app for testing HuggingFace Spaces deployment
Step 2: Testing ChromaDB imports
"""

import gradio as gr

# Test ChromaDB import
try:
    import chromadb
    import sentence_transformers
    chromadb_status = f"✅ ChromaDB {chromadb.__version__} loaded"
    st_status = f"✅ sentence-transformers {sentence_transformers.__version__} loaded"
except Exception as e:
    chromadb_status = f"❌ ChromaDB import failed: {e}"
    st_status = ""

def greet(name):
    status = f"{chromadb_status}\n{st_status}\n\n" if chromadb_status else ""
    return f"{status}Hello {name}! 🎲"

# Create simple interface
demo = gr.Interface(
    fn=greet,
    inputs=gr.Textbox(label="Your name"),
    outputs=gr.Textbox(label="Greeting"),
    title="D&D RAG System - Minimal Test",
    description="Testing HuggingFace Spaces deployment"
)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860
    )
