"""Integration tests for the PyMuPDF4LLM loader."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest

from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_pymupdf4llm import pymupdf4llm_loader as loader_module

_DOCS_DIR_PATH = Path(__file__).parents[1] / "examples"

pytestmark = pytest.mark.integration


@dataclass(frozen=True)
class _RequestCall:
    """Captured request arguments for mocked HTTP loader tests."""

    url: str
    headers: Mapping[str, str] | None
    timeout: int


@dataclass(frozen=True)
class _FakeResponse:
    """Minimal response shape used by BasePDFLoader."""

    status_code: int
    content: bytes


@pytest.mark.parametrize(
    ("mode", "file_path", "expected_output_doc_count", "expected_content_substring"),
    [
        (
            "single",
            str(_DOCS_DIR_PATH / "sample_1.pdf"),
            1,
            'print("Hello, World!")',
        ),
        ("page", str(_DOCS_DIR_PATH / "sample_1.pdf"), 2, "Row 2, Col 2"),
    ],
)
def test_pymupdf4llm_loader(
    mode: str,
    file_path: str,
    expected_output_doc_count: int,
    expected_content_substring: str,
) -> None:
    """Test loading PDFs from local paths."""
    loader = PyMuPDF4LLMLoader(
        file_path=file_path,
        mode=mode,  # type: ignore[arg-type]
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
    assert metadata["source"] == file_path


def test_pymupdf4llm_loader_http_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading a PDF from an HTTP URL without opening a socket."""
    file_path = "https://example.test/sample_1.pdf"
    headers = {"Authorization": "Bearer test-token"}
    calls: list[_RequestCall] = []

    def fake_get(
        url: str,
        *,
        headers: Mapping[str, str] | None,
        timeout: int,
    ) -> _FakeResponse:
        calls.append(_RequestCall(url=url, headers=headers, timeout=timeout))
        return _FakeResponse(
            status_code=loader_module.requests.codes.ok,
            content=(_DOCS_DIR_PATH / "sample_1.pdf").read_bytes(),
        )

    monkeypatch.setattr(loader_module.requests, "get", fake_get)

    loader = PyMuPDF4LLMLoader(
        file_path=file_path,
        mode="page",
        headers=headers,
    )

    doc_generator = loader.lazy_load()
    assert isinstance(doc_generator, Iterator)
    docs = list(doc_generator)
    assert len(docs) == 2

    content = docs[0].page_content
    assert isinstance(content, str)
    assert "Row 2, Col 2" in content

    metadata = docs[0].metadata
    assert isinstance(metadata, dict)
    assert metadata["source"] == file_path
    assert calls == [
        _RequestCall(
            url=file_path,
            headers=headers,
            timeout=loader_module._REQUEST_TIMEOUT_SECONDS,
        ),
    ]


def test_pymupdf4llm_loader_http_status_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test non-200 HTTP responses raise a clear ValueError."""
    file_path = "https://example.test/missing.pdf"

    def fake_get(
        url: str,
        *,
        headers: Mapping[str, str] | None,
        timeout: int,
    ) -> _FakeResponse:
        del url, headers, timeout
        return _FakeResponse(status_code=404, content=b"")

    monkeypatch.setattr(loader_module.requests, "get", fake_get)

    with pytest.raises(
        ValueError,
        match="Check the URL of your file; returned status code 404",
    ):
        PyMuPDF4LLMLoader(file_path=file_path)


def test_loader_forwards_use_layout() -> None:
    """Test the loader passes use_layout to its parser."""
    file_path = _DOCS_DIR_PATH / "sample_1.pdf"

    loader = PyMuPDF4LLMLoader(file_path=file_path, use_layout=True)

    assert loader.parser.use_layout is True
