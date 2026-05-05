.PHONY: build upload test lint mypy clean

# Building and Uploading
build:
	uv build

upload: build
	uv publish

# Testing and Quality
test:
	uv run pytest

cover:
	uv run pytest tests/ --cov src --cov-report term-missing

ruff:
	uv run ruff format && uv run ruff check

mypy:
	uv run mypy

format: ruff mypy

# Cleanup
clean:
	python -c "import shutil, os; [shutil.rmtree(p) for p in ['dist', 'build', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'src/pybencher.egg-info'] if os.path.exists(p)]"