"""
Mutate processor for LogFlow.
"""
import re
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime

from logflow.core.models import LogEvent
from logflow.processors.base import Processor


class MutateProcessor(Processor):
    """
    Processor that mutates fields in log events.
    """
    
    def __init__(self):
        """
        Initialize a new MutateProcessor.
        """
        self.add_fields = {}
        self.remove_fields = []
        self.rename_fields = {}
        self.uppercase_fields = []
        self.lowercase_fields = []
        self.convert_fields = {}
        self.gsub_fields = {}
        self.merge_fields = {}
        self.split_fields = {}
        self.strip_fields = []
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the processor with the provided configuration.
        
        Args:
            config: Processor configuration with the following keys:
                - add_fields: Dictionary of fields to add
                - remove_fields: List of fields to remove
                - rename_fields: Dictionary of fields to rename (old_name: new_name)
                - uppercase_fields: List of fields to convert to uppercase
                - lowercase_fields: List of fields to convert to lowercase
                - convert_fields: Dictionary of fields to convert (field: type)
                - gsub_fields: Dictionary of fields to apply regex substitution (field: [pattern, replacement])
                - merge_fields: Dictionary of fields to merge (target: [source1, source2, ...])
                - split_fields: Dictionary of fields to split (field: [separator, limit])
                - strip_fields: List of fields to strip whitespace
        """
        self.add_fields = config.get("add_fields", {})
        self.remove_fields = config.get("remove_fields", [])
        self.rename_fields = config.get("rename_fields", {})
        self.uppercase_fields = config.get("uppercase_fields", [])
        self.lowercase_fields = config.get("lowercase_fields", [])
        self.convert_fields = config.get("convert_fields", {})
        self.gsub_fields = config.get("gsub_fields", {})
        self.merge_fields = config.get("merge_fields", {})
        self.split_fields = config.get("split_fields", {})
        self.strip_fields = config.get("strip_fields", [])
        
        # Validate gsub_fields
        for field, config in self.gsub_fields.items():
            if not isinstance(config, list) or len(config) != 2:
                raise ValueError(f"gsub_fields.{field} must be a list with [pattern, replacement]")
            
            # Compile the regex
            try:
                self.gsub_fields[field][0] = re.compile(config[0])
            except re.error as e:
                raise ValueError(f"Invalid regex pattern for gsub_fields.{field}: {str(e)}")
        
        # Validate split_fields
        for field, config in self.split_fields.items():
            if not isinstance(config, list) or len(config) != 2:
                raise ValueError(f"split_fields.{field} must be a list with [separator, limit]")
            
            # Ensure limit is an integer
            try:
                self.split_fields[field][1] = int(config[1])
            except (ValueError, TypeError):
                raise ValueError(f"split_fields.{field}[1] must be an integer")
    
    def _convert_value(self, value: Any, target_type: str) -> Any:
        """
        Convert a value to the specified type.
        
        Args:
            value: Value to convert
            target_type: Target type (int, float, str, bool, etc.)
            
        Returns:
            Converted value
        """
        if value is None:
            return None
        
        try:
            if target_type == "int":
                return int(value)
            elif target_type == "float":
                return float(value)
            elif target_type == "str":
                return str(value)
            elif target_type == "bool":
                if isinstance(value, str):
                    return value.lower() in ("true", "yes", "y", "1")
                return bool(value)
            elif target_type == "list":
                if isinstance(value, str):
                    return [item.strip() for item in value.split(",")]
                elif isinstance(value, (list, tuple)):
                    return list(value)
                return [value]
            elif target_type == "timestamp":
                if isinstance(value, (int, float)):
                    return datetime.fromtimestamp(value)
                elif isinstance(value, str):
                    # Try common formats
                    for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
                        try:
                            return datetime.strptime(value, fmt)
                        except ValueError:
                            continue
                    # If no format matches, raise an error
                    raise ValueError(f"Could not parse timestamp: {value}")
                return value
            else:
                raise ValueError(f"Unsupported conversion type: {target_type}")
        except Exception as e:
            raise ValueError(f"Error converting value '{value}' to {target_type}: {str(e)}")
    
    async def process(self, event: LogEvent) -> Optional[LogEvent]:
        """
        Process a log event by mutating fields.
        
        Args:
            event: The log event to process
            
        Returns:
            The processed log event
        """
        # Add fields
        for field, value in self.add_fields.items():
            event.add_field(field, value)
        
        # Remove fields
        for field in self.remove_fields:
            if field in event.fields:
                del event.fields[field]
        
        # Rename fields
        for old_name, new_name in self.rename_fields.items():
            if old_name in event.fields:
                event.add_field(new_name, event.fields[old_name])
                del event.fields[old_name]
        
        # Uppercase fields
        for field in self.uppercase_fields:
            if field in event.fields and isinstance(event.fields[field], str):
                event.fields[field] = event.fields[field].upper()
        
        # Lowercase fields
        for field in self.lowercase_fields:
            if field in event.fields and isinstance(event.fields[field], str):
                event.fields[field] = event.fields[field].lower()
        
        # Convert fields
        for field, target_type in self.convert_fields.items():
            if field in event.fields:
                try:
                    event.fields[field] = self._convert_value(event.fields[field], target_type)
                except ValueError as e:
                    # Skip conversion if it fails
                    event.add_metadata(f"convert_error_{field}", str(e))
        
        # Apply regex substitution
        for field, (pattern, replacement) in self.gsub_fields.items():
            if field in event.fields and isinstance(event.fields[field], str):
                event.fields[field] = pattern.sub(replacement, event.fields[field])
        
        # Merge fields
        for target, sources in self.merge_fields.items():
            merged_value = ""
            for source in sources:
                if source in event.fields:
                    if merged_value:
                        merged_value += " "
                    merged_value += str(event.fields[source])
            if merged_value:
                event.add_field(target, merged_value)
        
        # Split fields
        for field, (separator, limit) in self.split_fields.items():
            if field in event.fields and isinstance(event.fields[field], str):
                event.fields[field] = event.fields[field].split(separator, limit)
        
        # Strip whitespace
        for field in self.strip_fields:
            if field in event.fields and isinstance(event.fields[field], str):
                event.fields[field] = event.fields[field].strip()
        
        return event
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        pass