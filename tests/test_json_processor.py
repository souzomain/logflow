"""
Tests for the JSON processor.
"""
import json

import pytest

from logflow.processors.json import JsonProcessor
from logflow.core.models import LogEvent


@pytest.mark.asyncio
async def test_json_processor_initialization():
    """Test initializing a JSON processor."""
    processor = JsonProcessor()
    
    # Initialize with default configuration
    await processor.initialize({})
    
    assert processor.field == "raw_data"
    assert processor.target_field == "parsed"
    assert processor.preserve_original is True
    assert processor.ignore_errors is False
    
    # Initialize with custom configuration
    await processor.initialize({
        "field": "message",
        "target_field": "json",
        "preserve_original": False,
        "ignore_errors": True
    })
    
    assert processor.field == "message"
    assert processor.target_field == "json"
    assert processor.preserve_original is False
    assert processor.ignore_errors is True


@pytest.mark.asyncio
async def test_json_processor_process_raw_data():
    """Test processing JSON in raw_data."""
    processor = JsonProcessor()
    await processor.initialize({})
    
    # Create a test event with JSON in raw_data
    event = LogEvent(
        raw_data='{"level": "INFO", "message": "Test message", "timestamp": "2023-01-01T00:00:00Z"}',
        source_type="test",
        source_name="test_source"
    )
    
    # Process the event
    processed_event = await processor.process(event)
    
    # Check that the JSON was parsed
    assert processed_event is not None
    assert "parsed" in processed_event.fields
    assert processed_event.fields["parsed"]["level"] == "INFO"
    assert processed_event.fields["parsed"]["message"] == "Test message"
    assert processed_event.fields["parsed"]["timestamp"] == "2023-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_json_processor_process_field():
    """Test processing JSON in a field."""
    processor = JsonProcessor()
    await processor.initialize({
        "field": "json_data",
        "target_field": "parsed"
    })
    
    # Create a test event with JSON in a field
    event = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event.add_field("json_data", '{"level": "INFO", "message": "Test message"}')
    
    # Process the event
    processed_event = await processor.process(event)
    
    # Check that the JSON was parsed
    assert processed_event is not None
    assert "parsed" in processed_event.fields
    assert processed_event.fields["parsed"]["level"] == "INFO"
    assert processed_event.fields["parsed"]["message"] == "Test message"
    assert "json_data" in processed_event.fields  # Original field is preserved


@pytest.mark.asyncio
async def test_json_processor_process_no_target_field():
    """Test processing JSON with no target field."""
    processor = JsonProcessor()
    await processor.initialize({
        "field": "json_data",
        "target_field": ""
    })
    
    # Create a test event with JSON in a field
    event = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event.add_field("json_data", '{"level": "INFO", "message": "Test message"}')
    
    # Process the event
    processed_event = await processor.process(event)
    
    # Check that the JSON fields were added directly to the event
    assert processed_event is not None
    assert "level" in processed_event.fields
    assert "message" in processed_event.fields
    assert processed_event.fields["level"] == "INFO"
    assert processed_event.fields["message"] == "Test message"


@pytest.mark.asyncio
async def test_json_processor_process_invalid_json():
    """Test processing invalid JSON."""
    # Test with ignore_errors=False
    processor1 = JsonProcessor()
    await processor1.initialize({
        "ignore_errors": False
    })
    
    event1 = LogEvent(
        raw_data='{"invalid": "json"',  # Missing closing brace
        source_type="test",
        source_name="test_source"
    )
    
    # Process the event
    processed_event1 = await processor1.process(event1)
    
    # Check that the event was dropped
    assert processed_event1 is None
    
    # Test with ignore_errors=True
    processor2 = JsonProcessor()
    await processor2.initialize({
        "ignore_errors": True
    })
    
    event2 = LogEvent(
        raw_data='{"invalid": "json"',  # Missing closing brace
        source_type="test",
        source_name="test_source"
    )
    
    # Process the event
    processed_event2 = await processor2.process(event2)
    
    # Check that the event was not dropped
    assert processed_event2 is not None
    assert "json_error" in processed_event2.metadata