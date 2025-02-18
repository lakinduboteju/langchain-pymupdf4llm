FROM python:3.9-slim

RUN apt update -y
# Build tools are used for pymupdf during installation
RUN apt install -y --no-install-recommends build-essential

# Install Poetry
RUN pip install -U poetry

# Cleanup
RUN rm -rf /var/lib/apt/lists/*
