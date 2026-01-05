# System Architecture

## 1. Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PRESENTATION LAYER                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        React Frontend (SPA)                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │Dashboard │ │  Nodes   │ │ Settings │ │  Users   │ │  Audit   │   │   │
│  │  │   Page   │ │   Page   │ │   Page   │ │   Page   │ │   Logs   │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                              Nginx Proxy
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                             SERVICE LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       FastAPI Backend                                │   │
│  │                                                                      │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │   │
│  │  │ Auth Endpoints │  │ Node Endpoints │  │ Admin Endpoints│         │   │
│  │  │ - /auth/login  │  │ - /nodes       │  │ - /admin/users │         │   │
│  │  │ - /auth/keycloak│ │ - /nodes/{id}  │  │ - /admin/audit │         │   │
│  │  │ - /auth/profile│  │ - /heartbeat   │  │                │         │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘         │   │
│  │                                                                      │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │   │
│  │  │  Pool Service  │  │ Metrics Service│  │ Analytics Svc  │         │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘         │   │
│  │                                                                      │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │   │
│  │  │  Role Service  │  │ Keycloak Svc   │  │ Audit Service  │         │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        PostgreSQL Database                           │   │
│  │                                                                      │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │   │
│  │  │ users  │ │ nodes  │ │ pools  │ │metrics │ │ audit  │ │schedules│ │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Details

### 2.1 Frontend Architecture

```
src/
├── components/
│   ├── auth/                    # Authentication components
│   │   ├── AuthPage.tsx         # Login page wrapper
│   │   ├── LoginForm.tsx        # Local login form
│   │   └── KeycloakLoginButton.tsx  # SSO login trigger
│   │
│   ├── dashboard/               # Dashboard components
│   │   ├── DashboardHeader.tsx  # Page header with title
│   │   ├── SystemMetricsCards.tsx   # Analytics summary cards
│   │   ├── InstancePoolsSection.tsx # Pool listing
│   │   ├── InstancePoolCard.tsx     # Individual pool card
│   │   ├── NodeConfigDialog.tsx     # YAML config editor
│   │   └── NodeLifecycleLogs.tsx    # Node event history
│   │
│   ├── layout/                  # Layout components
│   │   ├── Header.tsx           # Top navigation bar
│   │   └── Sidebar.tsx          # Side navigation menu
│   │
│   └── ui/                      # shadcn/ui components
│
├── hooks/
│   ├── useAuth.tsx              # Authentication state management
│   └── useSystemAnalytics.tsx   # Analytics data fetching
│
├── lib/
│   ├── api.ts                   # API client with all endpoints
│   ├── runtimeConfig.ts         # Runtime configuration loader
│   └── utils.ts                 # Utility functions
│
├── pages/
│   ├── Index.tsx                # Main dashboard
│   ├── Nodes.tsx                # Node management
│   ├── Settings.tsx             # User settings
│   └── admin/
│       ├── Users.tsx            # User management (admin)
│       └── AuditLogs.tsx        # Audit log viewer (admin)
│
└── App.tsx                      # Root component with routing
```

### 2.2 Backend Architecture

```
backend/
├── main.py                      # FastAPI application entry point
│                                # - CORS configuration
│                                # - Route definitions
│                                # - Dependency injection
│
├── services.py                  # Business logic services
│   ├── AuthService              # Token creation/validation
│   ├── UserService              # User CRUD operations
│   ├── NodeService              # Node management
│   ├── PoolService              # Pool management
│   ├── MetricService            # Metrics recording
│   ├── ScheduleService          # Schedule management
│   ├── HeartbeatService         # Node heartbeat processing
│   ├── AnalyticsService         # Analytics calculations
│   └── NodeLifecycleService     # Lifecycle event logging
│
├── models.py                    # SQLAlchemy ORM models
│   ├── Node                     # Autoscaler node entity
│   ├── Pool                     # Instance pool entity
│   ├── Metric                   # Time-series metrics
│   ├── Schedule                 # Scaling schedules
│   ├── User                     # User accounts
│   ├── AuditLog                 # Audit trail
│   └── ...                      # Other entities
│
├── schemas.py                   # Pydantic request/response models
│
├── auth_middleware.py           # API key authentication
├── role_service.py              # RBAC implementation
├── keycloak_service.py          # Keycloak integration
├── audit_service.py             # Audit logging service
├── analytics_calculator.py      # Dashboard analytics
│
├── database.py                  # Database connection setup
├── migration_manager.py         # Database initialization
│
└── alembic/                     # Database migrations
    └── versions/                # Migration scripts
```

