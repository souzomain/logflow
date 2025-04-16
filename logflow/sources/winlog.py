"""
Windows Event Log source for LogFlow.
"""
import asyncio
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from typing import AsyncIterator, Dict, Any, List, Optional

from logflow.core.models import LogEvent
from logflow.sources.base import Source


class WinlogSource(Source):
    """
    Source that reads Windows Event Logs.
    
    This source can read Windows Event Logs directly or from Winlogbeat output.
    """
    
    def __init__(self):
        """
        Initialize a new WinlogSource.
        """
        self.mode = "file"  # file, directory, tcp
        self.path = None
        self.channels = ["Application", "System", "Security"]
        self.level = None
        self.event_ids = []
        self.providers = []
        self.poll_interval = 10.0  # seconds
        self.tail = True
        self.host = "0.0.0.0"
        self.port = 5044
        self.running = False
        self.processed_files = set()
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the source with the provided configuration.
        
        Args:
            config: Source configuration with the following keys:
                - mode: Source mode (file, directory, tcp)
                - path: Path to Winlogbeat output file or directory
                - channels: List of Windows Event Log channels to read
                - level: Minimum event level to read (1-5)
                - event_ids: List of event IDs to filter
                - providers: List of event providers to filter
                - poll_interval: Interval in seconds to poll for new events
                - tail: Whether to continuously read new events
                - host: Host to bind to for TCP mode
                - port: Port to bind to for TCP mode
        """
        self.mode = config.get("mode", "file")
        if self.mode not in ["file", "directory", "tcp"]:
            raise ValueError(f"Invalid mode: {self.mode}")
        
        self.path = config.get("path")
        if self.mode in ["file", "directory"] and not self.path:
            raise ValueError("Path is required for file or directory mode")
        
        self.channels = config.get("channels", ["Application", "System", "Security"])
        self.level = config.get("level")
        self.event_ids = config.get("event_ids", [])
        self.providers = config.get("providers", [])
        self.poll_interval = float(config.get("poll_interval", 10.0))
        self.tail = config.get("tail", True)
        self.host = config.get("host", "0.0.0.0")
        self.port = int(config.get("port", 5044))
        
        # Validate configuration
        if self.mode == "file" and not os.path.isfile(self.path):
            raise ValueError(f"File not found: {self.path}")
        
        if self.mode == "directory" and not os.path.isdir(self.path):
            raise ValueError(f"Directory not found: {self.path}")
        
        if self.level is not None and not (1 <= self.level <= 5):
            raise ValueError("Level must be between 1 and 5")
    
    async def _read_file(self, path: str, position: int = 0) -> AsyncIterator[LogEvent]:
        """
        Read events from a file.
        
        Args:
            path: Path to the file
            position: Position to start reading from
            
        Yields:
            LogEvent objects
        """
        try:
            # Open the file and seek to the position
            async with open(path, "r") as f:
                await f.seek(position)
                
                # Read lines
                while True:
                    line = await f.readline()
                    
                    # If we reached the end of the file
                    if not line:
                        if self.tail:
                            # Wait before checking for new data
                            await asyncio.sleep(self.poll_interval)
                            continue
                        else:
                            break
                    
                    # Skip empty lines
                    if not line.strip():
                        continue
                    
                    # Parse the line as JSON
                    try:
                        data = json.loads(line)
                        
                        # Check if it's a Windows Event Log entry
                        if "winlog" in data:
                            # Apply filters
                            if self._apply_filters(data):
                                # Create and yield a log event
                                event = self._create_event(data)
                                yield event
                    except json.JSONDecodeError:
                        # Skip invalid JSON
                        continue
        
        except Exception as e:
            # Log the error and continue
            print(f"Error reading file {path}: {str(e)}")
    
    async def _scan_directory(self) -> AsyncIterator[LogEvent]:
        """
        Scan a directory for Winlogbeat output files.
        
        Yields:
            LogEvent objects
        """
        while self.running:
            try:
                # Get all files in the directory
                files = [os.path.join(self.path, f) for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, f))]
                
                # Sort files by modification time (oldest first)
                files.sort(key=lambda f: os.path.getmtime(f))
                
                # Process each file
                for file_path in files:
                    if file_path not in self.processed_files:
                        # Process the file
                        async for event in self._read_file(file_path):
                            yield event
                        
                        # Mark the file as processed
                        self.processed_files.add(file_path)
                
                # Wait before scanning again
                await asyncio.sleep(self.poll_interval)
            
            except Exception as e:
                # Log the error and continue
                print(f"Error scanning directory {self.path}: {str(e)}")
                await asyncio.sleep(self.poll_interval)
    
    async def _start_tcp_server(self) -> AsyncIterator[LogEvent]:
        """
        Start a TCP server to receive Winlogbeat events.
        
        Yields:
            LogEvent objects
        """
        # Create a server
        server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        
        # Start the server
        async with server:
            await server.serve_forever()
    
    async def _handle_client(self, reader, writer):
        """
        Handle a client connection.
        
        Args:
            reader: StreamReader
            writer: StreamWriter
        """
        try:
            # Read data
            while self.running:
                # Read a line
                line = await reader.readline()
                
                # If the client closed the connection
                if not line:
                    break
                
                # Parse the line as JSON
                try:
                    data = json.loads(line)
                    
                    # Check if it's a Windows Event Log entry
                    if "winlog" in data:
                        # Apply filters
                        if self._apply_filters(data):
                            # Create a log event
                            event = self._create_event(data)
                            
                            # Yield the event
                            yield event
                except json.JSONDecodeError:
                    # Skip invalid JSON
                    continue
        
        except Exception as e:
            # Log the error
            print(f"Error handling client: {str(e)}")
        
        finally:
            # Close the connection
            writer.close()
            await writer.wait_closed()
    
    def _apply_filters(self, data: Dict[str, Any]) -> bool:
        """
        Apply filters to a Windows Event Log entry.
        
        Args:
            data: Windows Event Log entry
            
        Returns:
            True if the entry passes the filters, False otherwise
        """
        winlog = data.get("winlog", {})
        
        # Filter by channel
        if self.channels and winlog.get("channel") not in self.channels:
            return False
        
        # Filter by level
        if self.level is not None:
            event_level = winlog.get("level")
            if event_level is None:
                return False
            
            # Convert level to integer
            try:
                event_level = int(event_level)
            except (ValueError, TypeError):
                return False
            
            # Check level
            if event_level < self.level:
                return False
        
        # Filter by event ID
        if self.event_ids:
            event_id = winlog.get("event_id")
            if event_id is None:
                return False
            
            # Convert event ID to integer
            try:
                event_id = int(event_id)
            except (ValueError, TypeError):
                return False
            
            # Check event ID
            if event_id not in self.event_ids:
                return False
        
        # Filter by provider
        if self.providers:
            provider = winlog.get("provider", {}).get("name")
            if provider is None:
                return False
            
            # Check provider
            if provider not in self.providers:
                return False
        
        return True
    
    def _create_event(self, data: Dict[str, Any]) -> LogEvent:
        """
        Create a LogEvent from a Windows Event Log entry.
        
        Args:
            data: Windows Event Log entry
            
        Returns:
            LogEvent
        """
        winlog = data.get("winlog", {})
        
        # Get timestamp
        timestamp = None
        if "@timestamp" in data:
            try:
                timestamp = datetime.fromisoformat(data["@timestamp"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        
        # Create the event
        event = LogEvent(
            raw_data=json.dumps(data),
            source_type="winlog",
            source_name=winlog.get("channel", "unknown"),
            timestamp=timestamp or datetime.utcnow(),
            fields={
                "event_id": winlog.get("event_id"),
                "level": winlog.get("level"),
                "provider": winlog.get("provider", {}).get("name"),
                "computer_name": winlog.get("computer_name"),
                "record_id": winlog.get("record_id"),
                "task": winlog.get("task"),
                "keywords": winlog.get("keywords"),
                "message": data.get("message"),
                "host": data.get("host", {})
            },
            metadata={
                "winlog_source": self.mode,
                "winlog_channel": winlog.get("channel")
            }
        )
        
        # Add event data
        if "event_data" in winlog:
            event.add_field("event_data", winlog["event_data"])
        
        # Add user data
        if "user" in winlog:
            event.add_field("user", winlog["user"])
        
        return event
    
    async def read(self) -> AsyncIterator[LogEvent]:
        """
        Read log events from Windows Event Logs.
        
        Yields:
            LogEvent objects
        """
        self.running = True
        
        try:
            if self.mode == "file":
                # Read from a single file
                async for event in self._read_file(self.path):
                    yield event
            
            elif self.mode == "directory":
                # Scan a directory for files
                async for event in self._scan_directory():
                    yield event
            
            elif self.mode == "tcp":
                # Start a TCP server
                async for event in self._start_tcp_server():
                    yield event
        
        except asyncio.CancelledError:
            # Handle cancellation
            pass
        
        except Exception as e:
            # Log the error
            print(f"Error reading Windows Event Logs: {str(e)}")
        
        finally:
            self.running = False
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        self.running = False