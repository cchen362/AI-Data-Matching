# 🚀 AI Data Matching Tool - Production Deployment Guide

Complete guide for deploying the AI Data Matching Tool to your POP server (chee@75.163.171.40:8081).

## 🏗️ Server Requirements

### System Requirements
- **OS**: Ubuntu/Debian (POP OS)
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: Minimum 10GB free space
- **Network**: Internet access for API calls

### Required Software
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git (for code updates)

## 🔧 Initial Server Setup

### 1. Connect to Your Server
```bash
ssh -p 8081 chee@75.163.171.40
```

### 2. Install Docker (if not already installed)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### 3. Clone the Repository
```bash
# Clone to home directory
cd ~
git clone https://github.com/cchen362/AI-Data-Matching.git
cd AI-Data-Matching

# Make scripts executable
chmod +x scripts/*.sh
```

## 🚀 Deployment Options

### Option A: Quick Deploy (Recommended)
```bash
# Run the automated deployment script
./scripts/quick-deploy.sh
```
This script will:
- Build the Docker image
- Prompt for your OpenAI API key
- Start the application on port 8503
- Configure production settings

### Option B: Manual Deployment
```bash
# 1. Set your OpenAI API key
echo "OPENAI_API_KEY=your-actual-key-here" > .env

# 2. Build and start the application
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. Verify deployment
docker-compose ps
```

### Option C: Interactive Deployment
```bash
# Use the interactive script (prompts for API key)
./scripts/deploy.sh
```

## 🔍 Verification & Access

### 1. Check Container Status
```bash
# View running containers
docker ps

# Check specific container
docker-compose ps

# View logs
docker-compose logs -f ai-data-matching-prod
```

### 2. Health Check
```bash
# Run health check
docker exec ai-data-matching-prod python health_check.py

# Check container health status
docker inspect ai-data-matching-prod | grep Health -A 10
```

### 3. Access the Application
- **Internal**: `http://localhost:8503`
- **External**: `http://75.163.171.40:8503`
- **Browser**: Open the external URL in your web browser

## 🔐 Security Configuration

### 1. Firewall Setup
```bash
# Allow port 8503 through firewall
sudo ufw allow 8503/tcp

# Check firewall status
sudo ufw status
```

### 2. Environment Security
```bash
# Secure the .env file
chmod 600 .env
chown $USER:$USER .env

# Verify permissions
ls -la .env
```

### 3. Container Security
The Docker configuration includes:
- Non-root user execution
- Resource limits
- Health checks
- Secure environment variable handling

## 🔄 Management Operations

### Starting/Stopping the Application
```bash
# Start
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View status
docker-compose ps
```

### Updating the Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Clean up old images (optional)
docker system prune -f
```

### Managing the OpenAI API Key
```bash
# Update API key
./scripts/update-api-key.sh

# Or manually edit .env
nano .env
docker-compose restart
```

### Log Management
```bash
# View live logs
docker-compose logs -f

# View specific container logs
docker logs ai-data-matching-prod

# Export logs
docker-compose logs > app-logs-$(date +%Y%m%d).txt
```

## 📊 Monitoring

### Container Health
```bash
# Check health status
docker inspect ai-data-matching-prod --format='{{.State.Health.Status}}'

# View health check logs
docker inspect ai-data-matching-prod --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
```

### Resource Usage
```bash
# View resource usage
docker stats ai-data-matching-prod

# View system resources
htop
df -h
```

### Application Metrics
- Health check endpoint runs every 30 seconds
- Automatic restart on failure
- Resource limits: 2GB RAM, 1 CPU core max

## 🐛 Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs for errors
docker-compose logs ai-data-matching-prod

# Verify OpenAI API key
grep OPENAI_API_KEY .env

# Rebuild container
docker-compose down
docker-compose up -d --build
```

**Port already in use:**
```bash
# Check what's using the port
sudo lsof -i :8503

# Use different port (edit docker-compose.yml)
# Change "8503:8501" to "8504:8501"
```

**API key not working:**
```bash
# Test API key manually
docker exec ai-data-matching-prod python -c "
import os
print('API Key:', os.getenv('OPENAI_API_KEY')[:10] + '...' if os.getenv('OPENAI_API_KEY') else 'NOT SET')
"
```

**Application not accessible:**
```bash
# Check firewall
sudo ufw status

# Check if service is binding to all interfaces
docker port ai-data-matching-prod

# Test local connection
curl -I http://localhost:8503
```

### Getting Help
1. Check container logs: `docker-compose logs -f`
2. Run health check: `python health_check.py`
3. Verify network connectivity: `curl -I http://localhost:8503`
4. Check resource usage: `docker stats`

## 🔄 Backup & Recovery

### Data Backup
```bash
# Create backup directory
mkdir -p ~/backups/ai-data-matching

# Backup volumes
docker run --rm -v ai-data-matching_data:/data -v ~/backups:/backup alpine tar czf /backup/data-backup-$(date +%Y%m%d).tar.gz -C /data .

# Backup configuration
cp .env ~/backups/ai-data-matching/env-backup-$(date +%Y%m%d)
```

### Recovery
```bash
# Restore from backup
docker run --rm -v ai-data-matching_data:/data -v ~/backups:/backup alpine tar xzf /backup/data-backup-YYYYMMDD.tar.gz -C /data

# Restart application
docker-compose restart
```

## 📞 Support

For technical issues:
1. Check the logs first: `docker-compose logs -f`
2. Run health checks: `python health_check.py`
3. Verify your OpenAI API key is valid and has credits
4. Ensure port 8503 is not blocked by firewall

---

**🎉 Your AI Data Matching Tool is now deployed and ready to use at: http://75.163.171.40:8503**