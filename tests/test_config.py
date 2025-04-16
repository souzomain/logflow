"""
Tests for the configuration module.
"""
import os
import tempfile

import pytest
import yaml

from logflow.core.config import load_config_file, validate_pipeline_config, ConfigError


def test_load_config_file():
    """Test loading a configuration file."""
    # Create a temporary configuration file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"name": "test", "sources": [], "sinks": []}, f)
    
    try:
        # Load the configuration
        config = load_config_file(f.name)
        
        assert config["name"] == "test"
        assert config["sources"] == []
        assert config["sinks"] == []
    
    finally:
        # Clean up
        os.unlink(f.name)


def test_load_config_file_not_found():
    """Test loading a non-existent configuration file."""
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config_file("/nonexistent/file.yaml")


def test_load_config_file_invalid_yaml():
    """Test loading an invalid YAML file."""
    # Create a temporary file with invalid YAML
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content:")
    
    try:
        # Try to load the configuration
        with pytest.raises(ConfigError, match="Error parsing YAML"):
            load_config_file(f.name)
    
    finally:
        # Clean up
        os.unlink(f.name)


def test_validate_pipeline_config():
    """Test validating a pipeline configuration."""
    # Valid configuration
    config = {
        "name": "test",
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
    
    # This should not raise an exception
    validate_pipeline_config(config)


def test_validate_pipeline_config_missing_required_keys():
    """Test validating a pipeline configuration with missing required keys."""
    # Configuration without name
    config1 = {
        "sources": [],
        "sinks": []
    }
    
    with pytest.raises(ConfigError, match="Missing required configuration key: name"):
        validate_pipeline_config(config1)
    
    # Configuration without sources
    config2 = {
        "name": "test",
        "sinks": []
    }
    
    with pytest.raises(ConfigError, match="Missing required configuration key: sources"):
        validate_pipeline_config(config2)
    
    # Configuration without sinks
    config3 = {
        "name": "test",
        "sources": []
    }
    
    with pytest.raises(ConfigError, match="Missing required configuration key: sinks"):
        validate_pipeline_config(config3)


def test_validate_pipeline_config_invalid_sources():
    """Test validating a pipeline configuration with invalid sources."""
    # Empty sources list
    config1 = {
        "name": "test",
        "sources": [],
        "sinks": [{"name": "test", "type": "test", "config": {}}]
    }
    
    with pytest.raises(ConfigError, match="At least one source must be configured"):
        validate_pipeline_config(config1)
    
    # Invalid source (not a dict)
    config2 = {
        "name": "test",
        "sources": ["invalid"],
        "sinks": [{"name": "test", "type": "test", "config": {}}]
    }
    
    with pytest.raises(ConfigError, match="Invalid source configuration at index 0"):
        validate_pipeline_config(config2)
    
    # Source without name
    config3 = {
        "name": "test",
        "sources": [{"type": "test", "config": {}}],
        "sinks": [{"name": "test", "type": "test", "config": {}}]
    }
    
    with pytest.raises(ConfigError, match="Source at index 0 is missing a name"):
        validate_pipeline_config(config3)
    
    # Source without type
    config4 = {
        "name": "test",
        "sources": [{"name": "test", "config": {}}],
        "sinks": [{"name": "test", "type": "test", "config": {}}]
    }
    
    with pytest.raises(ConfigError, match="Source at index 0 is missing a type"):
        validate_pipeline_config(config4)
    
    # Source without config
    config5 = {
        "name": "test",
        "sources": [{"name": "test", "type": "test"}],
        "sinks": [{"name": "test", "type": "test", "config": {}}]
    }
    
    with pytest.raises(ConfigError, match="Source at index 0 is missing a valid config"):
        validate_pipeline_config(config5)


def test_validate_pipeline_config_invalid_sinks():
    """Test validating a pipeline configuration with invalid sinks."""
    # Empty sinks list
    config1 = {
        "name": "test",
        "sources": [{"name": "test", "type": "test", "config": {}}],
        "sinks": []
    }
    
    with pytest.raises(ConfigError, match="At least one sink must be configured"):
        validate_pipeline_config(config1)
    
    # Invalid sink (not a dict)
    config2 = {
        "name": "test",
        "sources": [{"name": "test", "type": "test", "config": {}}],
        "sinks": ["invalid"]
    }
    
    with pytest.raises(ConfigError, match="Invalid sink configuration at index 0"):
        validate_pipeline_config(config2)
    
    # Sink without name
    config3 = {
        "name": "test",
        "sources": [{"name": "test", "type": "test", "config": {}}],
        "sinks": [{"type": "test", "config": {}}]
    }
    
    with pytest.raises(ConfigError, match="Sink at index 0 is missing a name"):
        validate_pipeline_config(config3)
    
    # Sink without type
    config4 = {
        "name": "test",
        "sources": [{"name": "test", "type": "test", "config": {}}],
        "sinks": [{"name": "test", "config": {}}]
    }
    
    with pytest.raises(ConfigError, match="Sink at index 0 is missing a type"):
        validate_pipeline_config(config4)
    
    # Sink without config
    config5 = {
        "name": "test",
        "sources": [{"name": "test", "type": "test", "config": {}}],
        "sinks": [{"name": "test", "type": "test"}]
    }
    
    with pytest.raises(ConfigError, match="Sink at index 0 is missing a valid config"):
        validate_pipeline_config(config5)