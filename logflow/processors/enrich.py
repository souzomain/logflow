"""
Enrich processor for LogFlow.
"""
import json
import os
import re
import socket
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime
import ipaddress

from logflow.core.models import LogEvent
from logflow.processors.base import Processor


class EnrichProcessor(Processor):
    """
    Processor that enriches log events with additional data.
    """
    
    def __init__(self):
        """
        Initialize a new EnrichProcessor.
        """
        self.enrich_type = "none"
        self.source_field = None
        self.target_field = None
        self.lookup_table = {}
        self.default_value = None
        self.preserve_existing = True
        self.ignore_missing = True
        self.geo_db_path = None
        self.geo_db = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the processor with the provided configuration.
        
        Args:
            config: Processor configuration with the following keys:
                - enrich_type: Type of enrichment (lookup, geo, dns, useragent)
                - source_field: Field to use as source for enrichment
                - target_field: Field to store enrichment results
                - lookup_table: Dictionary for lookup enrichment
                - lookup_file: Path to JSON file with lookup data
                - default_value: Default value if lookup fails
                - preserve_existing: Whether to preserve existing target field
                - ignore_missing: Whether to ignore missing source field
                - geo_db_path: Path to GeoIP database (for geo enrichment)
        """
        self.enrich_type = config.get("enrich_type", "none")
        if self.enrich_type not in ["lookup", "geo", "dns", "useragent", "none"]:
            raise ValueError(f"Invalid enrichment type: {self.enrich_type}")
        
        self.source_field = config.get("source_field")
        if not self.source_field:
            raise ValueError("Source field is required")
        
        self.target_field = config.get("target_field")
        if not self.target_field:
            raise ValueError("Target field is required")
        
        self.default_value = config.get("default_value")
        self.preserve_existing = config.get("preserve_existing", True)
        self.ignore_missing = config.get("ignore_missing", True)
        
        # Initialize based on enrichment type
        if self.enrich_type == "lookup":
            # Load lookup table
            self.lookup_table = config.get("lookup_table", {})
            
            # Load lookup file if provided
            lookup_file = config.get("lookup_file")
            if lookup_file:
                if not os.path.exists(lookup_file):
                    raise ValueError(f"Lookup file not found: {lookup_file}")
                
                try:
                    with open(lookup_file, "r") as f:
                        file_data = json.load(f)
                        if isinstance(file_data, dict):
                            self.lookup_table.update(file_data)
                        else:
                            raise ValueError(f"Lookup file must contain a JSON object: {lookup_file}")
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in lookup file: {str(e)}")
        
        elif self.enrich_type == "geo":
            # Load GeoIP database
            self.geo_db_path = config.get("geo_db_path")
            if not self.geo_db_path:
                raise ValueError("GeoIP database path is required for geo enrichment")
            
            if not os.path.exists(self.geo_db_path):
                raise ValueError(f"GeoIP database not found: {self.geo_db_path}")
            
            try:
                # Lazy import to avoid dependency if not used
                import geoip2.database
                self.geo_db = geoip2.database.Reader(self.geo_db_path)
            except ImportError:
                raise ValueError("geoip2 module is required for geo enrichment. Install with: pip install geoip2")
            except Exception as e:
                raise ValueError(f"Error loading GeoIP database: {str(e)}")
        
        elif self.enrich_type == "useragent":
            try:
                # Lazy import to avoid dependency if not used
                import user_agents
            except ImportError:
                raise ValueError("user-agents module is required for useragent enrichment. Install with: pip install user-agents")
    
    async def process(self, event: LogEvent) -> Optional[LogEvent]:
        """
        Process a log event by enriching it with additional data.
        
        Args:
            event: The log event to process
            
        Returns:
            The processed log event
        """
        # Get the source field value
        source_value = None
        if self.source_field == "raw_data":
            source_value = event.raw_data
        else:
            source_value = event.fields.get(self.source_field)
        
        # Check if source field exists
        if source_value is None:
            if self.ignore_missing:
                return event
            else:
                # Add a metadata entry about the missing field
                event.add_metadata("enrich_error", f"Source field not found: {self.source_field}")
                return event
        
        # Check if target field already exists
        if self.target_field in event.fields and self.preserve_existing:
            return event
        
        # Perform enrichment based on type
        try:
            if self.enrich_type == "lookup":
                # Lookup enrichment
                enriched_value = self.lookup_table.get(str(source_value), self.default_value)
                if enriched_value is not None:
                    event.add_field(self.target_field, enriched_value)
            
            elif self.enrich_type == "geo":
                # GeoIP enrichment
                try:
                    # Try to parse as IP address
                    ip = ipaddress.ip_address(source_value)
                    
                    # Skip private IPs
                    if ip.is_private:
                        return event
                    
                    # Get geo data
                    if self.geo_db:
                        if ip.version == 4:
                            geo_data = self.geo_db.city(source_value)
                        else:
                            geo_data = self.geo_db.city(source_value)
                        
                        # Extract relevant fields
                        geo_info = {
                            "country_code": geo_data.country.iso_code,
                            "country_name": geo_data.country.name,
                            "city_name": geo_data.city.name,
                            "region_name": geo_data.subdivisions.most_specific.name if geo_data.subdivisions else None,
                            "region_code": geo_data.subdivisions.most_specific.iso_code if geo_data.subdivisions else None,
                            "continent_code": geo_data.continent.code,
                            "latitude": geo_data.location.latitude,
                            "longitude": geo_data.location.longitude,
                            "timezone": geo_data.location.time_zone,
                            "postal_code": geo_data.postal.code if geo_data.postal else None
                        }
                        
                        event.add_field(self.target_field, geo_info)
                except (ValueError, ipaddress.AddressValueError):
                    # Not a valid IP address
                    if not self.ignore_missing:
                        event.add_metadata("enrich_error", f"Invalid IP address: {source_value}")
            
            elif self.enrich_type == "dns":
                # DNS enrichment
                try:
                    # Try to resolve hostname or IP
                    if re.match(r"^\d+\.\d+\.\d+\.\d+$", source_value):
                        # Reverse DNS lookup
                        hostname, _, _ = socket.gethostbyaddr(source_value)
                        event.add_field(self.target_field, hostname)
                    else:
                        # Forward DNS lookup
                        ip = socket.gethostbyname(source_value)
                        event.add_field(self.target_field, ip)
                except (socket.herror, socket.gaierror):
                    # DNS lookup failed
                    if self.default_value is not None:
                        event.add_field(self.target_field, self.default_value)
                    elif not self.ignore_missing:
                        event.add_metadata("enrich_error", f"DNS lookup failed for: {source_value}")
            
            elif self.enrich_type == "useragent":
                # User-Agent enrichment
                try:
                    # Lazy import to avoid dependency if not used
                    from user_agents import parse
                    
                    # Parse User-Agent string
                    ua = parse(source_value)
                    
                    # Extract relevant information
                    ua_info = {
                        "browser_family": ua.browser.family,
                        "browser_version": str(ua.browser.version),
                        "os_family": ua.os.family,
                        "os_version": str(ua.os.version),
                        "device_family": ua.device.family,
                        "device_brand": ua.device.brand,
                        "device_model": ua.device.model,
                        "is_mobile": ua.is_mobile,
                        "is_tablet": ua.is_tablet,
                        "is_pc": ua.is_pc,
                        "is_bot": ua.is_bot
                    }
                    
                    event.add_field(self.target_field, ua_info)
                except ImportError:
                    event.add_metadata("enrich_error", "user-agents module not available")
                except Exception as e:
                    if not self.ignore_missing:
                        event.add_metadata("enrich_error", f"User-Agent parsing failed: {str(e)}")
        
        except Exception as e:
            # Add error metadata
            event.add_metadata("enrich_error", str(e))
        
        return event
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        if self.geo_db:
            self.geo_db.close()