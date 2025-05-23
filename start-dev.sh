
#!/bin/bash

echo "Starting Oracle Cloud Autoscaling Management System..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start all services
echo "Building and starting services..."
docker-compose up --build

echo "Services started successfully!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
