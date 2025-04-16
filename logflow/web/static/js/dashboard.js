// Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // WebSocket connection
    let ws;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    
    // Connect to WebSocket
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            console.log('WebSocket connected');
            reconnectAttempts = 0;
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        };
        
        ws.onclose = function() {
            console.log('WebSocket disconnected');
            
            // Attempt to reconnect
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                setTimeout(connectWebSocket, 2000 * reconnectAttempts);
            }
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
    }
    
    // Handle WebSocket messages
    function handleWebSocketMessage(data) {
        if (data.type === 'pipelines') {
            updatePipelines(data.data);
        }
    }
    
    // Update pipelines table
    function updatePipelines(pipelines) {
        const table = document.getElementById('pipelinesTable');
        
        // Clear table
        table.innerHTML = '';
        
        // Update metrics
        let totalProcessed = 0;
        let totalDropped = 0;
        let totalErrors = 0;
        
        // Add pipelines to table
        if (pipelines.length === 0) {
            table.innerHTML = '<tr><td colspan="10" class="text-center">No pipelines found</td></tr>';
        } else {
            pipelines.forEach(pipeline => {
                // Update metrics
                totalProcessed += pipeline.events_processed;
                totalDropped += pipeline.events_dropped;
                totalErrors += pipeline.processing_errors;
                
                // Create row
                const row = document.createElement('tr');
                
                // Format uptime
                const uptime = formatUptime(pipeline.uptime);
                
                // Add cells
                row.innerHTML = `
                    <td>${pipeline.name}</td>
                    <td>
                        <span class="badge ${pipeline.running ? 'bg-success' : 'bg-danger'}">
                            ${pipeline.running ? 'Running' : 'Stopped'}
                        </span>
                    </td>
                    <td>${pipeline.sources}</td>
                    <td>${pipeline.processors}</td>
                    <td>${pipeline.sinks}</td>
                    <td>${pipeline.events_processed.toLocaleString()}</td>
                    <td>${pipeline.events_dropped.toLocaleString()}</td>
                    <td>${pipeline.processing_errors.toLocaleString()}</td>
                    <td>${uptime}</td>
                    <td>
                        ${pipeline.running ? 
                            `<button class="btn btn-sm btn-danger action-btn" data-action="stop" data-pipeline="${pipeline.name}">
                                <i class="bi bi-stop-fill"></i> Stop
                            </button>` : 
                            `<button class="btn btn-sm btn-success action-btn" data-action="start" data-pipeline="${pipeline.name}">
                                <i class="bi bi-play-fill"></i> Start
                            </button>`
                        }
                    </td>
                `;
                
                table.appendChild(row);
            });
            
            // Add event listeners to action buttons
            document.querySelectorAll('.action-btn').forEach(button => {
                button.addEventListener('click', handlePipelineAction);
            });
        }
        
        // Update metrics
        document.getElementById('pipelineCount').textContent = pipelines.length;
        document.getElementById('eventsProcessed').textContent = totalProcessed.toLocaleString();
        document.getElementById('eventsDropped').textContent = totalDropped.toLocaleString();
        document.getElementById('processingErrors').textContent = totalErrors.toLocaleString();
    }
    
    // Format uptime
    function formatUptime(seconds) {
        if (!seconds) return '0s';
        
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        let result = '';
        if (days > 0) result += `${days}d `;
        if (hours > 0) result += `${hours}h `;
        if (minutes > 0) result += `${minutes}m `;
        if (secs > 0 || result === '') result += `${secs}s`;
        
        return result.trim();
    }
    
    // Handle pipeline actions (start/stop)
    async function handlePipelineAction(event) {
        const button = event.currentTarget;
        const action = button.dataset.action;
        const pipeline = button.dataset.pipeline;
        
        try {
            // Disable button
            button.disabled = true;
            
            // Send request
            const response = await fetch(`/api/pipelines/${pipeline}/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                // Refresh pipelines
                fetchPipelines();
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        } finally {
            // Re-enable button
            button.disabled = false;
        }
    }
    
    // Fetch pipelines from API
    async function fetchPipelines() {
        try {
            const response = await fetch('/api/pipelines');
            const data = await response.json();
            updatePipelines(data.pipelines);
        } catch (error) {
            console.error('Error fetching pipelines:', error);
        }
    }
    
    // Load configuration
    async function loadConfiguration() {
        const configPath = document.getElementById('configPath').value.trim();
        
        if (!configPath) {
            alert('Please enter a configuration file path');
            return;
        }
        
        try {
            const response = await fetch('/api/load-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ path: configPath })
            });
            
            const data = await response.json();
            
            if (data.error) {
                alert(`Error: ${data.error}`);
            } else {
                alert(`Configuration loaded successfully: ${data.message}`);
                fetchPipelines();
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('configModal'));
                modal.hide();
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
            alert('An error occurred. Please try again.');
        }
    }
    
    // Event listeners
    document.getElementById('refreshBtn').addEventListener('click', fetchPipelines);
    document.getElementById('loadConfigBtn').addEventListener('click', loadConfiguration);
    
    // Initial setup
    connectWebSocket();
    fetchPipelines();
});