"""Load PDFs and parse their contents to Markdown with PyMuPDF4LLM."""

from __future__ import annotations

import logging
import re
import tempfile
from collections.abc import Iterator, Mapping
from pathlib import Path, PurePath
from typing import Literal
from urllib.parse import urlparse

import requests as requests
from langchain_core.document_loaders import BaseBlobParser, BaseLoader, Blob
from langchain_core.documents import Document

from langchain_pymupdf4llm.pymupdf4llm_parser import PyMuPDF4LLMParser

_DEFAULT_PAGES_DELIMITER = "\n-----\n\n"
_REQUEST_TIMEOUT_SECONDS = 30

logger = logging.getLogger(__name__)


class BasePDFLoader(BaseLoader):
    """Base loader class for PDF files.

    If the file is a web path, it is downloaded to a temporary file and cleaned
    up when the loader is destroyed.
    """

    def __init__(
        self,
        file_path: str | PurePath,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize the loader with a local path or URL."""
        self.file_path = str(file_path)
        if self.file_path.startswith("~"):
            self.file_path = str(Path(self.file_path).expanduser())
        self.web_path: str | None = None
        self.headers = dict(headers) if headers is not None else None

        if not Path(self.file_path).is_file() and self._is_valid_url(self.file_path):
            self.temp_dir: tempfile.TemporaryDirectory[str] = (
                tempfile.TemporaryDirectory()
            )
            suffix = Path(urlparse(self.file_path).path).suffix
            if self._is_s3_presigned_url(self.file_path):
                suffix = Path(urlparse(self.file_path).path).name
            temp_pdf = Path(self.temp_dir.name) / f"tmp{suffix}"
            self.web_path = self.file_path
            if not self._is_s3_url(self.file_path):
                response = requests.get(
                    self.file_path,
                    headers=self.headers,
                    timeout=_REQUEST_TIMEOUT_SECONDS,
                )
                if response.status_code != requests.codes.ok:
                    message = (
                        "Check the URL of your file; returned status code "
                        f"{response.status_code}"
                    )
                    raise ValueError(message)

                temp_pdf.write_bytes(response.content)
                self.file_path = str(temp_pdf)
        elif not Path(self.file_path).is_file():
            message = f"File path {self.file_path} is not a valid file or URL"
            raise ValueError(message)

    def __del__(self) -> None:
        """Clean up temporary files used for downloaded PDFs."""
        if hasattr(self, "temp_dir"):
            self.temp_dir.cleanup()

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Return whether a string is a syntactically valid URL."""
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    @staticmethod
    def _is_s3_url(url: str) -> bool:
        """Return whether a URL points to S3."""
        try:
            result = urlparse(url)
        except ValueError:
            return False
        return result.scheme == "s3" and bool(result.netloc)

    @staticmethod
    def _is_s3_presigned_url(url: str) -> bool:
        """Return whether a URL looks like a presigned S3 URL."""
        try:
            result = urlparse(url)
        except ValueError:
            return False
        return bool(re.search(r"\.s3\.amazonaws\.com$", result.netloc))

    @property
    def source(self) -> str:
        """Return the original source path or URL."""
        return self.web_path if self.web_path is not None else self.file_path


class PyMuPDF4LLMLoader(BasePDFLoader):
    """Load and parse a PDF file to Markdown using PyMuPDF4LLM."""

    def __init__(
        self,
        file_path: str | PurePath,
        *,
        headers: Mapping[str, str] | None = None,
        password: str | None = None,
        mode: Literal["single", "page"] = "page",
        pages_delimiter: str = _DEFAULT_PAGES_DELIMITER,
        extract_images: bool = False,
        images_parser: BaseBlobParser | None = None,
        use_layout: bool = False,
        **pymupdf4llm_kwargs: object,
    ) -> None:
        """Initialize the PDF loader.

        Args:
            file_path: Local path or URL to the PDF file.
            headers: Optional headers for URL downloads.
            password: Optional password for encrypted PDFs.
            mode: Extraction mode, either ``single`` or ``page``.
            pages_delimiter: Delimiter for page content in ``single`` mode.
            extract_images: Whether to replace extracted images with parser text.
            images_parser: Image parser required when ``extract_images`` is true.
            use_layout: Whether to enable PyMuPDF4LLM layout mode when available.
            **pymupdf4llm_kwargs: Extra arguments passed to ``to_markdown``.
        """
        super().__init__(file_path, headers=headers)
        self.parser = PyMuPDF4LLMParser(
            password=password,
            mode=mode,
            pages_delimiter=pages_delimiter,
            extract_images=extract_images,
            images_parser=images_parser,
            use_layout=use_layout,
            **pymupdf4llm_kwargs,
        )

    def _lazy_load(self, **kwargs: object) -> Iterator[Document]:
        """Lazily parse the configured PDF document."""
        if kwargs:
            logger.warning(
                "Received runtime arguments %s. Runtime arguments passed to "
                "`load` are ignored. Pass arguments during initialization instead.",
                kwargs,
            )
        if self.web_path:
            blob = Blob.from_data(Path(self.file_path).read_bytes(), path=self.web_path)
        else:
            blob = Blob.from_path(self.file_path)
        yield from self.parser.lazy_parse(blob)

    def load(self, **kwargs: object) -> list[Document]:
        """Load PDF content eagerly."""
        return list(self._lazy_load(**kwargs))

    def lazy_load(self) -> Iterator[Document]:
        """Load PDF content lazily."""
        yield from self._lazy_load()
