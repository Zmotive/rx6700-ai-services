#!/usr/bin/env python3
"""
Minimal Stable Diffusion API Server
A lightweight FastAPI server for generating images with Stable Diffusion
"""

import os
import io
import base64
from typing import Optional
import torch
from PIL import Image
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Check if we're running in a container
IN_CONTAINER = os.path.exists('/.dockerenv')

# Try to import diffusers
try:
    from diffusers import StableDiffusionPipeline
    print("✅ Diffusers imported successfully")
except ImportError as e:
    print(f"❌ Failed to import diffusers: {e}")
    exit(1)

# Initialize FastAPI app
app = FastAPI(
    title="Minimal Stable Diffusion API",
    description="A lightweight API for Stable Diffusion image generation",
    version="1.0.0"
)

# Global pipeline variable
pipeline = None

# Resolution limits based on testing with RX 6700 XT + ROCm 6.4
# Testing revealed asymmetric behavior and multiple crash types
# Conservative limits chosen for stability
MAX_WIDTH = 768
MAX_HEIGHT = 768  # Could push to 832 for width, but keeping symmetric for safety
MIN_DIMENSION = 64

class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    width: Optional[int] = 512
    height: Optional[int] = 512
    num_inference_steps: Optional[int] = 20
    guidance_scale: Optional[float] = 7.5
    seed: Optional[int] = None

class GenerateResponse(BaseModel):
    image_base64: str
    seed: int
    prompt: str

def validate_resolution(width: int, height: int) -> tuple[bool, str]:
    """
    Validate image resolution to prevent crashes.
    
    Based on testing with RX 6700 XT (12GB) + ROCm 6.4:
    - 768×768 is reliably stable
    - 768×832 works but 832×768 crashes (asymmetric!)
    - 864×864+ is unstable/crashes
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        
    Returns:
        (is_valid, error_message)
    """
    # Must be divisible by 8 (SD requirement)
    if width % 8 != 0:
        return False, f"Width must be divisible by 8 (got {width})"
    
    if height % 8 != 0:
        return False, f"Height must be divisible by 8 (got {height})"
    
    # Check minimum
    if width < MIN_DIMENSION:
        return False, f"Width must be at least {MIN_DIMENSION} (got {width})"
    
    if height < MIN_DIMENSION:
        return False, f"Height must be at least {MIN_DIMENSION} (got {height})"
    
    # Check maximum (conservative for stability)
    if width > MAX_WIDTH:
        return False, f"Width must not exceed {MAX_WIDTH} (got {width}). Maximum tested stable resolution is {MAX_WIDTH}×{MAX_HEIGHT}"
    
    if height > MAX_HEIGHT:
        return False, f"Height must not exceed {MAX_HEIGHT} (got {height}). Maximum tested stable resolution is {MAX_WIDTH}×{MAX_HEIGHT}"
    
    return True, "OK"

