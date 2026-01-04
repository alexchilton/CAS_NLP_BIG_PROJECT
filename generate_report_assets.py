import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def generate_assets():
    print("🎨 Generating Report Assets...")
    ensure_dir("report_assets")
    
    db = ChromaDBManager()
    
    # --- MONSTERS ---
    print("Fetching Monster Data...")
    monsters_coll = db.get_or_create_collection(settings.COLLECTION_NAMES['monsters'])
    m_data = monsters_coll.get()
    
    if m_data['metadatas']:
        df_monsters = pd.DataFrame(m_data['metadatas'])
        
        # CR Distribution
        if 'challenge_rating' in df_monsters.columns:
            # Clean CRs (handle fractions like '1/4')
            def parse_cr(x):
                x = str(x).split('(')[0].strip()
                if '/' in x:
                    n, d = x.split('/')
                    return float(n)/float(d)
                try:
                    return float(x)
                except:
                    return -1

            df_monsters['cr_value'] = df_monsters['challenge_rating'].apply(parse_cr)
            df_monsters = df_monsters[df_monsters['cr_value'] >= 0] # Filter unknown
            
            plt.figure(figsize=(10, 6))
            df_monsters['cr_value'].hist(bins=30, color='skyblue', edgecolor='black')
            plt.title('Distribution of Monster Challenge Ratings (CR)')
            plt.xlabel('Challenge Rating')
            plt.ylabel('Count')
            plt.grid(axis='y', alpha=0.75)
            plt.savefig('report_assets/monster_cr_dist.png')
            plt.close()
            print("✓ Saved monster_cr_dist.png")

        # Type Distribution
        if 'monster_type' in df_monsters.columns:
            # Extract main type (e.g., "Large beast" -> "beast")
            def get_main_type(x):
                if not x: return "Unknown"
                parts = str(x).split()
                # Common types in 5e
                types = ['aberration', 'beast', 'celestial', 'construct', 'dragon', 
                         'elemental', 'fey', 'fiend', 'giant', 'humanoid', 
                         'monstrosity', 'ooze', 'plant', 'undead']
                for t in parts:
                    clean_t = t.lower().strip(',').strip()
                    if clean_t in types:
                        return clean_t.capitalize()
                return "Other"

            df_monsters['main_type'] = df_monsters['monster_type'].apply(get_main_type)
            
            plt.figure(figsize=(12, 6))
            type_counts = df_monsters['main_type'].value_counts()
            type_counts.plot(kind='bar', color='salmon', edgecolor='black')
            plt.title('Distribution of Monster Types')
            plt.xlabel('Type')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('report_assets/monster_type_dist.png')
            plt.close()
            print("✓ Saved monster_type_dist.png")

    # --- SPELLS ---
    print("Fetching Spell Data...")
    spells_coll = db.get_or_create_collection(settings.COLLECTION_NAMES['spells'])
    s_data = spells_coll.get()
    
    if s_data['metadatas']:
        df_spells = pd.DataFrame(s_data['metadatas'])
        
        # Filter for spell objects (not class lists etc if any)
        # Using level presence as proxy
        if 'level' in df_spells.columns:
            plt.figure(figsize=(10, 6))
            
            # Map integer levels to display names
            def format_level(val):
                try:
                    ival = int(val)
                    if ival == 0: return "Cantrip"
                    return str(ival)
                except:
                    return str(val)

            df_spells['level_display'] = df_spells['level'].apply(format_level)
            
            # Count values
            level_counts = df_spells['level_display'].value_counts()
            
            # Define sort order
            level_order = ['Cantrip'] + [str(i) for i in range(1, 10)]
            
            # Reindex to ensure correct order (filling missing with 0)
            level_counts = level_counts.reindex(level_order).fillna(0)
            
            level_counts.plot(kind='bar', color='mediumpurple', edgecolor='black')
            plt.title('Distribution of Spells by Level')
            plt.xlabel('Spell Level')
            plt.ylabel('Count')
            plt.xticks(rotation=0)
            plt.savefig('report_assets/spell_level_dist.png')
            plt.close()
            print("✓ Saved spell_level_dist.png")

        if 'school' in df_spells.columns:
            plt.figure(figsize=(10, 6))
            df_spells['school'].value_counts().plot(kind='bar', color='lightgreen', edgecolor='black')
            plt.title('Distribution of Spells by School')
            plt.xlabel('School of Magic')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig('report_assets/spell_school_dist.png')
            plt.close()
            print("✓ Saved spell_school_dist.png")

    # --- SUMMARY STATS ---
    stats = {
        "total_monsters": len(m_data['ids']) if m_data else 0,
        "total_spells": len(s_data['ids']) if s_data else 0,
        "monster_cr_mean": float(df_monsters['cr_value'].mean()) if 'cr_value' in locals() else 0,
        "monster_cr_max": float(df_monsters['cr_value'].max()) if 'cr_value' in locals() else 0,
    }
    
    with open('report_assets/db_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    print("✓ Saved db_stats.json")

if __name__ == "__main__":
    generate_assets()
