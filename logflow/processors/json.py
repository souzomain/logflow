"""
JSON processor for LogFlow.
"""
import json
from typing import Dict, Any, Optional

from logflow.core.models import LogEvent
from logflow.processors.base import Processor


class JsonProcessor(Processor):
    """
    Processor that parses JSON data from log events.
    """
    
    def __init__(self):
        """
        Initialize a new JsonProcessor.
        """
        self.field = "raw_data"
        self.target_field = "parsed"
        self.preserve_original = True
        self.ignore_errors = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the processor with the provided configuration.
        
        Args:
            config: Processor configuration with the following keys:
                - field: Field containing the JSON data (default: "raw_data")
                - target_field: Field to store the parsed data (default: "parsed")
                - preserve_original: Whether to preserve the original field (default: True)
                - ignore_errors: Whether to ignore parsing errors (default: False)
        """
        self.field = config.get("field", "raw_data")
        self.target_field = config.get("target_field", "parsed")
        self.preserve_original = config.get("preserve_original", True)
        self.ignore_errors = config.get("ignore_errors", False)
    
    async def process(self, event: LogEvent) -> Optional[LogEvent]:
        """
        Process a log event by parsing JSON data.
        
        Args:
            event: The log event to process
            
        Returns:
            The processed log event, or None if the event should be dropped
        """
        # Get the field value
        field_value = None
        if self.field == "raw_data":
            field_value = event.raw_data
        else:
            field_value = event.fields.get(self.field)
        
        if not field_value:
            # If the field doesn't exist or is empty, return the event as is
            return event
        
        try:
            # Parse the JSON data
            parsed_data = json.loads(field_value)
            
            # Store the parsed data
            if self.target_field:
                event.add_field(self.target_field, parsed_data)
            else:
                # If no target field is specified, add all parsed fields to the event
                if isinstance(parsed_data, dict):
                    for key, value in parsed_data.items():
                        event.add_field(key, value)
            
            # Remove the original field if not preserving it
            if not self.preserve_original and self.field != "raw_data" and self.field in event.fields:
                del event.fields[self.field]
            
            return event
        
        except json.JSONDecodeError as e:
            # Handle parsing errors
            if self.ignore_errors:
                # If ignoring errors, return the event as is
                event.add_metadata("json_error", str(e))
                return event
            else:
                # Otherwise, drop the event
                return None
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        pass