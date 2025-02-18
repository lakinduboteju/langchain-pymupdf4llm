# langchain-pymupdf4llm
## An integration package connecting PyMuPDF4LLM to LangChain

### Development

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
