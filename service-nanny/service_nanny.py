#!/usr/bin/env python3
"""
Service Nanny - AI Service Orchestrator
Manages lifecycle of AI services with GPU arbitration and health monitoring
"""

import os
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import requests
import docker

# Constants
SERVICES_DIR = Path(os.environ.get("SERVICES_DIR", "/home/zack/ai-workspace/services"))
SERVICE_MANIFEST = "service.yaml"

# Docker client
try:
    docker_client = docker.from_env()
except Exception as e:
    print(f"⚠️ Warning: Could not connect to Docker: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="Service Nanny",
    description="AI Service Orchestrator with GPU arbitration",
    version="1.0.0"
)

# Global state
services_registry = {}
running_services = {}
gpu_service_running = None

# Models
class ServiceInfo(BaseModel):
    name: str
    description: str
    version: str
    gpu_required: bool
    vram_gb: int
    ports: List[str]
    health_endpoint: str
    tags: List[str]
    status: str  # discovered, stopped, starting, running, error

class ServiceStatus(BaseModel):
    name: str
    status: str
    is_running: bool
    is_healthy: bool
    uptime: Optional[str] = None
    error: Optional[str] = None

class StartServiceRequest(BaseModel):
    force: bool = False  # Force stop GPU service if another is running

class ServiceListResponse(BaseModel):
    total: int
    services: List[ServiceInfo]
    gpu_service_running: Optional[str] = None

# Service Discovery
def discover_services():
    """Scan services directory for service.yaml manifests"""
    global services_registry
    services_registry = {}
    
    print(f"🔍 Discovering services in {SERVICES_DIR}")
    
    for item in SERVICES_DIR.iterdir():
        if not item.is_dir():
            continue
        
        # Skip template and service-nanny itself
        if item.name.startswith("_") or item.name == "service-nanny" or item.name.startswith("."):
            continue
        
        manifest_path = item / SERVICE_MANIFEST
        if not manifest_path.exists():
            print(f"⚠️  No service.yaml found in {item.name}")
            continue
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = yaml.safe_load(f)
            
            service_name = manifest.get("name", item.name)
            services_registry[service_name] = {
                "manifest": manifest,
                "path": item,
                "discovered_at": datetime.now().isoformat()
            }
            
            print(f"✅ Discovered: {service_name}")
            
        except Exception as e:
            print(f"❌ Error loading {item.name}/service.yaml: {e}")
    
    print(f"📊 Total services discovered: {len(services_registry)}")
    return services_registry

def get_service_info(service_name: str) -> ServiceInfo:
    """Convert registry entry to ServiceInfo model"""
    if service_name not in services_registry:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    entry = services_registry[service_name]
    manifest = entry["manifest"]
    
    # Determine status
    status = "stopped"
    if service_name in running_services:
        status = "running"
    
    return ServiceInfo(
        name=manifest.get("name", service_name),
        description=manifest.get("description", "No description"),
        version=manifest.get("version", "unknown"),
        gpu_required=manifest.get("gpu_required", False),
        vram_gb=manifest.get("vram_gb", 0),
        ports=manifest.get("ports", []),
        health_endpoint=manifest.get("health_endpoint", ""),
        tags=manifest.get("tags", []),
        status=status
    )

def check_service_health(service_name: str) -> bool:
    """Check if a service is healthy via its health endpoint"""
    if service_name not in services_registry:
        return False
    
    manifest = services_registry[service_name]["manifest"]
    health_endpoint = manifest.get("health_endpoint")
    
    if not health_endpoint:
        return False
    
    # Replace localhost with host.docker.internal for container-to-host communication
    health_endpoint = health_endpoint.replace("localhost", "host.docker.internal")
    
    try:
        response = requests.get(health_endpoint, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed for {service_name}: {e}")
        return False

def get_docker_compose_status(service_path: Path) -> bool:
    """Check if docker-compose service is running using Docker SDK"""
    try:
        # Get project name from directory name
        project_name = service_path.name
        
        # List containers for this project
        containers = docker_client.containers.list(
            filters={"label": f"com.docker.compose.project={project_name}"}
        )
        
        return len(containers) > 0
    except Exception as e:
        print(f"Error checking Docker status for {service_path.name}: {e}")
        return False

# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Discover services on startup"""
    discover_services()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Service Nanny is running!",
        "version": "1.0.0",
        "services_discovered": len(services_registry),
        "gpu_service_running": gpu_service_running
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "services_discovered": len(services_registry),
        "services_running": len(running_services)
    }

@app.get("/services", response_model=ServiceListResponse)
async def list_services():
    """List all discovered services"""
    services = [get_service_info(name) for name in services_registry.keys()]
    
    return ServiceListResponse(
        total=len(services),
        services=services,
        gpu_service_running=gpu_service_running
    )

