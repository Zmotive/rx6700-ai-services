# Dia TTS Service - Technical Implementation & Challenge

**Date**: November 10, 2025  
**Status**: ⚠️ Implementation Complete, ROCm Integration Blocked  
**Hardware**: AMD RX 6700 XT (12GB VRAM, gfx1031) with ROCm 6.4.4

---

## Overview

Dia is a 1.6B parameter text-to-dialogue TTS model from Nari Labs that generates natural conversations with voice control and 21 non-verbal sound effects (laughs, coughs, sighs, etc.). This document details our complete implementation and the technical roadblock encountered.

**Repository**: https://github.com/nari-labs/dia  
**Model**: nari-labs/Dia-1.6B-0626 (HuggingFace)  
**License**: Apache 2.0

---

## What We Built

### Complete Service Implementation (7 Files)

#### 1. **service.yaml** - Service Metadata
```yaml
name: dia
description: Text-to-dialogue TTS with voice control and non-verbal sounds
version: 1.6B-0626
port: 8002
health_endpoint: /health
tags: [tts, dialogue, voice-cloning, sound-effects]
model:
  name: nari-labs/Dia-1.6B-0626
  parameters: 1.6B
  vram: ~4.4GB (FP16)
```

**Purpose**: Service discovery and metadata for orchestration.

---

#### 2. **docker-compose.yml** - Container Configuration
```yaml
services:
  dia:
    image: rocm/pytorch:rocm6.2_ubuntu22.04_py3.10_pytorch_release_2.3.0
    container_name: dia
    ports: ["8002:8002"]
    devices: ["/dev/kfd", "/dev/dri"]
    group_add: ["44", "109"]  # video, render groups
    environment:
      - HSA_OVERRIDE_GFX_VERSION=10.3.0
      - PYTORCH_ROCM_ARCH=gfx1031
      - HIP_VISIBLE_DEVICES=0
    volumes:
      - ./:/workspace
      - ~/.cache/huggingface:/root/.cache/huggingface
    command: bash start.sh
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      start_period: 120s
```

**Key Features**:
- ROCm 6.2 PyTorch 2.3 base image
- Proper GPU passthrough (`/dev/kfd`, `/dev/dri`)
- GFX version override for RX 6700 XT compatibility
- HuggingFace model cache mounted

---

#### 3. **dia_api.py** - FastAPI Server (~250 lines)

**Endpoints**:
- `GET /` - Service information
- `GET /health` - Health check with GPU status
- `POST /generate` - Generate dialogue audio
- `GET /nonverbals` - List 21 supported sound effects
- `GET /docs` - Swagger UI

**Request Model**:
```python
class GenerateRequest(BaseModel):
    text: str  # With [S1]/[S2] speaker tags and (nonverbal) tags
    cfg_scale: float = 3.0  # 1.0-10.0
    temperature: float = 1.8  # 0.1-2.5
    top_p: float = 0.90  # 0.0-1.0
    top_k: int = 45  # 1-100
    seed: Optional[int] = None  # For reproducibility
    output_format: str = "mp3"  # mp3, wav, base64
```

**Response**:
```python
class GenerateResponse(BaseModel):
    audio_base64: str
    message: str
    duration_seconds: float
    sample_rate: int = 24000
```

**Features**:
- Speaker tag validation ([S1], [S2])
- Multiple output formats (MP3, WAV, base64)
- Configurable generation parameters
- GPU detection and diagnostics
- Proper error handling

---

#### 4. **start.sh** - Startup Script (59 lines)

**Initialization Flow**:
1. Display ROCm environment information
2. Install system dependencies (ffmpeg, libsndfile1, curl)
3. Install Dia from GitHub with dependency management
4. Install FastAPI stack (uvicorn, python-multipart)
5. Verify PyTorch and ROCm availability
6. Start API server on port 8002

**Critical Section** (The Problem Area):
```bash
# Install Dia from GitHub (skip torch dependency - we already have ROCm PyTorch)
pip install --no-cache-dir -q --no-deps git+https://github.com/nari-labs/dia.git

# Install other dependencies Dia needs (except torch which is already installed with ROCm)
pip install --no-cache-dir -q \
    descript-audio-codec \
    transformers \
    numpy \
    scipy \
    soundfile \
    fastapi \
    uvicorn[standard] \
    python-multipart
```

---

#### 5. **app.py** - Python Client (~200 lines)

**DiaClient Class**:
```python
class DiaClient:
    def __init__(self, base_url="http://localhost:8002"):
        self.base_url = base_url
    
    def health_check(self) -> dict:
        """Check service health and GPU status"""
    
    def generate(self, text, cfg_scale=3.0, temperature=1.8, 
                 top_p=0.90, top_k=45, seed=None, 
                 output_format="mp3", save_path=None) -> dict:
        """Generate dialogue audio"""
    
    def list_nonverbals(self) -> dict:
        """Get list of supported non-verbal sound effects"""
```

**Example Usage**:
```python
client = DiaClient()

# Generate conversation with sound effects
response = client.generate(
    text="[S1] Hey! How are you? [S2] I'm great! (laughs) How about you?",
    save_path="conversation.mp3"
)
```

