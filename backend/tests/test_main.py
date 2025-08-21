"""Tests for main module."""

import pytest
from src.main import main


def test_main(capsys):
    """Test main function."""
    main()
    captured = capsys.readouterr()
    assert "Hello from line-drive-ai!" in captured.out
