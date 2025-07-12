#!/bin/bash

echo "🔍 Brainrot Generator Production Status Check"
echo "=============================================="

echo ""
echo "📊 Service Status:"
echo "-----------------"
sudo systemctl is-active brainrot-generator && echo "✅ Flask App: ACTIVE" || echo "❌ Flask App: INACTIVE"
sudo systemctl is-active nginx && echo "✅ Nginx: ACTIVE" || echo "❌ Nginx: INACTIVE"

echo ""
echo "🌐 Application URLs:"
echo "-------------------"
echo "Frontend: http://$(curl -s ifconfig.me)"
echo "API Health: http://$(curl -s ifconfig.me)/api/health"

echo ""
echo "📁 File Permissions:"
echo "-------------------"
ls -la brainrot-generator.sock
ls -la frontend/build/index.html

echo ""
echo "📋 Recent Logs:"
echo "---------------"
echo "Flask App (last 5 lines):"
sudo tail -n 5 /var/log/brainrot-generator/error.log

echo ""
echo "Nginx (last 5 lines):"
sudo tail -n 5 /var/log/nginx/error.log 