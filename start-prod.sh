#!/bin/bash

echo "Starting Oracle Cloud Autoscaling Management System in Production Mode..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please copy .env.production to .env and configure your production settings:"
    echo "cp .env.production .env"
    echo "Then edit .env with your production values."
    exit 1
fi

# Build and start all services in production mode
echo "Building and starting services in production mode..."
docker-compose -f docker-compose.prod.yaml up --build -d

echo "✅ Services started successfully in production mode!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "📊 View logs with:"
echo "  docker-compose -f docker-compose.prod.yaml logs -f"
echo ""
echo "🛑 Stop services with:"
echo "  docker-compose -f docker-compose.prod.yaml down"