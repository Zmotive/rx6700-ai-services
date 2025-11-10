# Service Nanny - Visual Quick Reference

## 🎯 What is Service Nanny?

```
         ┌─────────────────────────────────────┐
         │   "I need to start a GPU service"   │
         └──────────────┬──────────────────────┘
                        │
                        ↓
         ┌─────────────────────────────────────┐
         │      Service Nanny (Port 8080)      │
         │                                      │
         │  ✓ Auto-discovers services          │
         │  ✓ Enforces GPU one-of rule         │
         │  ✓ Monitors health                  │
         │  ✓ Manages lifecycle                │
         └──────────────┬──────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ↓              ↓              ↓
    ┌────────┐    ┌────────┐    ┌────────┐
    │ Stable │    │Service │    │Service │
    │   SD   │    │   2    │    │   3    │
    │  API   │    │        │    │        │
    └────────┘    └────────┘    └────────┘
```

## 🚀 Quick Start (3 Commands)

```bash
# 1. Start Service Nanny
cd service-nanny && ./start.sh

# 2. Start a service
curl -X POST http://localhost:8080/services/minimal-sd-api/start

# 3. Check it's running
curl http://localhost:8000/health
```

## 📋 Adding a New Service (5 Steps)

```bash
# Step 1: Copy template
cp -r _template my-awesome-service

# Step 2: Edit service.yaml
cd my-awesome-service
vim service.yaml
# Change: name, description, ports, gpu_required

# Step 3: Edit docker-compose.yml  
vim docker-compose.yml
# Match ports to service.yaml

# Step 4: Test it works
docker compose up -d
curl http://localhost:8001/health  # Your port
docker compose down

# Step 5: Register with Service Nanny
curl -X POST http://localhost:8080/rediscover
curl http://localhost:8080/services | jq
```

## 🎮 GPU Arbitration Flow

```
┌─────────────────────────────────────────────────┐
│ Scenario: Two GPU services                     │
└─────────────────────────────────────────────────┘

  Start Service A (GPU)
         ↓
  ✅ Success - GPU free
         ↓
  Service A running
         ↓
  Start Service B (GPU)
         ↓
  ❌ 409 Conflict!
  "Service A is using GPU"
         ↓
  Start Service B (force=true)
         ↓
  🛑 Stops Service A
         ↓
  🚀 Starts Service B
         ↓
  ✅ Success
```

## 📊 API Cheat Sheet

| Want to... | Command |
|------------|---------|
| List all services | `curl http://localhost:8080/services \| jq` |
| Start a service | `curl -X POST http://localhost:8080/services/NAME/start` |
| Force start GPU service | `curl -X POST http://localhost:8080/services/NAME/start -d '{"force":true}'` |
| Stop a service | `curl -X POST http://localhost:8080/services/NAME/stop` |
| Check if healthy | `curl http://localhost:8080/services/NAME/status \| jq .is_healthy` |
| Get logs | `curl http://localhost:8080/services/NAME/logs?tail=50` |
| Rediscover services | `curl -X POST http://localhost:8080/rediscover` |

## 🗂️ File Structure at a Glance

```
services/
│
├── 🔧 service-nanny/          ← The orchestrator
│   ├── service_nanny.py       ← Main app (350 lines)
│   ├── docker-compose.yml     ← Runs on port 8080
│   ├── start.sh               ← Quick start
│   ├── test_api.sh            ← Test the API
│   ├── README.md              ← Full API docs
│   ├── ARCHITECTURE.md        ← Design details
│   └── IMPLEMENTATION.md      ← This implementation
│
├── 📋 _template/              ← Copy-paste this!
│   ├── service.yaml           ← Manifest for Service Nanny
│   ├── docker-compose.yml     ← Container config
│   ├── app.py                 ← FastAPI starter
│   ├── SETUP.md               ← Step-by-step guide
│   └── README.md              ← Template docs
│
└── 🎨 minimal-sd-api/         ← Example service
    ├── service.yaml           ← ✨ NEW - Nanny compatible
    └── ...                    ← Existing files
```

## 🔄 Typical Workflow

```
┌──────────────────────────────────────────────┐
│ Developer wants to add image upscaling API   │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ 1. Copy template → upscale-api/              │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ 2. Edit service.yaml:                        │
│    name: upscale-api                         │
│    gpu_required: true                        │
│    ports: ["8001:8000"]                      │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ 3. Implement app.py logic                    │
│    - Load upscaling model                    │
│    - POST /upscale endpoint                  │
│    - Keep GET /health                        │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ 4. Test locally                              │
│    docker compose up -d                      │
│    curl http://localhost:8001/health         │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ 5. Register with Service Nanny               │
│    curl -X POST .../rediscover               │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ ✅ Done! Now manageable via Service Nanny    │
│                                               │
│ Start: POST /services/upscale-api/start      │
│ (Auto stops minimal-sd-api if running)       │
└──────────────────────────────────────────────┘
```

## 🎯 Port Allocation Guide

```
Port Range    Purpose              Currently Used
─────────────────────────────────────────────────
8000          GPU Service #1       minimal-sd-api
8001-8009     More GPU services    (available)
8010-8079     CPU services         (available)
8080          Service Nanny        RESERVED
8081-8099     (reserved)           (future use)
9000+         MCP servers          (future)
```

## 🔐 Security Levels

```
Current (Development):
┌────────────────────────────────┐
│ No auth - Trusted users only   │
│ Docker socket access           │
│ localhost only                 │
└────────────────────────────────┘

Future (Production):
┌────────────────────────────────┐
│ API key authentication         │
│ Role-based access control      │
│ Rate limiting                  │
│ HTTPS only                     │
│ Behind reverse proxy           │
└────────────────────────────────┘
```

## 🎓 Learning Path

```
Beginner:
├─ Read: main README.md
├─ Start: ./start.sh
└─ Try: curl commands from cheat sheet

Intermediate:
├─ Copy template
├─ Create simple CPU service
├─ Test with Service Nanny
└─ Read: ARCHITECTURE.md

Advanced:
├─ Create GPU service
├─ Understand GPU arbitration
├─ Read: service_nanny.py source
└─ Plan: MCP integration

Expert:
├─ Contribute to Service Nanny
├─ Add new features (auth, metrics)
├─ Implement MCP protocol
└─ Deploy to production
```

## 🐛 Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| Service Nanny won't start | `docker compose logs` |
| Service not discovered | Check `service.yaml` exists |
| Can't start GPU service | Another GPU service running? |
| Health check fails | Check service's `/health` endpoint |
| Port conflict | Update `service.yaml` and `docker-compose.yml` |
| Docker permission denied | Add user to `docker` group |

## 🎉 Success Indicators

✅ You know it's working when:
- `curl http://localhost:8080/health` returns 200
- `curl http://localhost:8080/services` lists your services
- Starting a GPU service auto-stops another GPU service
- `/services/NAME/status` shows `is_healthy: true`
- New services appear after `POST /rediscover`

## 🚦 Next Steps

1. ✅ **You are here** - Service Nanny is built and documented
2. ⏭️ **Test it** - Run `./start.sh` and try the API
3. ⏭️ **Add a service** - Use the template to create something new
4. ⏭️ **MCP integration** - Make Service Nanny an MCP server
5. ⏭️ **Scale up** - Add authentication, metrics, HA

---

**🎯 Remember**: The whole point is to make it *easy* to:
- Add new AI services (copy template)
- Start/stop them (one API call)
- Never worry about GPU conflicts (handled automatically)
- Eventually control everything via AI (MCP layer)
