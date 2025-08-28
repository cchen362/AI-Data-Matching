#!/bin/bash
# AI Data Matching Tool - POP Server Setup Script
# This script automates the complete server setup process

set -e

SERVER_HOST="75.163.171.40"
SERVER_PORT="8081"
SERVER_USER="chee"
APP_DIR="/home/chee/ai-data-matching"
APP_PORT="8503"

echo "🏗️  AI Data Matching Tool - Server Setup"
echo "========================================"
echo "Target: ${SERVER_USER}@${SERVER_HOST}:${SERVER_PORT}"
echo "App Directory: ${APP_DIR}"
echo "App Port: ${APP_PORT}"
echo ""

# Function to check if we can connect to server
check_server_connection() {
    echo "🔍 Checking server connection..."
    if ssh -p ${SERVER_PORT} -o ConnectTimeout=5 ${SERVER_USER}@${SERVER_HOST} "echo 'Connection successful'" 2>/dev/null; then
        echo "✅ Server connection verified"
        return 0
    else
        echo "❌ Cannot connect to server. Please check:"
        echo "   - SSH key is set up"
        echo "   - Server is reachable"
        echo "   - Port ${SERVER_PORT} is open"
        return 1
    fi
}

# Function to check/install Docker on server
setup_docker() {
    echo "🐳 Setting up Docker on server..."
    
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} << 'EOF'
        # Check if Docker is installed
        if command -v docker &> /dev/null; then
            echo "✅ Docker is already installed"
            docker --version
        else
            echo "📦 Installing Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
            echo "✅ Docker installed"
        fi
        
        # Check if Docker Compose is available
        if docker compose version &> /dev/null; then
            echo "✅ Docker Compose is available"
            docker compose version
        else
            echo "📦 Installing Docker Compose..."
            sudo apt update
            sudo apt install -y docker-compose-plugin
            echo "✅ Docker Compose installed"
        fi
        
        # Start Docker service
        sudo systemctl enable docker
        sudo systemctl start docker
        
        echo "🔧 Docker setup complete"
EOF
    
    echo "✅ Docker setup completed on server"
}

# Function to deploy application code
deploy_code() {
    echo "📤 Deploying application code to server..."
    
    # Create app directory on server
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${APP_DIR}"
    
    # Sync code to server (excluding unnecessary files)
    rsync -avz --progress \
        --exclude='.git' \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='node_modules' \
        --exclude='*.log' \
        -e "ssh -p ${SERVER_PORT}" \
        ./ ${SERVER_USER}@${SERVER_HOST}:${APP_DIR}/
    
    # Make scripts executable
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} "chmod +x ${APP_DIR}/scripts/*.sh"
    
    echo "✅ Code deployed to server"
}

# Function to configure environment
configure_environment() {
    echo "🔧 Configuring environment on server..."
    
    # Get OpenAI API key
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "🔑 OpenAI API Key Configuration"
        read -p "Enter your OpenAI API Key: " -s OPENAI_API_KEY
        echo ""
    fi
    
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "❌ OpenAI API Key is required"
        exit 1
    fi
    
    # Create .env file on server
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} << EOF
        cd ${APP_DIR}
        echo "OPENAI_API_KEY=${OPENAI_API_KEY}" > .env
        chmod 600 .env
        echo "✅ Environment file created"
EOF
    
    echo "✅ Environment configured"
}

# Function to setup firewall
setup_firewall() {
    echo "🔥 Configuring firewall..."
    
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} << EOF
        # Check if ufw is installed and enabled
        if command -v ufw &> /dev/null; then
            # Allow the application port
            sudo ufw allow ${APP_PORT}/tcp
            echo "✅ Firewall configured to allow port ${APP_PORT}"
            
            # Show firewall status
            echo "🔍 Firewall status:"
            sudo ufw status
        else
            echo "⚠️  UFW not installed, skipping firewall configuration"
        fi
EOF
}

# Function to build and start application
start_application() {
    echo "🚀 Building and starting application..."
    
    ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} << EOF
        cd ${APP_DIR}
        
        # Stop any existing containers
        docker-compose down 2>/dev/null || true
        
        # Build and start with production configuration
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
        
        # Wait for container to start
        echo "⏳ Waiting for application to start..."
        sleep 15
        
        # Check container status
        docker-compose ps
        
        # Test health check
        echo "🏥 Running health check..."
        docker exec ai-data-matching-prod python health_check.py || echo "⚠️  Health check warning (may be normal on first start)"
EOF
    
    echo "✅ Application started"
}

# Function to verify deployment
verify_deployment() {
    echo "🔍 Verifying deployment..."
    
    # Check if container is running
    CONTAINER_STATUS=$(ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} "docker-compose -f ${APP_DIR}/docker-compose.yml -f ${APP_DIR}/docker-compose.prod.yml ps -q ai-data-matching" 2>/dev/null || echo "")
    
    if [ -n "$CONTAINER_STATUS" ]; then
        echo "✅ Container is running"
        
        # Test if application is responding
        echo "🌐 Testing application endpoint..."
        if ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} "curl -s -I http://localhost:${APP_PORT} | head -1" 2>/dev/null | grep -q "200\|HTTP"; then
            echo "✅ Application is responding"
        else
            echo "⚠️  Application may still be starting up"
        fi
        
        return 0
    else
        echo "❌ Container is not running"
        return 1
    fi
}

# Function to show completion summary
show_summary() {
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo ""
    echo "📍 Application URL: http://${SERVER_HOST}:${APP_PORT}"
    echo "🖥️  Server: ${SERVER_USER}@${SERVER_HOST}:${SERVER_PORT}"
    echo "📁 Directory: ${APP_DIR}"
    echo ""
    echo "🔧 Management Commands:"
    echo "   ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST}"
    echo "   cd ${APP_DIR}"
    echo "   docker-compose ps                    # Check status"
    echo "   docker-compose logs -f              # View logs"
    echo "   docker-compose restart              # Restart app"
    echo "   docker-compose down                 # Stop app"
    echo "   ./scripts/update-api-key.sh         # Update API key"
    echo ""
    echo "🌐 Access your application at: http://${SERVER_HOST}:${APP_PORT}"
}

# Main execution
main() {
    echo "Starting automated server setup..."
    echo ""
    
    # Check prerequisites
    if ! command -v rsync &> /dev/null; then
        echo "❌ rsync is required but not installed"
        exit 1
    fi
    
    if ! command -v ssh &> /dev/null; then
        echo "❌ ssh is required but not installed"
        exit 1
    fi
    
    # Execute setup steps
    check_server_connection || exit 1
    setup_docker
    deploy_code
    configure_environment
    setup_firewall
    start_application
    
    # Verify and show results
    if verify_deployment; then
        show_summary
        exit 0
    else
        echo "❌ Deployment verification failed"
        echo "Check the logs with: ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} 'cd ${APP_DIR} && docker-compose logs'"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --verify       Only verify existing deployment"
        echo "  --update       Update existing deployment"
        echo ""
        echo "Environment Variables:"
        echo "  OPENAI_API_KEY    Your OpenAI API key (will prompt if not set)"
        exit 0
        ;;
    --verify)
        check_server_connection && verify_deployment
        exit $?
        ;;
    --update)
        echo "🔄 Updating existing deployment..."
        check_server_connection || exit 1
        deploy_code
        ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_HOST} "cd ${APP_DIR} && docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build"
        verify_deployment && show_summary
        exit $?
        ;;
    "")
        main
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac