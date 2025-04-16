"""
Command-line interface for LogFlow.
"""
import asyncio
import logging
import os
import sys
from typing import List

import click

from logflow.core.engine import Engine


def setup_logging(verbose: bool) -> None:
    """
    Set up logging configuration.
    
    Args:
        verbose: Whether to enable verbose logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Configure the root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout
    )


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, verbose):
    """LogFlow: A flexible ETL system for log processing."""
    # Set up logging
    setup_logging(verbose)
    
    # Create an engine instance and store it in the context
    ctx.obj = {"engine": Engine()}
    
# Import web command
from logflow.cli.web import web
cli.add_command(web)


@cli.command()
@click.option("--config", "-c", required=True, multiple=True, help="Path to pipeline configuration file(s)")
@click.pass_context
def start(ctx, config):
    """Start LogFlow with the specified pipeline configuration(s)."""
    engine = ctx.obj["engine"]
    
    # Validate configuration paths
    for path in config:
        if not os.path.exists(path):
            click.echo(f"Error: Configuration file not found: {path}", err=True)
            sys.exit(1)
    
    # Run the engine
    try:
        asyncio.run(engine.start(config))
    except KeyboardInterrupt:
        click.echo("Stopping LogFlow...")
        asyncio.run(engine.stop())
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show the status of all pipelines."""
    engine = ctx.obj["engine"]
    
    # Get pipeline names
    pipeline_names = engine.get_pipeline_names()
    
    if not pipeline_names:
        click.echo("No pipelines are running")
        return
    
    # Print status for each pipeline
    click.echo("Pipeline Status:")
    click.echo("---------------")
    
    for name in pipeline_names:
        try:
            status = engine.get_pipeline_status(name)
            
            # Format status
            running = "RUNNING" if status["running"] else "STOPPED"
            processed = status["events_processed"]
            dropped = status["events_dropped"]
            errors = status["processing_errors"]
            
            click.echo(f"{name}: {running}")
            click.echo(f"  Sources: {status['sources']}")
            click.echo(f"  Processors: {status['processors']}")
            click.echo(f"  Sinks: {status['sinks']}")
            click.echo(f"  Events: {processed} processed, {dropped} dropped, {errors} errors")
            
            if status["running"]:
                uptime = status["uptime"]
                click.echo(f"  Uptime: {uptime:.2f} seconds")
            
            click.echo("")
        
        except Exception as e:
            click.echo(f"Error getting status for {name}: {str(e)}", err=True)


@cli.command()
@click.argument("pipeline", required=True)
@click.pass_context
def restart(ctx, pipeline):
    """Restart a specific pipeline."""
    engine = ctx.obj["engine"]
    
    try:
        # Stop the pipeline
        asyncio.run(engine.stop_pipeline(pipeline))
        
        # Start the pipeline
        asyncio.run(engine.start_pipeline(pipeline))
        
        click.echo(f"Pipeline {pipeline} restarted")
    
    except KeyError:
        click.echo(f"Error: Pipeline not found: {pipeline}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli(obj={})