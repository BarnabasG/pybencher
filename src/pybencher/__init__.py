"""PyBencher - decorator-based benchmarking suite for Python."""

from importlib.metadata import version

from .core import BenchmarkResult, BenchmarkResults, Suite

__all__ = ["Suite", "BenchmarkResult", "BenchmarkResults", "__version__"]
__version__: str = version("pybencher")
