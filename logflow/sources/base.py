"""
Base interface for log sources.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any

from logflow.core.models import LogEvent


class Source(ABC):
    """
    Abstract base class for all log sources.
    
    Sources are responsible for collecting logs from different origins
    and converting them to LogEvent objects.
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the source with the provided configuration.
        
        Args:
            config: Source configuration
        """
        pass
    
    @abstractmethod
    async def read(self) -> AsyncIterator[LogEvent]:
        """
        Read log events from the source.
        
        Yields:
            LogEvent objects
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        pass