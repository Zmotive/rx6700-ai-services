# AI Services

Production-ready Docker Compose services for AI/ML workloads on AMD RX 6700 XT with ROCm.

## 🔧 Service Orchestration

All services are managed by **Service Nanny**, an orchestrator that:
- Auto-discovers services via `service.yaml` manifests
- Enforces GPU arbitration (one GPU service at a time)
- Provides REST API for service lifecycle management
- Monitors service health
- Future: MCP server for AI-assisted orchestration

**Quick Start with Service Nanny:**
```bash
# Start the orchestrator
cd service-nanny/
docker compose up -d

# List all services
curl http://localhost:8080/services | jq

# Start a service
curl -X POST http://localhost:8080/services/minimal-sd-api/start

# Check status
curl http://localhost:8080/services/minimal-sd-api/status | jq
```

See [service-nanny/README.md](./service-nanny/README.md) for full API documentation.

## ⚠️ GPU Arbitration

**Important**: These services share GPU resources. Service Nanny enforces **"one GPU service at a time"** to prevent VRAM conflicts. CPU-only services can run concurrently.

## Available Services

### 🔧 service-nanny (Orchestrator)
**AI Service Orchestrator with GPU arbitration**

- **Status**: Production Ready
- **Port**: 8080
- **Features**:
  - Auto-discovery of services
  - REST API for service management
  - GPU arbitration (one-of enforcement)
  - Health monitoring
  - Future MCP server support
- **Location**: `./service-nanny/`
- **Docs**: [service-nanny/README.md](./service-nanny/README.md)

### 1. minimal-sd-api ✅ Production Ready
**Stable Diffusion API with GPU acceleration**

- **Status**: Stable, tested, production-ready
- **GPU**: Required (8GB VRAM typical)
- **Port**: 8000
- **Performance**: 768×768 images in ~9 seconds (10 steps)
- **Features**: 
  - FastAPI REST endpoint
  - Resolution validation (prevents crashes)
  - Phase 1 optimizations (attention slicing, VAE tiling)
  - ROCm 6.4 compatible
- **Hardware**: AMD RX 6700 XT (12GB VRAM)
- **Location**: `./minimal-sd-api/`
- **Quick Start**: See [minimal-sd-api/README.md](./minimal-sd-api/README.md)

---

## Quick Start

### Option 1: Using Service Nanny (Recommended)

```bash
# 1. Start Service Nanny
cd service-nanny/
docker compose up -d

# 2. Start a service via API
curl -X POST http://localhost:8080/services/minimal-sd-api/start

# 3. Check status
curl http://localhost:8080/services/minimal-sd-api/status | jq

# 4. Stop service
curl -X POST http://localhost:8080/services/minimal-sd-api/stop
```

### Option 2: Direct Docker Compose

```bash
# Navigate to a service
cd minimal-sd-api/

# Start the service
docker compose up -d

# Check logs
docker compose logs -f

# Stop the service (before starting another GPU service)
docker compose down
```

## System Requirements

- **GPU**: AMD RX 6700 XT (12GB VRAM)
- **ROCm**: 6.4.0+ on host
- **Docker**: 24.0+
- **Docker Compose**: 2.0+
- **OS**: Ubuntu 22.04/24.04

## Adding New Services

### Using the Template (Recommended)

```bash
# 1. Copy the template
cd ~/ai-workspace/services
cp -r _template my-new-service
cd my-new-service

# 2. Edit service.yaml
# - Change name, description, ports
# - Set gpu_required and vram_gb
# - Update health_endpoint

# 3. Edit docker-compose.yml
# - Change service name and container name
# - Update ports to match service.yaml
# - Uncomment GPU sections if needed

# 4. Edit app.py
# - Implement your service logic
# - Keep /health endpoint (required!)

# 5. Test locally
docker compose up -d
curl http://localhost:8001/health  # Use your port
docker compose down

# 6. Rediscover with Service Nanny
curl -X POST http://localhost:8080/rediscover

# 7. Verify registration
curl http://localhost:8080/services | jq
```

See [_template/SETUP.md](./_template/SETUP.md) for detailed instructions.

### Service Requirements

Each service must have:
1. **`service.yaml`** - Manifest for Service Nanny discovery
2. **`docker-compose.yml`** - Container configuration
3. **`/health` endpoint** - Returns 200 OK when healthy
4. **Unique port** - No conflicts with other services

### Port Registry

| Port | Service | Status |
|------|---------|--------|
| 8000 | minimal-sd-api | In use |
| 8080 | service-nanny | In use |
| 8001-8099 | (available) | - |
