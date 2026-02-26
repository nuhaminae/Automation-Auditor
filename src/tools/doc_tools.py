# src/tools/doc_tools.py
# DocAnalyst (detective) tools for parsing and analysing PDF reports using Docling.

import os
import warnings
from pathlib import Path
from typing import Dict, List

from docling.document_converter import DocumentConverter
from docling_core.types.doc import DoclingDocument

# Ignore all DeprecationWarnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


class DocError(Exception):
    """Custom exception for document analysis errors."""


def ingest_pdf(pdf_path: str) -> str:
    """
    Ingest a PDF report using Docling.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Extracted plain text from the PDF.

    Notes:
        - Uses Docling's DocumentConverter for robust PDF parsing.
        - Raises FileNotFoundError if the file does not exist.
        - Raises DocError if conversion fails or returns empty text.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    converter = DocumentConverter()
    try:
        result = converter.convert(Path(pdf_path))
        doc: DoclingDocument = result.document
        text = doc.export_to_text()
        if not text or text.strip() == "":
            raise DocError(f"Docling returned empty text for {pdf_path}")
        return text
    except Exception as e:
        raise DocError(f"Failed to ingest PDF {pdf_path}: {e}") from e


def chunk_document(text: str, chunk_size: int = 500) -> List[str]:
    """
    Split extracted PDF text into chunks for querying.

    Args:
        text (str): Extracted plain text from the PDF.
        chunk_size (int): Maximum number of characters per chunk.

    Returns:
        List[str]: List of text chunks.

    Notes:
        - Helps prevent context overflow when querying large PDFs.
        - Default chunk size is 500 characters.
        - Raises DocError if text is empty.
    """
    if not text or text.strip() == "":
        raise DocError("No text provided to chunk.")
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def query_document(chunks: List[str], keyword: str) -> List[str]:
    """
    Search for a keyword across document chunks.

    Args:
        chunks (List[str]): List of text chunks from the PDF.
        keyword (str): Keyword or phrase to search for.

    Returns:
        List[str]: List of chunks containing the keyword.

    Notes:
        - Case-insensitive search.
        - Useful for verifying deep understanding of concepts like
          'Dialectical Synthesis' or 'Fan-In/Fan-Out'.
        - Raises DocError if chunks list is empty.
    """
    if not chunks:
        raise DocError("No chunks provided for query.")
    return [chunk for chunk in chunks if keyword.lower() in chunk.lower()]


def cross_reference_paths(chunks: List[str], repo_files: List[str]) -> Dict[str, bool]:
    """
    Cross-reference file paths mentioned in the PDF against actual repo files.

    Args:
        chunks (List[str]): List of text chunks from the PDF.
        repo_files (List[str]): List of file paths present in the repository.

    Returns:
        Dict[str, bool]: Mapping of mentioned file paths to existence status.

    Notes:
        - Flags hallucinations when the report cites non-existent files.
        - Example: "src/nodes/judges.py" → True if exists, False if hallucinated.
        - Raises DocError if chunks list is empty.
    """
    if not chunks:
        raise DocError("No chunks provided for cross-reference.")
    mentioned_paths = []
    for chunk in chunks:
        for word in chunk.split():
            if word.startswith("src/") and word.endswith(".py"):
                mentioned_paths.append(word)

    return {path: (path in repo_files) for path in mentioned_paths}
