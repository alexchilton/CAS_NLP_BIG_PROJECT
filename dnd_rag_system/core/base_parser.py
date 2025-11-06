"""
Base Parser Classes

Abstract base classes and utilities for parsing D&D content from various sources.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import re
import pdfplumber
from dataclasses import dataclass


@dataclass
class ParsedContent:
    """Container for parsed content from any source."""
    content_type: str  # 'spell', 'monster', 'class', 'race'
    name: str
    raw_text: str
    metadata: Dict[str, Any]
    chunks: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.chunks is None:
            self.chunks = []


class BaseParser(ABC):
    """
    Abstract base class for all content parsers.

    Subclasses must implement:
    - parse(): Main parsing logic
    - validate(): Content validation
    """

    def __init__(self, content_type: str):
        """
        Initialize parser.

        Args:
            content_type: Type of content this parser handles ('spell', 'monster', 'class', 'race')
        """
        self.content_type = content_type
        self.parsed_items: List[ParsedContent] = []

    @abstractmethod
    def parse(self, source: Union[str, Path]) -> List[ParsedContent]:
        """
        Parse content from source.

        Args:
            source: Path to source file or raw text

        Returns:
            List of ParsedContent objects

        Raises:
            ValueError: If source is invalid or parsing fails
        """
        pass

    @abstractmethod
    def validate(self, content: ParsedContent) -> bool:
        """
        Validate parsed content.

        Args:
            content: ParsedContent object to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get parsing statistics.

        Returns:
            Dictionary with statistics about parsed items
        """
        return {
            "content_type": self.content_type,
            "total_items": len(self.parsed_items),
            "item_names": [item.name for item in self.parsed_items]
        }


class PDFParser(BaseParser):
    """
    Base class for parsers that extract content from PDF files.

    Provides common PDF extraction utilities using pdfplumber.
    """

    def __init__(self, content_type: str):
        super().__init__(content_type)

    def extract_pdf_text(
        self,
        pdf_path: Union[str, Path],
        start_page: Optional[int] = None,
        end_page: Optional[int] = None
    ) -> str:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file
            start_page: First page to extract (1-indexed, inclusive)
            end_page: Last page to extract (1-indexed, inclusive)

        Returns:
            Extracted text

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF extraction fails
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            full_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)

                # Determine page range
                start_idx = (start_page - 1) if start_page else 0
                end_idx = end_page if end_page else total_pages

                # Extract pages
                for page_num in range(start_idx, min(end_idx, total_pages)):
                    try:
                        page = pdf.pages[page_num]
                        page_text = page.extract_text()

                        if page_text:
                            full_text += page_text + "\n\n"
                    except Exception as e:
                        print(f"Warning: Could not extract page {page_num + 1}: {e}")
                        continue

            return full_text

        except Exception as e:
            raise Exception(f"Failed to extract PDF {pdf_path}: {str(e)}")

    def extract_pdf_pages_separately(
        self,
        pdf_path: Union[str, Path],
        start_page: Optional[int] = None,
        end_page: Optional[int] = None
    ) -> Dict[int, str]:
        """
        Extract text from PDF, returning each page separately.

        Args:
            pdf_path: Path to PDF file
            start_page: First page to extract (1-indexed)
            end_page: Last page to extract (1-indexed)

        Returns:
            Dictionary mapping page numbers to extracted text
        """
        pdf_path = Path(pdf_path)
        pages_text = {}

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                start_idx = (start_page - 1) if start_page else 0
                end_idx = end_page if end_page else total_pages

                for page_num in range(start_idx, min(end_idx, total_pages)):
                    try:
                        page = pdf.pages[page_num]
                        page_text = page.extract_text()

                        if page_text:
                            pages_text[page_num + 1] = page_text  # 1-indexed
                    except Exception as e:
                        print(f"Warning: Could not extract page {page_num + 1}: {e}")
                        continue

            return pages_text

        except Exception as e:
            raise Exception(f"Failed to extract PDF pages from {pdf_path}: {str(e)}")


class TextParser(BaseParser):
    """
    Base class for parsers that extract content from text files.

    Provides common text file reading utilities.
    """

    def __init__(self, content_type: str):
        super().__init__(content_type)

    def read_text_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        Read text from file.

        Args:
            file_path: Path to text file
            encoding: Text encoding (default: utf-8)

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If file reading fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Text file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Failed to read text file {file_path}: {str(e)}")

    def read_text_lines(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> List[str]:
        """
        Read text file as list of lines.

        Args:
            file_path: Path to text file
            encoding: Text encoding (default: utf-8)

        Returns:
            List of lines from file
        """
        text = self.read_text_file(file_path, encoding)
        return text.split('\n')


# ============================================================================
# TEXT CLEANING UTILITIES
# ============================================================================

def clean_extracted_text(text: str) -> str:
    """
    Clean and normalize extracted text.

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)

    # Fix common PDF extraction issues
    text = text.replace('\r', '\n')

    # Normalize line endings
    text = '\n'.join(line.strip() for line in text.split('\n'))

    # Remove empty lines
    lines = [line for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)

    return text.strip()


def split_by_headers(text: str, header_pattern: str) -> List[Dict[str, str]]:
    """
    Split text into sections based on headers.

    Args:
        text: Text to split
        header_pattern: Regex pattern to match headers

    Returns:
        List of dictionaries with 'header' and 'content' keys
    """
    sections = []

    # Find all headers
    matches = list(re.finditer(header_pattern, text, re.MULTILINE | re.IGNORECASE))

    for i, match in enumerate(matches):
        header = match.group(0).strip()
        start_pos = match.end()

        # Find end position (start of next header or end of text)
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        content = text[start_pos:end_pos].strip()

        sections.append({
            'header': header,
            'content': content,
            'start_pos': match.start(),
            'end_pos': end_pos
        })

    return sections


def extract_pattern(text: str, pattern: str, group: int = 1) -> Optional[str]:
    """
    Extract text matching a regex pattern.

    Args:
        text: Text to search
        pattern: Regex pattern
        group: Group number to extract (default: 1)

    Returns:
        Matched text or None if not found
    """
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if match and len(match.groups()) >= group:
        return match.group(group).strip()
    return None


def extract_all_patterns(text: str, pattern: str) -> List[str]:
    """
    Extract all text matching a regex pattern.

    Args:
        text: Text to search
        pattern: Regex pattern

    Returns:
        List of all matches
    """
    matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
    return [m.strip() if isinstance(m, str) else m[0].strip() for m in matches]
