"""
Tests for the file source.
"""
import os
import tempfile
from pathlib import Path

import pytest
import asyncio

from logflow.sources.file import FileSource
from logflow.core.models import LogEvent


@pytest.fixture
def temp_log_file():
    """Create a temporary log file."""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        f.write("line 1\n")
        f.write("line 2\n")
        f.write("line 3\n")
        path = f.name
    
    yield path
    
    # Clean up
    os.unlink(path)


@pytest.mark.asyncio
async def test_file_source_initialization():
    """Test initializing a file source."""
    source = FileSource()
    
    # Initialize with a valid configuration
    await source.initialize({
        "path": "/tmp/test.log",
        "tail": True,
        "read_from_start": True,
        "poll_interval": 0.1
    })
    
    assert source.path == "/tmp/test.log"
    assert source.tail is True
    assert source.read_from_start is True
    assert source.poll_interval == 0.1
    
    # Initialize with an invalid configuration (missing path)
    with pytest.raises(ValueError, match="File path is required"):
        await source.initialize({})


@pytest.mark.asyncio
async def test_file_source_read(temp_log_file):
    """Test reading from a file source."""
    source = FileSource()
    
    # Initialize with the temporary file
    await source.initialize({
        "path": temp_log_file,
        "tail": False,  # Don't tail the file
        "read_from_start": True,  # Read from the start
        "poll_interval": 0.1
    })
    
    # Read events from the source
    events = []
    async for event in source.read():
        events.append(event)
    
    # Check that we got the expected events
    assert len(events) == 3
    assert events[0].raw_data == "line 1"
    assert events[1].raw_data == "line 2"
    assert events[2].raw_data == "line 3"
    
    # Check event properties
    for event in events:
        assert event.source_type == "file"
        assert event.source_name == temp_log_file
        assert "file_path" in event.metadata
        assert "file_position" in event.metadata


@pytest.mark.asyncio
async def test_file_source_tail(temp_log_file):
    """Test tailing a file source."""
    source = FileSource()
    
    # Initialize with the temporary file
    await source.initialize({
        "path": temp_log_file,
        "tail": True,  # Tail the file
        "read_from_start": True,  # Read from the start
        "poll_interval": 0.1
    })
    
    # Start reading in a separate task
    read_task = asyncio.create_task(source.read().__anext__())
    
    # Wait a bit for the task to start
    await asyncio.sleep(0.2)
    
    # Append a new line to the file
    with open(temp_log_file, "a") as f:
        f.write("line 4\n")
    
    # Wait for the event
    event = await asyncio.wait_for(read_task, timeout=1.0)
    
    # Check the event
    assert event.raw_data == "line 1"
    
    # Stop the source
    await source.shutdown()