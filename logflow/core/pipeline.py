"""
Pipeline implementation for LogFlow.
"""
import asyncio
from typing import Any, Dict, List, Optional, Type
import importlib
import logging
import time

from logflow.core.models import LogEvent
from logflow.sources.base import Source
from logflow.processors.base import Processor
from logflow.sinks.base import Sink


class Pipeline:
    """
    A processing pipeline that connects sources, processors, and sinks.
    
    The pipeline is responsible for:
    1. Initializing all components
    2. Reading events from sources
    3. Passing events through processors
    4. Writing processed events to sinks
    5. Managing the lifecycle of all components
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize a new pipeline.
        
        Args:
            name: Pipeline name
            config: Pipeline configuration
        """
        self.name = name
        self.config = config
        self.sources: List[Source] = []
        self.processors: List[Processor] = []
        self.sinks: List[Sink] = []
        self.running = False
        self.logger = logging.getLogger(f"logflow.pipeline.{name}")
        
        # Metrics
        self.events_processed = 0
        self.events_dropped = 0
        self.processing_errors = 0
        self.start_time = 0
    
    async def initialize(self) -> None:
        """
        Initialize all components of the pipeline.
        
        Raises:
            Exception: If any component fails to initialize
        """
        self.logger.info(f"Initializing pipeline: {self.name}")
        
        # Initialize sources
        for source_config in self.config.get("sources", []):
            source = self._create_component(
                component_type="source",
                component_name=source_config["name"],
                component_class=source_config["type"]
            )
            await source.initialize(source_config.get("config", {}))
            self.sources.append(source)
        
        # Initialize processors
        for processor_config in self.config.get("processors", []):
            processor = self._create_component(
                component_type="processor",
                component_name=processor_config["name"],
                component_class=processor_config["type"]
            )
            await processor.initialize(processor_config.get("config", {}))
            self.processors.append(processor)
        
        # Initialize sinks
        for sink_config in self.config.get("sinks", []):
            sink = self._create_component(
                component_type="sink",
                component_name=sink_config["name"],
                component_class=sink_config["type"]
            )
            await sink.initialize(sink_config.get("config", {}))
            self.sinks.append(sink)
        
        self.logger.info(f"Pipeline initialized: {self.name} "
                        f"({len(self.sources)} sources, "
                        f"{len(self.processors)} processors, "
                        f"{len(self.sinks)} sinks)")
    
    def _create_component(self, component_type: str, component_name: str, component_class: str) -> Any:
        """
        Create a component instance by importing its class.
        
        Args:
            component_type: Type of component (source, processor, sink)
            component_name: Name of the component
            component_class: Class name of the component
            
        Returns:
            Component instance
            
        Raises:
            ImportError: If the component class cannot be imported
            Exception: If the component cannot be instantiated
        """
        try:
            # Determine the module path based on component type and class
            if "." in component_class:
                # If the class name includes a module path, use it directly
                module_path = component_class
                class_name = module_path.split(".")[-1]
                module_path = ".".join(module_path.split(".")[:-1])
            else:
                # Otherwise, use the default module path based on component type
                # Map simplified names to actual class names
                component_map = {
                    # Sources
                    "file": "FileSource",
                    "kafka": "KafkaSource",
                    "s3": "S3Source",
                    "winlog": "WinlogSource",
                    
                    # Processors
                    "json": "JsonProcessor",
                    "filter": "FilterProcessor",
                    "regex": "RegexProcessor",
                    "grok": "GrokProcessor",
                    "mutate": "MutateProcessor",
                    "enrich": "EnrichProcessor",
                    
                    # Sinks
                    "file": "FileSink",
                    "elasticsearch": "ElasticsearchSink",
                    "opensearch": "OpenSearchSink",
                    "s3": "S3Sink"
                }
                
                # Get the actual class name from the map, or use the original name
                actual_class = component_map.get(component_class.lower(), component_class)
                
                # Use the module path based on component type and the original class name
                module_path = f"logflow.{component_type}s.{component_class.lower()}"
                class_name = actual_class
            
            # Import the module and get the class
            module = importlib.import_module(module_path)
            component_cls = getattr(module, class_name)
            
            # Create and return an instance
            return component_cls()
        except ImportError as e:
            self.logger.error(f"Failed to import {component_type} class {component_class}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to create {component_type} {component_name}: {str(e)}")
            raise
    
    async def run(self) -> None:
        """
        Run the pipeline until stopped.
        """
        if self.running:
            self.logger.warning(f"Pipeline {self.name} is already running")
            return
        
        self.running = True
        self.start_time = time.time()
        self.logger.info(f"Starting pipeline: {self.name}")
        
        try:
            # Create tasks for each source
            source_tasks = [
                asyncio.create_task(self._process_source(source))
                for source in self.sources
            ]
            
            # Wait for all source tasks to complete
            await asyncio.gather(*source_tasks)
        except asyncio.CancelledError:
            self.logger.info(f"Pipeline {self.name} was cancelled")
        except Exception as e:
            self.logger.error(f"Error in pipeline {self.name}: {str(e)}", exc_info=True)
            self.processing_errors += 1
        finally:
            self.running = False
            self.logger.info(f"Pipeline {self.name} stopped")
    
    async def _process_source(self, source: Source) -> None:
        """
        Process events from a single source.
        
        Args:
            source: Source to process
        """
        batch_size = self.config.get("batch_size", 100)
        batch_timeout = self.config.get("batch_timeout", 5.0)  # seconds
        
        try:
            batch: List[LogEvent] = []
            last_flush_time = time.time()
            
            async for event in source.read():
                if not self.running:
                    break
                
                # Process the event through all processors
                processed_event = await self._process_event(event)
                
                # If the event wasn't dropped, add it to the batch
                if processed_event:
                    batch.append(processed_event)
                
                # Flush the batch if it's full or if the timeout has elapsed
                current_time = time.time()
                if (len(batch) >= batch_size or 
                    current_time - last_flush_time >= batch_timeout) and batch:
                    await self._flush_batch(batch)
                    batch = []
                    last_flush_time = current_time
            
            # Flush any remaining events
            if batch:
                await self._flush_batch(batch)
        except Exception as e:
            self.logger.error(f"Error processing source: {str(e)}", exc_info=True)
            self.processing_errors += 1
    
    async def _process_event(self, event: LogEvent) -> Optional[LogEvent]:
        """
        Process an event through all processors.
        
        Args:
            event: Event to process
            
        Returns:
            Processed event, or None if the event was dropped
        """
        try:
            current_event = event
            
            # Pass the event through each processor in sequence
            for processor in self.processors:
                if current_event is None:
                    break
                
                current_event = await processor.process(current_event)
            
            if current_event:
                self.events_processed += 1
            else:
                self.events_dropped += 1
            
            return current_event
        except Exception as e:
            self.logger.error(f"Error processing event: {str(e)}", exc_info=True)
            self.processing_errors += 1
            self.events_dropped += 1
            return None
    
    async def _flush_batch(self, batch: List[LogEvent]) -> None:
        """
        Flush a batch of events to all sinks.
        
        Args:
            batch: Batch of events to flush
        """
        if not batch:
            return
        
        # Send the batch to each sink
        for sink in self.sinks:
            try:
                await sink.write(batch)
            except Exception as e:
                self.logger.error(f"Error writing to sink: {str(e)}", exc_info=True)
                self.processing_errors += 1
    
    async def stop(self) -> None:
        """
        Stop the pipeline and clean up resources.
        """
        if not self.running:
            self.logger.warning(f"Pipeline {self.name} is not running")
            return
        
        self.logger.info(f"Stopping pipeline: {self.name}")
        self.running = False
        
        # Shutdown all components
        components = self.sources + self.processors + self.sinks
        for component in components:
            try:
                await component.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down component: {str(e)}", exc_info=True)
        
        # Log pipeline statistics
        runtime = time.time() - self.start_time
        self.logger.info(
            f"Pipeline {self.name} statistics: "
            f"processed={self.events_processed}, "
            f"dropped={self.events_dropped}, "
            f"errors={self.processing_errors}, "
            f"runtime={runtime:.2f}s"
        )