"""
Configuration management for LogFlow.
"""
import os
from typing import Any, Dict, List, Optional, Union
import yaml


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


def load_config_file(path: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        path: Path to the configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        ConfigError: If the file cannot be loaded or parsed
    """
    if not os.path.exists(path):
        raise ConfigError(f"Configuration file not found: {path}")
    
    try:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            
        if not isinstance(config, dict):
            raise ConfigError(f"Invalid configuration format in {path}")
            
        return config
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML in {path}: {str(e)}")
    except Exception as e:
        raise ConfigError(f"Error loading configuration from {path}: {str(e)}")


def validate_pipeline_config(config: Dict[str, Any]) -> None:
    """
    Validate a pipeline configuration.
    
    Args:
        config: Pipeline configuration dictionary
        
    Raises:
        ConfigError: If the configuration is invalid
    """
    # Check required top-level keys
    required_keys = ["name", "sources", "sinks"]
    for key in required_keys:
        if key not in config:
            raise ConfigError(f"Missing required configuration key: {key}")
    
    # Validate sources
    if not isinstance(config["sources"], list) or not config["sources"]:
        raise ConfigError("At least one source must be configured")
    
    for i, source in enumerate(config["sources"]):
        if not isinstance(source, dict):
            raise ConfigError(f"Invalid source configuration at index {i}")
        if "name" not in source:
            raise ConfigError(f"Source at index {i} is missing a name")
        if "type" not in source:
            raise ConfigError(f"Source at index {i} is missing a type")
        if "config" not in source or not isinstance(source["config"], dict):
            raise ConfigError(f"Source at index {i} is missing a valid config")
    
    # Validate processors (optional)
    if "processors" in config:
        if not isinstance(config["processors"], list):
            raise ConfigError("Processors must be a list")
        
        for i, processor in enumerate(config["processors"]):
            if not isinstance(processor, dict):
                raise ConfigError(f"Invalid processor configuration at index {i}")
            if "name" not in processor:
                raise ConfigError(f"Processor at index {i} is missing a name")
            if "type" not in processor:
                raise ConfigError(f"Processor at index {i} is missing a type")
            if "config" not in processor or not isinstance(processor["config"], dict):
                raise ConfigError(f"Processor at index {i} is missing a valid config")
    
    # Validate sinks
    if not isinstance(config["sinks"], list) or not config["sinks"]:
        raise ConfigError("At least one sink must be configured")
    
    for i, sink in enumerate(config["sinks"]):
        if not isinstance(sink, dict):
            raise ConfigError(f"Invalid sink configuration at index {i}")
        if "name" not in sink:
            raise ConfigError(f"Sink at index {i} is missing a name")
        if "type" not in sink:
            raise ConfigError(f"Sink at index {i} is missing a type")
        if "config" not in sink or not isinstance(sink["config"], dict):
            raise ConfigError(f"Sink at index {i} is missing a valid config")