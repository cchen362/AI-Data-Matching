#!/bin/bash
# Update OpenAI API Key in running container
# Usage: ./update-api-key.sh [new-api-key]

set -e

CONTAINER_NAME="ai-data-matching"

echo "🔑 AI Data Matching Tool - API Key Update"
echo "========================================="

# Check if container is running
if ! docker ps --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '${CONTAINER_NAME}' is not running"
    echo "Start it with: docker-compose up -d"
    exit 1
fi

# Get API key
if [ -n "$1" ]; then
    NEW_API_KEY="$1"
else
    read -p "Enter new OpenAI API Key: " -s NEW_API_KEY
    echo ""
fi

if [ -z "$NEW_API_KEY" ]; then
    echo "❌ No API key provided"
    exit 1
fi

echo "🔄 Updating API key in container..."

# Method 1: Update .env file and restart (recommended)
echo "OPENAI_API_KEY=$NEW_API_KEY" > .env
echo "✅ Updated .env file"

echo "🔄 Restarting container to apply changes..."
docker-compose restart

echo "✅ API key updated successfully!"
echo "🌐 Application available at: http://localhost:8503"

# Method 2: Alternative - set environment variable without restart
echo ""
echo "💡 Alternative: To update without restart (may not work for all features):"
echo "docker exec $CONTAINER_NAME /bin/bash -c 'export OPENAI_API_KEY=\"$NEW_API_KEY\"'"