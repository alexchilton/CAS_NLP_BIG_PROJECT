#!/usr/bin/env python3
"""
Minimal Gradio app for testing HuggingFace Spaces deployment
"""

import gradio as gr

def greet(name):
    return f"Hello {name}! 🎲"

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
