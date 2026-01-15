#!/usr/bin/env python3
"""
Game Content Ingestion Script

Loads magic items and class features into ChromaDB for RAG.

Usage:
    python ingest_game_content.py [--clear]
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import core infrastructure
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.core.base_chunker import Chunk
from dnd_rag_system.config import settings

# Import data sources
from dnd_rag_system.data.magic_items import MAGIC_ITEMS, get_all_item_names
from dnd_rag_system.data.class_features import CLASS_FEATURES, get_available_classes


# =============================================================================
# MAGIC ITEMS LOADER
# =============================================================================

def load_magic_items(db_manager: ChromaDBManager, clear: bool = False):
    """
    Load magic items into ChromaDB.

    Args:
        db_manager: ChromaDB manager instance
        clear: Whether to clear existing collection
    """
    print("\n" + "="*70)
    print("✨ LOADING MAGIC ITEMS")
    print("="*70)

    collection_name = 'magic_items'

    if clear:
        print(f"🗑️  Clearing existing '{collection_name}' collection...")
        db_manager.clear_collection(collection_name)

    print(f"📦 Processing {len(MAGIC_ITEMS)} magic items...")

    chunks = []

    for item_name, item_data in MAGIC_ITEMS.items():
        # Create comprehensive chunk for each item
        chunk_content = _create_magic_item_chunk(item_name, item_data)

        # Create metadata
        metadata = {
            'name': item_name,
            'rarity': item_data.get('rarity', 'unknown'),
            'type': item_data.get('type', 'unknown'),
            'attunement': item_data.get('attunement', False),
            'content_type': 'magic_item'
        }

        # Create tags
        tags = {'magic_item', f"rarity_{item_data.get('rarity', 'unknown')}"}
        tags.add(f"type_{item_data.get('type', 'unknown')}")

        if item_data.get('attunement', False):
            tags.add('requires_attunement')

        # Create chunk
        chunk = Chunk(
            content=chunk_content,
            chunk_type='magic_item',
            metadata=metadata,
            tags=tags
        )

        chunks.append(chunk)

    print(f"✓ Created {len(chunks)} magic item chunks")

    # Add to ChromaDB
    if chunks:
        print(f"💾 Adding chunks to ChromaDB...")
        db_manager.add_chunks(collection_name, chunks)
        print(f"✅ Successfully loaded {len(chunks)} magic items into '{collection_name}' collection")
    else:
        print("❌ No chunks created")

    return len(chunks)


def _create_magic_item_chunk(item_name: str, item_data: Dict[str, Any]) -> str:
    """
    Create a comprehensive text chunk for a magic item.

    Args:
        item_name: Name of the magic item
        item_data: Item data dictionary

    Returns:
        Formatted text chunk
    """
    lines = []

    # Header with item name (weighted for better retrieval)
    lines.append(f"MAGIC ITEM: {item_name}")
    lines.append(f"{item_name}")
    lines.append("")

    # Basic info
    lines.append(f"**{item_name}**")
    lines.append(f"*{item_data.get('type', 'unknown').title()}, {item_data.get('rarity', 'unknown')}*")

    if item_data.get('attunement', False):
        lines.append("*(requires attunement)*")

    lines.append("")

    # Description
    if 'description' in item_data:
        lines.append(item_data['description'])
        lines.append("")

    # Effects
    if 'effects' in item_data:
        lines.append("**Effects:**")
        effects = item_data['effects']

        for effect_name, effect_value in effects.items():
            effect_str = effect_name.replace('_', ' ').title()
            lines.append(f"- {effect_str}: {effect_value}")

        lines.append("")

    # Notes
    if 'notes' in item_data:
        lines.append(f"**Note:** {item_data['notes']}")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# CLASS FEATURES LOADER
# =============================================================================

def load_class_features(db_manager: ChromaDBManager, clear: bool = False):
    """
    Load class features into ChromaDB.

    Args:
        db_manager: ChromaDB manager instance
        clear: Whether to clear existing collection
    """
    print("\n" + "="*70)
    print("⚔️  LOADING CLASS FEATURES")
    print("="*70)

    collection_name = 'class_features'

    if clear:
        print(f"🗑️  Clearing existing '{collection_name}' collection...")
        db_manager.clear_collection(collection_name)

    print(f"📖 Processing {len(CLASS_FEATURES)} classes...")

    chunks = []

    for class_name, class_data in CLASS_FEATURES.items():
        # Create overview chunk for each class
        overview_chunk = _create_class_overview_chunk(class_name, class_data)
        chunks.append(overview_chunk)

        # Create chunks for each feature
        features_by_level = class_data.get('features_by_level', {})

        for level, features in features_by_level.items():
            for feature in features:
                feature_chunk = _create_class_feature_chunk(class_name, level, feature)
                chunks.append(feature_chunk)

    print(f"✓ Created {len(chunks)} class feature chunks")

    # Add to ChromaDB
    if chunks:
        print(f"💾 Adding chunks to ChromaDB...")
        db_manager.add_chunks(collection_name, chunks)
        print(f"✅ Successfully loaded {len(chunks)} class features into '{collection_name}' collection")
    else:
        print("❌ No chunks created")

    return len(chunks)


def _create_class_overview_chunk(class_name: str, class_data: Dict[str, Any]) -> Chunk:
    """
    Create an overview chunk for a class.

    Args:
        class_name: Name of the class
        class_data: Class data dictionary

    Returns:
        Chunk object
    """
    lines = []

    # Header
    lines.append(f"CLASS: {class_name}")
    lines.append(f"{class_name}")
    lines.append("")

    lines.append(f"**{class_name}** - D&D 5e Class")
    lines.append("")

    # Basic info
    lines.append(f"**Hit Dice:** {class_data.get('hit_dice', 'd8')}")
    lines.append(f"**Primary Ability:** {class_data.get('primary_ability', 'unknown')}")

    saves = class_data.get('saving_throw_proficiencies', [])
    lines.append(f"**Saving Throw Proficiencies:** {', '.join([s.title() for s in saves])}")

    if 'spellcasting_ability' in class_data:
        lines.append(f"**Spellcasting Ability:** {class_data['spellcasting_ability'].title()}")

    lines.append("")

    # List key features
    lines.append("**Key Features:**")
    features_by_level = class_data.get('features_by_level', {})

    for level in sorted(features_by_level.keys())[:5]:  # First 5 levels
        features = features_by_level[level]
        feature_names = [f['name'] for f in features]
        lines.append(f"- Level {level}: {', '.join(feature_names)}")

    content = "\n".join(lines)

    # Metadata
    metadata = {
        'class_name': class_name,
        'hit_dice': class_data.get('hit_dice', 'd8'),
        'primary_ability': class_data.get('primary_ability', 'unknown'),
        'content_type': 'class_overview'
    }

    # Tags
    tags = {'class', f'class_{class_name.lower()}', 'overview'}

    return Chunk(
        content=content,
        chunk_type='class_overview',
        metadata=metadata,
        tags=tags
    )


def _create_class_feature_chunk(class_name: str, level: int, feature: Dict[str, Any]) -> Chunk:
    """
    Create a chunk for a specific class feature.

    Args:
        class_name: Name of the class
        level: Level at which feature is gained
        feature: Feature data dictionary

    Returns:
        Chunk object
    """
    lines = []

    feature_name = feature.get('name', 'Unknown Feature')

    # Header
    lines.append(f"CLASS FEATURE: {feature_name}")
    lines.append(f"{class_name} - {feature_name}")
    lines.append("")

    lines.append(f"**{feature_name}**")
    lines.append(f"*{class_name} Level {level} Feature*")
    lines.append("")

    # Description
    if 'description' in feature:
        lines.append(feature['description'])
        lines.append("")

    # Usage information
    if 'usage' in feature:
        lines.append(f"**Usage:** {feature['usage']}")

    if 'uses' in feature:
        lines.append(f"**Uses:** {feature['uses']}")

    if 'recharge' in feature:
        lines.append(f"**Recharge:** {feature['recharge']}")

    if 'frequency' in feature:
        lines.append(f"**Frequency:** {feature['frequency']}")

    # Mechanics
    if 'damage_by_level' in feature:
        lines.append("")
        lines.append("**Damage by Level:**")
        damage_by_level = feature['damage_by_level']
        for lvl in sorted(damage_by_level.keys())[:6]:  # First 6 entries
            lines.append(f"- Level {lvl}: {damage_by_level[lvl]}")

    if 'uses_by_level' in feature:
        lines.append("")
        lines.append("**Uses by Level:**")
        uses_by_level = feature['uses_by_level']
        for lvl in sorted(uses_by_level.keys()):
            lines.append(f"- Level {lvl}: {uses_by_level[lvl]}")

    if 'options' in feature:
        lines.append("")
        lines.append(f"**Options:** {', '.join(feature['options'])}")

    # Special cases
    if 'trigger' in feature:
        lines.append(f"**Trigger:** {feature['trigger']}")

    if 'effect' in feature:
        lines.append(f"**Effect:** {feature['effect']}")

    content = "\n".join(lines)

    # Metadata
    metadata = {
        'class_name': class_name,
        'feature_name': feature_name,
        'level': level,
        'content_type': 'class_feature'
    }

    # Tags
    tags = {'class_feature', f'class_{class_name.lower()}', f'level_{level}'}

    return Chunk(
        content=content,
        chunk_type='class_feature',
        metadata=metadata,
        tags=tags
    )


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Main ingestion function."""
    parser = argparse.ArgumentParser(description='Ingest Magic Items and Class Features into ChromaDB')
    parser.add_argument('--clear', action='store_true', help='Clear existing collections')
    parser.add_argument('--only', type=str, help='Load only specific content (magic_items, class_features)')
    args = parser.parse_args()

    print("\n" + "="*70)
    print("🎲 D&D GAME CONTENT INGESTION")
    print("="*70)

    # Initialize ChromaDB
    print("\n🔧 Initializing ChromaDB...")
    db_manager = ChromaDBManager()

    # Determine what to load
    load_all = args.only is None
    to_load = args.only.split(',') if args.only else ['magic_items', 'class_features']

    # Load each content type
    results = {}

    if load_all or 'magic_items' in to_load:
        results['magic_items'] = load_magic_items(db_manager, args.clear)

    if load_all or 'class_features' in to_load:
        results['class_features'] = load_class_features(db_manager, args.clear)

    # Summary
    print("\n" + "="*70)
    print("📊 INGESTION SUMMARY")
    print("="*70)

    total_chunks = sum(results.values())
    for content_type, count in results.items():
        print(f"  {content_type.replace('_', ' ').title()}: {count} chunks")

    print(f"\n✅ Total: {total_chunks} chunks loaded into ChromaDB")

    # Show collection stats
    print("\n📈 Collection Statistics:")
    stats = db_manager.get_all_stats()
    for collection_name in ['magic_items', 'class_features']:
        if collection_name in stats['collections']:
            col_stats = stats['collections'][collection_name]
            print(f"  {collection_name}: {col_stats.get('total_documents', 0)} documents")

    print("\n🎉 Ingestion complete!")
    print(f"   Database: {db_manager.persist_dir}")

    print("\n💡 Next steps:")
    print("   - Test searches: python query_rag.py")
    print("   - Query example: 'Ring of Protection'")
    print("   - Query example: 'Rogue Sneak Attack'")


if __name__ == '__main__':
    main()
