#!/usr/bin/env python3
"""
Example of using LogFlow programmatically.
"""
import asyncio
import logging
import signal
import sys

from logflow.core.engine import Engine
from logflow.core.models import LogEvent
from logflow.sources.file import FileSource
from logflow.processors.json import JsonProcessor
from logflow.processors.filter import FilterProcessor
from logflow.sinks.file import FileSink


async def run_custom_pipeline():
    """Run a custom pipeline programmatically."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout
    )
    
    # Create components
    source = FileSource()
    await source.initialize({
        "path": "/tmp/test.log",
        "tail": True,
        "read_from_start": True
    })
    
    json_processor = JsonProcessor()
    await json_processor.initialize({
        "field": "raw_data",
        "target_field": "",
        "preserve_original": True
    })
    
    filter_processor = FilterProcessor()
    await filter_processor.initialize({
        "condition": "level in [ERROR, CRITICAL]",
        "mode": "all"
    })
    
    sink = FileSink()
    await sink.initialize({
        "path": "/tmp/errors.log",
        "format": "text",
        "template": "{timestamp} [{level}] {service}: {message}"
    })
    
    # Process events
    try:
        logging.info("Starting custom pipeline")
        
        # Set up signal handling
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(cleanup()))
        
        # Process events
        batch = []
        async for event in source.read():
            # Process the event
            processed_event = await json_processor.process(event)
            if processed_event:
                filtered_event = await filter_processor.process(processed_event)
                if filtered_event:
                    batch.append(filtered_event)
                    
                    # Write batch if it reaches 10 events
                    if len(batch) >= 10:
                        await sink.write(batch)
                        batch = []
        
        # Write any remaining events
        if batch:
            await sink.write(batch)
    
    finally:
        # Clean up
        await cleanup()


async def cleanup():
    """Clean up resources."""
    logging.info("Cleaning up resources")
    # This would normally clean up your resources


async def run_with_engine():
    """Run using the Engine API."""
    # Create an engine
    engine = Engine()
    
    # Load and start a pipeline from a configuration file
    await engine.load_pipeline("/workspace/logflow/examples/simple.yaml")
    await engine.start_pipeline("simple-pipeline")
    
    # Wait for Ctrl+C
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        # Stop the engine
        await engine.stop()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Example of using LogFlow programmatically")
    parser.add_argument("--mode", choices=["custom", "engine"], default="engine",
                        help="Mode to run in: custom (custom pipeline) or engine (using Engine API)")
    args = parser.parse_args()
    
    if args.mode == "custom":
        asyncio.run(run_custom_pipeline())
    else:
        asyncio.run(run_with_engine())