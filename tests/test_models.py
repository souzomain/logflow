"""
Tests for the core models.
"""
import json
from datetime import datetime

import pytest

from logflow.core.models import LogEvent


def test_log_event_creation():
    """Test creating a LogEvent."""
    event = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    
    assert event.raw_data == "test log message"
    assert event.source_type == "test"
    assert event.source_name == "test_source"
    assert isinstance(event.timestamp, datetime)
    assert isinstance(event.id, str)
    assert event.fields == {}
    assert event.metadata == {}
    assert event.tags == []


def test_log_event_add_field():
    """Test adding fields to a LogEvent."""
    event = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    
    event.add_field("level", "INFO")
    event.add_field("message", "This is a test")
    
    assert event.fields["level"] == "INFO"
    assert event.fields["message"] == "This is a test"


def test_log_event_add_metadata():
    """Test adding metadata to a LogEvent."""
    event = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    
    event.add_metadata("processed_by", "test_processor")
    event.add_metadata("processing_time", 0.5)
    
    assert event.metadata["processed_by"] == "test_processor"
    assert event.metadata["processing_time"] == 0.5


def test_log_event_add_tag():
    """Test adding tags to a LogEvent."""
    event = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source"
    )
    
    event.add_tag("test")
    event.add_tag("example")
    
    assert "test" in event.tags
    assert "example" in event.tags
    
    # Adding the same tag twice should not duplicate it
    event.add_tag("test")
    assert len(event.tags) == 2


def test_log_event_to_dict():
    """Test converting a LogEvent to a dictionary."""
    event = LogEvent(
        raw_data="test log message",
        source_type="test",
        source_name="test_source",
        event_id="test-id"
    )
    
    event.add_field("level", "INFO")
    event.add_metadata("processed_by", "test_processor")
    event.add_tag("test")
    
    event_dict = event.to_dict()
    
    assert event_dict["id"] == "test-id"
    assert event_dict["raw_data"] == "test log message"
    assert event_dict["source_type"] == "test"
    assert event_dict["source_name"] == "test_source"
    assert event_dict["fields"]["level"] == "INFO"
    assert event_dict["metadata"]["processed_by"] == "test_processor"
    assert "test" in event_dict["tags"]


def test_log_event_from_dict():
    """Test creating a LogEvent from a dictionary."""
    timestamp = datetime.utcnow()
    
    event_dict = {
        "id": "test-id",
        "timestamp": timestamp.isoformat(),
        "raw_data": "test log message",
        "source_type": "test",
        "source_name": "test_source",
        "fields": {"level": "INFO"},
        "metadata": {"processed_by": "test_processor"},
        "tags": ["test"]
    }
    
    event = LogEvent.from_dict(event_dict)
    
    assert event.id == "test-id"
    assert event.raw_data == "test log message"
    assert event.source_type == "test"
    assert event.source_name == "test_source"
    assert event.fields["level"] == "INFO"
    assert event.metadata["processed_by"] == "test_processor"
    assert "test" in event.tags
    assert event.timestamp.isoformat() == timestamp.isoformat()