"""Provide tests for project version."""
from fluidstate import __version__


def test_version() -> None:
    """Test project metadata version."""
    assert __version__ == '1.3.1a0'
