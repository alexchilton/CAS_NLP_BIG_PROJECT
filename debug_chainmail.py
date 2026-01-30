
import pdfplumber
import re
from pathlib import Path

# Path to PHB
phb_path = Path("dnd_rag_system/data/reference/players_handbook.pdf")

if not phb_path.exists():
    print("PHB not found.")
    exit()

def debug_chainmail():
    print("Searching for 'Chain Mail' in PHB pages 143-150...")
    with pdfplumber.open(phb_path) as pdf:
        for i in range(143, 150):
            if i >= len(pdf.pages): break
            page = pdf.pages[i]
            text = page.extract_text()
            
            if not text: continue
            
            # Normalize for search
            if "chain mail" in text.lower() or "chainmail" in text.lower():
                print(f"\n[Page {i+1} Match]")
                # Print context around match
                lines = text.split('\n')
                for j, line in enumerate(lines):
                    if "chain" in line.lower() and "mail" in line.lower():
                        print(f"  Line {j}: {line}")
                        # Print surrounding lines
                        if j > 0: print(f"    Prev: {lines[j-1]}")
                        if j < len(lines)-1: print(f"    Next: {lines[j+1]}")

debug_chainmail()
