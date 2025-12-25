#!/usr/bin/env python3
"""
D&D RAG Game Master - Hugging Face Spaces Entry Point

This file is the entry point for Hugging Face Spaces deployment.
It imports and launches the main Gradio app from web/app_gradio.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the main Gradio app
from web.app_gradio import demo

if __name__ == "__main__":
    # Launch the app
    # HF Spaces automatically detects the demo object and runs it
    demo.launch()
