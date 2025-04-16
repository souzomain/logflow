"""
Base interface for log sinks.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

from logflow.core.models import LogEvent


class Sink(ABC):
    """
    Abstract base class for all log sinks.
    
    Sinks are responsible for sending processed log events to their
    final destinations.
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the sink with the provided configuration.
        
        Args:
            config: Sink configuration
        """
        pass
    
    @abstractmethod
    async def write(self, events: List[LogEvent]) -> None:
        """
        Write a batch of log events to the destination.
        
        Args:
            events: List of log events to write
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        pass