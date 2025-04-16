"""
Tests for the filter processor.
"""
import pytest

from logflow.processors.filter import FilterProcessor
from logflow.core.models import LogEvent


@pytest.mark.asyncio
async def test_filter_processor_initialization():
    """Test initializing a filter processor."""
    processor = FilterProcessor()
    
    # Initialize with a single condition
    await processor.initialize({
        "condition": "level == 'INFO'"
    })
    
    assert len(processor.conditions) == 1
    assert processor.mode == "any"
    assert processor.negate is False
    
    # Initialize with multiple conditions
    await processor.initialize({
        "conditions": ["level == 'INFO'", "service == 'web'"],
        "mode": "all",
        "negate": True
    })
    
    assert len(processor.conditions) == 2
    assert processor.mode == "all"
    assert processor.negate is True
    
    # Initialize with invalid mode
    with pytest.raises(ValueError, match="Invalid mode: invalid"):
        await processor.initialize({
            "condition": "level == 'INFO'",
            "mode": "invalid"
        })
    
    # Initialize without conditions
    with pytest.raises(ValueError, match="At least one condition is required"):
        await processor.initialize({})


@pytest.mark.asyncio
async def test_filter_processor_equals_condition():
    """Test filtering with equals condition."""
    processor = FilterProcessor()
    await processor.initialize({
        "condition": "level == 'INFO'"
    })
    
    # Create test events
    event1 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event1.add_field("level", "INFO")
    
    event2 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event2.add_field("level", "ERROR")
    
    # Process the events
    processed_event1 = await processor.process(event1)
    processed_event2 = await processor.process(event2)
    
    # Check the results
    assert processed_event1 is not None  # Event with level=INFO passes
    assert processed_event2 is None  # Event with level=ERROR is dropped


@pytest.mark.asyncio
async def test_filter_processor_not_equals_condition():
    """Test filtering with not equals condition."""
    processor = FilterProcessor()
    await processor.initialize({
        "condition": "level != 'DEBUG'"
    })
    
    # Create test events
    event1 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event1.add_field("level", "INFO")
    
    event2 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event2.add_field("level", "DEBUG")
    
    # Process the events
    processed_event1 = await processor.process(event1)
    processed_event2 = await processor.process(event2)
    
    # Check the results
    assert processed_event1 is not None  # Event with level=INFO passes
    assert processed_event2 is None  # Event with level=DEBUG is dropped


@pytest.mark.asyncio
async def test_filter_processor_comparison_conditions():
    """Test filtering with comparison conditions."""
    processor = FilterProcessor()
    await processor.initialize({
        "condition": "status_code < 400"
    })
    
    # Create test events
    event1 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event1.add_field("status_code", 200)
    
    event2 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event2.add_field("status_code", 500)
    
    # Process the events
    processed_event1 = await processor.process(event1)
    processed_event2 = await processor.process(event2)
    
    # Check the results
    assert processed_event1 is not None  # Event with status_code=200 passes
    assert processed_event2 is None  # Event with status_code=500 is dropped


@pytest.mark.asyncio
async def test_filter_processor_regex_conditions():
    """Test filtering with regex conditions."""
    processor = FilterProcessor()
    await processor.initialize({
        "condition": "message =~ 'error|warning'"
    })
    
    # Create test events
    event1 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event1.add_field("message", "This is an error message")
    
    event2 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event2.add_field("message", "This is a success message")
    
    # Process the events
    processed_event1 = await processor.process(event1)
    processed_event2 = await processor.process(event2)
    
    # Check the results
    assert processed_event1 is not None  # Event with error in message passes
    assert processed_event2 is None  # Event without error in message is dropped


@pytest.mark.asyncio
async def test_filter_processor_in_conditions():
    """Test filtering with in conditions."""
    processor = FilterProcessor()
    await processor.initialize({
        "condition": "level in [INFO, WARN, ERROR]"
    })
    
    # Create test events
    event1 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event1.add_field("level", "INFO")
    
    event2 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event2.add_field("level", "DEBUG")
    
    # Process the events
    processed_event1 = await processor.process(event1)
    processed_event2 = await processor.process(event2)
    
    # Check the results
    assert processed_event1 is not None  # Event with level=INFO passes
    assert processed_event2 is None  # Event with level=DEBUG is dropped


@pytest.mark.asyncio
async def test_filter_processor_exists_conditions():
    """Test filtering with exists conditions."""
    processor = FilterProcessor()
    await processor.initialize({
        "condition": "exists:error_code"
    })
    
    # Create test events
    event1 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event1.add_field("error_code", 500)
    
    event2 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    
    # Process the events
    processed_event1 = await processor.process(event1)
    processed_event2 = await processor.process(event2)
    
    # Check the results
    assert processed_event1 is not None  # Event with error_code field passes
    assert processed_event2 is None  # Event without error_code field is dropped


@pytest.mark.asyncio
async def test_filter_processor_multiple_conditions():
    """Test filtering with multiple conditions."""
    # Test with mode=any
    processor1 = FilterProcessor()
    await processor1.initialize({
        "conditions": ["level == 'ERROR'", "message =~ 'critical'"],
        "mode": "any"
    })
    
    # Create test events
    event1 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event1.add_field("level", "ERROR")
    event1.add_field("message", "Normal message")
    
    event2 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event2.add_field("level", "INFO")
    event2.add_field("message", "Critical issue detected")
    
    event3 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event3.add_field("level", "INFO")
    event3.add_field("message", "Normal message")
    
    # Process the events
    processed_event1 = await processor1.process(event1)
    processed_event2 = await processor1.process(event2)
    processed_event3 = await processor1.process(event3)
    
    # Check the results
    assert processed_event1 is not None  # Passes due to level=ERROR
    assert processed_event2 is not None  # Passes due to message containing 'critical'
    assert processed_event3 is None  # Doesn't match any condition
    
    # Test with mode=all
    processor2 = FilterProcessor()
    await processor2.initialize({
        "conditions": ["level == 'ERROR'", "message =~ 'critical'"],
        "mode": "all"
    })
    
    # Create a test event that matches both conditions
    event4 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event4.add_field("level", "ERROR")
    event4.add_field("message", "Critical issue detected")
    
    # Process the events
    processed_event1 = await processor2.process(event1)
    processed_event2 = await processor2.process(event2)
    processed_event4 = await processor2.process(event4)
    
    # Check the results
    assert processed_event1 is None  # Doesn't match all conditions
    assert processed_event2 is None  # Doesn't match all conditions
    assert processed_event4 is not None  # Matches all conditions


@pytest.mark.asyncio
async def test_filter_processor_negation():
    """Test filtering with negation."""
    processor = FilterProcessor()
    await processor.initialize({
        "condition": "level == 'ERROR'",
        "negate": True
    })
    
    # Create test events
    event1 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event1.add_field("level", "ERROR")
    
    event2 = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    event2.add_field("level", "INFO")
    
    # Process the events
    processed_event1 = await processor.process(event1)
    processed_event2 = await processor.process(event2)
    
    # Check the results
    assert processed_event1 is None  # Event with level=ERROR is dropped due to negation
    assert processed_event2 is not None  # Event with level=INFO passes due to negation