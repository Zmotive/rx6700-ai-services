# My Service

Brief description of what this service does.

## Quick Start

```bash
# Start the service
docker compose up -d

# Check logs
docker compose logs -f

# Test the service
curl http://localhost:8001/health

# Stop the service
docker compose down
```

## API Endpoints

### GET /
Root endpoint with basic info.

### GET /health
Health check endpoint (required for service-nanny).

**Response:**
```json
{
  "status": "healthy",
  "service": "my-service",
  "version": "1.0.0"
}
```

### POST /process
Example endpoint that processes requests.

**Request:**
```json
{
  "message": "your message here"
}
```

**Response:**
```json
{
  "result": "Processed: your message here",
  "status": "success"
}
```

## Configuration

Edit `service.yaml` to configure:
- Service name and description
- GPU requirements
- Port mappings
- Health check settings
- Tags and metadata

## Development

1. Modify `app.py` with your service logic
2. Update `docker-compose.yml` if you need different dependencies
3. Test locally: `docker compose up`
4. Update this README with your API documentation

## Integration with Service Nanny

This service is managed by `service-nanny`. Once registered:

```bash
# Start via service-nanny API
curl -X POST http://localhost:8080/services/my-service/start

# Check status
curl http://localhost:8080/services/my-service/status

# Stop service
curl -X POST http://localhost:8080/services/my-service/stop
```

## Requirements

- Docker 24.0+
- Docker Compose 2.0+
- (For GPU services): AMD ROCm 6.4+ on host
