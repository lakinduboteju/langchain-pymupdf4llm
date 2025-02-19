"""Contains PyMuPDF4LLM parser class to parse blobs from PDFs."""

import logging
import re
import threading
from datetime import datetime
from tempfile import TemporaryDirectory
from typing import (
    Any,
    Iterator,
    Literal,
    Optional,
)

from langchain_core.documents import Document
from langchain_core.document_loaders import (
    Blob,
    BaseBlobParser
)

import pymupdf


_DEFAULT_PAGES_DELIMITER = "\n-----\n\n"
_STD_METADATA_KEYS = {"source", "total_pages", "creationdate", "creator", "producer"}


logger = logging.getLogger(__name__)


def _validate_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Validate that the metadata has all the standard keys and the page is an integer.

    The standard keys are:
    - source
    - total_page
    - creationdate
    - creator
    - producer

    Validate that page is an integer if it is present.
    """
    if not _STD_METADATA_KEYS.issubset(metadata.keys()):
        raise ValueError("The PDF parser must valorize the standard metadata.")
    if not isinstance(metadata.get("page", 0), int):
        raise ValueError("The PDF metadata page must be a integer.")
    return metadata


def _purge_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Purge metadata from unwanted keys and normalize key names.

    Args:
        metadata: The original metadata dictionary.

    Returns:
        The cleaned and normalized the key format of metadata dictionary.
    """
    new_metadata: dict[str, Any] = {}
    map_key = {
        "page_count": "total_pages",
        "file_path": "source",
    }
    for k, v in metadata.items():
        if type(v) not in [str, int]:
            v = str(v)
        if k.startswith("/"):
            k = k[1:]
        k = k.lower()
        if k in ["creationdate", "moddate"]:
            try:
                new_metadata[k] = datetime.strptime(
                    v.replace("'", ""), "D:%Y%m%d%H%M%S%z"
                ).isoformat("T")
            except ValueError:
                new_metadata[k] = v
        elif k in map_key:
            # Normalize key with others PDF parser
            new_metadata[map_key[k]] = v
            new_metadata[k] = v
        elif isinstance(v, str):
            new_metadata[k] = v.strip()
        elif isinstance(v, int):
            new_metadata[k] = v
    return new_metadata


