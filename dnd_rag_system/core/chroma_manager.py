"""
ChromaDB Manager

Unified interface for managing ChromaDB collections and operations.
Auto-ingests SRD data on first use.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import uuid
import json

# Import project settings and chunker
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings
from core.base_chunker import Chunk


class ChromaDBManager:
    """
    Manages all ChromaDB operations for the D&D RAG system.

    Provides a unified interface for:
    - Collection management
    - Adding/updating chunks
    - Querying across single or multiple collections
    - Statistics and reporting
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        """
        Initialize ChromaDB manager.

        Args:
            persist_dir: Directory for persistent storage (default from settings)
            embedding_model: Embedding model name (default from settings)
        """
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL_NAME

        # Ensure persist directory exists
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(allow_reset=settings.CHROMA_ALLOW_RESET)
        )

        # Cache for collections
        self._collections = {}
        
        # Auto-ingest SRD data if not present
        self._ensure_srd_data()

        print(f"ChromaDB Manager initialized:")
        print(f"  Persist dir: {self.persist_dir}")
        print(f"  Embedding model: {self.embedding_model}")
    
    def _ensure_srd_data(self):
        """Ensure SRD data is ingested (runs once on first use)."""
        try:
            # Check if SRD collection exists and has data
            try:
                srd_collection = self.client.get_collection("dnd5e_srd")
                if srd_collection.count() > 0:
                    return  # Already ingested
            except:
                pass  # Collection doesn't exist yet
            
            # Need to ingest SRD data
            print("📚 First-time SRD setup: Parsing and ingesting D&D 5e data...")
            
            from pathlib import Path
            srd_pdf = Path(__file__).parent.parent / "data" / "reference" / "SRD-OGL_V5.1.pdf"
            
            if not srd_pdf.exists():
                print(f"⚠️  SRD PDF not found at {srd_pdf}, skipping SRD ingestion")
                return
            
            # Run parser and ingestion
            import subprocess
            scripts_dir = Path(__file__).parent.parent.parent / "scripts"
            
            # Parse PDF
            parse_script = scripts_dir / "parse_srd_pdf.py"
            if parse_script.exists():
                print("  ⏳ Parsing SRD PDF...")
                subprocess.run([sys.executable, str(parse_script)], 
                             capture_output=True, check=True)
            
            # Ingest to ChromaDB
            ingest_script = scripts_dir / "ingest_srd_to_chromadb.py"
            if ingest_script.exists():
                print("  ⏳ Ingesting to ChromaDB...")
                subprocess.run([sys.executable, str(ingest_script)], 
                             capture_output=True, check=True)
                print("  ✅ SRD data ready!")
            
        except Exception as e:
            print(f"⚠️  Could not auto-ingest SRD data: {e}")
            print("   Character creation will use basic fallback features")

    def get_or_create_collection(
        self,
        collection_name: str,
        metadata: Optional[Dict[str, str]] = None
    ):
        """
        Get existing collection or create new one.

        Args:
            collection_name: Name of the collection
            metadata: Optional metadata for the collection

        Returns:
            ChromaDB collection object
        """
        # Check cache first
        if collection_name in self._collections:
            return self._collections[collection_name]

        # Get or create from ChromaDB
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata=metadata or settings.COLLECTION_METADATA.get(collection_name, {})
            )
            self._collections[collection_name] = collection
            print(f"✓ Collection '{collection_name}' ready ({collection.count()} documents)")
            return collection
        except Exception as e:
            raise Exception(f"Failed to get/create collection '{collection_name}': {e}")

    def add_chunks(
        self,
        collection_name: str,
        chunks: List[Chunk],
        batch_size: Optional[int] = None
    ) -> int:
        """
        Add chunks to a collection.

        Args:
            collection_name: Name of collection to add to
            chunks: List of Chunk objects
            batch_size: Batch size for adding (default from settings)

        Returns:
            Number of chunks added

        Raises:
            ValueError: If chunks is empty or invalid
        """
        if not chunks:
            raise ValueError("Cannot add empty chunks list")

        batch_size = batch_size or settings.CHROMA_BATCH_SIZE
        collection = self.get_or_create_collection(collection_name)

        # Prepare data
        documents = []
        metadatas = []
        ids = []

        for chunk in chunks:
            # Get retrieval text
            documents.append(chunk.get_retrieval_text())

            # Convert metadata to ChromaDB-compatible format
            metadata = self._prepare_metadata(chunk.metadata)
            metadata['chunk_type'] = chunk.chunk_type
            metadata['token_estimate'] = chunk.token_estimate
            metadata['tags'] = ','.join(sorted(chunk.tags)) if chunk.tags else ''

            metadatas.append(metadata)

            # Generate unique ID
            ids.append(self._generate_chunk_id(collection_name, chunk))

        # Add in batches
        total_added = 0
        for i in range(0, len(documents), batch_size):
            batch_end = min(i + batch_size, len(documents))

            try:
                collection.add(
                    documents=documents[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                    ids=ids[i:batch_end]
                )
                total_added += (batch_end - i)
            except Exception as e:
                print(f"Warning: Failed to add batch {i//batch_size + 1}: {e}")
                continue

        print(f"✓ Added {total_added} chunks to '{collection_name}'")
        return total_added

    def search(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = None,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict:
        """
        Search a single collection.

        Args:
            collection_name: Name of collection to search
            query_text: Query text
            n_results: Number of results to return (default from settings)
            where: Metadata filters
            where_document: Document content filters

        Returns:
            Search results dictionary
        """
        n_results = n_results or settings.DEFAULT_RAG_RESULTS
        collection = self.get_or_create_collection(collection_name)

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            return results
        except Exception as e:
            print(f"Search error in '{collection_name}': {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

    def search_all(
        self,
        query_text: str,
        n_results_per_collection: int = 3,
        collections: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Search across multiple collections.

        Args:
            query_text: Query text
            n_results_per_collection: Results per collection
            collections: List of collection names (None = all)

        Returns:
            Dictionary mapping collection names to results
        """
        if collections is None:
            collections = list(settings.COLLECTION_NAMES.values())

        all_results = {}

        for collection_name in collections:
            try:
                results = self.search(
                    collection_name,
                    query_text,
                    n_results=n_results_per_collection
                )
                all_results[collection_name] = results
            except Exception as e:
                print(f"Warning: Could not search '{collection_name}': {e}")
                continue

        return all_results

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.

        Args:
            collection_name: Name of collection to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(name=collection_name)
            if collection_name in self._collections:
                del self._collections[collection_name]
            print(f"✓ Deleted collection '{collection_name}'")
            return True
        except Exception as e:
            print(f"Failed to delete collection '{collection_name}': {e}")
            return False

    def clear_collection(self, collection_name: str) -> bool:
        """
        Clear all documents from a collection.

        Args:
            collection_name: Name of collection to clear

        Returns:
            True if successful
        """
        try:
            self.delete_collection(collection_name)
            self.get_or_create_collection(collection_name)
            print(f"✓ Cleared collection '{collection_name}'")
            return True
        except Exception as e:
            print(f"Failed to clear collection '{collection_name}': {e}")
            return False

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.

        Args:
            collection_name: Name of collection

        Returns:
            Dictionary with statistics
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            total_docs = collection.count()

            if total_docs == 0:
                return {
                    'collection_name': collection_name,
                    'total_documents': 0,
                    'chunk_types': {},
                    'sample_items': []
                }

            # Sample some documents for analysis
            sample_size = min(100, total_docs)
            sample = collection.get(limit=sample_size)

            # Analyze chunk types
            chunk_types = {}
            items = set()

            if sample['metadatas']:
                for metadata in sample['metadatas']:
                    chunk_type = metadata.get('chunk_type', 'unknown')
                    chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

                    # Collect item names
                    if 'name' in metadata:
                        items.add(metadata['name'])

            return {
                'collection_name': collection_name,
                'total_documents': total_docs,
                'chunk_types': chunk_types,
                'unique_items': len(items),
                'sample_items': sorted(list(items))[:10]
            }

        except Exception as e:
            print(f"Error getting stats for '{collection_name}': {e}")
            return {'collection_name': collection_name, 'error': str(e)}

    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all collections.

        Returns:
            Dictionary with overall statistics
        """
        stats = {
            'persist_dir': self.persist_dir,
            'embedding_model': self.embedding_model,
            'collections': {}
        }

        for collection_name in settings.COLLECTION_NAMES.values():
            stats['collections'][collection_name] = self.get_collection_stats(collection_name)

        # Calculate totals
        stats['total_documents'] = sum(
            col_stats.get('total_documents', 0)
            for col_stats in stats['collections'].values()
        )

        return stats

    def export_collection_metadata(self, collection_name: str, output_file: Path) -> bool:
        """
        Export collection metadata to JSON file.

        Args:
            collection_name: Name of collection
            output_file: Path to output JSON file

        Returns:
            True if successful
        """
        try:
            stats = self.get_collection_stats(collection_name)
            collection = self.get_or_create_collection(collection_name)

            # Get all metadata
            all_data = collection.get()

            export_data = {
                'collection_name': collection_name,
                'statistics': stats,
                'metadata': all_data['metadatas'] if all_data['metadatas'] else []
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            print(f"✓ Exported collection metadata to {output_file}")
            return True

        except Exception as e:
            print(f"Failed to export collection metadata: {e}")
            return False

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Union[str, int, float, bool]]:
        """
        Prepare metadata for ChromaDB (only allows simple types).

        Args:
            metadata: Original metadata

        Returns:
            ChromaDB-compatible metadata
        """
        prepared = {}

        for key, value in metadata.items():
            if value is None:
                prepared[key] = "unknown"
            elif isinstance(value, (list, tuple)):
                # Convert lists to comma-separated strings
                prepared[key] = ','.join(str(v) for v in value) if value else ""
            elif isinstance(value, dict):
                # Convert dicts to JSON strings
                prepared[key] = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)):
                prepared[key] = value
            else:
                # Convert everything else to string
                prepared[key] = str(value)

        return prepared

    def _generate_chunk_id(self, collection_name: str, chunk: Chunk) -> str:
        """
        Generate unique ID for a chunk.

        Args:
            collection_name: Name of collection
            chunk: Chunk object

        Returns:
            Unique ID string
        """
        # Use name from metadata if available, otherwise use UUID
        base_name = chunk.metadata.get('name', 'chunk')
        base_name = base_name.lower().replace(' ', '_').replace("'", "")

        chunk_type = chunk.chunk_type.replace(' ', '_')

        # Add a short random suffix for uniqueness
        suffix = uuid.uuid4().hex[:8]

        return f"{collection_name}_{base_name}_{chunk_type}_{suffix}"
