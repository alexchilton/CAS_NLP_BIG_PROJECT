"""
RAG Retrieval and Formatting

Handles searching ChromaDB for D&D rules and formatting results for LLM prompts.
"""

from typing import Dict, Any
from dnd_rag_system.core.chroma_manager import ChromaDBManager
from dnd_rag_system.config import settings


class RAGRetriever:
    """
    Retrieves and formats D&D rules from RAG database.

    Responsibilities:
    - Search ChromaDB collections for relevant rules
    - Filter results by relevance
    - Format results for LLM context

    Extracted from GameMaster class to follow Single Responsibility Principle.
    """

    def __init__(self, db_manager: ChromaDBManager):
        """
        Initialize RAG retriever.

        Args:
            db_manager: ChromaDB manager instance
        """
        self.db = db_manager

    def search_rag(self, query: str, n_results: int = 3) -> Dict[str, Any]:
        """
        Search RAG database for relevant D&D content.

        Args:
            query: Search query
            n_results: Number of results per collection

        Returns:
            Dictionary with results from all collections
        """
        results = {}

        # Search each collection
        for collection_type, collection_name in settings.COLLECTION_NAMES.items():
            try:
                search_results = self.db.search(
                    collection_name,
                    query,
                    n_results=n_results
                )

                if search_results['documents'] and search_results['documents'][0]:
                    results[collection_type] = {
                        'documents': search_results['documents'][0],
                        'metadatas': search_results['metadatas'][0],
                        'distances': search_results['distances'][0]
                    }
            except Exception as e:
                print(f"Warning: Could not search {collection_type}: {e}")
                continue

        return results

    def format_rag_context(self, rag_results: Dict[str, Any]) -> str:
        """
        Format RAG search results into context for LLM prompt.

        Args:
            rag_results: Results from search_rag()

        Returns:
            Formatted context string
        """
        if not rag_results:
            return "No specific rules retrieved."

        context_parts = []

        for collection_type, results in rag_results.items():
            docs = results['documents']
            metas = results['metadatas']
            distances = results['distances']

            for doc, meta, dist in zip(docs, metas, distances):
                # Only include very relevant results (distance < 1.0)
                if dist < 1.0:
                    name = meta.get('name', 'Unknown')
                    context_parts.append(f"[{collection_type.upper()}] {name}:\n{doc[:400]}")

        return "\n\n".join(context_parts) if context_parts else "No highly relevant rules found."
