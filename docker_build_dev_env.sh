#!/bin/bash

set -euo pipefail

docker build -t langchain-pymupdf4llm-dev:latest -f dev.Dockerfile .
