# Qwen2.5-Coder-7B-Instruct Service

A code-specialized large language model running on Ollama with AMD ROCm support for the RX 6700 XT GPU.

## Model Information

- **Model**: Qwen2.5-Coder-7B-Instruct
- **Parameters**: 7.61 billion
- **Context Window**: 128K tokens
- **Specialization**: Code generation, debugging, and analysis
- **Backend**: Ollama with ROCm
- **VRAM Usage**: ~8-9GB

## Quick Start

### 1. Start the Service

```bash
docker compose up -d
```

### 2. Pull the Model (First Time)

```bash
# Pull the Qwen2.5-Coder model
docker exec -it qwen-coder ollama pull qwen2.5-coder:7b
```

### 3. Verify Service

```bash
curl http://localhost:8001/
```

## API Usage

Ollama provides an OpenAI-compatible API endpoint.

### Generate Completion

```bash
curl http://localhost:8001/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Write a Python function to calculate fibonacci numbers",
  "stream": false
}'
```

### Chat Completions (OpenAI-Compatible)

```bash
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder:7b",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful coding assistant."
      },
      {
        "role": "user",
        "content": "Write a Python function to reverse a string"
      }
    ]
  }'
```

### Python Client Example

```python
import requests
import json

def generate_code(prompt: str) -> str:
    response = requests.post(
        "http://localhost:8001/api/generate",
        json={
            "model": "qwen2.5-coder:7b",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

# Example usage
code = generate_code("Write a Python function to check if a number is prime")
print(code)
```

### Streaming Example

```python
import requests
import json

def stream_code(prompt: str):
    response = requests.post(
        "http://localhost:8001/api/generate",
        json={
            "model": "qwen2.5-coder:7b",
            "prompt": prompt,
            "stream": True
        },
        stream=True
    )
    
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            print(data["response"], end="", flush=True)
            if data.get("done"):
                break

# Example usage
stream_code("Explain how binary search works with Python code")
```

## Model Management

### List Available Models

```bash
docker exec -it qwen-coder ollama list
```

### Remove Model

```bash
docker exec -it qwen-coder ollama rm qwen2.5-coder:7b
```

### Pull Different Model

```bash
# Other Qwen2.5-Coder variants
docker exec -it qwen-coder ollama pull qwen2.5-coder:1.5b   # Smaller, faster
docker exec -it qwen-coder ollama pull qwen2.5-coder:3b     # Balanced
```

## Performance

- **First Start**: ~30 seconds (no model download needed after first pull)
- **Model Loading**: ~5-10 seconds
- **Inference Speed**: 20-40 tokens/second on RX 6700 XT
- **VRAM Usage**: ~8-9GB for 7B model

## Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - HSA_OVERRIDE_GFX_VERSION=10.3.0  # ROCm compatibility for RX 6700 XT
  - OLLAMA_HOST=0.0.0.0:11434        # API host and port
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs qwen-coder

# Verify GPU access
docker exec -it qwen-coder rocm-smi
```

### Model download fails

```bash
# Try pulling manually
docker exec -it qwen-coder ollama pull qwen2.5-coder:7b

# Check disk space
df -h ~/ai-workspace/models/ollama
```

### Out of memory

```bash
# Use smaller model variant
docker exec -it qwen-coder ollama pull qwen2.5-coder:3b
```

### Slow inference

- Verify GPU is being used: `docker exec -it qwen-coder rocm-smi`
- Check VRAM usage with `watch -n 1 rocm-smi`
- Consider using a smaller context length

## Advanced Usage

### Custom System Prompts

```bash
curl http://localhost:8001/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Write a FastAPI endpoint",
  "system": "You are an expert in Python web development. Provide production-ready code with error handling.",
  "stream": false
}'
```

### Temperature and Sampling

```bash
curl http://localhost:8001/api/generate -d '{
  "model": "qwen2.5-coder:7b",
  "prompt": "Create a creative sorting algorithm",
  "options": {
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 40
  },
  "stream": false
}'
```

## API Endpoints

- `GET /` - Health check
- `POST /api/generate` - Generate completion
- `POST /api/chat` - Chat conversation
- `POST /v1/chat/completions` - OpenAI-compatible chat
- `GET /api/tags` - List available models
- `POST /api/pull` - Pull a model
- `DELETE /api/delete` - Delete a model

## Links

- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Qwen2.5-Coder Model Card](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)
- [OpenAI API Compatibility](https://github.com/ollama/ollama/blob/main/docs/openai.md)
