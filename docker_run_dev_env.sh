#!/bin/bash

docker run -it -d \
    --name langchain-pymupdf4llm-dev \
    -v $(pwd):/app \
    -v $HOME/.aws:/root/.aws:ro \
    -w /app \
    -p 5678:5678 \
    -p 8888:8888 \
    langchain-pymupdf4llm-dev:latest \
    bash
