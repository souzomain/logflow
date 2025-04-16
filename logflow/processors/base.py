"""
Base interface for log processors.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from logflow.core.models import LogEvent


class Processor(ABC):
    """
    Abstract base class for all log processors.
    
    Processors are responsible for transforming, filtering, and enriching
    log events in the pipeline.
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the processor with the provided configuration.
        
        Args:
            config: Processor configuration
        """
        pass
    
    @abstractmethod
    async def process(self, event: LogEvent) -> Optional[LogEvent]:
        """
        Process a log event.
        
        Args:
            event: The log event to process
            
        Returns:
            The processed log event, or None if the event should be dropped
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        pass