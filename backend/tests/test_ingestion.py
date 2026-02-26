"""Tests for the ingestion pipeline components."""
import pytest
from app.ingestion.chunker import chunk_text
from app.ingestion.extractors import compute_hash


def test_chunk_text_basic():
    text = "Hello world. " * 200  # ~2600 chars
    chunks = chunk_text(text, metadata={"doc_id": "test"})
    assert len(chunks) > 1
    for chunk in chunks:
        assert "text" in chunk
        assert "metadata" in chunk
        assert chunk["metadata"]["doc_id"] == "test"
        assert "chunk_index" in chunk["metadata"]


def test_chunk_text_short():
    text = "Short text."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Short text."


def test_chunk_text_empty():
    chunks = chunk_text("")
    assert len(chunks) == 0 or chunks[0]["text"] == ""


def test_compute_hash():
    h1 = compute_hash("hello")
    h2 = compute_hash("hello")
    h3 = compute_hash("world")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # SHA-256 hex


def test_chunk_metadata_propagation():
    text = "A" * 2000
    meta = {"doc_name": "test.pdf", "page_number": 1}
    chunks = chunk_text(text, metadata=meta)
    for chunk in chunks:
        assert chunk["metadata"]["doc_name"] == "test.pdf"
        assert chunk["metadata"]["page_number"] == 1
        assert "total_chunks" in chunk["metadata"]
