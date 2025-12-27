#!/usr/bin/env python3
"""
D&D Game Master Dialogue - Simple Launcher

Start an interactive D&D session with RAG-enhanced AI GM.

Usage: python run_gm_dialogue.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.systems.gm_dialogue import main

if __name__ == '__main__':
    sys.exit(main())