@app.get("/services/{service_name}", response_model=ServiceInfo)
async def get_service(service_name: str):
    """Get details about a specific service"""
    return get_service_info(service_name)

@app.get("/services/{service_name}/status", response_model=ServiceStatus)
async def get_service_status(service_name: str):
    """Get detailed status of a service"""
    if service_name not in services_registry:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    service_path = services_registry[service_name]["path"]
    is_running = get_docker_compose_status(service_path)
    is_healthy = check_service_health(service_name) if is_running else False
    
    status = "stopped"
    uptime = None
    
    if is_running:
        status = "running" if is_healthy else "unhealthy"
        if service_name in running_services:
            started_at = running_services[service_name].get("started_at")
            if started_at:
                uptime = str(datetime.now() - datetime.fromisoformat(started_at))
    
    return ServiceStatus(
        name=service_name,
        status=status,
        is_running=is_running,
        is_healthy=is_healthy,
        uptime=uptime
    )

@app.post("/services/{service_name}/start")
async def start_service(service_name: str, request: StartServiceRequest = StartServiceRequest(force=True)):
    """Start a service (automatically stops conflicting GPU services by default)"""
    global gpu_service_running, running_services
    
    if service_name not in services_registry:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    entry = services_registry[service_name]
    manifest = entry["manifest"]
    service_path = entry["path"]
    
    # Check if already running
    if get_docker_compose_status(service_path):
        return {"message": f"Service '{service_name}' is already running", "status": "running"}
    
    # GPU arbitration - automatically detect and stop running GPU services
    if manifest.get("gpu_required", False):
        # Check if any GPU services are currently running (not just tracked ones)
        running_gpu_services = []
        for svc_name, svc_entry in services_registry.items():
            if svc_name != service_name and svc_entry["manifest"].get("gpu_required", False):
                if get_docker_compose_status(svc_entry["path"]):
                    running_gpu_services.append(svc_name)
        
        if running_gpu_services:
            if not request.force:
                raise HTTPException(
                    status_code=409,
                    detail=f"GPU service(s) {running_gpu_services} already running. Use force=true to stop them first."
                )
            else:
                # Stop all running GPU services
                for svc_name in running_gpu_services:
                    print(f"🛑 Auto-stopping GPU service: {svc_name}")
                    await stop_service(svc_name)
    
    # Start the service
    print(f"🚀 Starting {service_name}...")
    
    try:
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=service_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start service: {result.stderr}"
            )
        
        # Track running service
        running_services[service_name] = {
            "started_at": datetime.now().isoformat(),
            "manifest": manifest
        }
        
        if manifest.get("gpu_required", False):
            gpu_service_running = service_name
        
        print(f"✅ {service_name} started successfully")
        
        return {
            "message": f"Service '{service_name}' started successfully",
            "status": "running",
            "health_endpoint": manifest.get("health_endpoint")
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Service start timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting service: {str(e)}")

@app.post("/services/{service_name}/stop")
async def stop_service(service_name: str):
    """Stop a service"""
    global gpu_service_running, running_services
    
    if service_name not in services_registry:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    entry = services_registry[service_name]
    service_path = entry["path"]
    
    # Check if running
    if not get_docker_compose_status(service_path):
        return {"message": f"Service '{service_name}' is not running", "status": "stopped"}
    
    # Stop the service
    print(f"🛑 Stopping {service_name}...")
    
    try:
        result = subprocess.run(
            ["docker", "compose", "down"],
            cwd=service_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to stop service: {result.stderr}"
            )
        
        # Update state
        if service_name in running_services:
            del running_services[service_name]
        
        if gpu_service_running == service_name:
            gpu_service_running = None
        
        print(f"✅ {service_name} stopped successfully")
        
        return {
            "message": f"Service '{service_name}' stopped successfully",
            "status": "stopped"
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Service stop timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping service: {str(e)}")

@app.get("/services/{service_name}/logs")
async def get_service_logs(service_name: str, tail: int = 100):
    """Get logs for a service"""
    if service_name not in services_registry:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    
    entry = services_registry[service_name]
    service_path = entry["path"]
    
    try:
        result = subprocess.run(
            ["docker", "compose", "logs", "--tail", str(tail)],
            cwd=service_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "service": service_name,
            "logs": result.stdout,
            "tail": tail
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")

@app.post("/rediscover")
async def rediscover_services():
    """Manually trigger service discovery"""
    discover_services()
    return {
        "message": "Service discovery completed",
        "services_discovered": len(services_registry)
    }

if __name__ == "__main__":
    print("🔧 Service Nanny - AI Service Orchestrator")
    print(f"📂 Services directory: {SERVICES_DIR}")
    print("🚀 Starting API server...")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
