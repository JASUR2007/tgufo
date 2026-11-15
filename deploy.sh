#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# YouTube Clone — One-Command Ubuntu Deployment Script
# Designed for clean Ubuntu 20.04 / 22.04 / 24.04 LTS installations
# ==============================================================================

echo "======================================================================"
echo "🚀 Starting YouTube Clone Single-Command Deployment on Ubuntu..."
echo "======================================================================"

# 1. Check & Install Docker / Docker Compose if missing
if ! command -v docker &> /dev/null; then
    echo "📦 Docker not detected. Installing Docker via official install script..."
    if command -v curl &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm -f get-docker.sh
    else
        apt-get update && apt-get install -y curl
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm -f get-docker.sh
    fi
    echo "✅ Docker successfully installed."
fi

# Determine compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "📦 Installing Docker Compose plugin..."
    apt-get update && apt-get install -y docker-compose-plugin
    DOCKER_COMPOSE="docker compose"
fi

# 2. Environment Setup
if [ ! -f .env ]; then
    echo "📝 Generating .env from .env.example..."
    cp .env.example .env
fi

# 3. Build & Boot Microservices
echo "🔨 Building and launching containers (PostgreSQL, MinIO, FastAPI Backend, React Frontend)..."
$DOCKER_COMPOSE down --remove-orphans || true
$DOCKER_COMPOSE up -d --build

# 4. Wait for Backend & Database health (using -sf to reject HTTP error codes)
echo "⏳ Waiting for backend service to become ready..."
RETRY=0
MAX_RETRIES=40
READY=false

while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        READY=true
        break
    fi
    RETRY=$((RETRY+1))
    echo "   ... waiting for API to respond healthy (attempt $RETRY/$MAX_RETRIES)"
    sleep 3
done

if [ "$READY" = false ]; then
    echo "❌ Deployment Error: Backend healthcheck failed after $MAX_RETRIES attempts."
    echo "Showing backend logs:"
    $DOCKER_COMPOSE logs backend
    exit 1
fi

echo "✅ Backend is healthy."

# 5. Database Migrations (Strict failure detection without || true)
echo "🌱 Running database migrations (alembic upgrade head)..."
if ! $DOCKER_COMPOSE exec -T backend alembic upgrade head; then
    echo "❌ Deployment Error: Database migrations failed!"
    $DOCKER_COMPOSE logs backend
    exit 1
fi
echo "✅ Migrations completed successfully."

# 6. Database Seed (Strict failure detection without || true)
echo "🌱 Seeding demo accounts and video assets (seed.py)..."
if ! $DOCKER_COMPOSE exec -T backend python -m app.scripts.seed; then
    echo "❌ Deployment Error: Database demo seed failed!"
    $DOCKER_COMPOSE logs backend
    exit 1
fi
echo "✅ Demo database populated successfully."

# 7. Final Verification of Public API
if ! curl -sf http://localhost/api/v1/videos > /dev/null 2>&1; then
    echo "❌ Deployment Warning: /api/v1/videos did not return 200 OK."
    exit 1
fi

# 8. Success Output Banner
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

echo "======================================================================"
echo "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "======================================================================"
echo "🌐 Web Application:       http://${SERVER_IP}/"
echo "📚 Interactive API Docs:  http://${SERVER_IP}/docs"
echo "🗄️ MinIO S3 Console:      http://${SERVER_IP}:9006/ (minioadmin / miniopassword)"
echo ""
echo "⚡ PRE-SEEDED TEST CREDENTIALS (or use 1-click Quick Switcher on Web):"
echo "  ┌────────────────┬──────────────────────────┬─────────────────┐"
echo "  │ Role           │ Email                    │ Password        │"
echo "  ├────────────────┼──────────────────────────┼─────────────────┤"
echo "  │ Admin          │ admin@youtube.local      │ AdminPass123!   │"
echo "  │ Moderator      │ moderator@youtube.local  │ ModPass123!     │"
echo "  │ Creator        │ creator@youtube.local    │ CreatorPass123! │"
echo "  │ Viewer         │ viewer@youtube.local     │ ViewerPass123!  │"
echo "  └────────────────┴──────────────────────────┴─────────────────┘"
echo "======================================================================"
