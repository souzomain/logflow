"""
Regex processor for LogFlow.
"""
import re
from typing import Dict, Any, Optional, List, Pattern

from logflow.core.models import LogEvent
from logflow.processors.base import Processor


class RegexProcessor(Processor):
    """
    Processor that extracts fields from log events using regular expressions.
    """
    
    def __init__(self):
        """
        Initialize a new RegexProcessor.
        """
        self.field = "raw_data"
        self.pattern = ""
        self.compiled_pattern = None
        self.named_groups = True
        self.group_names = []
        self.target_field = None
        self.preserve_original = True
        self.ignore_errors = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the processor with the provided configuration.
        
        Args:
            config: Processor configuration with the following keys:
                - field: Field containing the text to match (default: "raw_data")
                - pattern: Regular expression pattern (required)
                - named_groups: Whether to use named groups (default: True)
                - group_names: List of group names when not using named groups
                - target_field: Field to store the extracted data (default: None)
                - preserve_original: Whether to preserve the original field (default: True)
                - ignore_errors: Whether to ignore matching errors (default: False)
        """
        self.field = config.get("field", "raw_data")
        self.pattern = config.get("pattern")
        if not self.pattern:
            raise ValueError("Regular expression pattern is required")
        
        self.named_groups = config.get("named_groups", True)
        self.group_names = config.get("group_names", [])
        self.target_field = config.get("target_field")
        self.preserve_original = config.get("preserve_original", True)
        self.ignore_errors = config.get("ignore_errors", False)
        
        # Compile the regular expression
        try:
            self.compiled_pattern = re.compile(self.pattern)
            
            # Validate group names if not using named groups
            if not self.named_groups and not self.group_names:
                # Count the number of capturing groups
                group_count = sum(1 for _ in re.finditer(r'(?<!\\)\((?!\?)', self.pattern))
                if group_count > 0:
                    raise ValueError(f"When named_groups is False, group_names must be provided for {group_count} capturing groups")
        except re.error as e:
            raise ValueError(f"Invalid regular expression pattern: {str(e)}")
    
    async def process(self, event: LogEvent) -> Optional[LogEvent]:
        """
        Process a log event by extracting fields using regular expressions.
        
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
            # Match the pattern
            match = self.compiled_pattern.search(str(field_value))
            
            if match:
                # Extract the matched groups
                if self.named_groups:
                    # Use named groups
                    extracted = match.groupdict()
                else:
                    # Use numbered groups with provided names
                    groups = match.groups()
                    extracted = {}
                    for i, value in enumerate(groups):
                        if i < len(self.group_names):
                            extracted[self.group_names[i]] = value
                        else:
                            extracted[f"group{i+1}"] = value
                
                # Store the extracted data
                if self.target_field:
                    # Store under a target field
                    event.add_field(self.target_field, extracted)
                else:
                    # Add all extracted fields to the event
                    for key, value in extracted.items():
                        if value is not None:  # Skip None values
                            event.add_field(key, value)
                
                # Remove the original field if not preserving it
                if not self.preserve_original and self.field != "raw_data" and self.field in event.fields:
                    del event.fields[self.field]
            
            return event
        
        except Exception as e:
            # Handle errors
            if self.ignore_errors:
                # If ignoring errors, return the event as is
                event.add_metadata("regex_error", str(e))
                return event
            else:
                # Otherwise, drop the event
                return None
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        pass