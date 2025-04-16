"""
Tests for the CLI.
"""
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from logflow.cli.commands import cli


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as f:
        f.write("""
name: test-pipeline
sources:
  - name: test-source
    type: FileSource
    config:
      path: /tmp/test.log
sinks:
  - name: test-sink
    type: FileSink
    config:
      path: /tmp/output.log
""")
        path = f.name
    
    yield path
    
    # Clean up
    os.unlink(path)


def test_cli_start(temp_config_file):
    """Test the start command."""
    runner = CliRunner()
    
    # Mock the asyncio.run function
    with patch("asyncio.run") as mock_run:
        # Run the command
        result = runner.invoke(cli, ["start", "--config", temp_config_file])
        
        # Check the result
        assert result.exit_code == 0
        assert mock_run.called


def test_cli_start_nonexistent_config():
    """Test the start command with a nonexistent configuration file."""
    runner = CliRunner()
    
    # Run the command
    result = runner.invoke(cli, ["start", "--config", "/nonexistent/file.yaml"])
    
    # Check the result
    assert result.exit_code == 1
    assert "Error: Configuration file not found" in result.output


def test_cli_status():
    """Test the status command."""
    runner = CliRunner()
    
    # Mock the engine
    mock_engine = MagicMock()
    mock_engine.get_pipeline_names.return_value = ["pipeline1", "pipeline2"]
    mock_engine.get_pipeline_status.side_effect = lambda name: {
        "pipeline1": {
            "name": "pipeline1",
            "running": True,
            "sources": 1,
            "processors": 2,
            "sinks": 1,
            "events_processed": 100,
            "events_dropped": 10,
            "processing_errors": 5,
            "uptime": 60
        },
        "pipeline2": {
            "name": "pipeline2",
            "running": False,
            "sources": 2,
            "processors": 1,
            "sinks": 2,
            "events_processed": 50,
            "events_dropped": 5,
            "processing_errors": 2,
            "uptime": 0
        }
    }[name]
    
    # Run the command
    with patch("logflow.cli.commands.Engine", return_value=mock_engine):
        result = runner.invoke(cli, ["status"])
    
    # Check the result
    assert result.exit_code == 0
    assert "pipeline1: RUNNING" in result.output
    assert "pipeline2: STOPPED" in result.output
    assert "Events: 100 processed, 10 dropped, 5 errors" in result.output
    assert "Events: 50 processed, 5 dropped, 2 errors" in result.output
    assert "Uptime: 60.00 seconds" in result.output


def test_cli_status_no_pipelines():
    """Test the status command with no pipelines."""
    runner = CliRunner()
    
    # Mock the engine
    mock_engine = MagicMock()
    mock_engine.get_pipeline_names.return_value = []
    
    # Run the command
    with patch("logflow.cli.commands.Engine", return_value=mock_engine):
        result = runner.invoke(cli, ["status"])
    
    # Check the result
    assert result.exit_code == 0
    assert "No pipelines are running" in result.output


def test_cli_restart():
    """Test the restart command."""
    runner = CliRunner()
    
    # Mock the asyncio.run function
    with patch("asyncio.run") as mock_run:
        # Run the command
        result = runner.invoke(cli, ["restart", "test-pipeline"])
        
        # Check the result
        assert result.exit_code == 0
        assert mock_run.call_count == 2  # Once for stop, once for start


def test_cli_restart_nonexistent_pipeline():
    """Test the restart command with a nonexistent pipeline."""
    runner = CliRunner()
    
    # Mock the asyncio.run function to raise KeyError
    with patch("asyncio.run", side_effect=KeyError("Pipeline not found")):
        # Run the command
        result = runner.invoke(cli, ["restart", "nonexistent-pipeline"])
        
        # Check the result
        assert result.exit_code == 1
        assert "Error: Pipeline not found" in result.output