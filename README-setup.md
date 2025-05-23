
# Oracle Cloud Autoscaling Management System

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Running with Docker (Recommended)

1. **Start all services:**
   ```bash
   chmod +x start-dev.sh
   ./start-dev.sh
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

3. **Create your first user:**
   Visit the frontend and register a new account.

### Development Setup

#### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development
```bash
npm install
npm run dev
```

### Environment Variables

Create a `.env` file in the backend directory:
```
DATABASE_URL=mysql+pymysql://autoscaling_user:autoscaling_pass@localhost:3306/autoscaling_db
SECRET_KEY=your-very-secure-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Database Management

The application uses MySQL with SQLAlchemy ORM. Database tables are automatically created when the application starts.

### API Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /nodes` - List all autoscaling nodes
- `POST /nodes` - Register new node
- `GET /pools` - List all instance pools
- `POST /pools` - Create new pool
- `GET /metrics` - Get metrics data
- `POST /metrics` - Submit metrics (used by nodes)
- `GET /schedules` - List scaling schedules
- `POST /schedules` - Create scaling schedule

### Next Steps

1. Register your first autoscaling node
2. Configure instance pools
3. Set up monitoring and schedules
4. Deploy autoscaling nodes in different Oracle Cloud regions
