#!/usr/bin/env python3
"""
Script to generate sample Windows Event Logs in Winlogbeat format.
"""
import argparse
import json
import random
import time
from datetime import datetime, timedelta


# Sample event IDs and their descriptions
EVENT_IDS = {
    "4624": "Successful logon",
    "4625": "Failed logon attempt",
    "4634": "Logoff",
    "4648": "Explicit credential logon",
    "4672": "Special privileges assigned to new logon",
    "4720": "User account created",
    "4726": "User account deleted",
    "4740": "User account locked out",
    "1000": "Application error",
    "1001": "System error",
    "7036": "Service started or stopped",
    "7040": "Service start type changed",
    "7045": "New service installed",
    "4697": "Service installation",
    "4698": "Scheduled task created",
    "4699": "Scheduled task deleted",
    "4700": "Scheduled task enabled",
    "4701": "Scheduled task disabled",
    "4702": "Scheduled task updated",
    "4719": "System audit policy changed",
    "4738": "User account changed",
    "4767": "User account unlocked"
}

# Sample users
USERS = [
    "Administrator",
    "SYSTEM",
    "LOCAL SERVICE",
    "NETWORK SERVICE",
    "John.Doe",
    "Jane.Smith",
    "Bob.Johnson",
    "Alice.Williams",
    "DOMAIN\\Administrator",
    "DOMAIN\\User1"
]

# Sample computers
COMPUTERS = [
    "DESKTOP-AB123CD",
    "LAPTOP-XYZ456",
    "SERVER-PROD01",
    "SERVER-DEV02",
    "WORKSTATION-HR1",
    "WORKSTATION-IT2"
]

# Sample IP addresses
IP_ADDRESSES = [
    "192.168.1.100",
    "192.168.1.101",
    "192.168.1.102",
    "10.0.0.50",
    "10.0.0.51",
    "172.16.0.10",
    "172.16.0.11",
    "8.8.8.8",
    "1.1.1.1"
]

# Sample channels
CHANNELS = {
    "Security": ["4624", "4625", "4634", "4648", "4672", "4720", "4726", "4740", "4719", "4738", "4767", "4697", "4698", "4699", "4700", "4701", "4702"],
    "System": ["7036", "7040", "7045"],
    "Application": ["1000", "1001"]
}

# Sample levels
LEVELS = {
    "Information": 0,
    "Warning": 3,
    "Error": 2,
    "Critical": 1
}

# Sample providers
PROVIDERS = {
    "Security": "Microsoft-Windows-Security-Auditing",
    "System": "Service Control Manager",
    "Application": "Application Error"
}


def generate_event():
    """Generate a random Windows Event Log entry in Winlogbeat format."""
    # Select random channel
    channel = random.choice(list(CHANNELS.keys()))
    
    # Select random event ID from the channel
    event_id = random.choice(CHANNELS[channel])
    
    # Select random level based on event ID
    if event_id in ["4625", "4740", "1000", "1001"]:
        level_name = random.choice(["Error", "Critical"])
    elif event_id in ["4720", "4726", "7045", "4697", "4698", "4699", "4700", "4701", "4702", "4719", "4738", "4767"]:
        level_name = random.choice(["Information", "Warning"])
    else:
        level_name = random.choice(list(LEVELS.keys()))
    
    level = LEVELS[level_name]
    
    # Select random timestamp within the last 24 hours
    timestamp = datetime.utcnow() - timedelta(hours=random.randint(0, 24), minutes=random.randint(0, 59), seconds=random.randint(0, 59))
    
    # Select random user
    user = random.choice(USERS)
    
    # Select random computer
    computer = random.choice(COMPUTERS)
    
    # Select random IP address
    ip_address = random.choice(IP_ADDRESSES)
    
    # Generate message based on event ID
    message = f"{EVENT_IDS[event_id]}. User: {user}, Source: {ip_address}, Computer: {computer}"
    
    # Create the event
    event = {
        "@timestamp": timestamp.isoformat() + "Z",
        "message": message,
        "host": {
            "name": computer,
            "hostname": computer,
            "architecture": "x86_64",
            "os": {
                "platform": "windows",
                "version": "10.0",
                "family": "windows",
                "name": "Windows",
                "kernel": "10.0.19041.1"
            },
            "ip": [ip_address]
        },
        "winlog": {
            "channel": channel,
            "computer_name": computer,
            "event_id": event_id,
            "level": level,
            "provider_name": PROVIDERS[channel],
            "record_id": random.randint(1000, 9999999),
            "task": random.randint(1, 100),
            "keywords": ["Audit Success"] if level_name == "Information" else ["Audit Failure"],
            "event_data": {
                "SubjectUserName": user,
                "SubjectDomainName": "DOMAIN" if "\\" in user else "WORKGROUP",
                "SubjectLogonId": f"0x{random.randint(10000, 999999):x}",
                "TargetUserName": random.choice(USERS),
                "TargetDomainName": "DOMAIN",
                "LogonType": random.randint(2, 10),
                "IpAddress": ip_address,
                "IpPort": str(random.randint(1024, 65535)),
                "ProcessName": f"C:\\Windows\\System32\\{random.choice(['svchost.exe', 'lsass.exe', 'winlogon.exe', 'explorer.exe'])}"
            },
            "user": {
                "domain": "DOMAIN" if "\\" in user else "WORKGROUP",
                "name": user.split("\\")[-1]
            }
        }
    }
    
    return event


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate sample Windows Event Logs in Winlogbeat format")
    parser.add_argument("--output", "-o", default="/tmp/winlogbeat.json", help="Output file path")
    parser.add_argument("--count", "-c", type=int, default=100, help="Number of events to generate")
    parser.add_argument("--interval", "-i", type=float, default=0.1, help="Interval between events in seconds")
    args = parser.parse_args()
    
    print(f"Generating {args.count} Windows Event Log entries to {args.output}")
    
    with open(args.output, "w") as f:
        for i in range(args.count):
            event = generate_event()
            f.write(json.dumps(event) + "\n")
            f.flush()
            
            if i < args.count - 1:
                time.sleep(args.interval)
    
    print(f"Generated {args.count} Windows Event Log entries to {args.output}")


if __name__ == "__main__":
    main()