"""
Web server for LogFlow.
"""
import asyncio
import logging
import os
import time
from typing import Dict, List, Any, Optional

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from logflow.core.engine import Engine


# Create the FastAPI app
app = FastAPI(
    title="LogFlow Dashboard",
    description="Web interface for monitoring LogFlow pipelines",
    version="0.1.0"
)

# Create the engine
engine = Engine()

# Set up logging
logger = logging.getLogger("logflow.web")

# Set up templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Set up static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_json(message)


# Create connection manager
manager = ConnectionManager()


@app.on_event("startup")
async def startup_event():
    """Initialize the engine on startup."""
    logger.info("Starting LogFlow web server")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the engine on shutdown."""
    logger.info("Stopping LogFlow web server")
    await engine.stop()


@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Get the dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/pipelines")
async def get_pipelines():
    """Get all pipelines."""
    pipeline_names = engine.get_pipeline_names()
    pipelines = []
    
    for name in pipeline_names:
        try:
            status = engine.get_pipeline_status(name)
            pipelines.append(status)
        except Exception as e:
            logger.error(f"Error getting status for pipeline {name}: {str(e)}")
    
    return {"pipelines": pipelines}


@app.get("/api/pipelines/{name}")
async def get_pipeline(name: str):
    """Get pipeline status."""
    try:
        return engine.get_pipeline_status(name)
    except KeyError:
        return {"error": f"Pipeline not found: {name}"}


@app.post("/api/pipelines/{name}/start")
async def start_pipeline(name: str):
    """Start a pipeline."""
    try:
        await engine.start_pipeline(name)
        return {"status": "started", "name": name}
    except KeyError:
        return {"error": f"Pipeline not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/pipelines/{name}/stop")
async def stop_pipeline(name: str):
    """Stop a pipeline."""
    try:
        await engine.stop_pipeline(name)
        return {"status": "stopped", "name": name}
    except KeyError:
        return {"error": f"Pipeline not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics."""
    metrics = {
        "pipelines": len(engine.get_pipeline_names()),
        "pipeline_metrics": {}
    }
    
    # Add metrics for each pipeline
    for name in engine.get_pipeline_names():
        try:
            status = engine.get_pipeline_status(name)
            metrics["pipeline_metrics"][name] = {
                "events_processed": status["events_processed"],
                "events_dropped": status["events_dropped"],
                "processing_errors": status["processing_errors"],
                "uptime": status["uptime"] if status["running"] else 0
            }
        except Exception:
            pass
    
    return metrics


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    
    try:
        # Send initial data
        pipeline_names = engine.get_pipeline_names()
        pipelines = []
        
        for name in pipeline_names:
            try:
                status = engine.get_pipeline_status(name)
                pipelines.append(status)
            except Exception:
                pass
        
        await websocket.send_json({"type": "pipelines", "data": pipelines})
        
        # Keep the connection alive and send updates
        while True:
            # Wait for a message (or timeout)
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
            except asyncio.TimeoutError:
                # Send updates periodically
                pipeline_names = engine.get_pipeline_names()
                pipelines = []
                
                for name in pipeline_names:
                    try:
                        status = engine.get_pipeline_status(name)
                        pipelines.append(status)
                    except Exception:
                        pass
                
                await websocket.send_json({"type": "pipelines", "data": pipelines})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def start_web_server(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    """
    Start the web server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Whether to enable auto-reload
    """
    uvicorn.run(
        "logflow.web.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )