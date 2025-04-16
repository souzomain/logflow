"""
Kafka source for LogFlow.
"""
import asyncio
from datetime import datetime
from typing import AsyncIterator, Dict, Any, List, Optional

from aiokafka import AIOKafkaConsumer

from logflow.core.models import LogEvent
from logflow.sources.base import Source


class KafkaSource(Source):
    """
    Source that reads logs from Kafka topics.
    
    Features:
    - Subscribes to one or more Kafka topics
    - Supports consumer groups for distributed processing
    - Automatic offset management
    """
    
    def __init__(self):
        """
        Initialize a new KafkaSource.
        """
        self.brokers = []
        self.topics = []
        self.group_id = None
        self.consumer = None
        self.running = False
        self.auto_offset_reset = "latest"
        self.max_poll_records = 500
        self.consumer_timeout_ms = 1000
        self.metadata = {}
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the source with the provided configuration.
        
        Args:
            config: Source configuration with the following keys:
                - brokers: List of Kafka brokers (required)
                - topics: List of topics to subscribe to (required)
                - group_id: Consumer group ID (optional)
                - auto_offset_reset: Where to start consuming from if no offset is stored
                  (default: "latest", options: "earliest", "latest")
                - max_poll_records: Maximum number of records to fetch in a single poll (default: 500)
                - consumer_timeout_ms: Timeout for consumer operations in milliseconds (default: 1000)
                - metadata: Additional metadata to include with each event (default: {})
        """
        self.brokers = config.get("brokers")
        if not self.brokers:
            raise ValueError("Kafka brokers are required")
        
        self.topics = config.get("topics")
        if not self.topics:
            raise ValueError("Kafka topics are required")
        
        self.group_id = config.get("group_id")
        self.auto_offset_reset = config.get("auto_offset_reset", "latest")
        self.max_poll_records = int(config.get("max_poll_records", 500))
        self.consumer_timeout_ms = int(config.get("consumer_timeout_ms", 1000))
        self.metadata = config.get("metadata", {})
        
        # Create the Kafka consumer
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.brokers,
            group_id=self.group_id,
            auto_offset_reset=self.auto_offset_reset,
            max_poll_records=self.max_poll_records,
            consumer_timeout_ms=self.consumer_timeout_ms,
            enable_auto_commit=True
        )
        
        # Start the consumer
        await self.consumer.start()
    
    async def read(self) -> AsyncIterator[LogEvent]:
        """
        Read log events from Kafka.
        
        Yields:
            LogEvent objects
        """
        self.running = True
        
        try:
            while self.running:
                try:
                    # Poll for messages
                    async for message in self.consumer:
                        if not self.running:
                            break
                        
                        # Get the message value as string
                        try:
                            raw_data = message.value.decode("utf-8")
                        except (UnicodeDecodeError, AttributeError):
                            # If decoding fails, use the raw bytes as string representation
                            raw_data = str(message.value)
                        
                        # Create and yield a log event
                        event = LogEvent(
                            raw_data=raw_data,
                            source_type="kafka",
                            source_name=message.topic,
                            timestamp=datetime.utcnow(),
                            metadata={
                                "kafka_topic": message.topic,
                                "kafka_partition": message.partition,
                                "kafka_offset": message.offset,
                                "kafka_timestamp": message.timestamp,
                                "kafka_key": message.key.decode("utf-8") if message.key else None,
                                **self.metadata
                            }
                        )
                        
                        yield event
                
                except asyncio.CancelledError:
                    # Handle cancellation
                    break
                
                except Exception as e:
                    # Log the error and continue
                    print(f"Error reading from Kafka: {str(e)}")
                    await asyncio.sleep(1)
        
        finally:
            # Ensure the consumer is stopped if we exit the loop
            if self.consumer and self.consumer._closed is False:
                await self.consumer.stop()
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        self.running = False
        
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None