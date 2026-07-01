PYTHON ?= python3
DIST_DIR ?= dist

.PHONY: help clean build wheel sdist check publish-test publish

help:
	@echo "Available targets:"
	@echo "  make build   Build wheel and sdist into $(DIST_DIR)/"
	@echo "  make wheel   Build wheel only"
	@echo "  make sdist   Build source distribution only"
	@echo "  make check   Validate built artifacts with twine"
	@echo "  make publish-test  Build, validate, and upload to TestPyPI"
	@echo "  make publish Build, validate, and upload to PyPI"
	@echo "  make clean   Remove build artifacts"
	@echo ""
	@echo "Publishing notes:"
	@echo "  Set TWINE_PASSWORD to your API token"
	@echo "  Optional: set TWINE_USERNAME (default: __token__)"

clean:
	rm -rf $(DIST_DIR) build *.egg-info

build: clean
	uv build

wheel: clean
	uv build --wheel

sdist: clean
	uv build --sdist

check: build
	uvx twine check $(DIST_DIR)/*