---

#### 6. **requirements.txt**
```
requests>=2.31.0
```

Simple dependency file for the Python client.

---

#### 7. **README.md** (~450 lines)

**Comprehensive Documentation**:
- Features and capabilities
- Model specifications (1.6B params, 24kHz, ~4.4GB VRAM)
- Hardware requirements (6GB+ VRAM recommended)
- Quick start guide
- API endpoint documentation
- Usage examples (curl, Python, speaker tags)
- **21 Non-Verbal Sound Effects Table**:
  - (laughs), (coughs), (sighs), (gasps), (clears throat)
  - (singing), (sings), (mumbles), (beep), (groans)
  - (sniffs), (claps), (screams), (inhales), (exhales)
  - (applause), (burps), (humming), (sneezes), (chuckle), (whistles)
- Best practices for text formatting
- Configuration parameters
- Performance benchmarks (estimated ~2x realtime on RTX 4090)
- Troubleshooting guide
- Service management commands

---

## The Technical Challenge

### Problem: PyTorch/ROCm Dependency Hell

**What Happened**:
1. Base image `rocm/pytorch:rocm6.2_ubuntu22.04_py3.10_pytorch_release_2.3.0` comes with **PyTorch 2.3.0a0+git96dd291 compiled with ROCm 6.2**
2. When installing Dia from GitHub, pip installs dependencies including `torch`
3. Dia's dependency tree requires `torch==2.6.0` (specified in nari-tts package)
4. Pip installs **PyTorch 2.9.0+cu128** (CUDA version) which overwrites ROCm PyTorch
5. CUDA PyTorch cannot detect AMD GPU through ROCm → `torch.cuda.is_available()` returns `False`
6. Service fails to start with: `RuntimeError: ROCm/CUDA not available`

**Evidence from Logs**:
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
nari-tts 0.1.0 requires torch==2.6.0, but you have torch 2.9.0 which is incompatible.

✅ PyTorch: 2.9.0+cu128  ← CUDA version, not ROCm!
✅ ROCm available: False  ← GPU not detected
```

**Container Status**: Crash-looping
```
Restarting (3) 38 seconds ago
```

---

### Why This Is Complex

1. **Dependency Conflict**: Dia requires specific PyTorch version (2.6.0) not available in ROCm builds
2. **pip Resolution**: Using `--no-deps` breaks other critical dependencies (descript-audio-codec, transformers)
3. **Docker Isolation**: Container needs both ROCm libraries AND ROCm-compiled PyTorch
4. **Version Mismatch**: 
   - Host ROCm: 6.4.4
   - Container ROCm: 6.2
   - Dia expects: PyTorch 2.6.0 (only available as CUDA)
   - Container has: PyTorch 2.3.0 (ROCm) → gets overwritten to 2.9.0 (CUDA)

---

## Potential Solutions

**Note**: CPU mode is NOT an option - GPU acceleration required for acceptable performance.

---

### Option A: Custom Docker Image 🔨 Complex, Robust
**Approach**: Build custom image with Dia pre-installed alongside ROCm PyTorch

**Dockerfile Strategy**:
```dockerfile
FROM rocm/pytorch:rocm6.2_ubuntu22.04_py3.10_pytorch_release_2.3.0

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg libsndfile1 curl git

# Clone Dia and manually install without torch dependency
RUN git clone https://github.com/nari-labs/dia.git /tmp/dia && \
    cd /tmp/dia && \
    # Remove torch from requirements
    sed -i '/torch==/d' requirements.txt && \
    pip install --no-cache-dir -e .

# Install other dependencies
RUN pip install --no-cache-dir fastapi uvicorn[standard] python-multipart

# Copy application files
COPY . /workspace
WORKDIR /workspace

CMD ["python3", "dia_api.py"]
```

**Pros**:
- Preserves ROCm PyTorch
- Reproducible builds
- Faster container startup

**Cons**:
- Requires maintaining custom image
- Build complexity
- May need updates when Dia updates

---

### Option B: Manual ROCm PyTorch Reinstall 🎯 Targeted, Fragile
**Approach**: Install Dia, then reinstall ROCm PyTorch from AMD wheels

**Modified start.sh**:
```bash
# Install Dia (gets CUDA PyTorch)
pip install git+https://github.com/nari-labs/dia.git