### 2.3 Autoscaler Node Architecture

```
autoscaler-node/auto_scaler_project/
├── src/
│   ├── main.py                  # Application entry point
│   │   ├── AutoscalerNode       # Node management class
│   │   ├── process_pool()       # Per-pool monitoring loop
│   │   └── main()               # Startup and orchestration
│   │
│   ├── collectors/              # Metrics collection
│   │   ├── base_collector.py    # Abstract collector interface
│   │   ├── oci_collector.py     # OCI Monitoring API collector
│   │   └── prometheus_collector.py  # Prometheus collector
│   │
│   ├── scaling_logic/
│   │   └── auto_scaler.py       # Core scaling decisions
│   │
│   ├── scheduler/
│   │   └── scheduler.py         # Time-based scaling
│   │
│   ├── oracle_sdk_wrapper/
│   │   └── oci_scaling.py       # OCI API wrappers
│   │
│   ├── instance_manager/
│   │   ├── instance_pool.py     # Instance pool operations
│   │   └── load_balancer.py     # Load balancer integration
│   │
│   ├── services/
│   │   └── heartbeat_service.py # Backend communication
│   │
│   ├── alerts/
│   │   └── webhook.py           # Alert notifications
│   │
│   └── user_config/
│       ├── config_manager.py    # Configuration loading
│       └── yaml_loader.py       # YAML parsing
│
├── config.yaml                  # Pool configuration file
└── requirements.txt             # Python dependencies
```

---

## 3. Communication Patterns

### 3.1 Frontend ↔ Backend

```
┌──────────────┐                    ┌──────────────┐
│   Frontend   │                    │   Backend    │
│   (React)    │                    │  (FastAPI)   │
└──────┬───────┘                    └──────┬───────┘
       │                                   │
       │  1. User opens dashboard          │
       ├──────────────────────────────────►│
       │     GET /nodes                    │
       │     Authorization: Bearer <JWT>   │
       │                                   │
       │◄──────────────────────────────────┤
       │     200 OK                        │
       │     [{ id: 1, name: "node-1" }]   │
       │                                   │
       │  2. User updates config           │
       ├──────────────────────────────────►│
       │     PUT /nodes/1/config           │
       │     { yaml_config: "..." }        │
       │                                   │
       │◄──────────────────────────────────┤
       │     200 OK                        │
       │     { config_hash: "abc123" }     │
       │                                   │
```

### 3.2 Autoscaler Node ↔ Backend

```
┌──────────────┐                    ┌──────────────┐
│  Autoscaler  │                    │   Backend    │
│    Node      │                    │  (FastAPI)   │
└──────┬───────┘                    └──────┬───────┘
       │                                   │
       │  1. Node registers on startup     │
       ├──────────────────────────────────►│
       │     POST /nodes/register          │
       │     { name, region, ip_address }  │
       │                                   │
       │◄──────────────────────────────────┤
       │     200 OK                        │
       │     { node_id, api_key }          │
       │                                   │
       │  2. Heartbeat every 60 seconds    │
       ├──────────────────────────────────►│
       │     POST /heartbeat               │
       │     X-API-Key: <api_key>          │
       │     { status, pool_analytics }    │
       │                                   │
       │◄──────────────────────────────────┤
       │     200 OK                        │
       │     { config_update_needed: bool }│
       │                                   │
       │  3. If config changed, fetch new  │
       ├──────────────────────────────────►│
       │     GET /nodes/{id}/config        │
       │                                   │
       │◄──────────────────────────────────┤
       │     200 OK                        │
       │     { yaml_config: "..." }        │
       │                                   │
```

### 3.3 Autoscaler Node ↔ OCI

