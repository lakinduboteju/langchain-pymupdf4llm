import pytest
import os
from pathlib import Path
from typing import (
    Iterator
)

from langchain_pymupdf4llm import PyMuPDF4LLMLoader


_DOCS_DIR_PATH = os.path.join(
    Path(__file__).parents[1],
    "examples",
)

@pytest.mark.parametrize(
    "mode,file_path,expected_output_doc_count,expected_content_substring",
    [
        (
            "page",
            "https://people.sc.fsu.edu/~jpeterson/hello_world.pdf",
            1,
            "the simplest example of a program one can write"
        ),
        ("single", os.path.join(_DOCS_DIR_PATH, "sample_1.pdf"), 1, 'print("Hello, World!")'),
        ("page", os.path.join(_DOCS_DIR_PATH, "sample_1.pdf"), 2, "Row 2, Col 2"),
    ]
)
def test_pymupdf4llm_loader(
    mode: str,
    file_path: str,
    expected_output_doc_count: int,
    expected_content_substring: str,
):
    loader = PyMuPDF4LLMLoader(
        file_path=file_path,
        mode=mode,
    )

    doc_generator = loader.lazy_load()
    assert isinstance(doc_generator, Iterator)
    docs = list(doc_generator)
    assert len(docs) == expected_output_doc_count

    content = docs[0].page_content
    assert isinstance(content, str)
    assert expected_content_substring in content

    metadata = docs[0].metadata
    assert isinstance(metadata, dict)
    assert metadata["source"] == str(file_path)
