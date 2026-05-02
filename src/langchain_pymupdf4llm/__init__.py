"""Main entrypoint for the ``langchain-pymupdf4llm`` package."""

from importlib import metadata

from langchain_pymupdf4llm.pymupdf4llm_loader import PyMuPDF4LLMLoader
from langchain_pymupdf4llm.pymupdf4llm_parser import PyMuPDF4LLMParser

try:
    __version__ = metadata.version(__package__ or "langchain-pymupdf4llm")
except metadata.PackageNotFoundError:
    __version__ = ""

__all__ = ["PyMuPDF4LLMLoader", "PyMuPDF4LLMParser", "__version__"]
