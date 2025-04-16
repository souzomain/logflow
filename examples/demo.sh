#!/bin/bash
# Demo script for LogFlow

# Set up colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
section() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Function to run a command with a description
run_cmd() {
    echo -e "${YELLOW}$ $1${NC}"
    eval "$1"
    echo ""
}

# Clean up any existing files
section "Cleaning up"
run_cmd "rm -f /tmp/test.log /tmp/processed.log /tmp/processed.txt /tmp/errors.log"

# Generate sample logs
section "Generating sample logs"
run_cmd "python3 /workspace/logflow/examples/generate_logs.py --count 50 --interval 0.01"
run_cmd "head -n 3 /tmp/test.log"

# Run LogFlow with simple configuration
section "Running LogFlow with simple configuration"
run_cmd "cd /workspace/logflow && python3 -m logflow.cli.commands start --config examples/simple.yaml &"
run_cmd "sleep 5"  # Give LogFlow time to process logs
run_cmd "cd /workspace/logflow && python3 -m logflow.cli.commands status"
run_cmd "head -n 3 /tmp/processed.log"

# Kill the LogFlow process
run_cmd "pkill -f 'python3 -m logflow.cli.commands start'"
run_cmd "sleep 2"

# Run LogFlow with complex configuration
section "Running LogFlow with complex configuration"
run_cmd "cd /workspace/logflow && python3 -m logflow.cli.commands start --config examples/complex.yaml &"
run_cmd "sleep 5"  # Give LogFlow time to process logs
run_cmd "cd /workspace/logflow && python3 -m logflow.cli.commands status"
run_cmd "head -n 3 /tmp/processed.txt"

# Kill the LogFlow process
run_cmd "pkill -f 'python3 -m logflow.cli.commands start'"
run_cmd "sleep 2"

# Generate more logs while LogFlow is running
section "Generating more logs while LogFlow is running"
run_cmd "cd /workspace/logflow && python3 -m logflow.cli.commands start --config examples/simple.yaml &"
run_cmd "sleep 2"
run_cmd "python3 /workspace/logflow/examples/generate_logs.py --count 20 --interval 0.1"
run_cmd "sleep 3"  # Give LogFlow time to process logs
run_cmd "cd /workspace/logflow && python3 -m logflow.cli.commands status"
run_cmd "wc -l /tmp/processed.log"

# Kill the LogFlow process
run_cmd "pkill -f 'python3 -m logflow.cli.commands start'"
run_cmd "sleep 2"

# Show how to use the API
section "Starting the API server"
run_cmd "cd /workspace/logflow && python3 examples/run_api.py --port 8000 &"
run_cmd "sleep 3"

# Use curl to interact with the API
section "Interacting with the API"
run_cmd "curl -s http://localhost:8000/api/v1/pipelines | jq"
run_cmd "curl -s -X POST -H 'Content-Type: application/json' -d '{\"config\": {\"name\": \"api-pipeline\", \"sources\": [{\"name\": \"test-source\", \"type\": \"FileSource\", \"config\": {\"path\": \"/tmp/test.log\"}}], \"sinks\": [{\"name\": \"test-sink\", \"type\": \"FileSink\", \"config\": {\"path\": \"/tmp/api-output.log\"}}]}}' http://localhost:8000/api/v1/pipelines | jq"
run_cmd "curl -s http://localhost:8000/api/v1/pipelines | jq"
run_cmd "curl -s -X POST http://localhost:8000/api/v1/pipelines/api-pipeline/start | jq"
run_cmd "sleep 2"
run_cmd "curl -s http://localhost:8000/api/v1/metrics | jq"
run_cmd "curl -s -X POST http://localhost:8000/api/v1/pipelines/api-pipeline/stop | jq"
run_cmd "curl -s -X DELETE http://localhost:8000/api/v1/pipelines/api-pipeline | jq"

# Kill the API server
run_cmd "pkill -f 'python3 examples/run_api.py'"
run_cmd "sleep 2"

section "Demo completed"
echo -e "${GREEN}LogFlow demo completed successfully!${NC}"