class PyMuPDF4LLMParser(BaseBlobParser):
    """Parse a blob from a PDF using `PyMuPDF4LLM` library.

    This class provides methods to parse a blob from a PDF document to
    extract the content in markdown, supporting various
    configurations such as handling password-protected PDFs,
    extracting images in form of text,
    defining table extraction strategy and content extraction mode.
    It integrates the 'PyMuPDF4LLM' library to extract PDF content in markdown format,
    and offers synchronous blob parsing.

    Examples:
        Setup:

        .. code-block:: bash

            pip install -U langchain-pymupdf4llm

        Load a blob from a PDF file:

        .. code-block:: python

            from langchain_core.documents.base import Blob

            blob = Blob.from_path("./example_data/layout-parser-paper.pdf")

        Instantiate the parser:

        .. code-block:: python

            from langchain_pymupdf4llm import PyMuPDF4LLMParser

            parser = PyMuPDF4LLMParser(
                # password = None,
                mode = "single",
                pages_delimiter = "\\n\\f",
                # images_parser = TesseractBlobParser(),
                # table_strategy = "lines",
            )

        Lazily parse the blob:

        .. code-block:: python

            docs = []
            docs_lazy = parser.lazy_parse(blob)

            for doc in docs_lazy:
                docs.append(doc)
            print(docs[0].page_content[:100])
            print(docs[0].metadata)
    """

    # PyMuPDF is not thread safe.
    # See https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html
    _lock = threading.Lock()

    def __init__(
        self,
        extract_images: bool = False,
        *,
        password: Optional[str] = None,
        mode: Literal["single", "page"] = "page",
        pages_delimiter: str = _DEFAULT_PAGES_DELIMITER,
        images_parser: Optional[BaseBlobParser] = None,
        table_strategy: Literal["lines_strict", "lines", "text"] = "lines_strict",
        ignore_code: bool = False,
    ) -> None:
        """Initialize a parser to extract PDF content in markdown using PyMuPDF4LLM.

        Args:
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
            This method does not directly return data. Use the `parse` or `lazy_parse`
            methods to retrieve parsed documents with content and metadata.

        Raises:
            ValueError: If the mode is not "single" or "page".
            ValueError: If the table strategy is not "lines_strict", "lines", or "text".
            ValueError: If `extract_images` is True and `images_parser` is not provided.
        """

        if mode not in ["single", "page"]:
            raise ValueError("mode must be single or page")
        if table_strategy not in ["lines_strict", "lines", "text"]:
            raise ValueError("table_strategy must be lines_strict, lines or text")
        if extract_images and not images_parser:
            raise ValueError("images_parser must be provided if extract_images is True")

        super().__init__()

        self.mode = mode
        self.pages_delimiter = pages_delimiter
        self.password = password
        self.extract_images = extract_images
        self.images_parser = images_parser
        self.table_strategy = table_strategy
        self.ignore_code = ignore_code

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        """Lazily parse a blob from a PDF document.

        Args:
            blob: The blob from a PDF document to parse.

        Raises:
            ImportError: If the `pymupdf4llm` package is not found.

        Yield:
            An iterator over the parsed documents with PDF content.
        """
        try:
            import pymupdf
            import pymupdf4llm  # noqa  # pylint: disable=unused-import
        except ImportError:
            raise ImportError(
                "pymupdf4llm package not found, please install it "
                "with `pip install pymupdf4llm`"
            )

        with PyMuPDF4LLMParser._lock:
            with blob.as_bytes_io() as file_path:
                if blob.data is None:
                    doc = pymupdf.open(file_path)
                else:
                    doc = pymupdf.open(stream=file_path, filetype="pdf")
                if doc.is_encrypted:
                    doc.authenticate(self.password)
                doc_metadata = self._extract_metadata(doc, blob)
                full_content_md = []
                for page in doc:
                    all_text_md = self._get_page_content_in_md(doc, page.number)
                    if all_text_md.endswith("\n-----\n\n"):
                        all_text_md = all_text_md[:-8]
                    if self.mode == "page":
                        yield Document(
                            page_content=all_text_md,
                            metadata=_validate_metadata(
                                doc_metadata | {"page": page.number}
                            ),
                        )
                    else:
                        full_content_md.append(all_text_md)

                if self.mode == "single":
                    yield Document(
                        page_content=self.pages_delimiter.join(full_content_md),
                        metadata=_validate_metadata(doc_metadata),
                    )

    def _get_page_content_in_md(
        self,
        doc: pymupdf.Document,
        page: int,
    ) -> str:
        """Get the content of the page in markdown using PyMuPDF4LLM and RapidOCR.

        Args:
            doc: The PyMuPDF document object.
            page: The page index.

        Returns:
            str: The content of the page in markdown.
        """
        import pymupdf4llm

        pymupdf4llm_params: dict[str, Any] = {}
        if self.extract_images:
            temp_dir = TemporaryDirectory()
            pymupdf4llm_params["write_images"] = True
            pymupdf4llm_params["image_path"] = temp_dir.name

            def find_img_paths_in_md(md_text: str) -> list[str]:
                md_img_pattern = r"!\[\]\((.*?)\)"  # Regex pattern to match ![](%s)
                img_paths = re.findall(md_img_pattern, md_text)
                return img_paths

        # Extract the content of the page in markdown format using PyMuPDF4LLM
        page_content_md = pymupdf4llm.to_markdown(
            doc,
            pages=[page],
            ignore_code=self.ignore_code,
            graphics_limit=5000,  # to deal with excess amounts of vector graphics
            table_strategy=self.table_strategy,
            show_progress=False,
            **pymupdf4llm_params,
        )

        if self.extract_images and self.images_parser:
            # Replace image paths in extracted markdown with
            # generated image text/descriptions using image parser
            img_paths = find_img_paths_in_md(page_content_md)
            for img_path in img_paths:
                blob = Blob.from_path(img_path)
                image_text = next(self.images_parser.lazy_parse(blob)).page_content
                image_text = image_text.replace("]", r"\\]")
                img_md = f"![{image_text}](#)"
                page_content_md = page_content_md.replace(f"![]({img_path})", img_md)

        return page_content_md

    def _extract_metadata(self, doc: pymupdf.Document, blob: Blob) -> dict:
        """Extract metadata from the PDF document.

        Args:
            doc: The PyMuPDF document object.
            blob: The blob being parsed.

        Returns:
            dict: The extracted metadata from the PDF.
        """
        metadata = _purge_metadata(
            {
                **{
                    "producer": "PyMuPDF4LLM",
                    "creator": "PyMuPDF4LLM",
                    "creationdate": "",
                    "source": blob.source,
                    "file_path": blob.source,
                    "total_pages": len(doc),
                },
                **{
                    k: doc.metadata[k]
                    for k in doc.metadata
                    if isinstance(doc.metadata[k], (str, int))
                },
            }
        )
        for k in ("modDate", "creationDate"):
            if k in doc.metadata:
                metadata[k] = doc.metadata[k]
        return metadata
