# Docker Setup Guide

This app can be run in Docker with Docker Compose, which includes both the Telegram betting bot and an Ollama LLM service.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Telegram Bot Token (from @BotFather)

### Setup

1. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your TELEGRAM_BOT_TOKEN
   ```

2. **Start services:**
   ```bash
   docker-compose up -d
   ```

   This will:
   - Pull Ollama image
   - Build bot image
   - Start Ollama service (http://localhost:11434)
   - Start bot service (connected to Ollama)
   - Create persistent data volume for databases

3. **Check status:**
   ```bash
   docker-compose logs -f bot
   docker-compose logs ollama
   ```

4. **Stop services:**
   ```bash
   docker-compose down
   ```

## Configuration

### Environment Variables

Set in `.env` before running `docker-compose up`:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OLLAMA_MODEL=gemma:7b          # or llama2:7b, mistral:7b
LOG_LEVEL=INFO                  # DEBUG for verbose output
```

### Ollama Model Selection

The first time Ollama runs, it will download the model. This may take a few minutes.

**Recommended models:**
- `gemma:7b` (default, fast, good reasoning) - ~4GB
- `llama2:7b` (powerful, slower) - ~4GB
- `mistral:7b` (fast, good reasoning) - ~5GB

To use a different model:
```bash
OLLAMA_MODEL=llama2:7b docker-compose up
```

### Persist Data

Database files are stored in `./data/` directory on host machine, so they survive container restarts.

## Troubleshooting

### Ollama not starting
```bash
docker-compose logs ollama
# Check if port 11434 is in use
lsof -i :11434
```

### Bot can't connect to Ollama
```bash
# Verify Ollama is healthy
docker-compose exec ollama curl http://localhost:11434/api/tags
```

### Out of memory
Ollama models can use 4-8GB RAM. Ensure Docker has enough memory allocated:
- **Docker Desktop**: Settings → Resources → Memory

### Bot logs
```bash
# Real-time logs
docker-compose logs -f bot

# Last 50 lines
docker-compose logs bot --tail=50
```

## Manual Docker Commands

If you prefer running without Compose:

### Build image
```bash
docker build -t betting-bot:latest .
```

### Run bot (requires Ollama on host at localhost:11434)
```bash
docker run -it \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v $(pwd)/data:/app/data \
  betting-bot:latest
```

### Run with Ollama in separate container
```bash
# Network for communication
docker network create betting-net

# Start Ollama
docker run -d \
  --name ollama \
  --network betting-net \
  -p 11434:11434 \
  ollama/ollama:latest

# Start bot (pulls model ~2min first time)
docker run -it \
  --network betting-net \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e OLLAMA_BASE_URL=http://ollama:11434 \
  -v $(pwd)/data:/app/data \
  betting-bot:latest
```

## Production Deployment

For production, consider:

1. **Use a registry**: Push image to Docker Hub, ECR, or private registry
2. **Environment secrets**: Use Docker secrets or env files (never commit .env)
3. **Resource limits**: Set memory/CPU limits in docker-compose.yml
4. **Logging**: Configure centralized logging (ELK stack, CloudWatch, etc.)
5. **Monitoring**: Add health checks and alerting
6. **Backup**: Regular backups of `./data/` volume

Example production docker-compose.yml modifications:
```yaml
services:
  bot:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

## Development

### Run with local code changes
```bash
# Rebuild image after code changes
docker-compose build bot
docker-compose up
```

### Access container shell
```bash
docker-compose exec bot bash
```

### Run tests inside container
```bash
docker-compose exec bot pytest tests/ -v
```

## Networking

- **Bot ↔ Ollama**: Both on `betting-network`, bot connects via hostname `ollama`
- **External access**: Ollama port 11434 exposed for debugging/monitoring
- **Bot service**: Internal only (Telegram connection is outbound)

## Files

- `Dockerfile` - Multi-stage build optimizing image size
- `docker-compose.yml` - Services: Ollama, Bot, Network, Volumes
- `.dockerignore` - Excludes unnecessary files from image
- `data/` - Persistent volume (created on first run)
