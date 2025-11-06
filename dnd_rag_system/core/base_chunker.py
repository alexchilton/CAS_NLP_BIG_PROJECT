"""
Base Chunker Classes

Abstract base classes and utilities for chunking D&D content for RAG retrieval.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, field
import re

# Import settings
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings


@dataclass
class Chunk:
    """
    Represents a single chunk of content for RAG retrieval.
    """
    content: str
    chunk_type: str  # e.g., 'stats', 'description', 'mechanics', 'lore'
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    token_estimate: int = 0

    def __post_init__(self):
        """Calculate token estimate if not provided."""
        if self.token_estimate == 0:
            self.token_estimate = estimate_tokens(self.content)

    def get_retrieval_text(self) -> str:
        """
        Get formatted text for embedding and retrieval.

        Returns:
            Formatted text combining metadata and content
        """
        # Include key metadata in retrieval text for better semantic search
        prefix_parts = []

        if 'name' in self.metadata:
            prefix_parts.append(f"**{self.metadata['name']}**")

        if 'type' in self.metadata:
            prefix_parts.append(f"({self.metadata['type']})")

        prefix = " ".join(prefix_parts)

        if prefix:
            return f"{prefix}\n{self.content}"
        return self.content

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for storage."""
        return {
            'content': self.content,
            'chunk_type': self.chunk_type,
            'metadata': self.metadata,
            'tags': list(self.tags),
            'token_estimate': self.token_estimate
        }


class BaseChunker(ABC):
    """
    Abstract base class for all content chunkers.

    Chunkers take parsed content and split it into optimized chunks
    for RAG retrieval.
    """

    def __init__(
        self,
        max_tokens: int = None,
        overlap_tokens: int = None,
        min_tokens: int = None
    ):
        """
        Initialize chunker.

        Args:
            max_tokens: Maximum tokens per chunk (default from settings)
            overlap_tokens: Overlap between chunks (default from settings)
            min_tokens: Minimum tokens per chunk (default from settings)
        """
        self.max_tokens = max_tokens or settings.MAX_CHUNK_TOKENS
        self.overlap_tokens = overlap_tokens or settings.CHUNK_OVERLAP_TOKENS
        self.min_tokens = min_tokens or settings.MIN_CHUNK_TOKENS

    @abstractmethod
    def create_chunks(self, parsed_content: Any) -> List[Chunk]:
        """
        Create chunks from parsed content.

        Args:
            parsed_content: Parsed content object (type depends on parser)

        Returns:
            List of Chunk objects
        """
        pass

    def split_long_text(
        self,
        text: str,
        chunk_type: str = "content",
        base_metadata: Dict[str, Any] = None
    ) -> List[Chunk]:
        """
        Split long text into multiple chunks with overlap.

        Args:
            text: Text to split
            chunk_type: Type of chunk
            base_metadata: Metadata to include in all chunks

        Returns:
            List of Chunk objects
        """
        if base_metadata is None:
            base_metadata = {}

        # Check if splitting is needed
        token_count = estimate_tokens(text)
        if token_count <= self.max_tokens:
            return [Chunk(
                content=text,
                chunk_type=chunk_type,
                metadata=base_metadata.copy(),
                token_estimate=token_count
            )]

        # Split by sentences
        sentences = split_into_sentences(text)
        chunks = []
        current_chunk = ""
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = estimate_tokens(sentence)

            # Check if adding this sentence would exceed max tokens
            if current_tokens + sentence_tokens > self.max_tokens and current_chunk:
                # Save current chunk
                chunks.append(Chunk(
                    content=current_chunk.strip(),
                    chunk_type=chunk_type,
                    metadata={**base_metadata, 'chunk_index': len(chunks)},
                    token_estimate=current_tokens
                ))

                # Start new chunk with overlap
                overlap_text = get_overlap_text(current_chunk, self.overlap_tokens)
                current_chunk = overlap_text + " " + sentence
                current_tokens = estimate_tokens(current_chunk)
            else:
                # Add sentence to current chunk
                current_chunk += (" " if current_chunk else "") + sentence
                current_tokens += sentence_tokens

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(Chunk(
                content=current_chunk.strip(),
                chunk_type=chunk_type,
                metadata={**base_metadata, 'chunk_index': len(chunks)},
                token_estimate=current_tokens
            ))

        return chunks

    def validate_chunk(self, chunk: Chunk) -> bool:
        """
        Validate that a chunk meets requirements.

        Args:
            chunk: Chunk to validate

        Returns:
            True if valid, False otherwise
        """
        # Check minimum size
        if chunk.token_estimate < self.min_tokens:
            return False

        # Check maximum size
        if chunk.token_estimate > self.max_tokens:
            return False

        # Check that content exists
        if not chunk.content or not chunk.content.strip():
            return False

        return True

    def get_statistics(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """
        Get statistics about created chunks.

        Args:
            chunks: List of chunks to analyze

        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {'total': 0}

        token_counts = [c.token_estimate for c in chunks]
        chunk_types = {}

        for chunk in chunks:
            chunk_types[chunk.chunk_type] = chunk_types.get(chunk.chunk_type, 0) + 1

        return {
            'total': len(chunks),
            'chunk_types': chunk_types,
            'total_tokens': sum(token_counts),
            'avg_tokens': sum(token_counts) // len(chunks),
            'min_tokens': min(token_counts),
            'max_tokens': max(token_counts),
            'all_tags': list(set().union(*[c.tags for c in chunks]))
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def estimate_tokens(text: str) -> int:
    """
    Estimate number of tokens in text.

    Uses rough approximation: 1 token ≈ 4 characters

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return len(text) // 4


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Simple sentence splitter (can be improved with nltk if needed)
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, text)
    return [s.strip() for s in sentences if s.strip()]


