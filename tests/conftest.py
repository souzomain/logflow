"""
Pytest configuration for LogFlow tests.
"""
import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure pytest
pytest_plugins = [
    "pytest_asyncio",
]