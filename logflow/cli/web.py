"""
CLI commands for the web interface.
"""
import click

from logflow.web.server import start_web_server


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8080, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def web(host, port, reload):
    """Start the web interface."""
    click.echo(f"Starting LogFlow web interface on http://{host}:{port}")
    start_web_server(host=host, port=port, reload=reload)