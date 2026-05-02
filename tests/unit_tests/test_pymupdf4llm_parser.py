"""Unit tests for the PyMuPDF4LLM parser."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Literal, cast
from unittest.mock import Mock

import pytest
from langchain_core.document_loaders import BaseBlobParser, Blob
from langchain_core.documents import Document

from langchain_pymupdf4llm.pymupdf4llm_parser import PyMuPDF4LLMParser

_DOCS_DIR_PATH = Path(__file__).parents[1] / "examples"


@pytest.mark.parametrize(
    ("mode", "pdf_filename", "expected_output_doc_count", "expected_content_substring"),
    [
        ("single", "sample_1.pdf", 1, 'print("Hello, World!")'),
        ("page", "sample_1.pdf", 2, "Row 2, Col 2"),
    ],
)
def test_pymupdf4llm_parser_modes(
    mode: str,
    pdf_filename: str,
    expected_output_doc_count: int,
    expected_content_substring: str,
) -> None:
    """Test supported parser modes."""
    doc_path = _DOCS_DIR_PATH / pdf_filename
    assert doc_path.exists()
    blob = Blob.from_path(doc_path)

    parser = PyMuPDF4LLMParser(mode=cast("Literal['single', 'page']", mode))

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


def test_invalid_mode() -> None:
    """Test that an invalid mode raises ValueError."""
    with pytest.raises(ValueError, match="mode must be single or page"):
        PyMuPDF4LLMParser(mode="invalid_mode")  # type: ignore[arg-type]


def test_missing_images_parser() -> None:
    """Test that image extraction requires an image parser."""
    with pytest.raises(
        ValueError,
        match="images_parser must be provided if extract_images is True",
    ):
        PyMuPDF4LLMParser(extract_images=True)


class DummyParser(BaseBlobParser):
    """Small parser used to satisfy the image parser type in tests."""

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        """Return deterministic image content."""
        del blob
        yield Document(page_content="image text")


@pytest.mark.parametrize(
    "conflicting_kwarg",
    [
        "ignore_images",
        "ignore_graphics",
    ],
)
def test_conflicting_image_kwargs(conflicting_kwarg: str) -> None:
    """Test conflicting image kwargs raise ValueError when extracting images."""
    kwargs = {conflicting_kwarg: True}
    with pytest.raises(
        ValueError,
        match=(
            f"PyMuPDF4LLM argument: {conflicting_kwarg} cannot be set to True "
            "when extract_images is True."
        ),
    ):
        PyMuPDF4LLMParser(
            extract_images=True,
            images_parser=DummyParser(),
            **kwargs,  # type: ignore[arg-type]
        )


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
def test_unsupported_kwargs(unsupported_kwarg: str) -> None:
    """Test unsupported PyMuPDF4LLM kwargs raise ValueError."""
    kwargs = {unsupported_kwarg: True}
    with pytest.raises(
        ValueError,
        match=f"PyMuPDF4LLM argument: {unsupported_kwarg} cannot be set to True.",
    ):
        PyMuPDF4LLMParser(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("valid_kwarg_key", "valid_kwarg_value"),
    [
        ("table_strategy", "lines"),
        ("ignore_code", True),
    ],
)
def test_valid_pymupdf4llm_kwargs(
    valid_kwarg_key: str,
    valid_kwarg_value: object,
) -> None:
    """Test valid PyMuPDF4LLM kwargs do not raise during initialization."""
    kwargs = {valid_kwarg_key: valid_kwarg_value}
    PyMuPDF4LLMParser(**kwargs)  # type: ignore[arg-type]


def test_use_layout_is_ignored_when_not_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test parsing works when pymupdf4llm has no use_layout support."""
    fake_to_markdown = Mock(return_value="page markdown")
    fake_module = SimpleNamespace(to_markdown=fake_to_markdown)
    monkeypatch.setitem(sys.modules, "pymupdf4llm", fake_module)

    parser = PyMuPDF4LLMParser(use_layout=True)

    assert parser._get_page_content_in_md(doc=object(), page=0) == "page markdown"  # type: ignore[arg-type]
    fake_to_markdown.assert_called_once()
    _, kwargs = fake_to_markdown.call_args
    assert kwargs["pages"] == [0]
    assert kwargs["show_progress"] is False
    assert kwargs["graphics_limit"] == 5000


def test_use_layout_is_called_when_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the parser forwards the configured use_layout value when available."""
    fake_to_markdown = Mock(return_value="page markdown")
    fake_use_layout = Mock()
    fake_module = SimpleNamespace(
        to_markdown=fake_to_markdown,
        use_layout=fake_use_layout,
    )
    monkeypatch.setitem(sys.modules, "pymupdf4llm", fake_module)

    parser = PyMuPDF4LLMParser(use_layout=True)

    assert parser._get_page_content_in_md(doc=object(), page=1) == "page markdown"  # type: ignore[arg-type]
    fake_use_layout.assert_called_once_with(True)
    fake_to_markdown.assert_called_once()
