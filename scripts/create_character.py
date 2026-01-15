#!/usr/bin/env python3
"""
D&D Character Creator - Simple Launcher

Quick start: python scripts/create_character.py
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dnd_rag_system.systems.character_creator import main

if __name__ == '__main__':
    main()
