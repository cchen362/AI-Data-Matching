#!/bin/bash
# Quick deployment script for your POP server
# Usage: ./quick-deploy.sh

set -e

echo "🚀 Quick Deploy to POP Server"
echo "=============================="

# Check if we're on the server or need to connect
if [[ "$HOSTNAME" == *"pop"* ]] || [[ "$USER" == "chee" ]]; then
    echo "✅ Running on POP server"
    LOCAL_DEPLOY=true
else
    echo "🌐 Connecting to POP server (chee@75.163.171.40:8081)"
    LOCAL_DEPLOY=false
fi

if [ "$LOCAL_DEPLOY" = true ]; then
    # Deploy locally on server
    echo "📦 Building Docker image..."
    docker build -t ai-data-matching:latest .
    
    echo "🔑 Setting up API key..."
    read -p "Enter your OpenAI API Key: " -s OPENAI_API_KEY
    echo ""
    
    echo "🚀 Starting application..."
    OPENAI_API_KEY="$OPENAI_API_KEY" docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    
    echo "✅ Deployment complete!"
    echo "🌐 Application should be available at: http://75.163.171.40:8503"
    
else
    # Deploy via SSH
    echo "📤 Uploading code to server..."
    rsync -avz --exclude='.git' --exclude='venv' --exclude='__pycache__' \
        ./ chee@75.163.171.40:/home/chee/ai-data-matching/
    
    echo "🔧 Deploying on server..."
    ssh -p 8081 chee@75.163.171.40 << 'EOF'
        cd /home/chee/ai-data-matching
        chmod +x scripts/*.sh
        ./scripts/deploy.sh
EOF
    
    echo "✅ Remote deployment complete!"
    echo "🌐 Application should be available at: http://75.163.171.40:8503"
fi