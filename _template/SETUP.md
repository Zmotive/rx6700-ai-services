# Template Service Setup Guide

This template provides a quick-start structure for creating new AI services.

## How to Use This Template

### 1. Copy the Template

```bash
cd ~/ai-workspace/services
cp -r _template my-new-service
cd my-new-service
```

### 2. Update `service.yaml`

```yaml
name: my-new-service  # Change this!
description: What your service does
version: 1.0.0

gpu_required: false  # Set to true if you need GPU
vram_gb: 0          # Set if GPU required

ports:
  - "8002:8000"  # Change host port to avoid conflicts

health_endpoint: http://localhost:8002/health  # Update port
```

**Important**: Choose a unique host port! Check existing services:
- `minimal-sd-api`: 8000
- `service-nanny`: 8080
- Your service: Pick 8001, 8002, 8003, etc.

### 3. Update `docker-compose.yml`

```yaml
services:
  my-new-service:  # Change service name
    container_name: my-new-service  # Change container name
    ports:
      - "8002:8000"  # Match service.yaml
    # ... rest of config
```

**For GPU Services:**
Uncomment the GPU-related sections:
- `devices` (for /dev/kfd, /dev/dri access)
- `group_add` (video and render groups)
- `environment` variables (HIP_PLATFORM, ROCm settings)

### 4. Update `app.py`

Replace the template logic with your service:

```python
app = FastAPI(
    title="My New Service",  # Update title
    description="Description",  # Update description
    version="1.0.0"
)

# Keep the /health endpoint as-is (required for service-nanny)
# Add your custom endpoints
```

### 5. Update `README.md`

- Change the title
- Document your API endpoints
- Update usage examples
- Add any special requirements

### 6. Test Your Service

```bash
# Start it
docker compose up -d

# Check health
curl http://localhost:8002/health  # Use your port

# View logs
docker compose logs -f

# Stop it
docker compose down
```

### 7. Register with Service Nanny

Once your service is working, it will be automatically discovered by service-nanny (if service-nanny is running).

Verify registration:
```bash
curl http://localhost:8080/services
```

## Template Checklist

Before deploying your new service:

- [ ] Updated `service.yaml` with unique name and port
- [ ] Updated `docker-compose.yml` service and container names
- [ ] Changed host port to avoid conflicts
- [ ] Kept `/health` endpoint in `app.py` (required!)
- [ ] Tested service starts successfully
- [ ] Tested health endpoint responds
- [ ] Updated README.md with actual documentation
- [ ] Added service to main `/services/README.md`

## Port Registry

Keep track of used ports to avoid conflicts:

| Port | Service |
|------|---------|
| 8000 | minimal-sd-api |
| 8080 | service-nanny |
| 8001 | (available) |
| 8002 | (available) |
| 8003 | (available) |

## GPU Service Notes

If `gpu_required: true` in `service.yaml`:

1. **Only one GPU service can run at a time** (enforced by service-nanny)
2. Uncomment GPU sections in `docker-compose.yml`
3. Set `vram_gb` to estimated usage
4. Test memory usage with: `rocm-smi`
5. Consider Phase 1 optimizations (see minimal-sd-api for examples)

## Common Patterns

### AI Model Service
```yaml
gpu_required: true
vram_gb: 8
volumes:
  - ${AI_WORKSPACE:-~/ai-workspace}/Models:/workspace/Models
tags:
  - ai
  - inference
```

### Data Processing Service
```yaml
gpu_required: false
volumes:
  - ${AI_WORKSPACE:-~/ai-workspace}/Data:/workspace/data
tags:
  - processing
  - utility
```

### Web API Service
```yaml
gpu_required: false
ports:
  - "8001:8000"
tags:
  - api
  - web
```

## Getting Help

- Check existing services for examples: `minimal-sd-api/`
- Read service-nanny API docs: `service-nanny/README.md`
- Review main README: `/services/README.md`
