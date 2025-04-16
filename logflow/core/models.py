"""
Core data models for LogFlow.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


class LogEvent:
    """
    Unified data model for representing log events during processing.
    
    Attributes:
        id: Unique identifier for the event
        timestamp: Date and time of the event
        source_type: Type of the source (file, syslog, etc.)
        source_name: Name or identifier of the source
        raw_data: Original raw data
        fields: Extracted and processed fields
        metadata: Processing metadata
        tags: Tags for categorization
    """
    
    def __init__(
        self,
        raw_data: str,
        source_type: str,
        source_name: str,
        timestamp: Optional[datetime] = None,
        fields: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        event_id: Optional[str] = None,
    ):
        """
        Initialize a new LogEvent.
        
        Args:
            raw_data: Original raw data
            source_type: Type of the source
            source_name: Name or identifier of the source
            timestamp: Date and time of the event (defaults to current time)
            fields: Extracted and processed fields
            metadata: Processing metadata
            tags: Tags for categorization
            event_id: Unique identifier (generated if not provided)
        """
        self.id = event_id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.utcnow()
        self.source_type = source_type
        self.source_name = source_name
        self.raw_data = raw_data
        self.fields = fields or {}
        self.metadata = metadata or {}
        self.tags = tags or []
    
    def add_field(self, key: str, value: Any) -> None:
        """
        Add or update a field in the event.
        
        Args:
            key: Field name
            value: Field value
        """
        self.fields[key] = value
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add or update metadata in the event.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the event if it doesn't already exist.
        
        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary representation.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "source_type": self.source_type,
            "source_name": self.source_name,
            "raw_data": self.raw_data,
            "fields": self.fields,
            "metadata": self.metadata,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogEvent":
        """
        Create a LogEvent from a dictionary representation.
        
        Args:
            data: Dictionary representation of the event
            
        Returns:
            LogEvent instance
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            raw_data=data["raw_data"],
            source_type=data["source_type"],
            source_name=data["source_name"],
            timestamp=timestamp,
            fields=data.get("fields", {}),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            event_id=data.get("id"),
        )