#!/bin/bash
set -e

echo "=================================================="
echo "ComfyUI ROCm Service Startup"
echo "=================================================="

# Check ROCm
echo "🔍 Checking ROCm availability..."
python3 -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'ROCm available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"

# Install ComfyUI if not already present
if [ ! -f "/workspace/ComfyUI/main.py" ]; then
    echo "📥 Cloning ComfyUI..."
    cd /workspace
    git clone https://github.com/comfyanonymous/ComfyUI.git
else
    echo "✅ ComfyUI already installed"
    cd /workspace/ComfyUI
    git pull --quiet || true  # Update to latest (ignore errors if offline)
fi

cd /workspace/ComfyUI

# Install Python dependencies (skip torch/torchvision/torchaudio as we use ROCm versions from base image)
echo "📦 Installing ComfyUI dependencies (excluding torch/torchvision/torchaudio)..."
grep -vE "^torch(==|>=| |$)|^torchvision|^torchaudio" requirements.txt > requirements-notorch.txt || cp requirements.txt requirements-notorch.txt
pip install -q --no-cache-dir -r requirements-notorch.txt

# Apply ROCm compatibility patch
bash /patch_rocm.sh

# Additional useful dependencies
echo "📦 Installing additional dependencies..."
pip install -q --no-cache-dir aiohttp pillow

# Create necessary directories
mkdir -p models/checkpoints
mkdir -p models/vae
mkdir -p models/loras
mkdir -p models/embeddings
mkdir -p models/controlnet
mkdir -p models/upscale_models
mkdir -p output
mkdir -p custom_nodes

# Download a starter model if none exists (optional - commented out for speed)
# if [ ! "$(ls -A models/checkpoints)" ]; then
#     echo "📥 Downloading starter model (SD 1.5)..."
#     cd models/checkpoints
#     wget -q https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors
#     cd /workspace/ComfyUI
# fi

echo ""
echo "=================================================="
echo "🚀 Starting ComfyUI Server on port ${COMFYUI_PORT:-8188}..."
echo "=================================================="
echo "Web UI: http://localhost:${COMFYUI_PORT:-8188}"
echo "API:    http://localhost:${COMFYUI_PORT:-8188}/docs"
echo "=================================================="
echo ""

# Start ComfyUI with GPU support
exec python3 main.py --listen 0.0.0.0 --port ${COMFYUI_PORT:-8188}
