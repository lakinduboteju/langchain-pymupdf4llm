# langchain-pymupdf4llm
## An integration package connecting PyMuPDF4LLM to LangChain

### Development

1. Bring up development environment on Docker.
    ``` bash
    bash ./docker_run_dev_env.sh
    docker exec -it langchain-pymupdf4llm-dev bash
    pip install poetry

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
