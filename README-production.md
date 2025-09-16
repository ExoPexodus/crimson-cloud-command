# Production Deployment Guide

This guide explains how to deploy the Oracle Cloud Autoscaling Management System in a production environment.

## Prerequisites

- Docker and Docker Compose installed
- Production domain and SSL certificates (recommended)
- Secure environment variables configured

## Quick Start

1. **Configure Environment Variables**
   ```bash
   cp .env.production .env
   ```
   Edit `.env` with your production values:
   - Set a strong `SECRET_KEY`
   - Configure your production domain in `CORS_ORIGINS`
   - Update `VITE_API_URL` to your production API endpoint
   - Configure Keycloak settings if using SSO

2. **Start Production Services**
   ```bash
   chmod +x start-prod.sh
   ./start-prod.sh
   ```

3. **Monitor Services**
   ```bash
   # View logs
   docker-compose -f docker-compose.prod.yaml logs -f
   
   # Check service status
   docker-compose -f docker-compose.prod.yaml ps
   ```

## Production Features

- **Multi-worker Backend**: Uses 4 Uvicorn workers for better performance
- **Optimized Frontend**: Built and served as static files with serve
- **Health Checks**: Built-in health monitoring for both services
- **Auto-restart**: Services automatically restart on failure
- **Log Rotation**: Prevents log files from growing too large
- **Security**: Non-root user execution in containers

## Security Considerations

- Change default `SECRET_KEY` to a secure random string
- Use HTTPS in production with proper SSL certificates
- Configure firewall rules to restrict access
- Regularly update Docker images and dependencies
- Monitor logs for suspicious activity

## Scaling

To scale the backend for higher load:
```bash
docker-compose -f docker-compose.prod.yaml up --scale backend=3
```

## Backup Strategy

Ensure you have backups of:
- Database data
- Configuration files (.env)
- SSL certificates
- Application logs

## Monitoring

The application includes health check endpoints:
- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:3000`

Use these for external monitoring systems.

## Stopping Services

```bash
docker-compose -f docker-compose.prod.yaml down
```

To remove all data (⚠️ destructive):
```bash
docker-compose -f docker-compose.prod.yaml down -v
```