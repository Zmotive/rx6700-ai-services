# ComfyUI Service

Visual workflow-based Stable Diffusion interface with full API support for the AMD RX 6700 XT.

## Overview

ComfyUI provides a powerful node-based interface for creating complex image generation workflows. Unlike simple text-to-image APIs, ComfyUI allows you to:

- **Build visual workflows** with drag-and-drop nodes
- **Chain operations** (txt2img → img2img → upscale → face restore)
- **Use advanced features** like ControlNet, IPAdapter, AnimateDiff
- **Export/import workflows** as JSON for sharing
- **Run workflows via API** for automation

## Features

- ✅ Visual node-based workflow builder
- ✅ Stable Diffusion 1.5, 2.x, SDXL support
- ✅ ControlNet for guided generation
- ✅ LoRA and embedding support
- ✅ Image upscaling and enhancement
- ✅ Real-time preview
- ✅ Custom nodes ecosystem
- ✅ Full REST API
- ✅ ROCm GPU acceleration (AMD RX 6700 XT)

## Quick Start

### 1. Start the Service

**Via Service Nanny (recommended - auto-manages GPU):**
```bash
curl -X POST http://localhost:8080/services/comfyui/start
```

**Via Docker Compose (manual):**
```bash
cd ~/ai-workspace/services/comfyui
docker compose up -d
```

### 2. Access the Web UI

Open in your browser:
```
http://localhost:8188
```

The ComfyUI interface will load with an example workflow.

### 3. Download Models

ComfyUI needs Stable Diffusion models to work. Place them in:

```bash
# SD 1.5 (smaller, faster)
cd ~/ai-workspace/services/comfyui/models/checkpoints
wget https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors

# SDXL (larger, higher quality)
wget https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors
```

After downloading, click the "Refresh" button in ComfyUI to detect the models.

## Using the Web UI

### Basic Workflow:

1. **Load a checkpoint** - Click on the "Load Checkpoint" node, select your model
2. **Enter prompt** - Type your prompt in the "CLIP Text Encode (Prompt)" node
3. **Queue prompt** - Click "Queue Prompt" to generate
4. **View output** - Image appears in the "Save Image" node

### Example Prompts:

```
Positive: "a beautiful sunset over mountains, highly detailed, 8k"
Negative: "blurry, low quality, distorted"
```

## API Usage

ComfyUI has a full REST API for automation.

### Key Endpoints:

```bash
# Get system stats (health check)
GET http://localhost:8188/system_stats

# Get available nodes and models
GET http://localhost:8188/object_info

# Queue a workflow
POST http://localhost:8188/prompt
{
  "prompt": { ... workflow JSON ... }
}

# Check queue status
GET http://localhost:8188/queue

# Get workflow history
GET http://localhost:8188/history/{prompt_id}

# Download generated image
GET http://localhost:8188/view?filename={image_name}
```

### Python API Example:

```python
import requests
import json

# 1. Load a workflow from the UI (right-click → Save as JSON)
with open('workflow.json') as f:
    workflow = json.load(f)

# 2. Modify prompt (find the text node ID from workflow)
workflow["3"]["inputs"]["text"] = "a majestic dragon in the sky"

# 3. Queue the workflow
response = requests.post(
    "http://localhost:8188/prompt",
    json={"prompt": workflow}
)
prompt_id = response.json()["prompt_id"]

# 4. Wait for completion and get result
import time
while True:
    history = requests.get(f"http://localhost:8188/history/{prompt_id}").json()
    if prompt_id in history:
        outputs = history[prompt_id]["outputs"]
        # Get image filename from outputs
        image_info = outputs["9"]["images"][0]  # Node 9 is Save Image
        filename = image_info["filename"]
        
        # Download image
        img_data = requests.get(
            f"http://localhost:8188/view",
            params={"filename": filename}
        )
        with open(f"output_{filename}", "wb") as f:
            f.write(img_data.content)
        break
    time.sleep(1)
```

## Directory Structure