def get_overlap_text(text: str, overlap_tokens: int) -> str:
    """
    Get the last N tokens from text for overlap.

    Args:
        text: Source text
        overlap_tokens: Number of tokens for overlap

    Returns:
        Text containing approximately overlap_tokens tokens
    """
    if not text:
        return ""

    # Rough estimation: take last N*4 characters
    overlap_chars = overlap_tokens * 4
    if len(text) <= overlap_chars:
        return text

    # Try to break at word boundary
    overlap_text = text[-overlap_chars:]
    first_space = overlap_text.find(' ')

    if first_space > 0:
        overlap_text = overlap_text[first_space + 1:]

    return overlap_text


def generate_tags(content: str, metadata: Dict[str, Any]) -> Set[str]:
    """
    Generate tags for a chunk based on content and metadata.

    Args:
        content: Chunk content
        metadata: Chunk metadata

    Returns:
        Set of tags
    """
    tags = set()

    # Add tags from metadata
    for key, value in metadata.items():
        if key in ['name', 'type', 'category', 'level', 'school']:
            if value:
                tag_value = str(value).lower().replace(' ', '_')
                tags.add(f"{key}_{tag_value}")

    # Add content-based tags
    content_lower = content.lower()

    # Common D&D keywords
    keywords = {
        'combat': ['attack', 'damage', 'hit points', 'armor class', 'saving throw'],
        'magic': ['spell', 'magic', 'cast', 'ritual', 'concentration'],
        'ability': ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'],
        'condition': ['frightened', 'stunned', 'paralyzed', 'poisoned', 'charmed']
    }

    for tag, words in keywords.items():
        if any(word in content_lower for word in words):
            tags.add(tag)

    return tags


def format_metadata_for_retrieval(metadata: Dict[str, Any]) -> str:
    """
    Format metadata as text for inclusion in retrieval.

    Args:
        metadata: Metadata dictionary

    Returns:
        Formatted metadata string
    """
    parts = []

    # Priority fields to include in retrieval text
    priority_fields = ['name', 'level', 'type', 'category', 'school', 'cr']

    for field in priority_fields:
        if field in metadata and metadata[field]:
            value = metadata[field]
            parts.append(f"{field.title()}: {value}")

    return " | ".join(parts) if parts else ""


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """
    Truncate text to approximately max_tokens.

    Args:
        text: Text to truncate
        max_tokens: Maximum tokens

    Returns:
        Truncated text
    """
    if estimate_tokens(text) <= max_tokens:
        return text

    # Approximate character count
    max_chars = max_tokens * 4

    if len(text) <= max_chars:
        return text

    # Truncate and try to break at sentence boundary
    truncated = text[:max_chars]
    last_period = truncated.rfind('.')

    if last_period > max_chars * 0.8:  # Only if we don't lose too much
        truncated = truncated[:last_period + 1]

    return truncated.strip()
