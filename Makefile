.PHONY: build upload test lint mypy clean

# Building and Uploading
build:
	uv build

upload: build
	uv publish

# Testing and Quality
test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

mypy:
	uv run mypy

# Cleanup
clean:
	python -c "import shutil, os; [shutil.rmtree(p) for p in ['dist', 'build', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'src/pybencher.egg-info'] if os.path.exists(p)]"