"""PyBencher - decorator-based benchmarking suite for Python."""

from importlib.metadata import PackageNotFoundError, version

from .core import BenchmarkResult, BenchmarkResults, Suite

__all__ = ["Suite", "BenchmarkResult", "BenchmarkResults", "__version__"]

try:
    __version__: str = version("pybencher")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"
