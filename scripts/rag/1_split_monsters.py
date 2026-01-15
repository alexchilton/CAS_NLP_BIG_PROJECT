import os
import re

# --- CONFIGURATION ---
SOURCE_FILE = 'dnd_rag_system/data/extracted/extracted_monsters.txt'
OUTPUT_DIR = 'data/monsters_raw'

# --- HELPER FUNCTIONS ---

def sanitize_filename(name: str) -> str:
    """Converts a monster name to a safe filename."""
    name = name.lower().strip()
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'\(.*\)', '', name)
    name = re.sub(r'[^a-z0-9_]', '', name)
    return f"{name.strip('_')}.txt"

def looks_like_monster_header(line: str) -> bool:
    """
    Checks if a line looks like a monster name header. (V2 Logic)
    """
    line = line.strip()
    if not line.isupper():
        return False
    if any(word in line for word in ['CONTENTS', 'CHAPTER', 'INDEX', 'CREDITS', 'APPENDIX', 'FOREWORD']):
        return False
    if len(line.replace(' ', '')) < 1: # Allow single-letter headers for now
        return False
    return True

# --- CORE LOGIC ---

def split_monsters_v2():
    """
    Reads the source text file, splits it into monster blocks based on headers,
    and saves each block to a file. This version is intentionally inclusive.
    """
    print(f"Starting monster splitting process (V2 - Inclusive)...")
    if not os.path.exists(SOURCE_FILE):
        print(f"Error: Source file '{SOURCE_FILE}' not found.")
        return

    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"Read {len(lines)} lines from source file.")

    monster_blocks = []
    current_block_lines = []
    current_monster_name = None

    start_index = 0
    for i, line in enumerate(lines):
        if line.strip() == 'ABOLETH':
            start_index = i
            print(f"Found starting monster 'ABOLETH' at line {i}.")
            break
    
    for line in lines[start_index:]:
        if looks_like_monster_header(line):
            if current_block_lines and current_monster_name:
                if len(current_block_lines) > 2: # A monster needs more than a couple of lines
                     monster_blocks.append({
                        "name": current_monster_name,
                        "content": ''.join(current_block_lines)
                    })
            
            current_monster_name = line.strip()
            current_block_lines = [line]
        else:
            if current_monster_name:
                current_block_lines.append(line)

    if current_block_lines and current_monster_name:
        monster_blocks.append({
            "name": current_monster_name,
            "content": ''.join(current_block_lines)
        })

    print(f"Found {len(monster_blocks)} potential monster blocks.")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Clearing old files from {OUTPUT_DIR}...")
    for item in os.listdir(OUTPUT_DIR):
        os.remove(os.path.join(OUTPUT_DIR, item))

    for block in monster_blocks:
        filename = sanitize_filename(block['name'])
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(block['content'])
    
    print(f"Successfully wrote {len(monster_blocks)} monster files to '{OUTPUT_DIR}'.")

if __name__ == "__main__":
    split_monsters_v2()