```
comfyui/
├── service.yaml          # Service Nanny manifest
├── docker-compose.yml    # Docker configuration
├── start.sh             # Startup script
├── README.md            # This file
├── comfyui/             # ComfyUI installation (auto-created)
├── models/              # Model files (persistent)
│   ├── checkpoints/     # SD models (.safetensors)
│   ├── vae/            # VAE models
│   ├── loras/          # LoRA weights
│   ├── embeddings/     # Textual inversions
│   ├── controlnet/     # ControlNet models
│   └── upscale_models/ # Upscaling models
├── output/              # Generated images (persistent)
└── custom_nodes/        # Extensions (persistent)
```

## Installing Custom Nodes

ComfyUI has a rich ecosystem of custom nodes. Install them via:

### ComfyUI Manager (recommended):
```bash
cd ~/ai-workspace/services/comfyui/custom_nodes
git clone https://github.com/ltdrdata/ComfyUI-Manager.git
# Restart ComfyUI
docker compose restart
```

The Manager provides a GUI to browse and install custom nodes.

### Manual Installation:
```bash
cd ~/ai-workspace/services/comfyui/custom_nodes
git clone <custom-node-repo-url>
docker compose restart
```

## Popular Custom Nodes

- **ComfyUI-Manager** - Package manager for custom nodes
- **ControlNet-Preprocessors** - Advanced ControlNet support
- **ComfyUI-AnimateDiff** - Video generation
- **ComfyUI-IPAdapter-Plus** - Image prompting
- **Efficiency Nodes** - Workflow optimization

## Troubleshooting

### ComfyUI won't start:
```bash
# Check logs
docker logs comfyui

# Restart service
docker compose restart
```

### Out of memory errors:
- Use smaller models (SD 1.5 instead of SDXL)
- Reduce batch size in workflow
- Lower resolution (512x512 instead of 1024x1024)

### Models not showing:
- Ensure models are in correct directory
- Click "Refresh" button in UI
- Check model format (.safetensors or .ckpt)

### Slow generation:
- Verify GPU is being used (check logs for "AMD Radeon RX 6700 XT")
- Close other GPU services via Service Nanny
- Reduce steps (20-30 is usually sufficient)

## VRAM Usage

- **SD 1.5 @ 512x512**: ~4GB
- **SD 1.5 @ 768x768**: ~6GB
- **SDXL @ 1024x1024**: ~8-10GB
- **With ControlNet**: +2-3GB
- **With upscaling**: +1-2GB

The RX 6700 XT (12GB) can handle:
- ✅ SD 1.5 workflows with ControlNet and upscaling
- ✅ SDXL at 1024x1024 (tight but works)
- ⚠️ Complex SDXL workflows may need optimization

## Service Management

### Start:
```bash
curl -X POST http://localhost:8080/services/comfyui/start
```

### Stop:
```bash
curl -X POST http://localhost:8080/services/comfyui/stop
```

### Status:
```bash
curl http://localhost:8080/services/comfyui
```

### Logs:
```bash
docker logs comfyui -f
```

## Resources

- **Official Repo**: https://github.com/comfyanonymous/ComfyUI
- **Examples**: https://comfyanonymous.github.io/ComfyUI_examples/
- **Custom Nodes**: https://github.com/WASasquatch/comfyui-plugins
- **Workflows**: https://openart.ai/workflows

## Integration with Other Services

ComfyUI can be used alongside other services via Service Nanny's GPU arbitration:

- **ComfyUI + Dia**: Generate images, then add voiceover (12.4GB total - tight)
- **ComfyUI only**: Full 12GB for complex SDXL workflows
- **ComfyUI → qwen-coder**: Generate image, then describe it with LLM

Service Nanny will automatically stop conflicting GPU services when starting ComfyUI.

## Next Steps

1. Download a Stable Diffusion model
2. Open http://localhost:8188
3. Try the default workflow
4. Explore custom nodes via ComfyUI Manager
5. Export workflows as JSON for API automation
6. Build your own image generation pipelines!
