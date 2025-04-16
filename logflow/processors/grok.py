"""
Grok processor for LogFlow.
"""
import re
from typing import Dict, Any, Optional, List, Pattern, Tuple

from logflow.core.models import LogEvent
from logflow.processors.base import Processor


# Default Grok patterns
DEFAULT_PATTERNS = {
    # Base patterns
    "WORD": r"\\w+",
    "NOTSPACE": r"\\S+",
    "SPACE": r"\\s+",
    "DATA": r".*?",
    "GREEDYDATA": r".*",
    "QUOTEDSTRING": r"(?>\"(?>[^\\\"]|\\\\.)*\"|\'(?>[^\\\']|\\\\.)*\'|`(?>[^\\\\`]|\\\\.)*`)",
    
    # Numbers
    "INT": r"(?:[+-]?(?:[0-9]+))",
    "BASE10NUM": r"(?<![0-9.+-])(?>[+-]?(?:(?:[0-9]+(?:\\.[0-9]+)?)|(?:\\.[0-9]+)))",
    "NUMBER": r"(?:%{BASE10NUM})",
    "BASE16NUM": r"(?<![0-9A-Fa-f])(?:[+-]?(?:0x)?(?:[0-9A-Fa-f]+))",
    "BASE16FLOAT": r"\\b(?<![0-9A-Fa-f.])(?:[+-]?(?:0x)?(?:(?:[0-9A-Fa-f]+(?:\\.[0-9A-Fa-f]*)?)|(?:\\.[0-9A-Fa-f]+)))\\b",
    
    # Networking
    "IP": r"(?:%{IPV4}|%{IPV6})",
    "IPV4": r"(?<![0-9])(?:(?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5])[.](?:[0-1]?[0-9]{1,2}|2[0-4][0-9]|25[0-5]))(?![0-9])",
    "IPV6": r"((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)(\\.(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)(\\.(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)(\\.(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)(\\.(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)(\\.(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)(\\.(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)(\\.(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)){3}))|:)))(%.+)?",
    "HOSTNAME": r"\\b(?:[0-9A-Za-z][0-9A-Za-z-]{0,62})(?:\\.(?:[0-9A-Za-z][0-9A-Za-z-]{0,62}))*(\\.?|\\b)",
    "HOST": r"%{HOSTNAME}",
    "IPORHOST": r"(?:%{IP}|%{HOSTNAME})",
    "HOSTPORT": r"(?:%{IPORHOST}:%{POSINT})",
    
    # Paths
    "PATH": r"(?:%{UNIXPATH}|%{WINPATH})",
    "UNIXPATH": r"(/[^/\\s]*)+",
    "WINPATH": r"([A-Za-z]:|\\\\)(?:\\\\[^\\\\?*]*)+",
    "TTY": r"(?:/dev/(pts|tty([pq])?)(\\w+)?/?(?:[0-9]+))",
    "URIPROTO": r"[A-Za-z]([A-Za-z0-9+\\-.])+",
    "URIHOST": r"%{IPORHOST}(?::%{POSINT})?",
    "URIPATH": r"(?:/[A-Za-z0-9$.+!*'(){},~:;=@#%_\\-]*)+",
    "URIPARAM": r"\\?[A-Za-z0-9$.+!*'|(){},~@#%&/=:;_?\\-\\[\\]<>]*",
    "URIPATHPARAM": r"%{URIPATH}(?:%{URIPARAM})?",
    "URI": r"%{URIPROTO}://(?:%{USER}(?::[^@]*)?@)?(?:%{URIHOST})?(?:%{URIPATHPARAM})?",
    
    # Date and time
    "MONTH": r"\\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\\b",
    "MONTHNUM": r"(?:0?[1-9]|1[0-2])",
    "MONTHNUM2": r"(?:0[1-9]|1[0-2])",
    "MONTHDAY": r"(?:(?:0[1-9])|(?:[12][0-9])|(?:3[01])|[1-9])",
    "DAY": r"(?:Mon(?:day)?|Tue(?:sday)?|Wed(?:nesday)?|Thu(?:rsday)?|Fri(?:day)?|Sat(?:urday)?|Sun(?:day)?)",
    "YEAR": r"(?:\\d\\d){1,2}",
    "HOUR": r"(?:2[0123]|[01]?[0-9])",
    "MINUTE": r"(?:[0-5][0-9])",
    "SECOND": r"(?:(?:[0-5]?[0-9]|60)(?:[:.,][0-9]+)?)",
    "TIME": r"(?!<[0-9])%{HOUR}:%{MINUTE}(?::%{SECOND})(?![0-9])",
    "DATE_US": r"%{MONTHNUM}[/-]%{MONTHDAY}[/-]%{YEAR}",
    "DATE_EU": r"%{MONTHDAY}[./-]%{MONTHNUM}[./-]%{YEAR}",
    "ISO8601_TIMEZONE": r"(?:Z|[+-]%{HOUR}(?::?%{MINUTE}))",
    "ISO8601_SECOND": r"(?:%{SECOND}|60)",
    "TIMESTAMP_ISO8601": r"%{YEAR}-%{MONTHNUM}-%{MONTHDAY}[T ]%{HOUR}:?%{MINUTE}(?::?%{SECOND})?%{ISO8601_TIMEZONE}?",
    "DATE": r"%{DATE_US}|%{DATE_EU}",
    "DATESTAMP": r"%{DATE}[- ]%{TIME}",
    "TZ": r"(?:[PMCE][SD]T|UTC)",
    "DATESTAMP_RFC822": r"%{DAY} %{MONTH} %{MONTHDAY} %{YEAR} %{TIME} %{TZ}",
    "DATESTAMP_RFC2822": r"%{DAY}, %{MONTHDAY} %{MONTH} %{YEAR} %{TIME} %{ISO8601_TIMEZONE}",
    "DATESTAMP_OTHER": r"%{DAY} %{MONTH} %{MONTHDAY} %{TIME} %{TZ} %{YEAR}",
    "DATESTAMP_EVENTLOG": r"%{YEAR}%{MONTHNUM2}%{MONTHDAY}%{HOUR}%{MINUTE}%{SECOND}",
    
    # Syslog
    "SYSLOGTIMESTAMP": r"%{MONTH} +%{MONTHDAY} %{TIME}",
    "PROG": r"[\\w._/%-]+",
    "SYSLOGPROG": r"%{PROG:program}(?:\\[%{POSINT:pid}\\])?",
    "SYSLOGHOST": r"%{IPORHOST}",
    "SYSLOGFACILITY": r"<%{NONNEGINT:facility}.%{NONNEGINT:priority}>",
    "HTTPDATE": r"%{MONTHDAY}/%{MONTH}/%{YEAR}:%{TIME} %{INT}",
    
    # Shortcuts
    "QS": r"%{QUOTEDSTRING}",
    
    # Log formats
    "SYSLOGBASE": r"%{SYSLOGTIMESTAMP:timestamp} (?:%{SYSLOGFACILITY} )?%{SYSLOGHOST:logsource} %{SYSLOGPROG}:",
    "COMMONAPACHELOG": r"%{IPORHOST:clientip} %{HTTPDUSER:ident} %{USER:auth} \\[%{HTTPDATE:timestamp}\\] \"(?:%{WORD:verb} %{NOTSPACE:request}(?: HTTP/%{NUMBER:httpversion})?|%{DATA:rawrequest})\" %{NUMBER:response} (?:%{NUMBER:bytes}|-)",
    "COMBINEDAPACHELOG": r"%{COMMONAPACHELOG} %{QS:referrer} %{QS:agent}",
    
    # Misc
    "POSINT": r"\\b(?:[1-9][0-9]*)\\b",
    "NONNEGINT": r"\\b(?:[0-9]+)\\b",
    "WORD": r"\\b\\w+\\b",
    "NOTSPACE": r"\\S+",
    "SPACE": r"\\s+",
    "DATA": r".*?",
    "GREEDYDATA": r".*",
    "QUOTEDSTRING": r"(?>\"(?>[^\\\"]|\\\\.)*\"|\'(?>[^\\\']|\\\\.)*\'|`(?>[^\\\\`]|\\\\.)*`)",
    
    # User names and IDs
    "USER": r"[a-zA-Z0-9._-]+",
    "USERNAME": r"[a-zA-Z0-9._-]+",
    "EMAILLOCALPART": r"[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+",
    "EMAILADDRESS": r"%{EMAILLOCALPART}@%{HOSTNAME}",
    
    # HTTP
    "HTTPDUSER": r"%{EMAILADDRESS}|%{USER}",
    "HTTPDERROR_DATE": r"%{DAY} %{MONTH} %{MONTHDAY} %{TIME} %{YEAR}",
}


class GrokProcessor(Processor):
    """
    Processor that extracts fields from log events using Grok patterns.
    """
    
    def __init__(self):
        """
        Initialize a new GrokProcessor.
        """
        self.field = "raw_data"
        self.patterns = []
        self.compiled_patterns = []
        self.custom_patterns = {}
        self.target_field = None
        self.preserve_original = True
        self.ignore_errors = False
        self.break_on_match = True
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the processor with the provided configuration.
        
        Args:
            config: Processor configuration with the following keys:
                - field: Field containing the text to match (default: "raw_data")
                - patterns: List of Grok patterns to try (required)
                - custom_patterns: Dictionary of custom pattern definitions
                - target_field: Field to store the extracted data (default: None)
                - preserve_original: Whether to preserve the original field (default: True)
                - ignore_errors: Whether to ignore matching errors (default: False)
                - break_on_match: Whether to stop after the first match (default: True)
        """
        self.field = config.get("field", "raw_data")
        self.patterns = config.get("patterns", [])
        if not self.patterns:
            raise ValueError("At least one Grok pattern is required")
        
        self.custom_patterns = config.get("custom_patterns", {})
        self.target_field = config.get("target_field")
        self.preserve_original = config.get("preserve_original", True)
        self.ignore_errors = config.get("ignore_errors", False)
        self.break_on_match = config.get("break_on_match", True)
        
        # Merge custom patterns with default patterns
        all_patterns = {**DEFAULT_PATTERNS, **self.custom_patterns}
        
        # Compile the Grok patterns
        for pattern in self.patterns:
            try:
                # Convert Grok pattern to regex
                regex_pattern, field_names = self._grok_to_regex(pattern, all_patterns)
                
                # Compile the regex
                compiled_regex = re.compile(regex_pattern)
                
                # Store the compiled pattern and field names
                self.compiled_patterns.append((compiled_regex, field_names))
            except Exception as e:
                raise ValueError(f"Invalid Grok pattern '{pattern}': {str(e)}")
    
    def _grok_to_regex(self, pattern: str, patterns: Dict[str, str]) -> Tuple[str, List[str]]:
        """
        Convert a Grok pattern to a regular expression.
        
        Args:
            pattern: Grok pattern
            patterns: Dictionary of pattern definitions
            
        Returns:
            Tuple of (regex pattern, field names)
        """
        field_names = []
        
        # Replace %{PATTERN:field} with (?P<field>PATTERN_REGEX)
        def replace_pattern(match):
            pattern_name = match.group(1)
            field_name = match.group(2) if match.group(2) else None
            
            if pattern_name not in patterns:
                raise ValueError(f"Unknown pattern: {pattern_name}")
            
            pattern_regex = patterns[pattern_name]
            
            # Check for nested patterns
            if "%{" in pattern_regex:
                pattern_regex, nested_fields = self._grok_to_regex(pattern_regex, patterns)
                if field_name:
                    field_names.append(field_name)
                field_names.extend(nested_fields)
            elif field_name:
                field_names.append(field_name)
                return f"(?P<{field_name}>{pattern_regex})"
            
            return f"({pattern_regex})"
        
        # Replace %{PATTERN:field} with (?P<field>PATTERN_REGEX)
        regex_pattern = re.sub(r"%{([A-Za-z0-9_]+)(?::([A-Za-z0-9_]+))?}", replace_pattern, pattern)
        
        return regex_pattern, field_names
    
    async def process(self, event: LogEvent) -> Optional[LogEvent]:
        """
        Process a log event by extracting fields using Grok patterns.
        
        Args:
            event: The log event to process
            
        Returns:
            The processed log event, or None if the event should be dropped
        """
        # Get the field value
        field_value = None
        if self.field == "raw_data":
            field_value = event.raw_data
        else:
            field_value = event.fields.get(self.field)
        
        if not field_value:
            # If the field doesn't exist or is empty, return the event as is
            return event
        
        try:
            # Try each pattern
            matched = False
            for compiled_pattern, field_names in self.compiled_patterns:
                # Match the pattern
                match = compiled_pattern.search(str(field_value))
                
                if match:
                    matched = True
                    
                    # Extract the matched groups
                    extracted = match.groupdict()
                    
                    # Store the extracted data
                    if self.target_field:
                        # Store under a target field
                        event.add_field(self.target_field, extracted)
                    else:
                        # Add all extracted fields to the event
                        for key, value in extracted.items():
                            if value is not None:  # Skip None values
                                event.add_field(key, value)
                    
                    # Break after the first match if configured to do so
                    if self.break_on_match:
                        break
            
            # Remove the original field if not preserving it and a match was found
            if matched and not self.preserve_original and self.field != "raw_data" and self.field in event.fields:
                del event.fields[self.field]
            
            return event
        
        except Exception as e:
            # Handle errors
            if self.ignore_errors:
                # If ignoring errors, return the event as is
                event.add_metadata("grok_error", str(e))
                return event
            else:
                # Otherwise, drop the event
                return None
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        pass