"""
Filter processor for LogFlow.
"""
from typing import Dict, Any, Optional, List, Callable
import re

from logflow.core.models import LogEvent
from logflow.processors.base import Processor


class FilterProcessor(Processor):
    """
    Processor that filters log events based on conditions.
    """
    
    def __init__(self):
        """
        Initialize a new FilterProcessor.
        """
        self.conditions = []
        self.mode = "any"  # any, all
        self.negate = False
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the processor with the provided configuration.
        
        Args:
            config: Processor configuration with the following keys:
                - condition: A single condition string (alternative to conditions)
                - conditions: List of condition strings
                - mode: How to combine conditions: "any" or "all" (default: "any")
                - negate: Whether to negate the result (default: False)
                
        Condition format:
            - "field == value": Field equals value
            - "field != value": Field does not equal value
            - "field > value": Field greater than value (numeric)
            - "field < value": Field less than value (numeric)
            - "field >= value": Field greater than or equal to value (numeric)
            - "field <= value": Field less than or equal to value (numeric)
            - "field =~ pattern": Field matches regex pattern
            - "field !~ pattern": Field does not match regex pattern
            - "field in [value1, value2, ...]": Field is in list of values
            - "field not in [value1, value2, ...]": Field is not in list of values
            - "exists:field": Field exists
            - "missing:field": Field does not exist
        """
        # Get conditions
        conditions = config.get("conditions", [])
        if "condition" in config:
            conditions.append(config["condition"])
        
        if not conditions:
            raise ValueError("At least one condition is required")
        
        # Parse conditions
        self.conditions = [self._parse_condition(cond) for cond in conditions]
        
        # Get mode and negate
        self.mode = config.get("mode", "any")
        if self.mode not in ["any", "all"]:
            raise ValueError(f"Invalid mode: {self.mode}")
        
        self.negate = config.get("negate", False)
    
    def _parse_condition(self, condition: str) -> Callable[[LogEvent], bool]:
        """
        Parse a condition string into a callable function.
        
        Args:
            condition: Condition string
            
        Returns:
            Function that evaluates the condition for a log event
        """
        # Check for exists/missing conditions
        if condition.startswith("exists:"):
            field = condition[7:].strip()
            return lambda event: field in event.fields
        
        if condition.startswith("missing:"):
            field = condition[8:].strip()
            return lambda event: field not in event.fields
        
        # Parse field comparison conditions
        match = re.match(r"(\w+)\s*(==|!=|>|<|>=|<=|=~|!~|in|not in)\s*(.*)", condition)
        if not match:
            raise ValueError(f"Invalid condition format: {condition}")
        
        field, op, value_str = match.groups()
        
        # Parse the value
        if op in ["in", "not in"]:
            # Parse list of values
            if not (value_str.startswith("[") and value_str.endswith("]")):
                raise ValueError(f"Invalid list format in condition: {condition}")
            
            value_list = [v.strip() for v in value_str[1:-1].split(",")]
            
            if op == "in":
                return lambda event: field in event.fields and str(event.fields[field]) in value_list
            else:  # not in
                return lambda event: field in event.fields and str(event.fields[field]) not in value_list
        
        elif op in ["=~", "!~"]:
            # Regex pattern
            pattern = re.compile(value_str.strip('"\''))
            
            if op == "=~":
                return lambda event: field in event.fields and bool(pattern.search(str(event.fields[field])))
            else:  # !~
                return lambda event: field in event.fields and not bool(pattern.search(str(event.fields[field])))
        
        else:
            # Simple comparison
            value = value_str.strip('"\'')
            
            if op == "==":
                return lambda event: field in event.fields and str(event.fields[field]) == value
            elif op == "!=":
                return lambda event: field in event.fields and str(event.fields[field]) != value
            elif op == ">":
                return lambda event: field in event.fields and float(event.fields[field]) > float(value)
            elif op == "<":
                return lambda event: field in event.fields and float(event.fields[field]) < float(value)
            elif op == ">=":
                return lambda event: field in event.fields and float(event.fields[field]) >= float(value)
            elif op == "<=":
                return lambda event: field in event.fields and float(event.fields[field]) <= float(value)
    
    async def process(self, event: LogEvent) -> Optional[LogEvent]:
        """
        Process a log event by applying filters.
        
        Args:
            event: The log event to process
            
        Returns:
            The event if it passes the filters, None otherwise
        """
        # Evaluate all conditions
        results = [condition(event) for condition in self.conditions]
        
        # Combine results based on mode
        if self.mode == "any":
            result = any(results)
        else:  # all
            result = all(results)
        
        # Apply negation if needed
        if self.negate:
            result = not result
        
        # Return the event if it passes the filters, None otherwise
        return event if result else None
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        pass