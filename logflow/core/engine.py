"""
Main engine for LogFlow.
"""
import asyncio
import logging
import os
import signal
import time
from typing import Dict, List, Optional

from logflow.core.config import load_config_file, validate_pipeline_config
from logflow.core.pipeline import Pipeline


class Engine:
    """
    Main engine for LogFlow.
    
    The engine is responsible for:
    1. Loading and validating configurations
    2. Creating and managing pipelines
    3. Handling signals and graceful shutdown
    """
    
    def __init__(self):
        """
        Initialize a new engine.
        """
        self.pipelines: Dict[str, Pipeline] = {}
        self.running = False
        self.logger = logging.getLogger("logflow.engine")
    
    async def load_pipeline(self, config_path: str) -> Pipeline:
        """
        Load a pipeline from a configuration file.
        
        Args:
            config_path: Path to the pipeline configuration file
            
        Returns:
            The created pipeline
            
        Raises:
            Exception: If the pipeline cannot be loaded
        """
        self.logger.info(f"Loading pipeline from {config_path}")
        
        # Load and validate the configuration
        config = load_config_file(config_path)
        validate_pipeline_config(config)
        
        # Create the pipeline
        pipeline_name = config["name"]
        if pipeline_name in self.pipelines:
            self.logger.warning(f"Replacing existing pipeline: {pipeline_name}")
            await self.stop_pipeline(pipeline_name)
        
        pipeline = Pipeline(pipeline_name, config)
        await pipeline.initialize()
        
        # Store the pipeline
        self.pipelines[pipeline_name] = pipeline
        
        return pipeline
    
    async def start_pipeline(self, pipeline_name: str) -> None:
        """
        Start a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline to start
            
        Raises:
            KeyError: If the pipeline does not exist
        """
        if pipeline_name not in self.pipelines:
            raise KeyError(f"Pipeline not found: {pipeline_name}")
        
        pipeline = self.pipelines[pipeline_name]
        asyncio.create_task(pipeline.run())
        self.logger.info(f"Started pipeline: {pipeline_name}")
    
    async def stop_pipeline(self, pipeline_name: str) -> None:
        """
        Stop a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline to stop
            
        Raises:
            KeyError: If the pipeline does not exist
        """
        if pipeline_name not in self.pipelines:
            raise KeyError(f"Pipeline not found: {pipeline_name}")
        
        pipeline = self.pipelines[pipeline_name]
        await pipeline.stop()
        self.logger.info(f"Stopped pipeline: {pipeline_name}")
    
    async def start(self, config_paths: List[str]) -> None:
        """
        Start the engine with the specified pipeline configurations.
        
        Args:
            config_paths: List of paths to pipeline configuration files
        """
        if self.running:
            self.logger.warning("Engine is already running")
            return
        
        self.running = True
        self.logger.info("Starting LogFlow engine")
        
        # Set up signal handlers
        self._setup_signal_handlers()
        
        # Load and start all pipelines
        for config_path in config_paths:
            try:
                pipeline = await self.load_pipeline(config_path)
                await self.start_pipeline(pipeline.name)
            except Exception as e:
                self.logger.error(f"Failed to start pipeline from {config_path}: {str(e)}", exc_info=True)
        
        self.logger.info(f"LogFlow engine started with {len(self.pipelines)} pipelines")
    
    async def stop(self) -> None:
        """
        Stop the engine and all pipelines.
        """
        if not self.running:
            self.logger.warning("Engine is not running")
            return
        
        self.logger.info("Stopping LogFlow engine")
        
        # Stop all pipelines
        for pipeline_name in list(self.pipelines.keys()):
            try:
                await self.stop_pipeline(pipeline_name)
            except Exception as e:
                self.logger.error(f"Error stopping pipeline {pipeline_name}: {str(e)}", exc_info=True)
        
        self.running = False
        self.logger.info("LogFlow engine stopped")
    
    def _setup_signal_handlers(self) -> None:
        """
        Set up signal handlers for graceful shutdown.
        """
        loop = asyncio.get_running_loop()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.stop())
            )
        
        self.logger.debug("Signal handlers set up")
    
    def get_pipeline(self, pipeline_name: str) -> Optional[Pipeline]:
        """
        Get a pipeline by name.
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            The pipeline, or None if it does not exist
        """
        return self.pipelines.get(pipeline_name)
    
    def get_pipeline_names(self) -> List[str]:
        """
        Get the names of all pipelines.
        
        Returns:
            List of pipeline names
        """
        return list(self.pipelines.keys())
    
    def get_pipeline_status(self, pipeline_name: str) -> Dict[str, any]:
        """
        Get the status of a pipeline.
        
        Args:
            pipeline_name: Name of the pipeline
            
        Returns:
            Dictionary with pipeline status information
            
        Raises:
            KeyError: If the pipeline does not exist
        """
        if pipeline_name not in self.pipelines:
            raise KeyError(f"Pipeline not found: {pipeline_name}")
        
        pipeline = self.pipelines[pipeline_name]
        
        return {
            "name": pipeline.name,
            "running": pipeline.running,
            "sources": len(pipeline.sources),
            "processors": len(pipeline.processors),
            "sinks": len(pipeline.sinks),
            "events_processed": pipeline.events_processed,
            "events_dropped": pipeline.events_dropped,
            "processing_errors": pipeline.processing_errors,
            "uptime": time.time() - pipeline.start_time if pipeline.running else 0
        }