"""
File source for LogFlow.
"""
import asyncio
import os
import time
from datetime import datetime
from typing import AsyncIterator, Dict, Any, Optional

import aiofiles
from aiofiles.os import stat as aio_stat

from logflow.core.models import LogEvent
from logflow.sources.base import Source


class FileSource(Source):
    """
    Source that reads logs from a file.
    
    Features:
    - Tail mode: Continuously read new lines as they are added
    - File rotation detection
    - Position tracking for resuming
    """
    
    def __init__(self):
        """
        Initialize a new FileSource.
        """
        self.path = ""
        self.tail = True
        self.read_from_start = False
        self.position = 0
        self.inode = 0
        self.poll_interval = 1.0  # seconds
        self.running = False
        self.file = None
        self.format = "raw"  # raw, json, etc.
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the source with the provided configuration.
        
        Args:
            config: Source configuration with the following keys:
                - path: Path to the log file (required)
                - tail: Whether to continuously read new lines (default: True)
                - read_from_start: Whether to read from the start of the file (default: False)
                - poll_interval: Interval in seconds to check for new data (default: 1.0)
                - format: Format of the log file (default: "raw")
        """
        self.path = config.get("path")
        if not self.path:
            raise ValueError("File path is required")
        
        self.tail = config.get("tail", True)
        self.read_from_start = config.get("read_from_start", False)
        self.poll_interval = float(config.get("poll_interval", 1.0))
        self.format = config.get("format", "raw")
        
        # Get the initial file information
        try:
            stats = await aio_stat(self.path)
            self.inode = stats.st_ino
            
            # Set the initial position
            if self.read_from_start:
                self.position = 0
            else:
                self.position = stats.st_size
        except FileNotFoundError:
            # If the file doesn't exist yet, start from the beginning when it appears
            self.position = 0
    
    async def read(self) -> AsyncIterator[LogEvent]:
        """
        Read log events from the file.
        
        Yields:
            LogEvent objects
        """
        self.running = True
        
        while self.running:
            # Check if the file exists
            try:
                stats = await aio_stat(self.path)
                current_inode = stats.st_ino
                
                # Check for file rotation
                if current_inode != self.inode:
                    self.inode = current_inode
                    self.position = 0
                
                # Check if there's new data
                if stats.st_size > self.position:
                    # Open the file and seek to the current position
                    async with aiofiles.open(self.path, mode='r') as file:
                        await file.seek(self.position)
                        
                        # Read new lines
                        while self.running:
                            line = await file.readline()
                            
                            # If we reached the end of the file
                            if not line:
                                break
                            
                            # Update the position
                            self.position += len(line)
                            
                            # Skip empty lines
                            if not line.strip():
                                continue
                            
                            # Create and yield a log event
                            event = LogEvent(
                                raw_data=line.strip(),
                                source_type="file",
                                source_name=self.path,
                                timestamp=datetime.utcnow(),
                                metadata={
                                    "file_path": self.path,
                                    "file_position": self.position - len(line)
                                }
                            )
                            
                            yield event
                
                # If we're not in tail mode, stop after reading the file once
                if not self.tail:
                    break
                
                # Wait before checking for new data
                await asyncio.sleep(self.poll_interval)
            
            except FileNotFoundError:
                # If the file doesn't exist, wait and try again
                await asyncio.sleep(self.poll_interval)
            
            except Exception as e:
                # Log the error and continue
                print(f"Error reading file {self.path}: {str(e)}")
                await asyncio.sleep(self.poll_interval)
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        self.running = False