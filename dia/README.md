# Dia Text-to-Dialogue Service

High-quality text-to-dialogue generation with voice control and non-verbal sound effects powered by Nari Labs' Dia 1.6B model.

## Features

- 🎭 **Multi-speaker Dialogue** - Generate conversations with `[S1]` and `[S2]` speaker tags
- 🎵 **Non-verbal Sounds** - 21 built-in sound effects: laughs, coughs, sighs, applause, etc.
- 🎤 **Voice Cloning** - Condition generation on audio samples for voice consistency
- 🎨 **Emotion Control** - Control tone and emotion through audio prompting
- ⚡ **Fast Inference** - ~2x realtime generation on AMD RX 6700 XT
- 🔓 **Open Source** - Apache 2.0 license, fully open weights

## Model Information

- **Model:** nari-labs/Dia-1.6B-0626
- **Parameters:** 1.6 billion
- **Sample Rate:** 24kHz
- **VRAM Usage:** ~4.4GB (FP16/BF16)
- **License:** Apache 2.0

## Hardware Requirements

- **GPU:** AMD RX 6700 XT or similar (6GB+ VRAM)
- **ROCm:** 6.2+ recommended
- **Disk Space:** ~3GB for model

## Quick Start

### Start the Service

```bash
cd ~/ai-workspace/services/dia
docker compose up -d
```

### Check Status

```bash
# View logs
docker logs dia -f

# Health check
curl http://localhost:8002/health
```

### Generate Your First Dialogue

```bash
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[S1] Hello! Welcome to Dia. [S2] Thanks! This is amazing! (laughs)",
    "output_format": "mp3"
  }' \
  --output dialogue.mp3
```

## API Endpoints

### POST /generate

Generate dialogue audio from text.

**Request Body:**
```json
{
  "text": "[S1] Your text here [S2] Response here",
  "cfg_scale": 3.0,
  "temperature": 1.8,
  "top_p": 0.90,
  "top_k": 45,
  "seed": null,
  "output_format": "mp3"
}
```

**Parameters:**
- `text` (required): Text with speaker tags `[S1]` and `[S2]`
- `cfg_scale` (default: 3.0): Guidance scale, range 1.0-10.0
  - Higher = more adherence to text
  - Lower = more natural variation
- `temperature` (default: 1.8): Sampling temperature, range 0.1-2.5
  - Higher = more variety
  - Lower = more consistent
- `top_p` (default: 0.90): Nucleus sampling, range 0.0-1.0
- `top_k` (default: 45): Top-k filtering, range 1-100
- `seed` (optional): Random seed for reproducibility
- `output_format`: "mp3", "wav", or "base64"

**Response:**
- Binary audio (MP3/WAV) or JSON with base64-encoded audio

### GET /nonverbals

List all supported non-verbal sound effects.

**Response:**
```json
{
  "nonverbals": [
    "(laughs)", "(clears throat)", "(sighs)", "(gasps)", 
    "(coughs)", "(singing)", "(mumbles)", "(claps)", ...
  ],
  "usage": "Insert these tags in your text where you want the sound effect",
  "example": "[S1] That's hilarious! (laughs) [S2] I know, right? (chuckle)"
}
```

### GET /health

Check service health status.

## Usage Examples

### Basic Dialogue

```bash
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[S1] Good morning! [S2] Good morning! How are you? [S1] Doing great, thanks!",
    "output_format": "mp3"
  }' \
  --output morning.mp3
```

### With Sound Effects

```bash
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[S1] (clears throat) Attention everyone! [S2] (gasps) What happened? [S1] (sighs) False alarm.",
    "output_format": "mp3"
  }' \
  --output sound_effects.mp3
```

### Controlled Generation (Reproducible)

```bash
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[S1] Let me tell you a story. [S2] I would love to hear it!",
    "seed": 42,
    "temperature": 1.5,
    "cfg_scale": 4.0,
    "output_format": "mp3"
  }' \
  --output story.mp3
```

### Get Base64 Audio (for embedding)

```bash
curl -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "[S1] Testing base64 output. [S2] This is useful for web apps!",
    "output_format": "base64"
  }'
```

## Python Client

Use the included Python client for easier integration:

```python
from app import DiaClient

# Initialize client
client = DiaClient()

# Check health
health = client.health_check()
print(f"Status: {health['status']}")

# Generate dialogue
client.generate(
    text="[S1] Hello! [S2] Hi there! (laughs)",
    save_path="output.mp3"
)

# List available sound effects
nonverbals = client.list_nonverbals()
print(f"Available sounds: {nonverbals['nonverbals']}")
```

## Non-Verbal Sound Effects

Dia supports 21 non-verbal tags:

