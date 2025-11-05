# langchain-pymupdf4llm
An integration package connecting PyMuPDF4LLM to LangChain as a Document Loader.

[![LangChain v1.0+](https://img.shields.io/badge/LangChain-v1.0+-blue)](https://github.com/langchain-ai/langchain)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Introduction
`langchain-pymupdf4llm` is a powerful LangChain integration package that
seamlessly incorporates the capabilities of PyMuPDF4LLM as a LangChain Document Loader.
This package is designed to facilitate the process of extracting and
converting PDF content into Markdown format,
making it an ideal tool for integrating with Large Language Models (LLMs) and
Retrieval-Augmented Generation (RAG) environments.

**✨ Now fully compatible with LangChain v1.0+ and LangGraph v1.0+!**

## Features

The core functionality of this integration relies on PyMuPDF4LLM,
which is designed to convert PDF pages to Markdown using the robust PyMuPDF library.
Key features inherited from PyMuPDF4LLM include:

- **Markdown Extraction:** Converts standard text and tables into GitHub-compatible Markdown format.
- **Advanced Formatting:** Detects and formats headers based on font size, bold and italic text, mono-spaced text, code blocks, as well as ordered and unordered lists.
- **Multi-Column and Graphics Support:** Easily manages multi-column pages and extracts images and vector graphics.

For more detailed information on PyMuPDF4LLM, visit the [official documentation webpage](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm).

The integration provided by `langchain-pymupdf4llm` adds additional features:

- **Markdown Content with Image Descriptions:** When image extraction is enabled, images are included in the Markdown output with descriptive text provided by an image parser instance provided during initialization of the Document Loader.

## Requirements

- Python 3.11 or higher
- LangChain Core v1.0.0 or higher
- LangGraph v1.0.0 or higher
- PyMuPDF4LLM v0.1.0 or higher

## Installation

Install the package using pip to start using the Document Loader:

```bash
pip install -U langchain-pymupdf4llm
```

For optional image parsing capabilities, you may also want to install:

```bash
# For OCR-based image parsing
pip install langchain-community
```

## Usage

You can easily integrate and use the `PyMuPDF4LLMLoader` in your Python application for loading and parsing PDFs. Below is an example of how to set up and utilize this loader.

### Import and Instantiate the Loader

Begin by importing the necessary class and creating an instance of `PyMuPDF4LLMLoader`:

```python
from langchain_pymupdf4llm import PyMuPDF4LLMLoader

# from langchain_community.document_loaders.parsers import (
#     TesseractBlobParser,
#     RapidOCRBlobParser,
#     LLMImageBlobParser,
# )

loader = PyMuPDF4LLMLoader(
    file_path="/path/to/input.pdf",
    # Headers to use for GET request to download a file from a web path
    # (if file_path is a web url)
    ## headers=None,

    # Password for opening encrypted PDF
    ## password=None,

    # Extraction mode, either "single" for the entire document or
    # "page" for page-wise extraction.
    mode="single",

    # Delimiter to separate pages in single-mode extraction
    # default value is "\n-----\n\n"
    pages_delimiter="\n\f",

    # Enable images extraction (as text based on images_parser)
    ## extract_images=True,

    # Image parser generates text for a provided image blob
    ## images_parser=TesseractBlobParser(),
    ## images_parser=RapidOCRBlobParser(),
    ## images_parser=LLMImageBlobParser(model=ChatOpenAI(
    ##     model="gpt-4o-mini",
    ##     max_tokens=1024
    ## )),

    # Additional keyword arguments to pass directly to the
    # underlying `pymupdf4llm.to_markdown` function.
    # See the `pymupdf4llm` documentation for available options.
    # Note that certain arguments (`ignore_images`, `ignore_graphics`,
    # `write_images`, `embed_images`, `image_path`, `filename`,
    # `page_chunks`, `extract_words`, `show_progress`) cannot be used as
    # they conflict with the loader's internal logic.
    # Example:
    # **{
    #     # Table extraction strategy to use. Options are
    #     # "lines_strict", "lines", or "text". "lines_strict" is the default
    #     # strategy and is the most accurate for tables with column and row lines,
    #     # but may not work well with all documents.
    #     # "lines" is a less strict strategy that may work better with
    #     # some documents.
    #     # "text" is the least strict strategy and may work better
    #     # with documents that do not have tables with lines.
    #     "table_strategy": "lines",
    #
    #     # Mono-spaced text will not be parsed as code blocks
    #     "ignore_code": True,
    # }
)
```

### Lazy Load Documents

Use the `lazy_load()` method to load documents efficiently.
This approach saves resources by loading pages on-demand:

```python
docs = []
docs_lazy = loader.lazy_load()

for doc in docs_lazy:
    docs.append(doc)
print(docs[0].page_content[:100])
print(docs[0].metadata)
```

### Asynchronous Loading

For applications that benefit from asynchronous operations,
load documents using the `aload()` method:

```python
docs = await loader.aload()
print(docs[0].page_content[:100])
print(docs[0].metadata)
```

### Using the Parser

```python
from langchain_community.document_loaders import FileSystemBlobLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_pymupdf4llm import PyMuPDF4LLMParser

loader = GenericLoader(
    blob_loader=FileSystemBlobLoader(
        path="path/to/docs/",
        glob="*.pdf",
    ),
    blob_parser=PyMuPDF4LLMParser(),
)
```

## Development

### Development using Docker

This project uses Docker for a consistent development environment. Follow these steps to get started:

1. **Build the Docker development environment:**
   ```bash
   bash ./docker_build_dev_env.sh
   ```

2. **Run the development container:**
   ```bash
   bash ./docker_run_dev_env.sh
   ```

3. **Access the container:**
   ```bash
   docker exec -it langchain-pymupdf4llm-dev bash
   ```

4. **Install dependencies inside the container:**
   ```bash
   poetry install --with dev,test
   ```

5. **Run tests:**
   ```bash
   poetry run pytest -v
   ```

6. **Build the package:**
   ```bash
   poetry build
   ```

### Managing the Docker Container

```bash
# Stop the container
docker stop langchain-pymupdf4llm-dev

# Start the container again
docker start langchain-pymupdf4llm-dev

# Remove the container
docker rm langchain-pymupdf4llm-dev
```

### Creating Test Documents

To create example PDF documents for testing using LaTeX:

```bash
apt update -y
apt install -y texlive

cd ./tests/examples
pdflatex sample_1.tex
```

### Using Jupyter Notebooks

To use Jupyter notebooks for development and testing:

```bash
poetry run jupyter notebook --allow-root --ip=0.0.0.0
```

## Contribute

We welcome contributions! Please feel free to submit issues and pull requests on our [GitHub repository](https://github.com/lakinduboteju/langchain-pymupdf4llm).
