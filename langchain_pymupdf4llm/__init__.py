"""Main entrypoint to **langchain-pymupdf4llm** package.
"""

from importlib import metadata

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)

from .pymupdf4llm_loader import PyMuPDF4LLMLoader
from .pymupdf4llm_parser import PyMuPDF4LLMParser
