#!/bin/bash

# Production Deployment Script for Brainrot Generator
set -e

echo "🚀 Starting production deployment..."

# Create log directory
sudo mkdir -p /var/log/brainrot-generator
sudo chown ubuntu:ubuntu /var/log/brainrot-generator

# Copy systemd service file
sudo cp brainrot-generator.service /etc/systemd/system/
sudo systemctl daemon-reload

# Copy Nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/brainrot-generator
sudo ln -sf /etc/nginx/sites-available/brainrot-generator /etc/nginx/sites-enabled/

# Remove default Nginx site
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Create uploads directory
mkdir -p uploads

# Set proper permissions
sudo chown -R ubuntu:ubuntu /home/ubuntu/brainrot-generator-main
chmod +x deploy.sh

# Enable and start services
sudo systemctl enable brainrot-generator
sudo systemctl start brainrot-generator
sudo systemctl restart nginx

# Check service status
echo "📊 Service Status:"
sudo systemctl status brainrot-generator --no-pager
sudo systemctl status nginx --no-pager

echo "✅ Deployment complete!"
echo "🌐 Your application should now be accessible at: http://$(curl -s ifconfig.me)"
echo "📝 Don't forget to:"
echo "   1. Update production.env with your actual configuration"
echo "   2. Set up SSL certificates with Let's Encrypt"
echo "   3. Configure your domain DNS"
echo "   4. Set up monitoring and logging" 