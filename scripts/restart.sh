#!/bin/bash
# Script to fully restart the project (clean and start again)

set -e

echo "🔄 Restarting project completely..."
echo ""

# 1. Clean Docker
echo "🗑️  1/3 - Cleaning Docker..."
docker compose down -v
echo ""

# 2. Start services
echo "📦 2/3 - Starting services..."
./scripts/docker-up.sh
echo ""

# 3. Wait and run migrations
echo "⏳ 3/3 - Waiting for PostgreSQL and running migrations..."
sleep 5
alembic upgrade head
echo ""

echo "✅ Project restarted successfully"
echo ""
echo "💡 To start the application:"
echo "   uvicorn app.main:app --reload"
