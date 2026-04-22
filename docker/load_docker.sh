#!/bin/bash
docker rm -f betting-ollama betting-bot db
docker compose down -v
docker rmi docker-betting-bot docker-betting-ollama docker-betting-db 2>/dev/null || true
docker compose build --no-cache
docker compose up -d