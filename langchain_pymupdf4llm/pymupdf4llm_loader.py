"""Contains PyMuPDF4LLM loader class to load PDFs, and parse contents to Markdown."""

import logging
import os
import re
import tempfile
from abc import ABC
from pathlib import PurePath
from typing import (
    TYPE_CHECKING,
    Any,
    Iterator,
    Literal,
    Optional,
    Union,
)
from urllib.parse import urlparse

import requests
from langchain_core.documents import Document
from langchain_core.document_loaders import (
    Blob,
    BaseLoader,
    BaseBlobParser,
)

from langchain_pymupdf4llm.pymupdf4llm_parser import PyMuPDF4LLMParser


_DEFAULT_PAGES_DELIMITER = "\n-----\n\n"


logger = logging.getLogger(__file__)


# Directly taken from:-
# github.com/langchain-ai/langchain/
# libs/community/langchain_community/document_loaders/pdf.py
class BasePDFLoader(BaseLoader, ABC):
    """Base Loader class for `PDF` files.

    If the file is a web path, it will download it to a temporary file, use it, then
        clean up the temporary file after completion.
    """

    def __init__(
        self, file_path: Union[str, PurePath], *, headers: Optional[dict] = None
    ):
        """Initialize with a file path.

        Args:
            file_path: Either a local, S3 or web path to a PDF file.
            headers: Headers to use for GET request to download a file from a web path.
        """
        self.file_path = str(file_path)
        self.web_path = None
        self.headers = headers
        if "~" in self.file_path:
            self.file_path = os.path.expanduser(self.file_path)

        # If the file is a web path or S3, download it to a temporary file,
        # and use that. It's better to use a BlobLoader.
        if not os.path.isfile(self.file_path) and self._is_valid_url(self.file_path):
            self.temp_dir = tempfile.TemporaryDirectory()
            _, suffix = os.path.splitext(self.file_path)
            if self._is_s3_presigned_url(self.file_path):
                suffix = urlparse(self.file_path).path.split("/")[-1]
            temp_pdf = os.path.join(self.temp_dir.name, f"tmp{suffix}")
            self.web_path = self.file_path
            if not self._is_s3_url(self.file_path):
                r = requests.get(self.file_path, headers=self.headers)
                if r.status_code != 200:
                    raise ValueError(
                        "Check the url of your file; returned status code %s"
                        % r.status_code
                    )

                with open(temp_pdf, mode="wb") as f:
                    f.write(r.content)
                self.file_path = str(temp_pdf)
        elif not os.path.isfile(self.file_path):
            raise ValueError("File path %s is not a valid file or url" % self.file_path)

    def __del__(self) -> None:
        if hasattr(self, "temp_dir"):
            self.temp_dir.cleanup()

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if the url is valid."""
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    @staticmethod
    def _is_s3_url(url: str) -> bool:
        """check if the url is S3"""
        try:
            result = urlparse(url)
            if result.scheme == "s3" and result.netloc:
                return True
            return False
        except ValueError:
            return False

    @staticmethod
    def _is_s3_presigned_url(url: str) -> bool:
        """Check if the url is a presigned S3 url."""
        try:
            result = urlparse(url)
            return bool(re.search(r"\.s3\.amazonaws\.com$", result.netloc))
        except ValueError:
            return False

    @property
    def source(self) -> str:
        return self.web_path if self.web_path is not None else self.file_path


class PyMuPDF4LLMLoader(BasePDFLoader):
    """Load and parse a PDF file to markdown using 'PyMuPDF4LLM' library.

    This class provides methods to load and parse PDF documents to markdown content,
    supporting various configurations such as handling password-protected files,
    extracting images in form of text, defining table extraction strategy and
    defining content extraction mode. It integrates the `PyMuPDF4LLM` library to
    extract PDF content in markdown format and
    offers both synchronous and asynchronous document loading.

    Examples:
        Setup:

        .. code-block:: bash

            pip install -U langchain-pymupdf4llm

        Instantiate the loader:

        .. code-block:: python

            from langchain_pymupdf4llm import PyMuPDF4LLMLoader

            loader = PyMuPDF4LLMLoader(
                file_path = "./example_data/layout-parser-paper.pdf",
                # headers = None
                # password = None,
                mode = "single",
                pages_delimiter = "\\n\\f",
                # extract_images = True,
                # images_parser = TesseractBlobParser(),
                # table_strategy = "lines",
            )

        Lazy load documents:

        .. code-block:: python

            docs = []
            docs_lazy = loader.lazy_load()

            for doc in docs_lazy:
                docs.append(doc)
            print(docs[0].page_content[:100])
            print(docs[0].metadata)

        Load documents asynchronously:

        .. code-block:: python

            docs = await loader.aload()
            print(docs[0].page_content[:100])
            print(docs[0].metadata)
    """

    def __init__(
        self,
        file_path: Union[str, PurePath],
        *,
        password: Optional[str] = None,
        mode: Literal["single", "page"] = "page",
        pages_delimiter: str = _DEFAULT_PAGES_DELIMITER,
        extract_images: bool = False,
        images_parser: Optional[BaseBlobParser] = None,
        table_strategy: Literal["lines_strict", "lines", "text"] = "lines_strict",
        ignore_code: bool = False,
        headers: Optional[dict] = None,
    ) -> None:
        """Initialize with a file path.

        Args:
            file_path: The path to the PDF file to be loaded.
            headers: Optional headers to use for GET request to download a file from a
              web path.
            password: Optional password for opening encrypted PDFs.
            mode: The extraction mode, either "single" for the entire document or "page"
                for page-wise extraction.
            pages_delimiter: A string delimiter to separate pages in single-mode
                extraction.
            extract_images: Whether to extract images from the PDF.
            images_parser: Optional image blob parser.
            table_strategy: The table extraction strategy to use. Options are
                "lines_strict", "lines", or "text". "lines_strict" is the default
                strategy and is the most accurate for tables with column and row lines,
                but may not work well with all documents.
                "lines" is a less strict strategy that may work better with
                some documents.
                "text" is the least strict strategy and may work better
                with documents that do not have tables with lines.
            ignore_code: if True then mono-spaced text will not be parsed as
                code blocks.

        Returns:
            This method does not directly return data. Use the `load`, `lazy_load`, or
            `aload` methods to retrieve parsed documents with markdown content and
            metadata.

        Raises:
            ValueError: If the `mode` argument is not one of "single" or "page".
            ValueError: If the `table_strategy` argument is not one of "lines_strict",
                "lines", or "text".
        """

        if mode not in ["single", "page"]:
            raise ValueError("mode must be single or page")
        if table_strategy not in ["lines_strict", "lines", "text"]:
            raise ValueError("table_strategy must be lines_strict, lines or text")

        super().__init__(file_path, headers=headers)
        self.parser = PyMuPDF4LLMParser(
            password=password,
            mode=mode,
            pages_delimiter=pages_delimiter,
            extract_images=extract_images,
            images_parser=images_parser,
            table_strategy=table_strategy,
            ignore_code=ignore_code,
        )

    def _lazy_load(self, **kwargs: Any) -> Iterator[Document]:
        """Lazily parse a blob from a PDF document.

        Args:
            blob: The blob from a PDF document to parse.

        Yield:
            An iterator over the parsed documents with PDF content.
        """
        if kwargs:
            logger.warning(
                f"Received runtime arguments {kwargs}. Passed runtime args to `load`"
                " are completely ignored."
                " Please pass arguments during initialization instead."
            )
        if self.web_path:
            blob = Blob.from_data(open(self.file_path, "rb").read(), path=self.web_path)
        else:
            blob = Blob.from_path(self.file_path)
        yield from self.parser.lazy_parse(blob)

    def load(self, **kwargs: Any) -> list[Document]:
        return list(self._lazy_load(**kwargs))

    def lazy_load(self) -> Iterator[Document]:
        yield from self._lazy_load()
