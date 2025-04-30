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
    "mode,pdf_filename,expected_output_doc_count,expected_content_substring",
    [
        ("single", "sample_1.pdf", 1, 'print("Hello, World!")'),
        ("page", "sample_1.pdf", 2, "Row 2, Col 2"),
    ]
)
def test_pymupdf4llm_parser_modes(
    mode: str,
    pdf_filename: str,
    expected_output_doc_count: int,
    expected_content_substring: str,
):
    doc_path = os.path.join(_DOCS_DIR_PATH, pdf_filename)
    assert os.path.exists(doc_path)
    blob = Blob.from_path(doc_path)

    parser = PyMuPDF4LLMParser(mode=mode)

    doc_generator = parser.lazy_parse(blob)
    assert isinstance(doc_generator, Iterator)
    docs = list(doc_generator)
    assert len(docs) == expected_output_doc_count

    content = docs[0].page_content
    assert isinstance(content, str)
    assert expected_content_substring in content

    metadata = docs[0].metadata
    assert isinstance(metadata, dict)
    assert metadata["source"] == str(doc_path)


def test_invalid_mode():
    """Test that an invalid mode raises ValueError."""
    with pytest.raises(ValueError, match="mode must be single or page"):
        PyMuPDF4LLMParser(mode="invalid_mode")


def test_missing_images_parser():
    """Test that ValueError is raised if extract_images is True but no images_parser."""
    with pytest.raises(
        ValueError, match="images_parser must be provided if extract_images is True"
    ):
        PyMuPDF4LLMParser(extract_images=True)


@pytest.mark.parametrize(
    "conflicting_kwarg",
    [
        "ignore_images",
        "ignore_graphics",
    ],
)
def test_conflicting_image_kwargs(conflicting_kwarg: str):
    """Test conflicting image-related kwargs raise ValueError when extract_images=True."""
    # A dummy parser is needed, even if not used, to satisfy the images_parser requirement
    class DummyParser:
        pass

    kwargs = {conflicting_kwarg: True}
    with pytest.raises(
        ValueError,
        match=f"PyMuPDF4LLM argument: {conflicting_kwarg} cannot be set to True when extract_images is True.",
    ):
        PyMuPDF4LLMParser(extract_images=True, images_parser=DummyParser(), **kwargs)


@pytest.mark.parametrize(
    "unsupported_kwarg",
    [
        "write_images",
        "embed_images",
        "image_path",
        "filename",
        "page_chunks",
        "extract_words",
        "show_progress",
    ],
)
def test_unsupported_kwargs(unsupported_kwarg: str):
    """Test that unsupported pymupdf4llm_kwargs raise ValueError."""
    kwargs = {unsupported_kwarg: True}  # The value doesn't matter, just its presence
    with pytest.raises(
        ValueError,
        match=f"PyMuPDF4LLM argument: {unsupported_kwarg} cannot be set to True.",
    ):
        PyMuPDF4LLMParser(**kwargs)
