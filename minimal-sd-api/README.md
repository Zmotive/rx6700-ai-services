# Minimal Stable Diffusion API

GPU-accelerated Stable Diffusion 1.5 API with FastAPI on AMD RX 6700 XT.

## Status: ✅ Production Ready

- **Performance**: 768×768 images in ~9 seconds (10 steps)
- **Stability**: Phase 1 optimizations proven stable
- **Resolution Protection**: API validates requests to prevent crashes
- **ROCm Version**: 6.4.4 (container) with 6.4.0 host

## Hardware Requirements

- **GPU**: AMD RX 6700 XT (12GB VRAM) - gfx1031
- **Host ROCm**: 6.4.0+
- **Docker**: 24.0+
- **VRAM**: ~8GB used at 768×768

## Quick Start

### Start the Service

```bash
cd ~/ai-workspace/services/minimal-sd-api
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Test Generation

```bash
# Generate a 768×768 image
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful mountain landscape at sunset",
    "num_inference_steps": 10,
    "width": 768,
    "height": 768,
    "seed": 42
  }' -o output.png

# Check service limits
curl http://localhost:8000/limits | python3 -m json.tool

# Health check
curl http://localhost:8000/health
```

### Stop the Service

```bash
docker compose down
```

## API Endpoints

### POST /generate
Generate an image from a text prompt.

**Request Body**:
```json
{
  "prompt": "your prompt here",
  "num_inference_steps": 10,
  "width": 768,
  "height": 768,
  "seed": 42
}
```

**Response**: PNG image (binary)

**Validation**:
- Width/height must be divisible by 8
- Maximum: 768×768
- Minimum: 64×64

### GET /limits
Returns resolution capabilities and hardware info.

```json
{
  "resolution": {
    "max_width": 768,
    "max_height": 768,
    "min_dimension": 64,
    "divisible_by": 8,
    "max_tested_stable": "768×768"
  },
  "hardware": {
    "gpu": "AMD Radeon RX 6700 XT",
    "vram": "12GB",
    "rocm_available": true
  }
}
```

### GET /health
Service health check with resolution limits included.

## Performance Benchmarks

| Resolution | Steps | Time | Status |
|------------|-------|------|--------|
| 512×512 | 10 | ~4-5s | ✅ Stable |
| 640×640 | 10 | ~6-7s | ✅ Stable |
| 768×768 | 10 | ~9s | ✅ **Recommended** |
| 832×832 | 10 | ~18s | ⚠️ Works but not validated |
| 1024×1024 | 10 | - | ❌ Crashes (memory corruption) |

## Phase 1 Optimizations (Active)

These optimizations are enabled by default in `minimal_sd_api.py`:

1. **Attention Slicing** - 20-30% memory reduction
2. **VAE Tiling** - Enables larger resolutions
3. **Channels-last Memory Format** - 5-10% performance boost
4. **Model CPU Offload** - Reduces VRAM usage

## Known Limitations

### Resolution Constraints
- **Maximum Safe**: 768×768 (conservative limit)
- **Asymmetric Behavior**: 768×832 (wide) works, but 832×768 (tall) crashes
- **Root Cause**: Memory corruption in ROCm/PyTorch stack (details in RESOLUTION_LIMITS.md)

### Error Types at High Resolutions
- `malloc(): invalid size (unsorted)` - Dimensional issues
- `munmap_chunk(): invalid pointer` - Memory corruption

See [RESOLUTION_LIMITS.md](./RESOLUTION_LIMITS.md) for detailed boundary testing results.

## Files

- `docker-compose.yml` - Service definition
- `minimal_sd_api.py` - FastAPI application with Phase 1 optimizations
- `start_api.sh` - Container startup script
- `find_crash_boundary.py` - Testing tool for resolution limits
- `RESOLUTION_LIMITS.md` - Detailed boundary testing documentation

## Troubleshooting

### Container won't start
```bash
# Check Docker logs
docker compose logs

# Verify ROCm devices
ls -la /dev/kfd /dev/dri

# Check host ROCm version
rocminfo | grep "Marketing Name"
```

### Generation crashes
- Ensure resolution is ≤768×768
- Check both dimensions are divisible by 8
- Verify with `/limits` endpoint first

### Slow performance
- Check GPU utilization: `rocm-smi`
- Verify Phase 1 optimizations are enabled (check container logs on startup)
- Ensure no other GPU processes are running

## Next Steps

### Potential Optimizations (Phase 2+)

1. **Push Resolution Limits**
   - Test 768×896, 768×960, 768×1024 (safe width, increase height)
   - Investigate asymmetric crash root cause
   - Try different Phase 1 optimization combinations

2. **Add SDXL Support**
   - Requires more VRAM optimization
   - May need model quantization
   - Test with 512×512 first

3. **Batch Generation**
   - Generate multiple images in one request
   - Memory constraints may limit batch size

4. **Dynamic Resolution Limits**
   - Calculate safe limits based on available VRAM
   - Adjust based on model size and optimizations

5. **Add LoRA Support**
   - Enable fine-tuned model loading
   - Test VRAM impact

### Infrastructure Improvements

1. **Helper Script** - `run-service.sh` to enforce one-of behavior
2. **Monitoring** - Prometheus metrics endpoint
3. **Caching** - Model caching for faster cold starts
4. **Queue System** - Handle multiple requests gracefully

## References

- Stable Diffusion 1.5: https://huggingface.co/runwayml/stable-diffusion-v1-5
- ROCm Documentation: https://rocm.docs.amd.com/
- PyTorch ROCm: https://pytorch.org/get-started/locally/
