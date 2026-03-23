#!/bin/bash

set -euo pipefail

CONTAINER_NAME="langchain-pymupdf4llm-dev"
IMAGE_NAME="langchain-pymupdf4llm-dev:latest"
DOCKER_ARGS=(
    -it
    -d
    --name "${CONTAINER_NAME}"
    -v "$(pwd):/app"
    -w /app
    -p 5678:5678
    -p 8888:8888
)

if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}$"; then
    echo "Container '${CONTAINER_NAME}' already exists. Removing it first."
    docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

if [ -d "$HOME/.aws" ]; then
    DOCKER_ARGS+=(-v "$HOME/.aws:/root/.aws:ro")
fi

docker run "${DOCKER_ARGS[@]}" "${IMAGE_NAME}" bash

echo "Container '${CONTAINER_NAME}' is running."
echo "To install dependencies inside the container:"
echo "  uv sync --extra dev --extra test --extra notebooks"
