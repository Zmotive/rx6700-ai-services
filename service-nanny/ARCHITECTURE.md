# Service Nanny Architecture

## System Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                    /home/zack/ai-workspace/services                 │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   service-nanny (Port 8080)                 │    │
│  │                                                             │    │
│  │  ┌───────────────────────────────────────────────────┐     │    │
│  │  │          Service Discovery Engine                 │     │    │
│  │  │  • Scans for service.yaml manifests              │     │    │
│  │  │  • Auto-registers services                       │     │    │
│  │  │  • Validates manifest schema                     │     │    │
│  │  └───────────────────────────────────────────────────┘     │    │
│  │                                                             │    │
│  │  ┌───────────────────────────────────────────────────┐     │    │
│  │  │          GPU Arbitration Engine                   │     │    │
│  │  │  • Enforces one-GPU-service-at-a-time            │     │    │
│  │  │  • Tracks gpu_service_running state              │     │    │
│  │  │  • Handles force-stop requests                   │     │    │
│  │  └───────────────────────────────────────────────────┘     │    │
│  │                                                             │    │
│  │  ┌───────────────────────────────────────────────────┐     │    │
│  │  │          Health Monitor                           │     │    │
│  │  │  • Polls service /health endpoints               │     │    │
│  │  │  • Tracks uptime                                 │     │    │
│  │  │  • Reports is_healthy status                    │     │    │
│  │  └───────────────────────────────────────────────────┘     │    │
│  │                                                             │    │
│  │  ┌───────────────────────────────────────────────────┐     │    │
│  │  │          Docker Compose Controller                │     │    │
│  │  │  • Executes docker compose up/down               │     │    │
│  │  │  • Reads logs via docker compose logs            │     │    │
│  │  │  • Checks status via docker compose ps           │     │    │
│  │  └───────────────────────────────────────────────────┘     │    │
│  │                                                             │    │
│  │  ┌───────────────────────────────────────────────────┐     │    │
│  │  │          REST API (FastAPI)                       │     │    │
│  │  │  GET  /services                                  │     │    │
│  │  │  POST /services/{name}/start                     │     │    │
│  │  │  POST /services/{name}/stop                      │     │    │
│  │  │  GET  /services/{name}/status                    │     │    │
│  │  │  GET  /services/{name}/logs                      │     │    │
│  │  └───────────────────────────────────────────────────┘     │    │
│  │                                                             │    │
│  │  [Future: MCP Server Layer]                                │    │
│  │  • Tools: start_service, stop_service, list_services       │    │
│  │  • Resources: service://status, service://logs             │    │
│  └────────────────────────────────────────────────────────────┘    │
│           │            │            │            │                  │
│           │            │            │            │                  │
│  ┌────────┴────┐  ┌───┴────┐  ┌───┴────┐  ┌───┴──────────┐       │
│  │minimal-sd-  │  │Service │  │Service │  │  _template/  │       │
│  │api (GPU)    │  │2 (CPU) │  │3 (GPU) │  │  (Copy Me!)  │       │
│  │             │  │        │  │        │  │              │       │
│  │service.yaml │  │service.│  │service.│  │service.yaml  │       │
│  │Port: 8000   │  │yaml    │  │yaml    │  │Port: 8001+   │       │
│  │VRAM: 8GB    │  │Port:   │  │VRAM: ? │  │VRAM: 0       │       │
│  └─────────────┘  │8002    │  └────────┘  └──────────────┘       │
│                   └────────┘                                       │
└────────────────────────────────────────────────────────────────────┘
```

## Service Lifecycle

### Service Registration

```
1. Service Nanny starts
   ↓
2. Scans /services directory for subdirectories
   ↓
3. For each directory, looks for service.yaml
   ↓
4. Validates manifest schema
   ↓
5. Adds to services_registry{}
   ↓
6. Service is now discoverable via API
```

### Starting a Service

```
API Request: POST /services/minimal-sd-api/start
   ↓
Check if service exists in registry
   ↓
Check if service already running (docker compose ps)
   ↓
If GPU required:
   ├─ Check if another GPU service is running
   ├─ If yes and force=false → Return 409 Conflict
   └─ If yes and force=true → Stop running GPU service first
   ↓
Execute: docker compose up -d (in service directory)
   ↓
Update running_services{} state
   ↓
If GPU service: Update gpu_service_running
   ↓
Return 200 OK with health endpoint
```

### Health Monitoring

```
While service is running:
   ↓
Poll health_endpoint every 30s (configurable)
   ↓
If 200 OK:
   └─ Mark as is_healthy: true
   ↓
If timeout/error:
   └─ Mark as is_healthy: false
   ↓
Track uptime (started_at → now)
```

### Stopping a Service

```
API Request: POST /services/minimal-sd-api/stop
   ↓
Check if service exists in registry
   ↓
Check if actually running (docker compose ps)
   ↓
Execute: docker compose down (in service directory)
   ↓
Remove from running_services{}
   ↓
If GPU service: Clear gpu_service_running
   ↓
