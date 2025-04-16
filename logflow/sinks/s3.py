"""
S3 sink for LogFlow.
"""
import asyncio
import io
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

import aiobotocore.session

from logflow.core.models import LogEvent
from logflow.sinks.base import Sink


class S3Sink(Sink):
    """
    Sink that writes log events to Amazon S3.
    """
    
    def __init__(self):
        """
        Initialize a new S3Sink.
        """
        self.bucket = ""
        self.key_prefix = ""
        self.region = "us-east-1"
        self.aws_access_key_id = None
        self.aws_secret_access_key = None
        self.aws_session_token = None
        self.endpoint_url = None
        self.format = "json"  # json, text
        self.template = "{timestamp} {message}"
        self.message_field = "message"
        self.buffer_size = 10 * 1024 * 1024  # 10 MB
        self.buffer = io.BytesIO()
        self.buffer_count = 0
        self.session = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the sink with the provided configuration.
        
        Args:
            config: Sink configuration with the following keys:
                - bucket: S3 bucket name (required)
                - key_prefix: S3 key prefix (default: "")
                - region: AWS region (default: "us-east-1")
                - aws_access_key_id: AWS access key ID (optional)
                - aws_secret_access_key: AWS secret access key (optional)
                - aws_session_token: AWS session token (optional)
                - endpoint_url: Custom endpoint URL for S3 (optional)
                - format: Output format: "json" or "text" (default: "json")
                - template: Template for text format (default: "{timestamp} {message}")
                - message_field: Field to use as message in text format (default: "message")
                - buffer_size: Buffer size in bytes before flushing to S3 (default: 10 MB)
        """
        self.bucket = config.get("bucket")
        if not self.bucket:
            raise ValueError("S3 bucket is required")
        
        self.key_prefix = config.get("key_prefix", "")
        self.region = config.get("region", "us-east-1")
        self.aws_access_key_id = config.get("aws_access_key_id")
        self.aws_secret_access_key = config.get("aws_secret_access_key")
        self.aws_session_token = config.get("aws_session_token")
        self.endpoint_url = config.get("endpoint_url")
        
        self.format = config.get("format", "json")
        if self.format not in ["json", "text"]:
            raise ValueError(f"Invalid format: {self.format}")
        
        self.template = config.get("template", "{timestamp} {message}")
        self.message_field = config.get("message_field", "message")
        self.buffer_size = int(config.get("buffer_size", 10 * 1024 * 1024))
        
        # Create the S3 session
        self.session = aiobotocore.session.get_session()
    
    async def _get_client(self):
        """
        Get an S3 client.
        
        Returns:
            S3 client
        """
        client_kwargs = {
            "region_name": self.region,
        }
        
        if self.aws_access_key_id and self.aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = self.aws_access_key_id
            client_kwargs["aws_secret_access_key"] = self.aws_secret_access_key
            
            if self.aws_session_token:
                client_kwargs["aws_session_token"] = self.aws_session_token
        
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url
        
        return self.session.create_client("s3", **client_kwargs)
    
    def _generate_key(self) -> str:
        """
        Generate an S3 key for the current batch.
        
        Returns:
            S3 key
        """
        now = datetime.utcnow()
        date_part = now.strftime("%Y/%m/%d/%H")
        timestamp = now.strftime("%Y%m%d%H%M%S")
        
        if self.key_prefix:
            return f"{self.key_prefix}/{date_part}/logs_{timestamp}_{self.buffer_count}.log"
        else:
            return f"{date_part}/logs_{timestamp}_{self.buffer_count}.log"
    
    async def _flush_buffer(self) -> None:
        """
        Flush the buffer to S3.
        """
        if self.buffer_count == 0:
            return
        
        # Reset the buffer position
        self.buffer.seek(0)
        
        # Generate the S3 key
        key = self._generate_key()
        
        try:
            # Upload the buffer to S3
            async with await self._get_client() as client:
                await client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=self.buffer.read()
                )
            
            # Reset the buffer
            self.buffer = io.BytesIO()
            self.buffer_count = 0
        
        except Exception as e:
            # Log the error
            print(f"Error flushing buffer to S3: {str(e)}")
            raise
    
    async def write(self, events: List[LogEvent]) -> None:
        """
        Write a batch of log events to S3.
        
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
            
            # Write the line to the buffer
            self.buffer.write(line.encode("utf-8"))
            self.buffer_count += 1
        
        # Flush the buffer if it's full
        if self.buffer.tell() >= self.buffer_size:
            await self._flush_buffer()
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        # Flush any remaining events
        await self._flush_buffer()