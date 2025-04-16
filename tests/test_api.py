"""
Tests for the API.
"""
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from logflow.api.server import app, engine


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_list_pipelines(client):
    """Test listing pipelines."""
    # Mock the engine
    engine.get_pipeline_names = MagicMock(return_value=["pipeline1", "pipeline2"])
    
    # Make the request
    response = client.get("/api/v1/pipelines")
    
    # Check the response
    assert response.status_code == 200
    assert response.json() == ["pipeline1", "pipeline2"]


def test_get_pipeline(client):
    """Test getting pipeline status."""
    # Mock the engine
    engine.get_pipeline_status = MagicMock(return_value={
        "name": "pipeline1",
        "running": True,
        "sources": 1,
        "processors": 2,
        "sinks": 1,
        "events_processed": 100,
        "events_dropped": 10,
        "processing_errors": 5,
        "uptime": 60
    })
    
    # Make the request
    response = client.get("/api/v1/pipelines/pipeline1")
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["name"] == "pipeline1"
    assert response.json()["running"] is True
    assert response.json()["events_processed"] == 100


def test_get_pipeline_not_found(client):
    """Test getting a nonexistent pipeline."""
    # Mock the engine
    engine.get_pipeline_status = MagicMock(side_effect=KeyError("Pipeline not found"))
    
    # Make the request
    response = client.get("/api/v1/pipelines/nonexistent")
    
    # Check the response
    assert response.status_code == 404
    assert response.json()["detail"] == "Pipeline not found: nonexistent"


def test_create_pipeline(client):
    """Test creating a pipeline."""
    # Mock the engine
    engine.get_pipeline_names = MagicMock(return_value=[])
    engine.load_pipeline = AsyncMock()
    
    mock_pipeline = MagicMock()
    mock_pipeline.name = "new-pipeline"
    engine.load_pipeline.return_value = mock_pipeline
    
    # Create a pipeline configuration
    config = {
        "name": "new-pipeline",
        "sources": [
            {
                "name": "test-source",
                "type": "FileSource",
                "config": {"path": "/tmp/test.log"}
            }
        ],
        "sinks": [
            {
                "name": "test-sink",
                "type": "FileSink",
                "config": {"path": "/tmp/output.log"}
            }
        ]
    }
    
    # Make the request
    with patch("os.makedirs"):
        with patch("builtins.open"):
            response = client.post(
                "/api/v1/pipelines",
                json={"config": config}
            )
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["name"] == "new-pipeline"
    assert response.json()["status"] == "created"


def test_create_pipeline_already_exists(client):
    """Test creating a pipeline that already exists."""
    # Mock the engine
    engine.get_pipeline_names = MagicMock(return_value=["existing-pipeline"])
    
    # Create a pipeline configuration
    config = {
        "name": "existing-pipeline",
        "sources": [
            {
                "name": "test-source",
                "type": "FileSource",
                "config": {"path": "/tmp/test.log"}
            }
        ],
        "sinks": [
            {
                "name": "test-sink",
                "type": "FileSink",
                "config": {"path": "/tmp/output.log"}
            }
        ]
    }
    
    # Make the request
    response = client.post(
        "/api/v1/pipelines",
        json={"config": config}
    )
    
    # Check the response
    assert response.status_code == 409
    assert response.json()["detail"] == "Pipeline already exists: existing-pipeline"


def test_delete_pipeline(client):
    """Test deleting a pipeline."""
    # Mock the engine
    engine.get_pipeline_names = MagicMock(return_value=["pipeline1"])
    engine.stop_pipeline = AsyncMock()
    engine.pipelines = {"pipeline1": MagicMock()}
    
    # Make the request
    response = client.delete("/api/v1/pipelines/pipeline1")
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["name"] == "pipeline1"
    assert response.json()["status"] == "deleted"
    assert engine.stop_pipeline.called


def test_delete_pipeline_not_found(client):
    """Test deleting a nonexistent pipeline."""
    # Mock the engine
    engine.get_pipeline_names = MagicMock(return_value=[])
    
    # Make the request
    response = client.delete("/api/v1/pipelines/nonexistent")
    
    # Check the response
    assert response.status_code == 404
    assert response.json()["detail"] == "Pipeline not found: nonexistent"


def test_start_pipeline(client):
    """Test starting a pipeline."""
    # Mock the engine
    engine.get_pipeline_names = MagicMock(return_value=["pipeline1"])
    
    # Make the request
    response = client.post("/api/v1/pipelines/pipeline1/start")
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["name"] == "pipeline1"
    assert response.json()["status"] == "starting"


def test_start_pipeline_not_found(client):
    """Test starting a nonexistent pipeline."""
    # Mock the engine
    engine.get_pipeline_names = MagicMock(return_value=[])
    
    # Make the request
    response = client.post("/api/v1/pipelines/nonexistent/start")
    
    # Check the response
    assert response.status_code == 404
    assert response.json()["detail"] == "Pipeline not found: nonexistent"


def test_stop_pipeline(client):
    """Test stopping a pipeline."""
    # Mock the engine
    engine.get_pipeline_names = MagicMock(return_value=["pipeline1"])
    engine.stop_pipeline = AsyncMock()
    
    # Make the request
    response = client.post("/api/v1/pipelines/pipeline1/stop")
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["name"] == "pipeline1"
    assert response.json()["status"] == "stopped"
    assert engine.stop_pipeline.called


def test_stop_pipeline_not_found(client):
    """Test stopping a nonexistent pipeline."""
    # Mock the engine
    engine.get_pipeline_names = MagicMock(return_value=[])
    
    # Make the request
    response = client.post("/api/v1/pipelines/nonexistent/stop")
    
    # Check the response
    assert response.status_code == 404
    assert response.json()["detail"] == "Pipeline not found: nonexistent"


def test_get_metrics(client):
    """Test getting metrics."""
    # Mock the engine
    engine.get_pipeline_names = MagicMock(return_value=["pipeline1", "pipeline2"])
    engine.get_pipeline_status = MagicMock(side_effect=lambda name: {
        "pipeline1": {
            "name": "pipeline1",
            "running": True,
            "sources": 1,
            "processors": 2,
            "sinks": 1,
            "events_processed": 100,
            "events_dropped": 10,
            "processing_errors": 5,
            "uptime": 60
        },
        "pipeline2": {
            "name": "pipeline2",
            "running": False,
            "sources": 2,
            "processors": 1,
            "sinks": 2,
            "events_processed": 50,
            "events_dropped": 5,
            "processing_errors": 2,
            "uptime": 0
        }
    }[name])
    
    # Make the request
    response = client.get("/api/v1/metrics")
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["pipelines"] == 2
    assert "pipeline1" in response.json()["pipeline_metrics"]
    assert "pipeline2" in response.json()["pipeline_metrics"]
    assert response.json()["pipeline_metrics"]["pipeline1"]["events_processed"] == 100
    assert response.json()["pipeline_metrics"]["pipeline2"]["events_processed"] == 50