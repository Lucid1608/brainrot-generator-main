#!/bin/bash

# Simple Deployment Script for Brainrot Generator
# This script deploys the app directly to a production server

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Deploying Brainrot Generator to Production${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   exit 1
fi

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required packages
echo -e "${YELLOW}📦 Installing required packages...${NC}"
sudo apt install -y python3 python3-pip python3-venv nginx ffmpeg postgresql postgresql-contrib redis-server

# Create application directory
APP_DIR="/var/www/brainrot-generator"
echo -e "${YELLOW}📁 Setting up application directory...${NC}"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
echo -e "${YELLOW}📁 Copying application files...${NC}"
cp -r . $APP_DIR/
cd $APP_DIR

# Create virtual environment
echo -e "${YELLOW}🐍 Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Set up environment file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚙️  Creating environment configuration...${NC}"
    cat > .env << EOF
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=postgresql://brainrot_user:$(python3 -c "import secrets; print(secrets.token_hex(16))")@localhost/brainrot_db

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# File Upload
UPLOAD_FOLDER=/var/www/brainrot-generator/uploads
MAX_CONTENT_LENGTH=16777216

# Frontend URL
FRONTEND_URL=https://yourdomain.com
EOF
    echo -e "${YELLOW}⚠️  Please edit .env file with your actual configuration${NC}"
fi

# Set up PostgreSQL
echo -e "${YELLOW}🗄️  Setting up PostgreSQL...${NC}"
sudo -u postgres psql -c "CREATE DATABASE brainrot_db;"
sudo -u postgres psql -c "CREATE USER brainrot_user WITH PASSWORD '$(python3 -c "import secrets; print(secrets.token_hex(16))")';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE brainrot_db TO brainrot_user;"

# Initialize database
echo -e "${YELLOW}🗄️  Initializing database...${NC}"
source venv/bin/activate
flask init-db

# Create upload directory
mkdir -p uploads
chmod 755 uploads

# Set up Gunicorn service
echo -e "${YELLOW}🔧 Setting up Gunicorn service...${NC}"
sudo tee /etc/systemd/system/brainrot-generator.service > /dev/null << EOF
[Unit]
Description=Brainrot Generator
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/gunicorn --workers 4 --bind unix:brainrot-generator.sock -m 007 run:app

[Install]
WantedBy=multi-user.target
EOF

# Set up Nginx
echo -e "${YELLOW}🌐 Setting up Nginx...${NC}"
sudo tee /etc/nginx/sites-available/brainrot-generator > /dev/null << EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://unix:$APP_DIR/brainrot-generator.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias $APP_DIR/frontend/build/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /uploads/ {
        alias $APP_DIR/uploads/;
        expires 1h;
        add_header Cache-Control "public";
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/brainrot-generator /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Build React frontend
echo -e "${YELLOW}⚛️  Building React frontend...${NC}"
cd frontend
npm install
npm run build
cd ..

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
sudo systemctl enable brainrot-generator
sudo systemctl start brainrot-generator
sudo systemctl restart nginx

# Set up firewall
echo -e "${YELLOW}🔥 Setting up firewall...${NC}"
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create admin user
echo -e "${YELLOW}👤 Creating admin user...${NC}"
source venv/bin/activate
flask create-admin

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo
echo -e "${GREEN}🎉 Your Brainrot Generator is now running!${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit .env file with your actual configuration"
echo "2. Set up SSL certificates with Let's Encrypt:"
echo "   sudo apt install certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d yourdomain.com"
echo "3. Access your application at: http://yourdomain.com"
echo
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View logs: sudo journalctl -u brainrot-generator -f"
echo "  Restart app: sudo systemctl restart brainrot-generator"
echo "  Check status: sudo systemctl status brainrot-generator" 