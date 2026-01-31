#!/bin/bash
# Script to start Docker services (PostgreSQL and Redis)

set -e

echo "🚀 Starting Docker services..."
docker compose up -d

echo ""
echo "✅ Services started successfully"
echo ""
echo "📊 Container status:"
docker compose ps

echo ""
echo "💡 To view logs:"
echo "   docker compose logs -f"
echo ""
echo "💡 To stop services:"
echo "   ./scripts/docker-down.sh"
