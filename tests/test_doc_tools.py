# tests/test_doc_tools.py
# run with: pytest tests/test_doc_tools.py
# Tests for DocTools in src/tools/doc_tools.py

from pathlib import Path

import pytest

from src.tools import doc_tools

# Path to a sample PDF in your repo (adjust if needed)
SAMPLE_PDF = Path("reports/interim_report.pdf")


@pytest.mark.skipif(not SAMPLE_PDF.exists(), reason="Sample PDF not available")
def test_ingest_pdf_returns_text():
    text = doc_tools.ingest_pdf(str(SAMPLE_PDF))
    assert isinstance(text, str)
    assert len(text) > 0
    # sanity check: should contain known phrase
    assert "Automation Auditor" in text


def test_chunk_document_splits_text():
    text = "This is a test document." * 50  # long enough
    chunks = doc_tools.chunk_document(text, chunk_size=100)
    assert isinstance(chunks, list)
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert len(chunks) > 1


def test_chunk_document_empty_text_raises():
    with pytest.raises(doc_tools.DocError):
        doc_tools.chunk_document("", chunk_size=100)


def test_query_document_finds_keyword():
    chunks = ["This is about RepoInvestigator.", "Nothing here."]
    results = doc_tools.query_document(chunks, "RepoInvestigator")
    assert len(results) == 1
    assert "RepoInvestigator" in results[0]


def test_query_document_empty_chunks_raises():
    with pytest.raises(doc_tools.DocError):
        doc_tools.query_document([], "keyword")


def test_cross_reference_paths_detects_files():
    chunks = ["We reference src/nodes/judges.py in this report."]
    repo_files = ["src/nodes/judges.py", "src/tools/doc_tools.py"]
    mapping = doc_tools.cross_reference_paths(chunks, repo_files)
    assert mapping["src/nodes/judges.py"] is True


def test_cross_reference_paths_flags_missing():
    chunks = ["Mention src/nodes/fake.py here."]
    repo_files = ["src/nodes/judges.py"]
    mapping = doc_tools.cross_reference_paths(chunks, repo_files)
    assert mapping["src/nodes/fake.py"] is False
