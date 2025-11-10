#!/bin/bash
# Dia TTS Service Startup Script

echo "🎙️ Starting Dia TTS Service..."
echo "🎮 GPU: AMD RX 6700 XT with ROCm"
echo ""

# Display ROCm information
echo "📊 ROCm Information:"
echo "HSA_OVERRIDE_GFX_VERSION=$HSA_OVERRIDE_GFX_VERSION"
echo "PYTORCH_ROCM_ARCH=$PYTORCH_ROCM_ARCH"
echo ""

# Check if Dia is already installed
if ! python3 -c "import dia" 2>/dev/null; then
    echo "📦 Installing Dia and dependencies..."
    
    # Install system dependencies
    apt-get update -qq
    apt-get install -y -qq ffmpeg libsndfile1 curl > /dev/null 2>&1
    
    # Install torch-compatible packages first (numpy, etc)
    pip install --no-cache-dir -q numpy==2.2.4 scipy soundfile
    
    # Install torchaudio from ROCm wheel (closest available version to our PyTorch 2.6.0+rocm)
    # Note: torchaudio 2.6.0 not available, using 2.8.0+rocm6.4
    pip install --no-cache-dir -q --index-url https://download.pytorch.org/whl/rocm6.4 \
        torchaudio==2.8.0+rocm6.4
    
    # Install Dia from GitHub (skip torch dependency - we already have ROCm PyTorch)
    pip install --no-cache-dir -q --no-deps git+https://github.com/nari-labs/dia.git
    
    # Install dependencies WITHOUT allowing torch upgrades
    pip install --no-cache-dir -q \
        einops \
        accelerate \
        safetensors \
        tokenizers \
        "huggingface-hub<1.0,>=0.34.0" \
        filelock \
        requests \
        tqdm \
        pyyaml \
        regex \
        packaging \
        "pydantic>=2.11.3"
    
    # Install transformers with --no-deps (would otherwise upgrade torch)
    pip install --no-cache-dir -q --no-deps transformers
    
    # Install descript-audio-codec and its dependencies
    # Note: dac requires audiotools which is from descriptinc/audiotools
    pip install --no-cache-dir -q git+https://github.com/descriptinc/audiotools
    pip install --no-cache-dir -q descript-audio-codec
    
    # Install other safe dependencies
    pip install --no-cache-dir -q \
        fastapi \
        uvicorn[standard] \
        python-multipart
    
    echo "✅ Dia installed successfully!"
else
    echo "✅ Dia already installed"
fi

# Verify installation
echo ""
echo "🔍 Verifying installation..."
python3 -c "
import torch
import dia
print(f'✅ PyTorch: {torch.__version__}')
print(f'✅ ROCm available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ GPU: {torch.cuda.get_device_name(0)}')
print(f'✅ Dia version: {dia.__version__ if hasattr(dia, \"__version__\") else \"installed\"}')
"

echo ""
echo "🚀 Starting Dia API server on port 8002..."
echo "📡 Endpoints:"
echo "   - http://localhost:8002/       (Info)"
echo "   - http://localhost:8002/health (Health check)"
echo "   - http://localhost:8002/generate (POST - Generate audio)"
echo "   - http://localhost:8002/nonverbals (List sound effects)"
echo "   - http://localhost:8002/docs   (Swagger UI)"
echo ""

# Start the API server
exec python3 dia_api.py