# Reinstall ROCm PyTorch from AMD
pip uninstall -y torch torchvision torchaudio
pip install torch==2.3.0 torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/rocm6.2
```

**Pros**:
- Keeps existing Docker setup
- Uses official AMD wheels

**Cons**:
- Version compatibility risks (Dia wants 2.6.0, ROCm has 2.3.0)
- Fragile if Dia's dependencies change
- Longer startup time

---

### Option C: Native Installation 🏠 Direct, Non-Containerized
**Approach**: Install Dia directly on host system with existing ROCm setup

**Steps**:
```bash
# On host (already has ROCm 6.4.4)
pip install git+https://github.com/nari-labs/dia.git
python3 dia_api.py
```

**Pros**:
- Uses host's working ROCm installation
- Simpler dependency management
- Faster iteration for debugging

**Cons**:
- No container isolation
- Harder to manage/deploy
- System-wide dependencies

---

## Hardware Specifications

**GPU**: AMD RX 6700 XT
- VRAM: 12GB GDDR6
- Architecture: RDNA 2 (gfx1031)
- Compute Units: 40
- ROCm Support: Yes (requires override)

**ROCm Configuration**:
- Host Version: 6.4.4
- Container Version: 6.2
- Required Override: `HSA_OVERRIDE_GFX_VERSION=10.3.0`
- Architecture: `PYTORCH_ROCM_ARCH=gfx1031`

**VRAM Allocation**:
- Qwen-Coder (running): ~8-9GB
- Dia (estimated): ~4.4GB (FP16)
- **Total Needed**: ~12-13GB
- **Available**: 12GB → **Potential memory pressure**

---

## Performance Estimates

Based on Dia documentation and RTX 4090 benchmarks:

| Hardware | Speed | Notes |
|----------|-------|-------|
| RTX 4090 (CUDA) | ~2x realtime | Reference benchmark |
| RX 6700 XT (ROCm) | ~1.5-2x realtime | Estimated (if working) |

**Example**: Generating 10 seconds of dialogue
- RTX 4090: ~5 seconds
- RX 6700 XT: ~5-7 seconds (estimated)

---

## Diagnostic Commands

**Check Container Status**:
```bash
docker ps -a | grep dia
docker logs dia --tail 50
```

**Verify PyTorch Version**:
```bash
docker exec dia python3 -c "import torch; print(f'Version: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

**Check ROCm in Base Image**:
```bash
docker run --rm rocm/pytorch:rocm6.2_ubuntu22.04_py3.10_pytorch_release_2.3.0 \
    python3 -c "import torch; print(torch.__version__); print(torch.version.hip if hasattr(torch.version, 'hip') else 'No ROCm')"
```

**Expected Output** (Base Image):
```
Version: 2.3.0a0+git96dd291
ROCm: 6.2.41133-dd7f95766
```

**Actual Output** (After Dia Install):
```
Version: 2.9.0+cu128  ← Problem!
CUDA: False
```

---

## Files Created

```
/home/zack/ai-workspace/services/dia/
├── service.yaml              # Service metadata (23 lines)
├── docker-compose.yml        # Container config (39 lines)
├── dia_api.py               # FastAPI server (258 lines)
├── start.sh                 # Startup script (59 lines, executable)
├── app.py                   # Python client (200 lines)
├── requirements.txt         # Client dependencies (1 line)
├── README.md                # Documentation (450+ lines)
└── TECHNICAL_NOTES.md       # This file
```

**Total**: 7 files, ~1,230 lines of code and documentation

---

## Next Steps for Resolution

### Immediate Action Items:
1. **Decision Required**: Choose solution approach (A, B, or C)
2. **Test PyTorch 2.6 ROCm**: Check if AMD provides ROCm wheels for PyTorch 2.6
3. **Contact Dia Maintainers**: Ask about ROCm support / relaxed PyTorch requirements
4. **Memory Analysis**: Confirm RX 6700 XT can run both qwen-coder + Dia simultaneously

### Research Tasks:
- [ ] Check PyTorch ROCm wheel availability: https://download.pytorch.org/whl/rocm6.2/
- [ ] Review Dia GitHub issues for ROCm/AMD GPU usage
- [ ] Measure actual VRAM usage with both services running

### Documentation:
- [x] Create technical implementation notes
- [x] Document dependency conflict root cause
- [x] Provide multiple solution approaches
- [ ] Create comparison matrix once solution chosen

---

## Useful Links

- **Dia Repository**: https://github.com/nari-labs/dia
- **Dia Model**: https://huggingface.co/nari-labs/Dia-1.6B-0626
- **Dia Demo**: https://huggingface.co/spaces/nari-labs/Dia
- **ROCm PyTorch Wheels**: https://pytorch.org/get-started/locally/
- **ROCm Documentation**: https://rocm.docs.amd.com/
- **AMD RX 6700 XT ROCm Support**: Requires `HSA_OVERRIDE_GFX_VERSION=10.3.0`

---

## Lessons Learned

1. **Docker GPU Passthrough is Complex**: ROCm requires proper device mapping, group permissions, and environment variables
2. **Python Dependency Resolution**: pip's resolver can introduce incompatible versions during transitive dependency installation
3. **PyTorch Distribution Fragmentation**: Different builds (CUDA, ROCm, CPU) are not interchangeable
4. **Version Pinning Trade-offs**: Strict version requirements (torch==2.6.0) limit flexibility for alternative backends
5. **Documentation Value**: Pre-built Docker images may have different PyTorch versions than expected

---

**Status**: Implementation complete, awaiting resolution strategy selection.  
**Recommendation**: Try Option B (Manual ROCm PyTorch Reinstall) first as it's least invasive.  
**Constraint**: GPU-only - CPU mode is not acceptable for production use.

---

_Last Updated: November 10, 2025_  
_Author: AI Assistant_  
_Review Status: Ready for decision_