| Sound Effect | Tag | Example Usage |
|--------------|-----|---------------|
| Laughing | `(laughs)` | `[S1] That's funny! (laughs)` |
| Chuckling | `(chuckle)` | `[S2] Hehe (chuckle)` |
| Clearing throat | `(clears throat)` | `[S1] (clears throat) Attention!` |
| Sighing | `(sighs)` | `[S2] (sighs) I'm tired.` |
| Gasping | `(gasps)` | `[S1] (gasps) No way!` |
| Coughing | `(coughs)` | `[S2] (coughs) Excuse me.` |
| Singing | `(singing)` | `[S1] (singing) La la la` |
| Mumbling | `(mumbles)` | `[S2] (mumbles) Not sure...` |
| Clapping | `(claps)` | `[S1] Great job! (claps)` |
| Screaming | `(screams)` | `[S2] Help! (screams)` |
| Applause | `(applause)` | `[S1] (applause) Well done!` |
| Whistling | `(whistles)` | `[S2] (whistles) Nice!` |

**Plus:** `(beep)`, `(groans)`, `(sniffs)`, `(inhales)`, `(exhales)`, `(burps)`, `(humming)`, `(sneezes)`

## Best Practices

### Text Length
- ⚠️ **Too short** (< 5 seconds): May sound unnatural
- ✅ **Ideal** (5-20 seconds): Best quality
- ⚠️ **Too long** (> 20 seconds): May sound rushed

### Speaker Tags
- ✅ Always start with `[S1]`
- ✅ Alternate between `[S1]` and `[S2]`
- ❌ Don't repeat same speaker tag twice: `[S1]... [S1]...`

### Non-verbals
- ✅ Use sparingly for best results
- ✅ Place naturally in conversation flow
- ❌ Don't overuse or combine too many at once

### Voice Consistency
- Use `seed` parameter for reproducible voices
- For voice cloning, provide 5-10 second audio samples
- Keep speaker tags consistent throughout generation

## Configuration

Edit `docker-compose.yml` to customize:

```yaml
environment:
  - HSA_OVERRIDE_GFX_VERSION=10.3.0  # ROCm compatibility for RX 6700 XT
  - PYTORCH_ROCM_ARCH=gfx1031        # GPU architecture
```

## Performance

Tested on AMD RX 6700 XT (12GB VRAM):
- **VRAM Usage:** ~4.4GB (FP16)
- **Speed:** ~2x realtime (estimated based on RTX 4090 benchmarks)
- **Latency:** Model loads in ~30-60 seconds on first run

## Troubleshooting

### Model Not Loading
```bash
# Check ROCm availability
docker exec dia python3 -c "import torch; print(torch.cuda.is_available())"

# View detailed logs
docker logs dia -f
```

### Out of Memory
- Reduce concurrent requests
- Check VRAM usage: `rocm-smi --showmeminfo vram`
- Ensure no other GPU services running

### Audio Quality Issues
- Try adjusting `cfg_scale` (3.0-5.0 recommended)
- Modify `temperature` (1.5-2.0 for more natural speech)
- Ensure text length is 5-20 seconds worth
- Check speaker tag formatting

## Service Management

### Start
```bash
docker compose up -d
```

### Stop
```bash
docker compose down
```

### Restart
```bash
docker compose restart
```

### Update Model
```bash
# Remove cached model
rm -rf ~/.cache/huggingface/hub/models--nari-labs--Dia-1.6B-0626

# Restart service to re-download
docker compose restart
```

## Advanced Usage

### Custom Temperature/Sampling
```python
# More creative, varied output
client.generate(
    text="[S1] Once upon a time... [S2] Oh, a story!",
    temperature=2.2,
    top_p=0.95,
    cfg_scale=2.5
)

# More consistent, predictable output
client.generate(
    text="[S1] The meeting is at 3pm. [S2] Got it, thanks.",
    temperature=1.3,
    top_p=0.85,
    cfg_scale=4.5
)
```

### Batch Generation
```python
dialogues = [
    "[S1] Hello! [S2] Hi there!",
    "[S1] How are you? [S2] Great, thanks!",
    "[S1] See you later! [S2] Goodbye!"
]

for i, text in enumerate(dialogues):
    client.generate(
        text=text,
        save_path=f"dialogue_{i}.mp3",
        seed=42 + i  # Different seed for variety
    )
```

## Files

- `docker-compose.yml` - Service definition
- `dia_api.py` - FastAPI server implementation
- `start.sh` - Container startup script
- `app.py` - Python client wrapper
- `requirements.txt` - Client dependencies
- `service.yaml` - Service metadata

## Links

- **Model:** https://huggingface.co/nari-labs/Dia-1.6B-0626
- **GitHub:** https://github.com/nari-labs/dia
- **Demo Space:** https://huggingface.co/spaces/nari-labs/Dia-1.6B
- **License:** https://github.com/nari-labs/dia/blob/main/LICENSE

## Credits

- **Dia Model:** Nari Labs (https://github.com/nari-labs)
- **License:** Apache 2.0
- **Inspired by:** SoundStorm, Parakeet, Descript Audio Codec
