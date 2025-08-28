#!/bin/bash
# Setup domain configuration for data.zyroi.com
# Run this on your POP server

DOMAIN="data.zyroi.com"
CONTAINER_IP="172.19.0.2"
CONTAINER_PORT="8501"

echo "🌐 Setting up domain: $DOMAIN"
echo "🔗 Pointing to: $CONTAINER_IP:$CONTAINER_PORT"

# Create Nginx site configuration
sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://$CONTAINER_IP:$CONTAINER_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        
        # Additional headers for Streamlit
        proxy_set_header X-Forwarded-Host \$server_name;
        proxy_buffering off;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

# Test Nginx configuration
echo "🧪 Testing Nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    # Reload Nginx
    echo "🔄 Reloading Nginx..."
    sudo systemctl reload nginx
    
    echo "✅ Domain setup complete!"
    echo "🌐 Your application should now be available at: http://$DOMAIN"
    echo ""
    echo "🔒 To add SSL certificate, run:"
    echo "sudo certbot --nginx -d $DOMAIN"
else
    echo "❌ Nginx configuration test failed"
    exit 1
fi