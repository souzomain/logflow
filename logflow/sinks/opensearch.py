"""
OpenSearch sink for LogFlow.
"""
import asyncio
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

from opensearchpy import AsyncOpenSearch, helpers

from logflow.core.models import LogEvent
from logflow.sinks.base import Sink


class OpenSearchSink(Sink):
    """
    Sink that writes log events to OpenSearch.
    """
    
    def __init__(self):
        """
        Initialize a new OpenSearchSink.
        """
        self.hosts = []
        self.index = "logs-{yyyy.MM.dd}"
        self.client = None
        self.username = None
        self.password = None
        self.api_key = None
        self.ssl_verify = True
        self.batch_size = 1000
        self.timeout = 30
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the sink with the provided configuration.
        
        Args:
            config: Sink configuration with the following keys:
                - hosts: List of OpenSearch hosts (required)
                - index: Index pattern (default: "logs-{yyyy.MM.dd}")
                - username: Username for authentication
                - password: Password for authentication
                - api_key: API key for authentication
                - ssl_verify: Whether to verify SSL certificates (default: True)
                - batch_size: Maximum batch size (default: 1000)
                - timeout: Request timeout in seconds (default: 30)
        """
        self.hosts = config.get("hosts")
        if not self.hosts:
            raise ValueError("OpenSearch hosts are required")
        
        self.index = config.get("index", "logs-{yyyy.MM.dd}")
        self.username = config.get("username")
        self.password = config.get("password")
        self.api_key = config.get("api_key")
        self.ssl_verify = config.get("ssl_verify", True)
        self.batch_size = int(config.get("batch_size", 1000))
        self.timeout = int(config.get("timeout", 30))
        
        # Create the OpenSearch client
        client_kwargs = {
            "hosts": self.hosts,
            "verify_certs": self.ssl_verify,
            "timeout": self.timeout
        }
        
        # Add authentication if provided
        if self.username and self.password:
            client_kwargs["http_auth"] = (self.username, self.password)
        elif self.api_key:
            client_kwargs["api_key"] = self.api_key
        
        self.client = AsyncOpenSearch(**client_kwargs)
    
    def _format_index(self, timestamp: datetime) -> str:
        """
        Format the index name using the timestamp.
        
        Args:
            timestamp: Timestamp to use for formatting
            
        Returns:
            Formatted index name
        """
        return self.index.format(
            yyyy=timestamp.strftime("%Y"),
            MM=timestamp.strftime("%m"),
            dd=timestamp.strftime("%d"),
            HH=timestamp.strftime("%H")
        )
    
    def _event_to_action(self, event: LogEvent) -> Dict[str, Any]:
        """
        Convert a log event to an OpenSearch bulk action.
        
        Args:
            event: Log event to convert
            
        Returns:
            OpenSearch bulk action
        """
        # Format the index name
        index = self._format_index(event.timestamp)
        
        # Convert the event to a document
        doc = event.to_dict()
        
        # Create the action
        return {
            "_index": index,
            "_id": event.id,
            "_source": doc
        }
    
    async def write(self, events: List[LogEvent]) -> None:
        """
        Write a batch of log events to OpenSearch.
        
        Args:
            events: List of log events to write
        """
        if not events:
            return
        
        # Convert events to bulk actions
        actions = [self._event_to_action(event) for event in events]
        
        # Send the bulk request
        try:
            success, failed = await helpers.async_bulk(
                client=self.client,
                actions=actions,
                chunk_size=self.batch_size,
                max_retries=3,
                initial_backoff=2,
                max_backoff=60
            )
            
            # Log the response
            if failed > 0:
                print(f"OpenSearch bulk write: {success} succeeded, {failed} failed")
        
        except Exception as e:
            # Log the error
            print(f"Error writing to OpenSearch: {str(e)}")
            raise
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        if self.client:
            await self.client.close()
            self.client = None