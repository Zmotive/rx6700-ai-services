#!/usr/bin/env python3
"""
Dia TTS API Server
Text-to-dialogue generation with voice control and non-verbal sounds
"""

import os
import io
import base64
import logging
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Dia TTS API",
    description="Text-to-dialogue generation with voice control and non-verbal sounds",
    version="1.6B-0626"
)

# Global model variable
model = None

# Request/Response Models
class GenerateRequest(BaseModel):
    text: str = Field(
        ...,
        description="Text with speaker tags [S1] and [S2]. Include non-verbals like (laughs), (coughs), etc.",
        example="[S1] Hello! How are you? [S2] I'm doing great! (laughs) [S1] That's wonderful to hear!"
    )
    cfg_scale: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="Classifier-free guidance scale (higher = more adherence to text)"
    )
    temperature: float = Field(
        default=1.8,
        ge=0.1,
        le=2.5,
        description="Sampling temperature (higher = more variety)"
    )
    top_p: float = Field(
        default=0.90,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling threshold"
    )
    top_k: int = Field(
        default=45,
        ge=1,
        le=100,
        description="Top-k filtering for sampling"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )
    output_format: str = Field(
        default="mp3",
        pattern="^(mp3|wav|base64)$",
        description="Output format: mp3, wav, or base64 (base64 returns WAV in base64)"
    )

class GenerateResponse(BaseModel):
    audio_base64: Optional[str] = None
    message: str
    duration_seconds: Optional[float] = None
    sample_rate: int = 24000

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    rocm_available: bool
    model_name: str = "nari-labs/Dia-1.6B-0626"
    vram_usage: str = "~4.4GB (FP16)"

def initialize_model():
    """Initialize Dia model"""
    global model
    
    logger.info("Initializing Dia model...")
    
    # Check ROCm availability
    if not torch.cuda.is_available():
        logger.error("ROCm/CUDA not available - cannot run Dia")
        raise RuntimeError("ROCm/CUDA not available")
    
    logger.info(f"Using device: {torch.cuda.get_device_name(0)}")
    
    try:
        # Import Dia
        from dia.model import Dia
        
        # Load model with FP16 for efficiency
        logger.info("Loading Dia-1.6B-0626 model...")
        model = Dia.from_pretrained(
            "nari-labs/Dia-1.6B-0626",
            compute_dtype="float16"  # Use FP16 for ~4.4GB VRAM
        )
        logger.info("Model loaded successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize model: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    try:
        initialize_model()
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise RuntimeError(f"Failed to initialize Dia model: {e}")

@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "service": "Dia TTS API",
        "version": "1.6B-0626",
        "model": "nari-labs/Dia-1.6B-0626",
        "endpoints": {
            "/health": "Health check",
            "/generate": "Generate dialogue audio (POST)",
            "/docs": "API documentation"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        device=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        rocm_available=torch.cuda.is_available()
    )

@app.post("/generate")
async def generate_audio(request: GenerateRequest):
    """Generate dialogue audio from text"""
    global model
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")
    
    # Validate text format
    if "[S1]" not in request.text and "[S2]" not in request.text:
        raise HTTPException(
            status_code=400,
            detail="Text must include speaker tags [S1] and/or [S2]"
        )
    
    try:
        logger.info(f"Generating audio for: {request.text[:100]}...")
        
        # Set seed if provided
        if request.seed is not None:
            torch.manual_seed(request.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(request.seed)
        
        # Generate audio
        output = model.generate(
            request.text,
            use_torch_compile=False,  # Disable for compatibility
            verbose=False,
            cfg_scale=request.cfg_scale,
            temperature=request.temperature,
            top_p=request.top_p,
            cfg_filter_top_k=request.top_k,
        )
        
        # Calculate duration
        sample_rate = 24000  # Dia's sample rate
        # Handle different output types
        if isinstance(output, (list, tuple)):
            audio_tensor = output[0] if len(output) > 0 else output
        else:
            audio_tensor = output
        
        # Ensure tensor is on CPU and get length
        if hasattr(audio_tensor, 'cpu'):
            audio_tensor = audio_tensor.cpu()
        if hasattr(audio_tensor, 'squeeze'):
            audio_tensor = audio_tensor.squeeze()
        
        duration = len(audio_tensor) / sample_rate if hasattr(audio_tensor, '__len__') else 0
        
        logger.info(f"Generated {duration:.2f}s of audio")
        
        # Return based on format
        if request.output_format == "base64":
            # Save to WAV in memory
            import soundfile as sf
            import numpy as np
            buffer = io.BytesIO()
            audio_np = audio_tensor.numpy() if hasattr(audio_tensor, 'numpy') else np.array(audio_tensor)
            sf.write(buffer, audio_np, sample_rate, format='WAV')
            audio_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return GenerateResponse(
                audio_base64=audio_base64,
                message="Audio generated successfully",
                duration_seconds=duration,
                sample_rate=sample_rate
            )
        else:
            # Save to file and return binary
            import tempfile
            import numpy as np
            audio_np = audio_tensor.numpy() if hasattr(audio_tensor, 'numpy') else np.array(audio_tensor)
            
            with tempfile.NamedTemporaryFile(suffix=f".{request.output_format}", delete=False) as tmp:
                # Use model's save function if available, otherwise use soundfile
                try:
                    model.save_audio(tmp.name, output)
                except:
                    import soundfile as sf
                    sf.write(tmp.name, audio_np, sample_rate)
                tmp_path = tmp.name
            
            # Read and return binary
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            os.unlink(tmp_path)
            
            media_type = "audio/mpeg" if request.output_format == "mp3" else "audio/wav"
            return Response(content=audio_data, media_type=media_type)
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/nonverbals")
async def list_nonverbals():
    """List supported non-verbal tags"""
    return {
        "nonverbals": [
            "(laughs)", "(clears throat)", "(sighs)", "(gasps)", "(coughs)",
            "(singing)", "(sings)", "(mumbles)", "(beep)", "(groans)",
            "(sniffs)", "(claps)", "(screams)", "(inhales)", "(exhales)",
            "(applause)", "(burps)", "(humming)", "(sneezes)", "(chuckle)",
            "(whistles)"
        ],
        "usage": "Insert these tags in your text where you want the sound effect",
        "example": "[S1] That's hilarious! (laughs) [S2] I know, right? (chuckle)"
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Dia TTS API Server...")
    logger.info(f"ROCm available: {torch.cuda.is_available()}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
