#!/usr/bin/env python3
"""
Script to generate sample logs for testing LogFlow.
"""
import argparse
import json
import logging
import random
import time
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Log levels
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Sample services
SERVICES = ["web", "api", "database", "auth", "cache", "worker"]

# Sample messages
MESSAGES = {
    "DEBUG": [
        "Processing request parameters",
        "Executing database query",
        "Parsing response data",
        "Initializing component",
        "Cache lookup for key: {key}"
    ],
    "INFO": [
        "Request processed successfully",
        "User {user} logged in",
        "Cache updated for key: {key}",
        "Task completed in {time}ms",
        "Service {service} started"
    ],
    "WARNING": [
        "Slow database query detected",
        "Rate limit approaching for client {client}",
        "Cache miss for frequently accessed key: {key}",
        "High memory usage detected",
        "Deprecated API endpoint accessed"
    ],
    "ERROR": [
        "Failed to connect to database",
        "Authentication failed for user {user}",
        "Exception occurred: {exception}",
        "Request timeout after {time}ms",
        "Service {service} unavailable"
    ],
    "CRITICAL": [
        "Database connection pool exhausted",
        "Out of memory error",
        "Unhandled exception in critical path: {exception}",
        "Service {service} crashed",
        "Data corruption detected"
    ]
}

# Sample exceptions
EXCEPTIONS = [
    "ValueError: Invalid input",
    "KeyError: 'config'",
    "TypeError: 'NoneType' object is not subscriptable",
    "ConnectionError: Failed to connect to server",
    "TimeoutError: Operation timed out"
]

# Sample users
USERS = ["alice", "bob", "charlie", "dave", "eve", "frank", "grace"]

# Sample clients
CLIENTS = ["mobile-app", "web-client", "admin-panel", "third-party-api", "internal-service"]

# Sample cache keys
CACHE_KEYS = ["user:profile:{id}", "product:{id}", "settings", "session:{id}", "stats:daily"]


def generate_log_entry():
    """Generate a random log entry."""
    # Select random values
    level = random.choices(LOG_LEVELS, weights=[10, 60, 20, 8, 2])[0]
    service = random.choice(SERVICES)
    timestamp = datetime.now().isoformat()
    
    # Select a random message template for the level
    message_template = random.choice(MESSAGES[level])
    
    # Fill in template placeholders
    message = message_template.format(
        user=random.choice(USERS),
        key=random.choice(CACHE_KEYS).format(id=random.randint(1000, 9999)),
        time=random.randint(10, 5000),
        service=random.choice(SERVICES),
        client=random.choice(CLIENTS),
        exception=random.choice(EXCEPTIONS)
    )
    
    # Create the log entry
    entry = {
        "timestamp": timestamp,
        "level": level,
        "service": service,
        "message": message,
        "request_id": f"req-{random.randint(10000, 99999)}",
        "host": f"srv-{random.randint(1, 10)}.example.com"
    }
    
    # Add additional fields based on level
    if level in ["ERROR", "CRITICAL"]:
        entry["stack_trace"] = "\n".join([
            "Traceback (most recent call last):",
            f"  File \"app.py\", line {random.randint(10, 500)}, in process_request",
            f"    {random.choice(EXCEPTIONS)}"
        ])
    
    if level in ["WARNING", "ERROR", "CRITICAL"]:
        entry["duration_ms"] = random.randint(500, 10000)
    
    return entry


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate sample logs for testing LogFlow")
    parser.add_argument("--output", "-o", default="/tmp/test.log", help="Output file path")
    parser.add_argument("--count", "-c", type=int, default=100, help="Number of log entries to generate")
    parser.add_argument("--interval", "-i", type=float, default=0.1, help="Interval between log entries in seconds")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="json", help="Log format")
    args = parser.parse_args()
    
    logging.info(f"Generating {args.count} log entries to {args.output}")
    
    with open(args.output, "w") as f:
        for i in range(args.count):
            entry = generate_log_entry()
            
            if args.format == "json":
                f.write(json.dumps(entry) + "\n")
            else:
                f.write(f"{entry['timestamp']} [{entry['level']}] {entry['service']}: {entry['message']}\n")
            
            f.flush()
            
            if i < args.count - 1:
                time.sleep(args.interval)
    
    logging.info(f"Generated {args.count} log entries to {args.output}")


if __name__ == "__main__":
    main()