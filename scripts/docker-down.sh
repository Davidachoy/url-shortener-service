#!/bin/bash
# Script to stop Docker services

set -e

echo "🛑 Stopping Docker services..."
docker compose down

echo ""
echo "✅ Services stopped successfully"
echo ""
echo "💡 Data persists in Docker volumes"
echo "💡 To remove data as well, run:"
echo "   ./scripts/docker-clean.sh"
