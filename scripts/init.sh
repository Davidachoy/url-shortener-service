#!/bin/bash
# Full project initialization script

set -e

echo "🎯 Initializing URL Shortener project..."
echo ""

# 1. Start Docker
echo "📦 1/4 - Starting Docker services..."
./scripts/docker-up.sh
echo ""

# 2. Wait for PostgreSQL to be ready
echo "⏳ 2/4 - Waiting for PostgreSQL to be ready..."
sleep 5

# 3. Run migrations
echo "🔄 3/4 - Running Alembic migrations..."
alembic upgrade head
echo ""

# 4. Show status
echo "✅ 4/4 - Project initialized successfully"
echo ""
echo "📊 Service status:"
docker compose ps
echo ""
echo "💡 To start the application:"
echo "   uvicorn app.main:app --reload"
echo ""
echo "💡 To view Docker logs:"
echo "   ./scripts/docker-logs.sh"
