# Docker Setup Guide

This app can be run in Docker with Docker Compose, which includes both the Telegram betting bot and an Ollama LLM service.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Telegram Bot Token (from @BotFather)
- Ollama models downloaded on host (run `ollama pull gemma4:latest`)

### Setup

1. **Download Ollama model on host:**
   ```bash
   ollama pull gemma4:latest
   # Verify model is available
   ollama list
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your TELEGRAM_BOT_TOKEN
   ```

3. **Start services:**
   ```bash
   docker-compose up -d
   ```

   This will:
   - Pull Ollama image
   - Build bot image
   - Start Ollama service with bind mount to host's ollama models (${HOME}/.ollama)
   - Start bot service (connected to Ollama)
   - Create persistent data volume for databases

4. **Check status:**
   ```bash
   docker-compose logs -f bot
   docker-compose logs ollama
   ```

5. **Stop services:**
   ```bash
   docker-compose down
   ```

## Configuration

### Environment Variables

Set in `.env` before running `docker-compose up`:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OLLAMA_MODEL=gemma4:latest       # Default model
OLLAMA_BASE_URL=http://localhost:11434
LOG_LEVEL=INFO                  # DEBUG for verbose output
```

### Ollama Model Setup

The bot uses a bind mount to access your host's Ollama models at `${HOME}/.ollama`. This means:

- **Models must be downloaded on the host** before starting Docker
- The container doesn't download models automatically
- Models persist on your host machine

**Download a model:**
```bash
ollama pull gemma4:latest
```

**List available models:**
```bash
ollama list
```

**Use a different model:**
```bash
# 1. Download the model on host
ollama pull llama2:7b

# 2. Update .env
echo "OLLAMA_MODEL=llama2:7b" >> .env

# 3. Restart bot
docker-compose up -d --force-recreate bot
```

### Persist Data

Database files are stored in `./data/` directory on host machine, so they survive container restarts.

## Troubleshooting

### Ollama not starting
```bash
docker-compose logs ollama
# Check if port 11434 is in use
lsof -i :11434
# Kill any existing ollama process
kill $(lsof -t -i:11434)
```

### Model not found in Ollama
```bash
# Check available models on host
ollama list

# If model not found, download it
ollama pull gemma4:latest

# Restart services
docker-compose restart bot
```

### Bot can't connect to Ollama
```bash
# Verify Ollama is healthy
docker-compose exec ollama bash -c 'echo > /dev/tcp/localhost/11434'
# Check if models are accessible
docker-compose exec ollama ollama list
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
  -e OLLAMA_MODEL=gemma4:latest \
  -v $(pwd)/data:/app/data \
  betting-bot:latest
```

### Run with Ollama in separate container
```bash
# Network for communication
docker network create betting-net

# Start Ollama with host models bind mount
docker run -d \
  --name ollama \
  --network betting-net \
  -p 11434:11434 \
  -v ${HOME}/.ollama:/root/.ollama \
  -e OLLAMA_HOST=0.0.0.0:11434 \
  ollama/ollama:latest

# Start bot
docker run -it \
  --network betting-net \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e OLLAMA_BASE_URL=http://ollama:11434 \
  -e OLLAMA_MODEL=gemma4:latest \
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
