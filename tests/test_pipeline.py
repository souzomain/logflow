"""
Tests for the pipeline.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from logflow.core.pipeline import Pipeline
from logflow.core.models import LogEvent
from logflow.sources.base import Source
from logflow.processors.base import Processor
from logflow.sinks.base import Sink


class MockSource(Source):
    """Mock source for testing."""
    
    def __init__(self):
        self.initialize_called = False
        self.shutdown_called = False
        self.events = []
    
    async def initialize(self, config):
        self.initialize_called = True
        self.config = config
    
    async def read(self):
        for event in self.events:
            yield event
    
    async def shutdown(self):
        self.shutdown_called = True


class MockProcessor(Processor):
    """Mock processor for testing."""
    
    def __init__(self):
        self.initialize_called = False
        self.shutdown_called = False
        self.processed_events = []
        self.drop_events = False
    
    async def initialize(self, config):
        self.initialize_called = True
        self.config = config
    
    async def process(self, event):
        self.processed_events.append(event)
        if self.drop_events:
            return None
        return event
    
    async def shutdown(self):
        self.shutdown_called = True


class MockSink(Sink):
    """Mock sink for testing."""
    
    def __init__(self):
        self.initialize_called = False
        self.shutdown_called = False
        self.written_events = []
    
    async def initialize(self, config):
        self.initialize_called = True
        self.config = config
    
    async def write(self, events):
        self.written_events.extend(events)
    
    async def shutdown(self):
        self.shutdown_called = True


@pytest.fixture
def mock_components():
    """Create mock components for testing."""
    source = MockSource()
    processor = MockProcessor()
    sink = MockSink()
    
    return source, processor, sink


@pytest.mark.asyncio
async def test_pipeline_initialization(mock_components):
    """Test initializing a pipeline."""
    source, processor, sink = mock_components
    
    # Create a pipeline configuration
    config = {
        "sources": [
            {
                "name": "test-source",
                "type": "MockSource",
                "config": {"test": "source-config"}
            }
        ],
        "processors": [
            {
                "name": "test-processor",
                "type": "MockProcessor",
                "config": {"test": "processor-config"}
            }
        ],
        "sinks": [
            {
                "name": "test-sink",
                "type": "MockSink",
                "config": {"test": "sink-config"}
            }
        ]
    }
    
    # Create a pipeline
    pipeline = Pipeline("test-pipeline", config)
    
    # Mock the _create_component method to return our mock components
    pipeline._create_component = MagicMock()
    pipeline._create_component.side_effect = [source, processor, sink]
    
    # Initialize the pipeline
    await pipeline.initialize()
    
    # Check that the components were created and initialized
    assert pipeline._create_component.call_count == 3
    assert source.initialize_called
    assert processor.initialize_called
    assert sink.initialize_called
    assert source.config == {"test": "source-config"}
    assert processor.config == {"test": "processor-config"}
    assert sink.config == {"test": "sink-config"}


@pytest.mark.asyncio
async def test_pipeline_processing(mock_components):
    """Test processing events through a pipeline."""
    source, processor, sink = mock_components
    
    # Create test events
    event1 = LogEvent(
        raw_data="test log message 1",
        source_type="test",
        source_name="test_source"
    )
    event2 = LogEvent(
        raw_data="test log message 2",
        source_type="test",
        source_name="test_source"
    )
    
    source.events = [event1, event2]
    
    # Create a pipeline configuration
    config = {
        "batch_size": 10,
        "batch_timeout": 0.1
    }
    
    # Create a pipeline
    pipeline = Pipeline("test-pipeline", config)
    pipeline.sources = [source]
    pipeline.processors = [processor]
    pipeline.sinks = [sink]
    
    # Run the pipeline for a short time
    pipeline.running = True
    run_task = asyncio.create_task(pipeline.run())
    
    # Wait for the pipeline to process the events
    await asyncio.sleep(0.2)
    
    # Stop the pipeline
    pipeline.running = False
    await run_task
    
    # Check that the events were processed
    assert len(processor.processed_events) == 2
    assert processor.processed_events[0] == event1
    assert processor.processed_events[1] == event2
    
    # Check that the events were written to the sink
    assert len(sink.written_events) == 2
    assert sink.written_events[0] == event1
    assert sink.written_events[1] == event2


@pytest.mark.asyncio
async def test_pipeline_event_dropping(mock_components):
    """Test dropping events in a pipeline."""
    source, processor, sink = mock_components
    
    # Configure the processor to drop events
    processor.drop_events = True
    
    # Create test events
    event1 = LogEvent(
        raw_data="test log message 1",
        source_type="test",
        source_name="test_source"
    )
    event2 = LogEvent(
        raw_data="test log message 2",
        source_type="test",
        source_name="test_source"
    )
    
    source.events = [event1, event2]
    
    # Create a pipeline configuration
    config = {
        "batch_size": 10,
        "batch_timeout": 0.1
    }
    
    # Create a pipeline
    pipeline = Pipeline("test-pipeline", config)
    pipeline.sources = [source]
    pipeline.processors = [processor]
    pipeline.sinks = [sink]
    
    # Run the pipeline for a short time
    pipeline.running = True
    run_task = asyncio.create_task(pipeline.run())
    
    # Wait for the pipeline to process the events
    await asyncio.sleep(0.2)
    
    # Stop the pipeline
    pipeline.running = False
    await run_task
    
    # Check that the events were processed
    assert len(processor.processed_events) == 2
    
    # Check that no events were written to the sink
    assert len(sink.written_events) == 0
    
    # Check the pipeline statistics
    assert pipeline.events_processed == 0
    assert pipeline.events_dropped == 2


@pytest.mark.asyncio
async def test_pipeline_shutdown(mock_components):
    """Test shutting down a pipeline."""
    source, processor, sink = mock_components
    
    # Create a pipeline
    pipeline = Pipeline("test-pipeline", {})
    pipeline.sources = [source]
    pipeline.processors = [processor]
    pipeline.sinks = [sink]
    pipeline.running = True
    
    # Stop the pipeline
    await pipeline.stop()
    
    # Check that the components were shut down
    assert source.shutdown_called
    assert processor.shutdown_called
    assert sink.shutdown_called
    assert not pipeline.running