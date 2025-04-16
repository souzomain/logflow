"""
API server for LogFlow.
"""
import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from logflow.core.engine import Engine
from logflow.core.config import load_config_file, validate_pipeline_config, ConfigError


# Create the FastAPI app
app = FastAPI(
    title="LogFlow API",
    description="API for managing LogFlow pipelines",
    version="0.1.0"
)

# Create the engine
engine = Engine()

# Set up logging
logger = logging.getLogger("logflow.api")


# Define API models
class PipelineConfig(BaseModel):
    """Pipeline configuration."""
    config: Dict[str, Any]


class PipelineStatus(BaseModel):
    """Pipeline status."""
    name: str
    running: bool
    sources: int
    processors: int
    sinks: int
    events_processed: int
    events_dropped: int
    processing_errors: int
    uptime: float


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str


@app.on_event("startup")
async def startup_event():
    """Initialize the engine on startup."""
    logger.info("Starting LogFlow API server")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the engine on shutdown."""
    logger.info("Stopping LogFlow API server")
    await engine.stop()


@app.get("/api/v1/pipelines", response_model=List[str])
async def list_pipelines():
    """List all pipelines."""
    return engine.get_pipeline_names()


@app.get("/api/v1/pipelines/{name}", response_model=PipelineStatus)
async def get_pipeline(name: str):
    """Get pipeline status."""
    try:
        return engine.get_pipeline_status(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Pipeline not found: {name}")


@app.post("/api/v1/pipelines")
async def create_pipeline(pipeline: PipelineConfig, background_tasks: BackgroundTasks):
    """Create a new pipeline."""
    try:
        # Validate the configuration
        validate_pipeline_config(pipeline.config)
        
        # Get the pipeline name
        name = pipeline.config["name"]
        
        # Check if the pipeline already exists
        if name in engine.get_pipeline_names():
            raise HTTPException(status_code=409, detail=f"Pipeline already exists: {name}")
        
        # Create a temporary configuration file
        config_dir = os.path.join(os.getcwd(), "temp_configs")
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, f"{name}.yaml")
        
        with open(config_path, "w") as f:
            import yaml
            yaml.dump(pipeline.config, f)
        
        # Load and start the pipeline
        pipeline = await engine.load_pipeline(config_path)
        background_tasks.add_task(engine.start_pipeline, pipeline.name)
        
        return {"name": name, "status": "created"}
    
    except ConfigError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating pipeline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/pipelines/{name}")
async def delete_pipeline(name: str):
    """Delete a pipeline."""
    try:
        # Check if the pipeline exists
        if name not in engine.get_pipeline_names():
            raise HTTPException(status_code=404, detail=f"Pipeline not found: {name}")
        
        # Stop the pipeline
        await engine.stop_pipeline(name)
        
        # Remove the pipeline
        del engine.pipelines[name]
        
        return {"name": name, "status": "deleted"}
    
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Pipeline not found: {name}")
    except Exception as e:
        logger.error(f"Error deleting pipeline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pipelines/{name}/start")
async def start_pipeline(name: str, background_tasks: BackgroundTasks):
    """Start a pipeline."""
    try:
        # Check if the pipeline exists
        if name not in engine.get_pipeline_names():
            raise HTTPException(status_code=404, detail=f"Pipeline not found: {name}")
        
        # Start the pipeline
        background_tasks.add_task(engine.start_pipeline, name)
        
        return {"name": name, "status": "starting"}
    
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Pipeline not found: {name}")
    except Exception as e:
        logger.error(f"Error starting pipeline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pipelines/{name}/stop")
async def stop_pipeline(name: str):
    """Stop a pipeline."""
    try:
        # Check if the pipeline exists
        if name not in engine.get_pipeline_names():
            raise HTTPException(status_code=404, detail=f"Pipeline not found: {name}")
        
        # Stop the pipeline
        await engine.stop_pipeline(name)
        
        return {"name": name, "status": "stopped"}
    
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Pipeline not found: {name}")
    except Exception as e:
        logger.error(f"Error stopping pipeline: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics")
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