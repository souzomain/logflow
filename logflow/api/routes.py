"""
API routes for LogFlow.
"""
import uvicorn

from logflow.api.server import app


def start_api_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Start the API server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Whether to enable auto-reload
    """
    uvicorn.run(
        "logflow.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )