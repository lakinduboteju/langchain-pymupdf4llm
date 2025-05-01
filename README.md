# langchain-pymupdf4llm
An integration package connecting PyMuPDF4LLM to LangChain as a Document Loader.

## Introduction
`langchain-pymupdf4llm` is a powerful LangChain integration package that
seamlessly incorporates the capabilities of PyMuPDF4LLM as a LangChain Document Loader.
This package is designed to facilitate the process of extracting and
converting PDF content into Markdown format,
making it an ideal tool for integrating with Large Language Models (LLMs) and
Retrieval-Augmented Generation (RAG) environments.

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

## Installation

Install the package using pip to start using the Document Loader:

```bash
pip install -U langchain-pymupdf4llm
# pip install -qU langchain_community
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

## Contribute

### Development Instructions

1. Bring up development environment on Docker.
    ``` bash
    # Build Docker image for dev env
    bash ./docker_build_dev_env.sh

    # Run dev env on Docker container
    bash ./docker_run_dev_env.sh

    # Start bash session on Docker container
    docker exec -it langchain-pymupdf4llm-dev bash

    # exit
    # docker stop langchain-pymupdf4llm-dev
    # docker start langchain-pymupdf4llm-dev
    # docker exec -it langchain-pymupdf4llm-dev bash
    # docker stop langchain-pymupdf4llm-dev
    # docker rm langchain-pymupdf4llm-dev
    # bash ./docker_run_dev_env.sh
    ```

2. Develop on Docker development environment.
    ``` bash
    poetry install --with dev,test
    ```

3. Create example documents for tests using LaTeX.
    ``` bash
    apt update -y
    apt install -y texlive

    cd ./tests/examples
    pdflatex sample_1.tex
    ```

4. Use Jupyter.
    ``` bash
    poetry run \
    jupyter notebook --allow-root --ip=0.0.0.0
    ```
