#!/usr/bin/env python3
"""
D&D Character Creator - Simple Launcher

Quick start: python create_character.py
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dnd_rag_system.systems.character_creator import main

if __name__ == '__main__':
    main()
