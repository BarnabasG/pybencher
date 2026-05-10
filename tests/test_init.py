from unittest.mock import patch
from importlib.metadata import PackageNotFoundError


def test_version_fallback() -> None:
    """Verify __version__ fallback when package is not installed."""
    import pybencher
    import importlib.metadata

    with patch("importlib.metadata.version", side_effect=PackageNotFoundError):
        importlib.reload(pybencher)
        assert pybencher.__version__ == "0.0.0-dev"

    importlib.reload(pybencher)  # Cleanup