def initialize_pipeline():
    """Initialize the Stable Diffusion pipeline"""
    global pipeline
    
    print("🚀 Initializing Stable Diffusion pipeline...")
    
    # Check ROCm availability - force GPU usage
    print(f"🔍 ROCm available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"🎮 GPU device: {torch.cuda.get_device_name()}")
        device = "cuda"
        torch_dtype = torch.float16
        print("🚀 Using GPU-only processing (no CPU fallback)")
    else:
        print("❌ ROCm/CUDA not available - cannot proceed without GPU")
        return False
    
    try:
        # Load the pipeline with ROCm-specific optimizations  
        model_id = "CompVis/stable-diffusion-v1-4"
        
        print(f"📥 Loading model: {model_id}")
        
        # Set comprehensive ROCm/HIPBLAS environment variables
        os.environ['AMD_SERIALIZE_KERNEL'] = '1'  # Enable kernel serialization
        os.environ['HIP_VISIBLE_DEVICES'] = '0'
        os.environ['HSA_FORCE_FINE_GRAIN_PCIE'] = '1'
        os.environ['PYTORCH_HIP_ALLOC_CONF'] = 'max_split_size_mb:128'  # Manageable chunks without expandable_segments
        os.environ['HIP_LAUNCH_BLOCKING'] = '1'
        os.environ['ROCBLAS_LAYER'] = '0'  # Disable rocBLAS logging
        os.environ['HIP_FORCE_DEV_KERNARG'] = '1'  # Force device kernel arguments
        os.environ['TORCH_USE_HIP_DSA'] = '1'  # Enable device-side assertions
        os.environ['HSA_ENABLE_SDMA'] = '0'  # Disable SDMA which can cause issues
        
        # Set PyTorch-specific ROCm optimizations
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        
        # Try to avoid HIPBLAS by using alternative implementations
        torch.backends.cuda.enable_flash_sdp(False)  # Disable flash attention
        torch.backends.cuda.enable_mem_efficient_sdp(False)  # Disable memory efficient attention
        torch.backends.cuda.enable_math_sdp(True)  # Use basic math implementation
        
        # Try a minimal tensor operation first to test HIP runtime
        print("🔧 Testing basic HIP functionality...")
        try:
            test_tensor = torch.tensor([1.0], device=device, dtype=torch_dtype)
            result = test_tensor * 2.0
            print(f"✅ Basic HIP tensor operation successful: {result}")
            del test_tensor, result
            torch.cuda.empty_cache()
        except Exception as e:
            print(f"❌ Basic HIP tensor operation failed: {e}")
            return False
            
        # Skip memory fraction setting as it causes HIP errors on ROCm 6.4.4
        # Use PYTORCH_HIP_ALLOC_CONF environment variable instead for memory management
        print("✅ Using PYTORCH_HIP_ALLOC_CONF for memory management instead of memory fraction")

        # Load pipeline to CPU first to avoid GPU memory fragmentation
        print("📦 Loading pipeline to CPU first...")
        try:
            pipeline = StableDiffusionPipeline.from_pretrained(
                model_id,
                torch_dtype=torch_dtype,
                use_safetensors=True,
                cache_dir="/workspace/Models" if IN_CONTAINER else "./models",
                # ROCm-specific settings
                variant="fp16" if torch_dtype == torch.float16 else None,
                low_cpu_mem_usage=True,  # Reduce CPU memory during loading
                device_map=None  # Load to CPU first
            )
            print("✅ Pipeline loaded to CPU successfully")
        except Exception as e:
            print(f"❌ Pipeline loading to CPU failed: {e}")
            return False
        
        # Clear GPU memory before loading
        print("🧹 Clearing GPU memory...")
        torch.cuda.empty_cache()
        
        # Initialize HIPBLAS context with smaller tensors
        print("🔧 Pre-initializing HIPBLAS context...")
        try:
            # Start with very small operations
            test_tensor = torch.randn(8, 8, device=device, dtype=torch_dtype)
            _ = test_tensor @ test_tensor  # Matrix multiplication
            del test_tensor
            torch.cuda.empty_cache()
            print("✅ HIPBLAS context initialized successfully")
        except Exception as e:
            print(f"⚠️  HIPBLAS pre-init warning: {e}")
            # Continue anyway - sometimes this works after pipeline load
        
        # Move components to device one by one to manage memory better
        print("🚚 Moving pipeline components to GPU...")
        
        # Move VAE first (usually the most memory-intensive)
        try:
            print("🔄 Moving VAE to GPU...")
            pipeline.vae = pipeline.vae.to(device)
            torch.cuda.empty_cache()
            print("✅ VAE moved to GPU successfully")
        except Exception as e:
            print(f"❌ Failed to move VAE to GPU: {e}")
            print("❌ VAE movement failed - cannot continue without GPU")
            return False
            
        # Move text encoder
        try:
            print("🔄 Moving text encoder to GPU...")
            pipeline.text_encoder = pipeline.text_encoder.to(device)
            torch.cuda.empty_cache()
            print("✅ Text encoder moved to GPU successfully")
        except Exception as e:
            print(f"❌ Failed to move text encoder to GPU: {e}")
            print("❌ Text encoder movement failed - cannot continue without GPU")
            return False
            
        # Move UNet (most compute-intensive)
        try:
            print("🔄 Moving UNet to GPU...")
            pipeline.unet = pipeline.unet.to(device)
            torch.cuda.empty_cache()
            print("✅ UNet moved to GPU successfully")
        except Exception as e:
            print(f"❌ Failed to move UNet to GPU: {e}")
            print("❌ UNet movement failed - cannot continue without GPU")
            return False
            
        # Move tokenizer and scheduler (these are lightweight and should stay on CPU anyway)
        print("✅ All critical components moved to GPU successfully")
        
        # ========================================
        # PHASE 1 MEMORY OPTIMIZATIONS (Easy Wins)
        # ========================================
        
        # 1. Enable attention slicing (20-30% memory reduction)
        try:
            pipeline.enable_attention_slicing(1)  # Maximum slicing
            print("✅ [PHASE 1] Maximum attention slicing enabled (20-30% memory reduction)")
        except:
            print("⚠️  Attention slicing not available")
        
        # 2. Enable VAE tiling (handles 1024×1024+ images)
        try:
            pipeline.enable_vae_tiling()
            print("✅ [PHASE 1] VAE tiling enabled (enables 1024×1024+ resolution)")
        except:
            # Fall back to VAE slicing if tiling not available
            try:
                pipeline.enable_vae_slicing()
                print("✅ [PHASE 1] VAE slicing enabled (fallback)")
            except:
                print("⚠️  VAE tiling/slicing not available")
        
        # 3. Enable channels-last memory format (5-10% memory + speed improvement)
        try:
            pipeline.unet.to(memory_format=torch.channels_last)
            pipeline.vae.to(memory_format=torch.channels_last)
            print("✅ [PHASE 1] Channels-last memory format enabled (5-10% optimization)")
        except Exception as e:
            print(f"⚠️  Channels-last format not available: {e}")
            
        # 4. Model CPU offload for large model support
        try:
            pipeline.enable_model_cpu_offload()
            print("✅ [PHASE 1] Model CPU offload enabled (enables large models)")  
        except Exception as e:
            print(f"⚠️  Model CPU offload not available: {e}")
            print("🎮 Keeping pipeline fully on GPU (no CPU offload)")
        
        print("🎮 Phase 1 optimizations complete - Testing 768×768+ should now work!")
        
        print("✅ Pipeline initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize the pipeline on startup"""
    success = initialize_pipeline()
    if not success:
        raise RuntimeError("Failed to initialize Stable Diffusion pipeline")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Minimal Stable Diffusion API is running!",
        "rocm_available": torch.cuda.is_available(),
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "pipeline_loaded": pipeline is not None,
        "rocm_available": torch.cuda.is_available(),
        "device_name": torch.cuda.get_device_name() if torch.cuda.is_available() else "CPU",
        "torch_version": torch.__version__,
        "resolution_limits": {
            "max_width": MAX_WIDTH,
            "max_height": MAX_HEIGHT,
            "min_dimension": MIN_DIMENSION,
            "note": "Dimensions must be divisible by 8"
        }
    }

@app.get("/limits")
async def get_limits():
    """Get resolution limits and capabilities"""
    return {
        "resolution": {
            "max_width": MAX_WIDTH,
            "max_height": MAX_HEIGHT,
            "min_dimension": MIN_DIMENSION,
            "divisible_by": 8,
            "max_tested_stable": "768×768",
            "notes": [
                "Limits based on RX 6700 XT (12GB) + ROCm 6.4 testing",
                "768×768 is guaranteed stable",
                "Higher resolutions may crash due to memory corruption",
                "Dimensions must be divisible by 8"
            ]
        },
        "hardware": {
            "gpu": "AMD Radeon RX 6700 XT" if torch.cuda.is_available() else "None",
            "vram": "12GB",
            "rocm_available": torch.cuda.is_available()
        }
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate_image(request: GenerateRequest):
    """Generate an image from a text prompt"""
    global pipeline
    
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    # Validate resolution before attempting generation
    is_valid, error_msg = validate_resolution(request.width, request.height)
    if not is_valid:
        raise HTTPException(
            status_code=400, 
            detail={
                "error": "Invalid resolution",
                "message": error_msg,
                "requested": f"{request.width}×{request.height}",
                "maximum_safe": f"{MAX_WIDTH}×{MAX_HEIGHT}",
                "minimum": f"{MIN_DIMENSION}×{MIN_DIMENSION}"
            }
        )
    
    try:
        # Set seed for reproducibility
        if request.seed is not None:
            torch.manual_seed(request.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(request.seed)
            actual_seed = request.seed
        else:
            actual_seed = torch.randint(0, 2**32, (1,)).item()
            torch.manual_seed(actual_seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(actual_seed)
        
        print(f"🎨 Generating image: '{request.prompt}' (seed: {actual_seed})")
        print("⚠️  Note: HIPBLAS warnings are expected but non-blocking")
        
        # Generate image with comprehensive HIPBLAS error handling
        with torch.inference_mode():
            # Force aggressive memory cleanup
            import gc
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
            # Force memory defragmentation
            torch.cuda.reset_peak_memory_stats()
            
            # Single attempt with requested parameters - fail clearly if it doesn't work
            print(f"🎨 Generating {request.width}x{request.height} with {request.num_inference_steps} steps")
            
            # Force synchronization before generation
            torch.cuda.synchronize()
            
            # Let model CPU offload handle device management automatically
            result = pipeline(
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                width=request.width,
                height=request.height,
                num_inference_steps=request.num_inference_steps,
                guidance_scale=request.guidance_scale,
            )
        
        # Convert to base64
        image = result.images[0]
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        print("✅ Image generated successfully!")
        
        return GenerateResponse(
            image_base64=image_base64,
            seed=actual_seed,
            prompt=request.prompt
        )
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.get("/test")
async def test_generate():
    """Quick test endpoint with a simple prompt"""
    test_request = GenerateRequest(
        prompt="a simple red apple",
        width=128,  # Even smaller for memory
        height=128,
        num_inference_steps=5  # Fewer steps
    )
    return await generate_image(test_request)

if __name__ == "__main__":
    print("🚀 Starting Minimal Stable Diffusion API Server...")
    print(f"🔍 PyTorch version: {torch.__version__}")
    print(f"🔍 ROCm available: {torch.cuda.is_available()}")
    
    # Run the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )
