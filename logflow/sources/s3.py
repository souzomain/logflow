"""
S3 source for LogFlow.
"""
import asyncio
import io
from datetime import datetime
from typing import AsyncIterator, Dict, Any, List, Optional

import aiobotocore.session

from logflow.core.models import LogEvent
from logflow.sources.base import Source


class S3Source(Source):
    """
    Source that reads logs from Amazon S3.
    
    Features:
    - Reads files from S3 buckets
    - Supports prefix filtering
    - Supports polling for new files
    """
    
    def __init__(self):
        """
        Initialize a new S3Source.
        """
        self.bucket = ""
        self.prefix = ""
        self.region = "us-east-1"
        self.aws_access_key_id = None
        self.aws_secret_access_key = None
        self.aws_session_token = None
        self.endpoint_url = None
        self.poll_interval = 60.0  # seconds
        self.processed_keys = set()
        self.running = False
        self.session = None
        self.client = None
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the source with the provided configuration.
        
        Args:
            config: Source configuration with the following keys:
                - bucket: S3 bucket name (required)
                - prefix: S3 key prefix (default: "")
                - region: AWS region (default: "us-east-1")
                - aws_access_key_id: AWS access key ID (optional)
                - aws_secret_access_key: AWS secret access key (optional)
                - aws_session_token: AWS session token (optional)
                - endpoint_url: Custom endpoint URL for S3 (optional)
                - poll_interval: Interval in seconds to poll for new files (default: 60.0)
        """
        self.bucket = config.get("bucket")
        if not self.bucket:
            raise ValueError("S3 bucket is required")
        
        self.prefix = config.get("prefix", "")
        self.region = config.get("region", "us-east-1")
        self.aws_access_key_id = config.get("aws_access_key_id")
        self.aws_secret_access_key = config.get("aws_secret_access_key")
        self.aws_session_token = config.get("aws_session_token")
        self.endpoint_url = config.get("endpoint_url")
        self.poll_interval = float(config.get("poll_interval", 60.0))
        
        # Create the S3 client
        self.session = aiobotocore.session.get_session()
    
    async def _get_client(self):
        """
        Get an S3 client.
        
        Returns:
            S3 client
        """
        client_kwargs = {
            "region_name": self.region,
        }
        
        if self.aws_access_key_id and self.aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = self.aws_access_key_id
            client_kwargs["aws_secret_access_key"] = self.aws_secret_access_key
            
            if self.aws_session_token:
                client_kwargs["aws_session_token"] = self.aws_session_token
        
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url
        
        return self.session.create_client("s3", **client_kwargs)
    
    async def _list_objects(self, client):
        """
        List objects in the S3 bucket.
        
        Args:
            client: S3 client
            
        Returns:
            List of object keys
        """
        paginator = client.get_paginator("list_objects_v2")
        
        new_keys = []
        
        async for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix):
            if "Contents" in page:
                for obj in page["Contents"]:
                    key = obj["Key"]
                    if key not in self.processed_keys:
                        new_keys.append(key)
        
        return new_keys
    
    async def _process_object(self, client, key):
        """
        Process an S3 object.
        
        Args:
            client: S3 client
            key: S3 object key
            
        Yields:
            LogEvent objects
        """
        try:
            # Get the object
            response = await client.get_object(Bucket=self.bucket, Key=key)
            
            # Read the object data
            async with response["Body"] as stream:
                data = await stream.read()
            
            # Process the data line by line
            text = data.decode("utf-8")
            for line in text.splitlines():
                if line.strip():
                    # Create and yield a log event
                    event = LogEvent(
                        raw_data=line,
                        source_type="s3",
                        source_name=f"s3://{self.bucket}/{key}",
                        timestamp=datetime.utcnow(),
                        metadata={
                            "s3_bucket": self.bucket,
                            "s3_key": key,
                            "s3_region": self.region
                        }
                    )
                    
                    yield event
            
            # Mark the key as processed
            self.processed_keys.add(key)
        
        except Exception as e:
            # Log the error and continue
            print(f"Error processing S3 object {key}: {str(e)}")
    
    async def read(self) -> AsyncIterator[LogEvent]:
        """
        Read log events from S3.
        
        Yields:
            LogEvent objects
        """
        self.running = True
        
        while self.running:
            try:
                async with await self._get_client() as client:
                    # List objects in the bucket
                    keys = await self._list_objects(client)
                    
                    # Process each object
                    for key in keys:
                        if not self.running:
                            break
                        
                        async for event in self._process_object(client, key):
                            yield event
                
                # Wait before polling again
                await asyncio.sleep(self.poll_interval)
            
            except asyncio.CancelledError:
                # Handle cancellation
                break
            
            except Exception as e:
                # Log the error and continue
                print(f"Error reading from S3: {str(e)}")
                await asyncio.sleep(self.poll_interval)
    
    async def shutdown(self) -> None:
        """
        Perform cleanup and release resources.
        """
        self.running = False