```
┌──────────────┐                    ┌──────────────┐
│  Autoscaler  │                    │     OCI      │
│    Node      │                    │    APIs      │
└──────┬───────┘                    └──────┬───────┘
       │                                   │
       │  1. Get instance pool details     │
       ├──────────────────────────────────►│
       │     GET /instancePools/{id}       │
       │                                   │
       │◄──────────────────────────────────┤
       │     { size: 3, lifecycleState }   │
       │                                   │
       │  2. Get metrics from Monitoring   │
       ├──────────────────────────────────►│
       │     POST /metrics/actions/        │
       │           summarizeMetricsData    │
       │                                   │
       │◄──────────────────────────────────┤
       │     { avg_cpu: 75%, avg_mem: 60% }│
       │                                   │
       │  3. Scale up/down if needed       │
       ├──────────────────────────────────►│
       │     PUT /instancePools/{id}       │
       │     { size: 5 }                   │
       │                                   │
       │◄──────────────────────────────────┤
       │     200 OK                        │
       │                                   │
```

---

## 4. Security Architecture

### 4.1 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Authentication Methods                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────┐     ┌─────────────────────────┐                │
│  │    Local Authentication │     │  Keycloak SSO           │                │
│  │                         │     │                         │                │
│  │  User ──► Login Form    │     │  User ──► Keycloak      │                │
│  │           │             │     │           │             │                │
│  │           ▼             │     │           ▼             │                │
│  │  Backend validates      │     │  Exchange code for      │                │
│  │  email/password         │     │  token at backend       │                │
│  │           │             │     │           │             │                │
│  │           ▼             │     │           ▼             │                │
│  │  Return JWT token       │     │  Validate Keycloak      │                │
│  │                         │     │  token, create local JWT│                │
│  └─────────────────────────┘     └─────────────────────────┘                │
│                                                                              │
│                            ▼                                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    All API requests include:                           │  │
│  │                    Authorization: Bearer <JWT>                         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Node Authentication

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Node API Key Flow                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Registration                                                             │
│     ┌────────────┐                         ┌────────────┐                   │
│     │ Autoscaler │ ── POST /nodes/register ──►│  Backend  │                  │
│     │    Node    │                         │            │                   │
│     │            │◄── { api_key: "..." } ──│            │                   │
│     └────────────┘                         └────────────┘                   │
│                                                                              │
│  2. Ongoing Communication                                                    │
│     ┌────────────┐                         ┌────────────┐                   │
│     │ Autoscaler │ ── POST /heartbeat ────►│  Backend   │                   │
│     │    Node    │    X-API-Key: <key>     │            │                   │
│     │            │                         │  Hash key, │                   │
│     │            │                         │  lookup in │                   │
│     │            │                         │  database  │                   │
│     │            │◄── 200 OK ──────────────│            │                   │
│     └────────────┘                         └────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Deployment Architecture

### 5.1 Production Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Docker Host / Kubernetes                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                              Nginx                                    │   │
│  │                         (Port 80/443)                                 │   │
│  │                                                                       │   │
│  │   /            ──►  Frontend Container (React)                        │   │
│  │   /api/*       ──►  Backend Container (FastAPI)                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│  │    Frontend      │  │    Backend       │  │   PostgreSQL     │           │
│  │    Container     │  │    Container     │  │   Container      │           │
│  │                  │  │                  │  │                  │           │
│  │  - React build   │  │  - FastAPI app   │  │  - Data volume   │           │
│  │  - Static files  │  │  - Uvicorn       │  │  - Port 5432     │           │
│  │  - Port 3000     │  │  - Port 8000     │  │                  │           │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Keycloak (Optional)                            │   │
│  │                          - Port 8080                                  │   │
│  │                          - OIDC Provider                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Backend | PostgreSQL connection string |
| `SECRET_KEY` | Backend | JWT signing key |
| `CORS_ORIGINS` | Backend | Allowed CORS origins |
| `KEYCLOAK_SERVER_URL` | Backend | Keycloak server URL |
| `KEYCLOAK_REALM` | Backend | Keycloak realm name |
| `KEYCLOAK_CLIENT_ID` | Backend | Keycloak client ID |
| `KEYCLOAK_CLIENT_SECRET` | Backend | Keycloak client secret |
| `VITE_API_BASE_URL` | Frontend | Backend API URL (dev only) |
| `NODE_ID` | Autoscaler | Registered node ID |
| `API_KEY` | Autoscaler | Node API key |
| `BACKEND_URL` | Autoscaler | Central backend URL |
