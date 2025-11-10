#!/usr/bin/env python3
"""
Template Service Application
Minimal FastAPI service template for quick service creation
"""

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="My Service",
    description="Template service for quick development",
    version="1.0.0"
)

# Example request/response models
class ExampleRequest(BaseModel):
    message: str

class ExampleResponse(BaseModel):
    result: str
    status: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "My Service is running!",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint - REQUIRED for service-nanny"""
    return {
        "status": "healthy",
        "service": "my-service",
        "version": "1.0.0"
    }

@app.post("/process", response_model=ExampleResponse)
async def process_request(request: ExampleRequest):
    """Example endpoint that processes a request"""
    # Add your logic here
    result = f"Processed: {request.message}"
    
    return ExampleResponse(
        result=result,
        status="success"
    )

if __name__ == "__main__":
    print("🚀 Starting My Service...")
    
    # Run the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )
