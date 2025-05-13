"""Contains PyMuPDF4LLM parser class to parse blobs from PDFs."""

import logging
import re
import threading
import os
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
        **pymupdf4llm_kwargs,
    ) -> None:
        """Initialize a parser to extract PDF content in markdown using PyMuPDF4LLM.

        Args:
            password: Optional password for opening encrypted PDFs.
            mode: The extraction mode, either "single" for the entire document or "page"
                for page-wise extraction.
            pages_delimiter: A string delimiter to separate pages in single-mode
                extraction.
            extract_images: Whether to extract images from the PDF. If True, requires
                `images_parser` to be set.
            images_parser: Optional image blob parser to process extracted images.
                Required if `extract_images` is True.
            **pymupdf4llm_kwargs: Additional keyword arguments to pass directly to the
                `pymupdf4llm.to_markdown` function. See the `pymupdf4llm`
                documentation for available options. Note that certain arguments
                (`ignore_images`, `ignore_graphics`, `write_images`, `embed_images`,
                `image_path`, `filename`, `page_chunks`, `extract_words`,
                `show_progress`) cannot be used as they conflict with the parser's
                internal logic.

        Returns:
            This method does not directly return data. Use the `parse` or `lazy_parse`
            methods to retrieve parsed documents with content and metadata.

        Raises:
            ValueError: If the mode is not "single" or "page".
            ValueError: If `extract_images` is True and `images_parser` is not provided.
            ValueError: If conflicting `pymupdf4llm_kwargs` are provided when
                `extract_images` is True (e.g., `ignore_images`, `ignore_graphics`,
                `write_images`, `embed_images`, `image_path`, `filename`).
            ValueError: If unsupported `pymupdf4llm_kwargs` are provided (e.g.,
                `page_chunks`, `extract_words`, `show_progress`).
        """

        if mode not in ["single", "page"]:
            raise ValueError("mode must be single or page")
        if extract_images and not images_parser:
            raise ValueError("images_parser must be provided if extract_images is True")
        # Prevent conflict with the parser's image extraction logic
        if extract_images and "ignore_images" in pymupdf4llm_kwargs:
            raise ValueError(
                "PyMuPDF4LLM argument: ignore_images cannot be set to True "
                "when extract_images is True."
            )
        # Prevent conflict with the parser's image extraction logic
        if extract_images and "ignore_graphics" in pymupdf4llm_kwargs:
            raise ValueError(
                "PyMuPDF4LLM argument: ignore_graphics cannot be set to True "
                "when extract_images is True."
            )
        # Parser handles image writing internally when extract_images is True
        if "write_images" in pymupdf4llm_kwargs:
            raise ValueError("PyMuPDF4LLM argument: write_images cannot be set to True.")
        # Parser does not support embedding images directly
        if "embed_images" in pymupdf4llm_kwargs:
            raise ValueError("PyMuPDF4LLM argument: embed_images cannot be set to True.")
        # Parser manages temporary image paths internally when extract_images is True
        if "image_path" in pymupdf4llm_kwargs:
            raise ValueError("PyMuPDF4LLM argument: image_path cannot be set to True.")
        # Parser manages image filenames internally when extract_images is True
        if "filename" in pymupdf4llm_kwargs:
            raise ValueError("PyMuPDF4LLM argument: filename cannot be set to True.")
        # Parser controls page handling via the 'mode' argument
        if "page_chunks" in pymupdf4llm_kwargs:
            raise ValueError("PyMuPDF4LLM argument: page_chunks cannot be set to True.")
        # Parser expects markdown output, not word-level extraction
        if "extract_words" in pymupdf4llm_kwargs:
            raise ValueError("PyMuPDF4LLM argument: extract_words cannot be set to True.")
        # Parser manages progress display internally
        if "show_progress" in pymupdf4llm_kwargs:
            raise ValueError("PyMuPDF4LLM argument: show_progress cannot be set to True.")

        super().__init__()

        self.mode = mode
        self.pages_delimiter = pages_delimiter
        self.password = password
        self.extract_images = extract_images
        self.images_parser = images_parser
        self.pymupdf4llm_kwargs = pymupdf4llm_kwargs

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

        pymupdf4llm_params: dict[str, Any] = {
            **self.pymupdf4llm_kwargs,
        }

        # To deal with excess amounts of vector graphics
        if "graphics_limit" not in self.pymupdf4llm_kwargs:
            pymupdf4llm_params["graphics_limit"] = 5000

        page_content_md = "" # Initialize page_content_md

        if self.extract_images and self.images_parser:
            with TemporaryDirectory() as temp_dir:
                pymupdf4llm_params["write_images"] = True
                pymupdf4llm_params["image_path"] = temp_dir

                def find_img_paths_in_md(md_text: str) -> list[str]:
                    # Regex pattern to match ![](%s)
                    md_img_pattern = r"!\[\]\((.*?)\)"
                    img_paths = re.findall(md_img_pattern, md_text)
                    return img_paths

                page_content_md = pymupdf4llm.to_markdown(
                    doc,
                    pages=[page],
                    show_progress=False,
                    **pymupdf4llm_params,
                )

                # Replace image paths in extracted markdown with
                # generated image text/descriptions using image parser
                img_paths = find_img_paths_in_md(page_content_md)
                for img_path in img_paths:
                    # Check if the image file actually exists before processing
                    if os.path.exists(img_path):
                        blob = Blob.from_path(img_path)
                        image_text = next(self.images_parser.lazy_parse(blob)).page_content
                        image_text = image_text.replace("]", r"\\]")
                        img_md = f"![{image_text}](#)"
                        page_content_md = page_content_md.replace(f"![]({img_path})", img_md)
                    else:
                        logger.warning(f"Image path referenced in markdown but not found: {img_path}")

        else:
            # Extract the content of the page in markdown format using PyMuPDF4LLM
            # when not extracting images
            page_content_md = pymupdf4llm.to_markdown(
                doc,
                pages=[page],
                show_progress=False,
                **pymupdf4llm_params,
            )


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
