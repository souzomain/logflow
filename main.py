"""
Main entry point for LogFlow.
"""
import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from logflow.cli.commands import cli


if __name__ == "__main__":
    cli(obj={})