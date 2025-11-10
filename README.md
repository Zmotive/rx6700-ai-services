# AI Services

Production-ready Docker Compose services for AI/ML workloads on AMD RX 6700 XT with ROCm.

## ⚠️ One-of Services

**Important**: These services are designed to run **one at a time** due to GPU resource constraints. Only start one service at a time to avoid VRAM conflicts.

## Available Services

### 1. minimal-sd-api ✅ Production Ready
**Stable Diffusion API with GPU acceleration**

- **Status**: Stable, tested, production-ready
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

```bash
# Navigate to a service
cd minimal-sd-api/

# Start the service
docker compose up -d

# Check logs
docker compose logs -f

# Stop the service (before starting another)
docker compose down
```

## System Requirements

- **GPU**: AMD RX 6700 XT (12GB VRAM)
- **ROCm**: 6.4.0+ on host
- **Docker**: 24.0+
- **Docker Compose**: 2.0+
- **OS**: Ubuntu 22.04/24.04

## Adding New Services

When adding a new service:

1. Create a new directory: `mkdir my-new-service/`
2. Add `docker-compose.yml` and related files
3. Create `README.md` with service-specific docs
4. Update this file to list the new service
5. Test that it works standalone
6. Document any next steps or known limitations

## Helper Scripts (Future)

Planned: `./run-service.sh <service-name>` to enforce one-of behavior and manage service lifecycle.
