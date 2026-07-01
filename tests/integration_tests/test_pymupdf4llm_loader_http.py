"""Integration tests for HTTP loading in PyMuPDF4LLMLoader."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest
import requests

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


def test_loader_http_url(monkeypatch: pytest.MonkeyPatch) -> None:
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
            status_code=requests.codes.ok,
            content=(_DOCS_DIR_PATH / "sample_1.pdf").read_bytes(),
        )

    monkeypatch.setattr(requests, "get", fake_get)

    loader = PyMuPDF4LLMLoader(
        file_path=file_path,
        mode="page",
        headers=headers,
    )

    docs = list(loader.lazy_load())

    assert len(docs) == 2
    assert "Row 2, Col 2" in docs[0].page_content
    assert docs[0].metadata["source"] == file_path
    assert calls == [
        _RequestCall(
            url=file_path,
            headers=headers,
            timeout=loader_module._REQUEST_TIMEOUT_SECONDS,
        ),
    ]
