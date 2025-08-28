#!/bin/bash
# AI Data Matching Tool - Deployment Script
# This script provides multiple ways to set the OpenAI API key

set -e

echo "🚀 AI Data Matching Tool - Deployment Script"
echo "============================================="

# Function to deploy with environment variable
deploy_with_env() {
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "❌ OPENAI_API_KEY environment variable not set"
        echo "Set it with: export OPENAI_API_KEY='your-key-here'"
        exit 1
    fi
    
    echo "✅ Using OPENAI_API_KEY from environment"
    docker-compose up -d
}

# Function to deploy with .env file
deploy_with_env_file() {
    if [ ! -f .env ]; then
        echo "📝 Creating .env file..."
        read -p "Enter your OpenAI API Key: " -s api_key
        echo ""
        echo "OPENAI_API_KEY=$api_key" > .env
        echo "✅ Created .env file"
    fi
    
    docker-compose up -d
}

# Function to deploy with direct prompt
deploy_with_prompt() {
    read -p "Enter your OpenAI API Key: " -s api_key
    echo ""
    OPENAI_API_KEY="$api_key" docker-compose up -d
}

# Main deployment options
echo "Choose deployment method:"
echo "1) Use existing OPENAI_API_KEY environment variable"
echo "2) Create/use .env file" 
echo "3) Enter API key now (secure prompt)"
echo "4) Run without API key (for testing - LLM features disabled)"

read -p "Select option (1-4): " choice

case $choice in
    1)
        deploy_with_env
        ;;
    2)
        deploy_with_env_file
        ;;
    3)
        deploy_with_prompt
        ;;
    4)
        echo "⚠️  Deploying without OpenAI API key - LLM features will be disabled"
        docker-compose up -d
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Deployment complete!"
echo "🌐 Application available at: http://localhost:8503"
echo "🔍 Check status: docker-compose ps"
echo "📋 View logs: docker-compose logs -f"
echo "🛑 Stop: docker-compose down"