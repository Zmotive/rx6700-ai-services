# Qwen2.5-Coder Service Setup

Complete setup guide for the Qwen2.5-Coder-7B-Instruct LLM service running on Ollama with AMD ROCm.

## Prerequisites

- Docker and Docker Compose installed
- AMD GPU with ROCm support (tested on RX 6700 XT)
- At least 12GB VRAM
- At least 10GB free disk space for model

## Quick Setup

### 1. Start the Service

```bash
cd ~/ai-workspace/services/qwen-coder
docker compose up -d
```

### 2. Pull the Model

```bash
# Pull the Qwen2.5-Coder 7B model (~4.7GB)
docker exec -it qwen-coder ollama pull qwen2.5-coder:7b
```

This will take 5-10 minutes depending on your internet connection.

### 3. Verify Installation

```bash
# Check service health
curl http://localhost:8001/

# List available models
docker exec qwen-coder ollama list

# Test code generation
curl http://localhost:8001/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Write a Python function to calculate factorial",
  "stream": false
}'
```

## Using the Python Client

The `app.py` file provides a convenient Python wrapper:

```python
from app import QwenCoderClient

# Initialize client
client = QwenCoderClient()

# Generate code
result = client.generate(
    prompt="Write a Python function to reverse a string",
    system="You are an expert Python developer."
)
print(result["response"])

# Chat-based interaction
chat_result = client.chat(
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "How do I implement quicksort?"}
    ]
)
```

## Service Management

### Start Service
```bash
docker compose up -d
```

### Stop Service
```bash
docker compose down
```

### View Logs
```bash
docker logs qwen-coder -f
```

### Check GPU Usage
```bash
rocm-smi --showuse --showmeminfo vram
```

### Restart Service
```bash
docker compose restart
```

## Model Management

### List Models
```bash
docker exec qwen-coder ollama list
```

### Pull Different Model
```bash
# Smaller, faster variant
docker exec qwen-coder ollama pull qwen2.5-coder:1.5b

# Balanced variant
docker exec qwen-coder ollama pull qwen2.5-coder:3b
```

### Remove Model
```bash
docker exec qwen-coder ollama rm qwen2.5-coder:7b
```

## API Endpoints

- `GET /` - Health check
- `POST /api/generate` - Generate completion
- `POST /api/chat` - Chat conversation
- `POST /v1/chat/completions` - OpenAI-compatible chat
- `GET /api/tags` - List available models

## Configuration

### Environment Variables

Edit `docker-compose.yml`:

```yaml
environment:
  - HSA_OVERRIDE_GFX_VERSION=10.3.0  # ROCm compatibility
  - OLLAMA_HOST=0.0.0.0:11434        # API host/port
```

### Port Configuration

The service runs on port 8001 by default. To change:

1. Update `docker-compose.yml`:
   ```yaml
   ports:
     - "8002:11434"  # Change 8001 to your preferred port
   ```

2. Update `service.yaml`:
   ```yaml
   ports:
     - "8002:11434"
   health_endpoint: http://localhost:8002/
   ```

## Troubleshooting

### Service won't start
```bash
# Check logs
docker logs qwen-coder

# Verify GPU access
docker exec -it qwen-coder ls -la /dev/kfd /dev/dri

# Check if port is in use
sudo netstat -tulpn | grep 8001
```

### Model download fails
```bash
# Check disk space
df -h ~/ai-workspace/models/ollama

# Try manual pull with verbose output
docker exec -it qwen-coder ollama pull qwen2.5-coder:7b
```

### GPU not detected
```bash
# Verify ROCm is working
rocm-smi

# Check HSA override version
docker exec qwen-coder env | grep HSA
```

### Out of memory
```bash
# Use smaller model
docker exec qwen-coder ollama pull qwen2.5-coder:3b

# Or check VRAM usage
rocm-smi --showmeminfo vram
```

## Integration with Service Nanny

The service is automatically discovered by Service Nanny via `service.yaml`.

```bash
# Check discovery
curl http://localhost:8080/services | jq '.services[] | select(.name=="qwen-coder")'

# Start via Service Nanny
curl -X POST http://localhost:8080/services/qwen-coder/start

# Stop via Service Nanny
curl -X POST http://localhost:8080/services/qwen-coder/stop
```

## Performance Tuning

### Adjust Context Length

For longer code files, you can adjust the context window in the API request:

```bash
curl http://localhost:8001/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Your long prompt here...",
  "options": {
    "num_ctx": 8192
  }
}'
```

### Temperature Settings

- `0.0` - Deterministic, focused responses
- `0.7` - Balanced (default)
- `1.0` - Creative, varied responses

### GPU Memory

The model uses ~8-9GB VRAM. Monitor with:
```bash
watch -n 1 rocm-smi --showmeminfo vram
```

## Links

- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Qwen2.5-Coder Model Card](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)
- [ROCm Documentation](https://rocm.docs.amd.com/)
