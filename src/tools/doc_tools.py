# src/tools/doc_tools.py
# DocAnalyst (detective) tools for parsing and analysing PDF reports using Docling.

import os
from typing import Dict, List

from docling.datamodel.document import Document
from docling.document_converter import PdfParser


def ingest_pdf(path: str) -> Document:
    """
    Ingest a PDF report using Docling.

    Args:
        path (str): Path to the PDF file.

    Returns:
        Document: A Docling Document object representing the parsed PDF.

    Notes:
        - Uses Docling's PdfParser for robust PDF parsing.
        - The Document object can be chunked and queried for specific content.
        - Raises FileNotFoundError if the file does not exist.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF file not found: {path}")

    parser = PdfParser()
    doc = parser.parse(path)
    return doc


def chunk_document(doc: Document, chunk_size: int = 500) -> List[str]:
    """
    Split a parsed PDF document into text chunks for querying.

    Args:
        doc (Document): Parsed Docling Document object.
        chunk_size (int): Maximum number of characters per chunk.

    Returns:
        List[str]: List of text chunks extracted from the document.

    Notes:
        - Helps prevent context overflow when querying large PDFs.
        - Default chunk size is 500 characters.
    """
    text = doc.text_content
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
    return chunks


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
    """
    results = []
    for chunk in chunks:
        if keyword.lower() in chunk.lower():
            results.append(chunk)
    return results


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
    """
    mentioned_paths = []
    for chunk in chunks:
        for word in chunk.split():
            if word.startswith("src/") and word.endswith(".py"):
                mentioned_paths.append(word)

    return {path: (path in repo_files) for path in mentioned_paths}
