"""Unit tests for the PyMuPDF4LLM loader internals."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import Mock

import pytest
from langchain_core.documents import Document

from langchain_pymupdf4llm import pymupdf4llm_loader as loader_module
from langchain_pymupdf4llm.pymupdf4llm_loader import BasePDFLoader, PyMuPDF4LLMLoader

_DOCS_DIR_PATH = Path(__file__).parents[1] / "examples"


class _FakeParser:
    """Minimal parser used to isolate loader behavior in unit tests."""

    def __init__(self, **_: object) -> None:
        """Accept parser kwargs without side effects."""

    def lazy_parse(self, blob: object) -> Iterator[Document]:
        """Return deterministic content with visible blob identity."""
        yield Document(page_content="ok", metadata={"blob": repr(blob)})


def test_base_loader_rejects_invalid_file_path() -> None:
    """Test invalid paths raise a clear ValueError."""
    with pytest.raises(
        ValueError,
        match="is not a valid file or URL",
    ):
        PyMuPDF4LLMLoader(file_path="definitely-not-a-real-file.pdf")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.test/file.pdf", True),
        ("s3://bucket/key.pdf", True),
        ("not-a-url", False),
        ("/tmp/file.pdf", False),
    ],
)
def test_url_validation_helper(url: str, expected: bool) -> None:
    """Test URL syntax helper recognizes valid and invalid inputs."""
    assert BasePDFLoader._is_valid_url(url) is expected


@pytest.mark.parametrize(
    ("url", "is_s3", "is_presigned"),
    [
        ("s3://bucket/key.pdf", True, False),
        (
            "https://bucket.s3.amazonaws.com/key.pdf?X-Amz-Signature=test",
            False,
            True,
        ),
        ("https://example.test/file.pdf", False, False),
    ],
)
def test_s3_helpers(url: str, is_s3: bool, is_presigned: bool) -> None:
    """Test S3 URL helper detection."""
    assert BasePDFLoader._is_s3_url(url) is is_s3
    assert BasePDFLoader._is_s3_presigned_url(url) is is_presigned


def test_loader_runtime_kwargs_emit_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Test runtime kwargs passed to load produce a warning and are ignored."""
    file_path = _DOCS_DIR_PATH / "sample_1.pdf"
    loader = PyMuPDF4LLMLoader(file_path=file_path, mode="page")

    docs = loader.load(unused_runtime_kwarg=True)

    assert len(docs) == 2
    assert "Runtime arguments passed to `load` are ignored" in caplog.text


def test_loader_uses_blob_from_path_for_local_files(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test local files are wrapped with Blob.from_path before parsing."""
    file_path = _DOCS_DIR_PATH / "sample_1.pdf"
    sentinel_blob = object()

    monkeypatch.setattr(loader_module, "PyMuPDF4LLMParser", _FakeParser)
    from_path = Mock(return_value=sentinel_blob)
    from_data = Mock()
    monkeypatch.setattr(loader_module.Blob, "from_path", from_path)
    monkeypatch.setattr(loader_module.Blob, "from_data", from_data)

    loader = PyMuPDF4LLMLoader(file_path=file_path)
    docs = loader.load()

    from_path.assert_called_once_with(str(file_path))
    from_data.assert_not_called()
    assert len(docs) == 1
    assert "blob" in docs[0].metadata


def test_loader_uses_blob_from_data_for_web_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test web sources are wrapped with Blob.from_data and preserve URL source."""
    file_path = _DOCS_DIR_PATH / "sample_1.pdf"
    sentinel_blob = object()
    web_source = "https://example.test/sample_1.pdf"

    monkeypatch.setattr(loader_module, "PyMuPDF4LLMParser", _FakeParser)
    from_path = Mock()
    from_data = Mock(return_value=sentinel_blob)
    monkeypatch.setattr(loader_module.Blob, "from_path", from_path)
    monkeypatch.setattr(loader_module.Blob, "from_data", from_data)

    loader = PyMuPDF4LLMLoader(file_path=file_path)
    loader.web_path = web_source

    docs = loader.load()

    from_path.assert_not_called()
    from_data.assert_called_once()
    call_args = from_data.call_args
    assert call_args is not None
    assert isinstance(call_args.args[0], bytes)
    assert call_args.kwargs["path"] == web_source
    assert len(docs) == 1
    assert "blob" in docs[0].metadata
