#!/usr/bin/env python3
"""
Minimal Gradio app for testing HuggingFace Spaces deployment
Step 3: Testing all production dependencies
"""

import gradio as gr

# Test all imports
status_lines = []

try:
    import chromadb
    status_lines.append(f"✅ ChromaDB {chromadb.__version__}")
except Exception as e:
    status_lines.append(f"❌ ChromaDB: {e}")

try:
    import sentence_transformers
    status_lines.append(f"✅ sentence-transformers {sentence_transformers.__version__}")
except Exception as e:
    status_lines.append(f"❌ sentence-transformers: {e}")

try:
    import pdfplumber
    status_lines.append(f"✅ pdfplumber {pdfplumber.__version__}")
except Exception as e:
    status_lines.append(f"❌ pdfplumber: {e}")

try:
    import PyPDF2
    status_lines.append(f"✅ PyPDF2 {PyPDF2.__version__}")
except Exception as e:
    status_lines.append(f"❌ PyPDF2: {e}")

try:
    import ollama
    status_lines.append(f"✅ ollama")
except Exception as e:
    status_lines.append(f"❌ ollama: {e}")

try:
    import rich
    version = getattr(rich, '__version__', 'installed')
    status_lines.append(f"✅ rich {version}")
except Exception as e:
    status_lines.append(f"❌ rich: {e}")

status_text = "\n".join(status_lines)

def greet(name):
    return f"{status_text}\n\nHello {name}! 🎲"

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
