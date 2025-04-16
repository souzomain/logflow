"""
Tests for the file sink.
"""
import os
import json
import tempfile
from datetime import datetime

import pytest

from logflow.sinks.file import FileSink
from logflow.core.models import LogEvent


@pytest.fixture
def temp_output_file():
    """Create a temporary output file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        path = f.name
    
    yield path
    
    # Clean up
    if os.path.exists(path):
        os.unlink(path)


@pytest.mark.asyncio
async def test_file_sink_initialization():
    """Test initializing a file sink."""
    sink = FileSink()
    
    # Initialize with a valid configuration
    with tempfile.NamedTemporaryFile(delete=False) as f:
        try:
            await sink.initialize({
                "path": f.name,
                "format": "json",
                "append": True
            })
            
            assert sink.path == f.name
            assert sink.format == "json"
            assert sink.append is True
            
            # Clean up
            await sink.shutdown()
        finally:
            os.unlink(f.name)
    
    # Initialize with an invalid configuration (missing path)
    with pytest.raises(ValueError, match="File path is required"):
        await sink.initialize({})
    
    # Initialize with an invalid format
    with pytest.raises(ValueError, match="Invalid format: invalid"):
        await sink.initialize({
            "path": "/tmp/test.log",
            "format": "invalid"
        })


@pytest.mark.asyncio
async def test_file_sink_write_json(temp_output_file):
    """Test writing events in JSON format."""
    sink = FileSink()
    
    # Initialize with the temporary file
    await sink.initialize({
        "path": temp_output_file,
        "format": "json",
        "append": True
    })
    
    # Create test events
    event1 = LogEvent(
        raw_data="test log message 1",
        source_type="test",
        source_name="test_source",
        event_id="test-id-1",
        timestamp=datetime(2023, 1, 1, 12, 0, 0)
    )
    event1.add_field("level", "INFO")
    
    event2 = LogEvent(
        raw_data="test log message 2",
        source_type="test",
        source_name="test_source",
        event_id="test-id-2",
        timestamp=datetime(2023, 1, 1, 12, 1, 0)
    )
    event2.add_field("level", "ERROR")
    
    # Write the events
    await sink.write([event1, event2])
    
    # Close the sink
    await sink.shutdown()
    
    # Read the output file
    with open(temp_output_file, "r") as f:
        lines = f.readlines()
    
    # Check the output
    assert len(lines) == 2
    
    event1_dict = json.loads(lines[0])
    assert event1_dict["id"] == "test-id-1"
    assert event1_dict["raw_data"] == "test log message 1"
    assert event1_dict["fields"]["level"] == "INFO"
    
    event2_dict = json.loads(lines[1])
    assert event2_dict["id"] == "test-id-2"
    assert event2_dict["raw_data"] == "test log message 2"
    assert event2_dict["fields"]["level"] == "ERROR"


@pytest.mark.asyncio
async def test_file_sink_write_text(temp_output_file):
    """Test writing events in text format."""
    sink = FileSink()
    
    # Initialize with the temporary file
    await sink.initialize({
        "path": temp_output_file,
        "format": "text",
        "append": True,
        "template": "{timestamp} [{level}] {message}",
        "message_field": "message"
    })
    
    # Create test events
    event1 = LogEvent(
        raw_data="raw message 1",
        source_type="test",
        source_name="test_source",
        event_id="test-id-1",
        timestamp=datetime(2023, 1, 1, 12, 0, 0)
    )
    event1.add_field("level", "INFO")
    event1.add_field("message", "Formatted message 1")
    
    event2 = LogEvent(
        raw_data="raw message 2",
        source_type="test",
        source_name="test_source",
        event_id="test-id-2",
        timestamp=datetime(2023, 1, 1, 12, 1, 0)
    )
    event2.add_field("level", "ERROR")
    event2.add_field("message", "Formatted message 2")
    
    # Write the events
    await sink.write([event1, event2])
    
    # Close the sink
    await sink.shutdown()
    
    # Read the output file
    with open(temp_output_file, "r") as f:
        lines = f.readlines()
    
    # Check the output
    assert len(lines) == 2
    assert lines[0].strip() == "2023-01-01T12:00:00 [INFO] Formatted message 1"
    assert lines[1].strip() == "2023-01-01T12:01:00 [ERROR] Formatted message 2"


@pytest.mark.asyncio
async def test_file_sink_append(temp_output_file):
    """Test appending to an existing file."""
    # Write initial content
    with open(temp_output_file, "w") as f:
        f.write("Initial content\n")
    
    # Create and initialize the sink with append=True
    sink1 = FileSink()
    await sink1.initialize({
        "path": temp_output_file,
        "format": "text",
        "append": True,
        "template": "{message}"
    })
    
    # Write an event
    event = LogEvent(
        raw_data="test message",
        source_type="test",
        source_name="test_source"
    )
    event.add_field("message", "Appended content")
    
    await sink1.write([event])
    await sink1.shutdown()
    
    # Read the file
    with open(temp_output_file, "r") as f:
        content = f.read()
    
    # Check that the content was appended
    assert "Initial content" in content
    assert "Appended content" in content
    
    # Create and initialize the sink with append=False
    sink2 = FileSink()
    await sink2.initialize({
        "path": temp_output_file,
        "format": "text",
        "append": False,
        "template": "{message}"
    })
    
    # Write another event
    event = LogEvent(
        raw_data="test message",
        source_type="test",
        source_name="test_source"
    )
    event.add_field("message", "Overwritten content")
    
    await sink2.write([event])
    await sink2.shutdown()
    
    # Read the file
    with open(temp_output_file, "r") as f:
        content = f.read()
    
    # Check that the content was overwritten
    assert "Initial content" not in content
    assert "Appended content" not in content
    assert "Overwritten content" in content