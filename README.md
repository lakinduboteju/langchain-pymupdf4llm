# langchain-pymupdf4llm
An independent LangChain integration package connecting PyMuPDF4LLM to LangChain as a document loader.

[![LangChain v1.0+](https://img.shields.io/badge/LangChain-v1.0+-blue)](https://github.com/langchain-ai/langchain)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Introduction
`langchain-pymupdf4llm` is a powerful LangChain integration package that
seamlessly incorporates the capabilities of PyMuPDF4LLM as a LangChain Document Loader.
This package is designed to facilitate the process of extracting and
converting PDF content into Markdown format,
making it an ideal tool for integrating with Large Language Models (LLMs) and
Retrieval-Augmented Generation (RAG) environments.

**✨ Now fully compatible with LangChain v1.0+!**

## Licensing
This package depends directly on `pymupdf4llm` / `pymupdf`, which are published
by Artifex under AGPL/commercial terms. Because this integration wraps that
stack directly, this repository is distributed under `AGPL-3.0-only`.

If you distribute software or provide a network service that uses this package,
you must evaluate your own AGPL compliance obligations. If you cannot comply
with the AGPL, obtain an appropriate commercial license for the PyMuPDF stack
from Artifex instead of relying on this package under the AGPL.

`langchain-core` remains MIT-licensed and is compatible with this package's
AGPL license. See `NOTICE` for third-party attribution details.

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
- PyMuPDF4LLM v1.27.2.1 up to, but not including, v1.28.0

## Installation

Install the package using pip to start using the Document Loader:

```bash
pip install -U langchain-pymupdf4llm
```

Before installing, make sure the AGPL/commercial licensing model of the
PyMuPDF stack works for your use case.

Optional extras:

```bash
# Optional image parser integrations
pip install -U "langchain-pymupdf4llm[community]"
```

## Licensing Correction For Existing Users
Earlier releases of this package were incorrectly labeled as MIT. The package
has always depended on the AGPL/commercial PyMuPDF stack, so existing users
should re-evaluate whether their usage and redistribution model is compatible
with that dependency chain.

Future corrective releases should:

1. keep the AGPL package metadata and repository license files aligned
2. clearly disclose the licensing correction in release notes
3. deprecate or supersede the incorrectly labeled release on package indexes where possible

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

    # Optional: toggle PyMuPDF layout mode when supported by
    # pymupdf4llm >= 1.27.2.1.
    ## use_layout=False,

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

### Quickstart (uv on host)

This repository uses [`uv`](https://docs.astral.sh/uv/) for local development.

```bash
uv sync --extra dev --extra test --extra notebooks
uv run ruff check .
uv run ruff format . --check
uv run mypy
uv run pytest -v
uv build
```

### Development Container (recommended)

This repository includes `.devcontainer/devcontainer.json`.

1. Open the repository in Cursor/VS Code.
2. Reopen in container when prompted.
3. The container runs `uv sync --extra dev --extra test --extra notebooks` automatically.

The dev container forwards:

- `5678` for `debugpy`
- `8888` for Jupyter notebooks

### Development using Docker scripts

If you prefer manual Docker commands:

1. Build the dev image:
   ```bash
   bash ./docker_build_dev_env.sh
   ```
2. Run the dev container:
   ```bash
   bash ./docker_run_dev_env.sh
   ```
3. Open a shell:
   ```bash
   docker exec -it langchain-pymupdf4llm-dev bash
   ```
4. Sync dependencies in the container:
   ```bash
   uv sync --extra dev --extra test --extra notebooks
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
uv run jupyter notebook --allow-root --ip=0.0.0.0
```

### Test markers

This project defines three pytest markers:

- `unit` for focused fast tests
- `integration` for end-to-end loader/parser behavior
- `network` for tests that require outbound HTTP access

By default, network tests are skipped via pytest config. To run them explicitly:

```bash
uv run pytest -v -m network
```

## Contribute

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development, testing, and release workflow details.