Return 200 OK
```

## Data Structures

### services_registry
```python
{
  "minimal-sd-api": {
    "manifest": {
      "name": "minimal-sd-api",
      "gpu_required": true,
      "vram_gb": 8,
      # ... full manifest
    },
    "path": Path("/home/zack/ai-workspace/services/minimal-sd-api"),
    "discovered_at": "2025-11-10T12:34:56"
  }
}
```

### running_services
```python
{
  "minimal-sd-api": {
    "started_at": "2025-11-10T12:35:00",
    "manifest": { /* copy of manifest */ }
  }
}
```

### gpu_service_running
```python
# String (service name) or None
"minimal-sd-api"  # Currently using GPU
None              # No GPU service running
```

## Security Considerations

### Docker Socket Access
- Service Nanny has `/var/run/docker.sock` mounted
- This gives it **full Docker control** on the host
- Only trusted users should access the API
- Future: Add authentication/authorization

### Service Isolation
- Each service runs in its own container
- Services cannot directly access each other's containers
- Shared volumes must be explicitly configured

### GPU Access
- Only services with `gpu_required: true` get GPU devices
- Enforced by docker-compose.yml configuration
- Service Nanny doesn't modify GPU access, just arbitrates timing

## Future Enhancements

### MCP Server Integration

```
Service Nanny as MCP Server:
┌─────────────────────────────────────┐
│      AI Assistant (Claude, etc)     │
│                                      │
│  "Start the image generator"        │
│  "What services are available?"     │
└──────────────┬──────────────────────┘
               │ MCP Protocol
               ↓
┌─────────────────────────────────────┐
│       Service Nanny MCP Layer       │
│                                      │
│  Tools:                              │
│  • start_service(name, force)        │
│  • stop_service(name)                │
│  • list_services(filter)             │
│  • get_service_status(name)          │
│                                      │
│  Resources:                          │
│  • service://status                  │
│  • service://logs/{name}             │
│  • service://metrics                 │
└──────────────┬──────────────────────┘
               │
               ↓
     [Current Service Nanny Core]
```

### Individual Services as MCP Servers

```
Service Nanny starts minimal-sd-api
        ↓
minimal-sd-api exposes MCP tools:
  • generate_image(prompt, width, height)
  • check_generation_status(id)
        ↓
AI Assistant can now:
  1. Ask Service Nanny to start minimal-sd-api
  2. Use minimal-sd-api's MCP tools to generate images
  3. Ask Service Nanny to stop service when done
```

### Service Manifest Extensions

```yaml
# Future service.yaml additions
mcp:
  enabled: true
  port: 9000  # MCP server port
  tools:
    - name: generate_image
      description: Generate image from prompt
      parameters:
        - name: prompt
          type: string
          required: true
  
dependencies:
  - service: vector-db
    required: false
  - service: cache-redis
    required: true

resources:
  cpu_limit: "4.0"
  memory_limit: "16GB"
  
scheduling:
  auto_start: false
  auto_stop_after: 3600  # seconds of inactivity
```

## Port Allocation Strategy

| Range | Purpose | Examples |
|-------|---------|----------|
| 8000-8009 | GPU Services | minimal-sd-api: 8000 |
| 8010-8019 | ML Inference | (available) |
| 8020-8039 | Data Services | (available) |
| 8040-8059 | Utilities | (available) |
| 8060-8079 | Web UIs | (available) |
| 8080 | **Service Nanny** | Reserved |
| 9000-9099 | MCP Server Ports | (future) |

## Error Handling

### Service Start Failures
```python
try:
    subprocess.run(["docker", "compose", "up", "-d"])
except subprocess.TimeoutExpired:
    return 500, "Service start timed out"
except subprocess.CalledProcessError as e:
    return 500, f"Docker error: {e.stderr}"
```

### GPU Conflict Resolution
```python
if gpu_required and gpu_service_running:
    if not force:
        raise HTTPException(409, "GPU in use")
    else:
        await stop_service(gpu_service_running)
        # Then proceed with start
```

### Health Check Failures
```python
# Non-blocking - just marks service as unhealthy
# Service continues running
# User can check via /status endpoint
```

## Testing Strategy

### Unit Tests (Future)
- Test service discovery logic
- Test GPU arbitration rules
- Test manifest validation
- Mock docker compose calls

### Integration Tests
```bash
# Current: Manual testing via test_api.sh
./test_api.sh

# Future: Automated integration tests
pytest tests/test_service_lifecycle.py
pytest tests/test_gpu_arbitration.py
pytest tests/test_health_monitoring.py
```

### End-to-End Tests
```bash
# Start Service Nanny
# Start a GPU service
# Verify it works
# Try to start another GPU service → Should fail
# Force start → First should stop, second should start
# Stop all services
# Verify cleanup
```

## Performance Considerations

### Service Discovery
- Only scans on startup or manual /rediscover
- Cached in memory (services_registry)
- No file watching (for now)

### Health Checks
- Currently synchronous HTTP requests
- Future: Async with aiohttp
- Configurable timeout per service

### Docker Operations
- Subprocess calls can block API
- Future: Use Docker Python SDK
- Consider async execution

## Deployment

### Production Checklist
- [ ] Add authentication to API
- [ ] Add rate limiting
- [ ] Enable HTTPS
- [ ] Add logging to file
- [ ] Add metrics collection
- [ ] Set up monitoring/alerting
- [ ] Add backup/restore for state
- [ ] Document disaster recovery

### High Availability (Future)
- Run multiple Service Nanny instances
- Use Redis for shared state
- Implement leader election
- Distributed health checks
