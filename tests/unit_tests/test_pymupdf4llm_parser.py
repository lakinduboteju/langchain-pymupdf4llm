import pytest
import os
from pathlib import Path
from typing import (
    Iterator
)

from langchain_core.document_loaders import Blob

from langchain_pymupdf4llm.pymupdf4llm_parser import PyMuPDF4LLMParser


_DOCS_DIR_PATH = os.path.join(
    Path(__file__).parents[1],
    "examples",
)

@pytest.mark.parametrize(
    "mode,doc_filename,page_count,expected_substring",
    [
        ("single", "sample_1.pdf", 1, 'print("Hello, World!")'),
        ("page", "sample_1.pdf", 2, "Row 2, Col 2"),
    ]
)
def test_pymupdf4llm_parser_modes(
    mode: str,
    doc_filename: str,
    page_count: int,
    expected_substring: str,
):
    doc_path = os.path.join(_DOCS_DIR_PATH, doc_filename)
    assert os.path.exists(doc_path)
    blob = Blob.from_path(doc_path)

    parser = PyMuPDF4LLMParser(mode=mode)

    doc_generator = parser.lazy_parse(blob)
    assert isinstance(doc_generator, Iterator)
    docs = list(doc_generator)
    assert len(docs) == page_count

    content = docs[0].page_content
    assert isinstance(content, str)
    assert expected_substring in content

    metadata = docs[0].metadata
    assert isinstance(metadata, dict)
    assert metadata["source"] == str(doc_path)
