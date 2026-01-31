#!/bin/bash
# Script to fully clean Docker (containers + volumes + networks)

set -e

echo "⚠️  This script will remove:"
echo "   - Containers"
echo "   - Volumes (POSTGRES AND REDIS DATA)"
echo "   - Networks"
echo ""
read -p "Are you sure? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Operation cancelled"
    exit 1
fi

echo "🗑️  Cleaning Docker..."
docker compose down -v

echo ""
echo "✅ Docker cleaned completely"
echo "💡 PostgreSQL and Redis data have been removed"
echo "💡 To start again: ./scripts/docker-up.sh"
