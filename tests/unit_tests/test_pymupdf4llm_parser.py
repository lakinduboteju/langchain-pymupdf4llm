import pytest
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import (
    Iterator
)
from unittest.mock import Mock

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


@pytest.mark.parametrize(
    "valid_kwarg_key, valid_kwarg_value",
    [
        ("table_strategy", "lines"),
        ("ignore_code", True),
        # Add other known valid kwargs if needed
    ],
)
def test_valid_pymupdf4llm_kwargs(valid_kwarg_key: str, valid_kwarg_value):
    """Test that valid pymupdf4llm_kwargs do not raise errors during init."""
    kwargs = {valid_kwarg_key: valid_kwarg_value}
    try:
        PyMuPDF4LLMParser(**kwargs)
    except ValueError as e:
        pytest.fail(f"Initialization failed unexpectedly with valid kwarg: {e}")


def test_use_layout_is_ignored_when_not_supported(monkeypatch: pytest.MonkeyPatch):
    """Test parsing still works when pymupdf4llm has no use_layout support."""
    fake_to_markdown = Mock(return_value="page markdown")
    fake_module = SimpleNamespace(to_markdown=fake_to_markdown)
    monkeypatch.setitem(sys.modules, "pymupdf4llm", fake_module)

    parser = PyMuPDF4LLMParser(use_layout=True)

    assert parser._get_page_content_in_md(doc=object(), page=0) == "page markdown"
    fake_to_markdown.assert_called_once()
    _, kwargs = fake_to_markdown.call_args
    assert kwargs["pages"] == [0]
    assert kwargs["show_progress"] is False
    assert kwargs["graphics_limit"] == 5000


def test_use_layout_is_called_when_supported(monkeypatch: pytest.MonkeyPatch):
    """Test the parser forwards the configured use_layout value when available."""
    fake_to_markdown = Mock(return_value="page markdown")
    fake_use_layout = Mock()
    fake_module = SimpleNamespace(
        to_markdown=fake_to_markdown,
        use_layout=fake_use_layout,
    )
    monkeypatch.setitem(sys.modules, "pymupdf4llm", fake_module)

    parser = PyMuPDF4LLMParser(use_layout=True)

    assert parser._get_page_content_in_md(doc=object(), page=1) == "page markdown"
    fake_use_layout.assert_called_once_with(True)
    fake_to_markdown.assert_called_once()
