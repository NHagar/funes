#!/bin/bash

echo "🛑 Stopping OpenMemory services..."

# Stop docker compose services
echo "📦 Stopping backend services..."
docker compose down

# Stop and remove the frontend container
echo "🎨 Stopping frontend..."
docker stop mem0_ui 2>/dev/null || echo "⚠️ mem0_ui container not running"
docker rm mem0_ui 2>/dev/null || echo "⚠️ mem0_ui container not found"

echo "✅ All services stopped"