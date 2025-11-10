# Service Nanny

AI Service Orchestrator with GPU arbitration and health monitoring.

## Overview

Service Nanny manages the lifecycle of AI services in the `/services` directory. It:
- **Auto-discovers** services with `service.yaml` manifests
- **Enforces GPU arbitration** (only one GPU service at a time)
- **Monitors health** via service health endpoints
- **Provides REST API** for service management
- **Future**: MCP server for AI-assisted service orchestration

## Quick Start

```bash
cd ~/ai-workspace/services/service-nanny
docker compose up -d

# Check status
curl http://localhost:8080/health

# View logs
docker compose logs -f
```

## API Endpoints

### Service Discovery

#### GET /services
List all discovered services.

**Response:**
```json
{
  "total": 2,
  "services": [
    {
      "name": "minimal-sd-api",
      "description": "Stable Diffusion image generation",
      "version": "1.0.0",
      "gpu_required": true,
      "vram_gb": 8,
      "ports": ["8000:8000"],
      "health_endpoint": "http://localhost:8000/health",
      "tags": ["image-generation", "stable-diffusion"],
      "status": "stopped"
    }
  ],
  "gpu_service_running": null
}
```

#### GET /services/{service_name}
Get details about a specific service.

```bash
curl http://localhost:8080/services/minimal-sd-api | jq
```

### Service Control

#### POST /services/{service_name}/start
Start a service.

**Request Body (optional):**
```json
{
  "force": false
}
```

Set `force: true` to automatically stop a running GPU service if starting another GPU service.

**Example:**
```bash
# Start service
curl -X POST http://localhost:8080/services/minimal-sd-api/start

# Force start (stops other GPU services)
curl -X POST http://localhost:8080/services/minimal-sd-api/start \
  -H "Content-Type: application/json" \
  -d '{"force": true}'
```

**Response:**
```json
{
  "message": "Service 'minimal-sd-api' started successfully",
  "status": "running",
  "health_endpoint": "http://localhost:8000/health"
}
```

#### POST /services/{service_name}/stop
Stop a service.

```bash
curl -X POST http://localhost:8080/services/minimal-sd-api/stop
```

**Response:**
```json
{
  "message": "Service 'minimal-sd-api' stopped successfully",
  "status": "stopped"
}
```

### Service Monitoring

#### GET /services/{service_name}/status
Get detailed status of a service.

```bash
curl http://localhost:8080/services/minimal-sd-api/status | jq
```

**Response:**
```json
{
  "name": "minimal-sd-api",
  "status": "running",
  "is_running": true,
  "is_healthy": true,
  "uptime": "0:05:23.123456"
}
```

#### GET /services/{service_name}/logs?tail=100
Get recent logs from a service.

```bash
curl http://localhost:8080/services/minimal-sd-api/logs?tail=50
```

### System Management

#### POST /rediscover
Manually trigger service discovery (useful after adding new services).

```bash
curl -X POST http://localhost:8080/rediscover
```

#### GET /health
Service Nanny health check.

```bash
curl http://localhost:8080/health
```

## GPU Arbitration

Service Nanny enforces **"one GPU service at a time"** to prevent VRAM conflicts.

### Rules:
1. Only one service with `gpu_required: true` can run at a time
2. Attempting to start a second GPU service returns `409 Conflict`
3. Use `force: true` to automatically stop the running GPU service first

### Example Flow:

```bash
# Start first GPU service
curl -X POST http://localhost:8080/services/minimal-sd-api/start
# ✅ Success

# Try to start another GPU service
curl -X POST http://localhost:8080/services/another-gpu-service/start
# ❌ 409 Conflict: GPU service 'minimal-sd-api' is already running

# Force start (stops minimal-sd-api first)
curl -X POST http://localhost:8080/services/another-gpu-service/start \
  -H "Content-Type: application/json" \
  -d '{"force": true}'
# ✅ Success (minimal-sd-api stopped, another-gpu-service started)
```

## Service Manifest (service.yaml)

Each service needs a `service.yaml` file for discovery:

```yaml
name: my-service
description: What the service does
version: 1.0.0

gpu_required: false  # Set to true for GPU services
vram_gb: 0           # Estimated VRAM usage

compose_file: docker-compose.yml
ports:
  - "8001:8000"

health_endpoint: http://localhost:8001/health
health_timeout: 30

tags:
  - category1
```

See `../_template/service.yaml` for full schema.

## Adding New Services

1. **Use the template:**
   ```bash
   cd ~/ai-workspace/services
   cp -r _template my-new-service
   cd my-new-service
   ```

2. **Update `service.yaml`** with service details

3. **Test locally:**
   ```bash
   docker compose up -d
   curl http://localhost:8001/health
   docker compose down
   ```

4. **Rediscover services:**
   ```bash
   curl -X POST http://localhost:8080/rediscover
   ```

5. **Verify registration:**
   ```bash
   curl http://localhost:8080/services | jq
   ```

See `../_template/SETUP.md` for detailed instructions.

## Architecture

```
┌─────────────────────────────────────┐
│      Service Nanny (Port 8080)      │
│  ┌───────────────────────────────┐  │
│  │   Service Discovery Engine    │  │
│  │   (scans for service.yaml)    │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │   GPU Arbitration Engine      │  │
│  │   (enforces one-of rule)      │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │   Health Monitor              │  │
│  │   (checks service endpoints)  │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │   Docker Compose Controller   │  │
│  │   (start/stop via socket)     │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
         │          │          │
    ┌────┴────┐ ┌──┴───┐ ┌────┴────┐
    │Service 1│ │Svc 2 │ │Service 3│
    │(GPU)    │ │(CPU) │ │(GPU)    │
    └─────────┘ └──────┘ └─────────┘
```

## Troubleshooting

### Service Nanny won't start
```bash
# Check logs
docker compose logs

# Verify Docker socket access
ls -la /var/run/docker.sock

# Check user is in docker group
groups | grep docker
```

### Services not discovered
```bash
# Check service.yaml exists
ls ../my-service/service.yaml

# Manually rediscover
curl -X POST http://localhost:8080/rediscover

# Check Service Nanny logs
docker compose logs -f
```

### Can't start GPU service
```bash
# Check what's running
curl http://localhost:8080/services | jq '.gpu_service_running'

# Force stop current GPU service
curl -X POST http://localhost:8080/services/my-service/start \
  -d '{"force": true}'
```

### Service health check fails
```bash
# Check service status
curl http://localhost:8080/services/my-service/status

# Verify health endpoint works directly
curl http://localhost:8001/health

# Check service logs
curl http://localhost:8080/services/my-service/logs?tail=50
```

## Future Features (MCP Server)

Service Nanny will become an MCP server providing:

### Tools
- `start_service(name, force=false)` - Start a service
- `stop_service(name)` - Stop a service
- `list_services(filter)` - List services with filtering
- `get_service_status(name)` - Get service details

### Resources
- `service://status` - Current service states
- `service://logs/{name}` - Service logs
- `service://metrics` - Usage metrics

### Prompts
- "What AI services are available?"
- "Start the image generation service"
- "Which service is using the GPU?"
- "Show me the logs for the last service"

## Requirements

- Docker 24.0+
- Docker Compose 2.0+
- Services must have `service.yaml` manifest
- Services must implement `/health` endpoint

## Development

Run locally without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python3 service_nanny.py

# API will be available at http://localhost:8080
```

## Related Documentation

- [Template Service](../_template/SETUP.md) - How to create new services
- [Main README](../README.md) - Services overview
- [minimal-sd-api](../minimal-sd-api/README.md) - Example service
