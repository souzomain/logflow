"""
Tests for the engine.
"""
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from logflow.core.engine import Engine
from logflow.core.pipeline import Pipeline


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as f:
        yaml.dump({
            "name": "test-pipeline",
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
        }, f)
        path = f.name
    
    yield path
    
    # Clean up
    os.unlink(path)


@pytest.mark.asyncio
async def test_engine_load_pipeline(temp_config_file):
    """Test loading a pipeline."""
    engine = Engine()
    
    # Mock the Pipeline class
    with patch("logflow.core.engine.Pipeline") as mock_pipeline_class:
        mock_pipeline = AsyncMock()
        mock_pipeline.name = "test-pipeline"
        mock_pipeline_class.return_value = mock_pipeline
        
        # Load the pipeline
        pipeline = await engine.load_pipeline(temp_config_file)
        
        # Check that the pipeline was created and initialized
        assert mock_pipeline_class.called
        assert mock_pipeline.initialize.called
        assert pipeline == mock_pipeline
        assert engine.pipelines["test-pipeline"] == mock_pipeline


@pytest.mark.asyncio
async def test_engine_start_pipeline():
    """Test starting a pipeline."""
    engine = Engine()
    
    # Create a mock pipeline
    mock_pipeline = AsyncMock()
    mock_pipeline.name = "test-pipeline"
    engine.pipelines["test-pipeline"] = mock_pipeline
    
    # Start the pipeline
    await engine.start_pipeline("test-pipeline")
    
    # Check that the pipeline was started
    assert mock_pipeline.run.called


@pytest.mark.asyncio
async def test_engine_stop_pipeline():
    """Test stopping a pipeline."""
    engine = Engine()
    
    # Create a mock pipeline
    mock_pipeline = AsyncMock()
    mock_pipeline.name = "test-pipeline"
    engine.pipelines["test-pipeline"] = mock_pipeline
    
    # Stop the pipeline
    await engine.stop_pipeline("test-pipeline")
    
    # Check that the pipeline was stopped
    assert mock_pipeline.stop.called


@pytest.mark.asyncio
async def test_engine_start(temp_config_file):
    """Test starting the engine."""
    engine = Engine()
    
    # Mock the load_pipeline and start_pipeline methods
    engine.load_pipeline = AsyncMock()
    engine.start_pipeline = AsyncMock()
    
    mock_pipeline = AsyncMock()
    mock_pipeline.name = "test-pipeline"
    engine.load_pipeline.return_value = mock_pipeline
    
    # Start the engine
    await engine.start([temp_config_file])
    
    # Check that the engine is running
    assert engine.running
    
    # Check that the pipeline was loaded and started
    assert engine.load_pipeline.called
    assert engine.start_pipeline.called


@pytest.mark.asyncio
async def test_engine_stop():
    """Test stopping the engine."""
    engine = Engine()
    engine.running = True
    
    # Create mock pipelines
    mock_pipeline1 = AsyncMock()
    mock_pipeline1.name = "test-pipeline-1"
    mock_pipeline2 = AsyncMock()
    mock_pipeline2.name = "test-pipeline-2"
    
    engine.pipelines = {
        "test-pipeline-1": mock_pipeline1,
        "test-pipeline-2": mock_pipeline2
    }
    
    # Stop the engine
    await engine.stop()
    
    # Check that the engine is not running
    assert not engine.running
    
    # Check that all pipelines were stopped
    assert mock_pipeline1.stop.called
    assert mock_pipeline2.stop.called


@pytest.mark.asyncio
async def test_engine_get_pipeline_status():
    """Test getting pipeline status."""
    engine = Engine()
    
    # Create a mock pipeline
    mock_pipeline = MagicMock()
    mock_pipeline.name = "test-pipeline"
    mock_pipeline.running = True
    mock_pipeline.sources = ["source1", "source2"]
    mock_pipeline.processors = ["processor1"]
    mock_pipeline.sinks = ["sink1", "sink2"]
    mock_pipeline.events_processed = 100
    mock_pipeline.events_dropped = 10
    mock_pipeline.processing_errors = 5
    mock_pipeline.start_time = 1000
    
    engine.pipelines["test-pipeline"] = mock_pipeline
    
    # Get the pipeline status
    with patch("time.time", return_value=1100):
        status = engine.get_pipeline_status("test-pipeline")
    
    # Check the status
    assert status["name"] == "test-pipeline"
    assert status["running"] is True
    assert status["sources"] == 2
    assert status["processors"] == 1
    assert status["sinks"] == 2
    assert status["events_processed"] == 100
    assert status["events_dropped"] == 10
    assert status["processing_errors"] == 5
    assert status["uptime"] == 100  # 1100 - 1000


def test_engine_get_pipeline_names():
    """Test getting pipeline names."""
    engine = Engine()
    
    # Add some pipelines
    engine.pipelines = {
        "pipeline1": MagicMock(),
        "pipeline2": MagicMock(),
        "pipeline3": MagicMock()
    }
    
    # Get the pipeline names
    names = engine.get_pipeline_names()
    
    # Check the names
    assert set(names) == {"pipeline1", "pipeline2", "pipeline3"}