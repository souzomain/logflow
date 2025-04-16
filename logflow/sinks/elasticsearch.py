"""
Elasticsearch sink for LogFlow.
"""
import asyncio
from datetime import datetime
import json
from typing import Dict, Any, List, Optional

from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk

from logflow.core.models import LogEvent
from logflow.sinks.base import Sink


class ElasticsearchSink(Sink):
    """
    Sink that writes log events to Elasticsearch.
    """
    
    def __init__(self):
        """
        Initialize a new ElasticsearchSink.
        """
        self.hosts = []
        self.index = "logs-{yyyy.MM.dd}"
        self.client = None
        self.username = None
        self.password = None
        self.api_key = None
        self.cloud_id = None
        self.ssl_verify = True
        self.batch_size = 1000
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the sink with the provided configuration.
        
        Args:
            config: Sink configuration with the following keys:
                - hosts: List of Elasticsearch hosts (required)
                - index: Index pattern (default: "logs-{yyyy.MM.dd}")
                - username: Username for authentication
                - password: Password for authentication
                - api_key: API key for authentication
                - cloud_id: Cloud ID for Elastic Cloud
                - ssl_verify: Whether to verify SSL certificates (default: True)
                - batch_size: Maximum batch size (default: 1000)
        """
        self.hosts = config.get("hosts")
        if not self.hosts:
            raise ValueError("Elasticsearch hosts are required")
        
        self.index = config.get("index", "logs-{yyyy.MM.dd}")
        self.username = config.get("username")
        self.password = config.get("password")
        self.api_key = config.get("api_key")
        self.cloud_id = config.get("cloud_id")
        self.ssl_verify = config.get("ssl_verify", True)
        self.batch_size = int(config.get("batch_size", 1000))
        
        # Create the Elasticsearch client
        client_kwargs = {
            "hosts": self.hosts,
            "verify_certs": self.ssl_verify,
        }
        
        # Add authentication if provided
        if self.username and self.password:
            client_kwargs["basic_auth"] = (self.username, self.password)
        elif self.api_key:
            client_kwargs["api_key"] = self.api_key
        
        if self.cloud_id:
            client_kwargs["cloud_id"] = self.cloud_id
        
        self.client = AsyncElasticsearch(**client_kwargs)
    
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
        Convert a log event to an Elasticsearch bulk action.
        
        Args:
            event: Log event to convert
            
        Returns:
            Elasticsearch bulk action
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
        Write a batch of log events to Elasticsearch.
        
        Args:
            events: List of log events to write
        """
        if not events:
            return
        
        # Convert events to bulk actions
        actions = [self._event_to_action(event) for event in events]
        
        # Send the bulk request
        try:
            response = await async_bulk(
                client=self.client,
                actions=actions,
                chunk_size=self.batch_size,
                max_retries=3,
                initial_backoff=2,
                max_backoff=60
            )
            
            # Log the response
            success, failed = response
            if failed > 0:
                print(f"Elasticsearch bulk write: {success} succeeded, {failed} failed")
        
        except Exception as e:
            # Log the error
            print(f"Error writing to Elasticsearch: {str(e)}")
            raise
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        if self.client:
            await self.client.close()
            self.client = None