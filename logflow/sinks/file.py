"""
File sink for LogFlow.
"""
import json
import os
from typing import Dict, Any, List

import aiofiles

from logflow.core.models import LogEvent
from logflow.sinks.base import Sink


class FileSink(Sink):
    """
    Sink that writes log events to a file.
    """
    
    def __init__(self):
        """
        Initialize a new FileSink.
        """
        self.path = ""
        self.format = "json"  # json, text
        self.append = True
        self.file = None
        self.template = "{timestamp} {message}"
        self.message_field = "message"
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the sink with the provided configuration.
        
        Args:
            config: Sink configuration with the following keys:
                - path: Path to the output file (required)
                - format: Output format: "json" or "text" (default: "json")
                - append: Whether to append to the file (default: True)
                - template: Template for text format (default: "{timestamp} {message}")
                - message_field: Field to use as message in text format (default: "message")
        """
        self.path = config.get("path")
        if not self.path:
            raise ValueError("File path is required")
        
        self.format = config.get("format", "json")
        if self.format not in ["json", "text"]:
            raise ValueError(f"Invalid format: {self.format}")
        
        self.append = config.get("append", True)
        self.template = config.get("template", "{timestamp} {message}")
        self.message_field = config.get("message_field", "message")
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        
        # Open the file
        mode = "a" if self.append else "w"
        self.file = await aiofiles.open(self.path, mode=mode)
    
    async def write(self, events: List[LogEvent]) -> None:
        """
        Write a batch of log events to the file.
        
        Args:
            events: List of log events to write
        """
        if not events:
            return
        
        for event in events:
            if self.format == "json":
                # Write as JSON
                line = json.dumps(event.to_dict()) + "\n"
            else:  # text
                # Write as text using the template
                context = {
                    "id": event.id,
                    "timestamp": event.timestamp.isoformat(),
                    "source_type": event.source_type,
                    "source_name": event.source_name,
                    "raw_data": event.raw_data,
                }
                
                # Add fields to context
                for key, value in event.fields.items():
                    context[key] = value
                
                # Use message field if available, otherwise use raw_data
                if self.message_field in event.fields:
                    context["message"] = event.fields[self.message_field]
                else:
                    context["message"] = event.raw_data
                
                # Format the line using the template
                try:
                    line = self.template.format(**context) + "\n"
                except KeyError as e:
                    # If a field is missing, use a simplified format
                    line = f"{event.timestamp.isoformat()} {event.raw_data}\n"
            
            # Write the line to the file
            await self.file.write(line)
        
        # Flush the file
        await self.file.flush()
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        if self.file:
            await self.file.close()
            self.file = None