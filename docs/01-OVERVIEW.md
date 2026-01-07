# Oracle Cloud Autoscaling Management System

## Executive Summary

The Oracle Cloud Autoscaling Management System is a distributed infrastructure management platform designed to automatically scale Oracle Cloud Infrastructure (OCI) instance pools based on real-time metrics. It provides centralized visibility and control over multiple autoscaling nodes deployed across different regions.

---

## 1. System Purpose

### Primary Goals

1. **Automated Scaling**: Dynamically adjust instance pool sizes based on CPU and memory utilization thresholds
2. **Centralized Management**: Provide a single dashboard to monitor and configure all autoscaling nodes
3. **Cost Optimization**: Prevent over-provisioning by scaling down during low utilization periods
4. **High Availability**: Ensure applications can handle traffic spikes by scaling up when needed
5. **Scheduled Scaling**: Support time-based scaling for predictable workload patterns

### Key Value Propositions

| Capability | Description |
|------------|-------------|
| **Multi-Region Support** | Manage instance pools across different OCI regions from a single interface |
| **Dual Metrics Sources** | Collect metrics from OCI native monitoring or Prometheus |
| **Real-Time Monitoring** | Track CPU, memory, and instance counts with live updates |
| **Enterprise Security** | Role-based access control with SSO support via Keycloak |
| **Audit Compliance** | Comprehensive logging of all user and system actions |

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CENTRAL MANAGEMENT LAYER                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   React + Vite  │◄──►│   FastAPI       │◄──►│   PostgreSQL    │         │
│  │   Frontend UI   │    │   Backend API   │    │   Database      │         │
│  └─────────────────┘    └────────┬────────┘    └─────────────────┘         │
│                                  │                                          │
│                           ┌──────┴──────┐                                   │
│                           │  Keycloak   │ (Optional SSO)                    │
│                           └─────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
        ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
        │ Autoscaler    │ │ Autoscaler    │ │ Autoscaler    │
        │ Node (US)     │ │ Node (EU)     │ │ Node (APAC)   │
        │               │ │               │ │               │
        │ ┌───────────┐ │ │ ┌───────────┐ │ │ ┌───────────┐ │
        │ │ OCI SDK   │ │ │ │ OCI SDK   │ │ │ │ OCI SDK   │ │
        │ └───────────┘ │ │ └───────────┘ │ │ └───────────┘ │
        └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
                │                 │                 │
                ▼                 ▼                 ▼
        ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
        │ OCI Instance  │ │ OCI Instance  │ │ OCI Instance  │
        │ Pool 1        │ │ Pool 2        │ │ Pool 3        │
        └───────────────┘ └───────────────┘ └───────────────┘
```

---

## 3. Component Overview

### 3.1 Central Management Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React + TypeScript + Tailwind CSS | User interface for monitoring and configuration |
| **Backend API** | FastAPI (Python) | RESTful API for all system operations |
| **Database** | PostgreSQL | Persistent storage for configurations, metrics, and logs |
| **Auth Provider** | Keycloak (optional) | Enterprise SSO and identity management |

### 3.2 Distributed Autoscaler Nodes

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Autoscaler Service** | Python | Core scaling logic and orchestration |
| **OCI SDK** | oracle-oci-python-sdk | Interface with Oracle Cloud APIs |
| **Metrics Collector** | OCI Monitoring / Prometheus | Gather CPU/memory utilization data |
| **Scheduler** | Python threading | Time-based scaling operations |
| **Heartbeat Service** | HTTP client | Report status to central backend |

---

## 4. User Roles

| Role | Permissions |
|------|-------------|
| **USER** | View-only access to dashboards and metrics (no Configure/View buttons on pool cards) |
| **DEVOPS** | Full access to nodes, pools, configurations, and schedules |
| **ADMIN** | All DEVOPS permissions + user management + audit log access + role override for Keycloak users |

### Role Management Features

- **Keycloak Role Mapping**: SSO users are automatically assigned roles based on Keycloak group memberships
- **Role Override**: Administrators can manually override roles for Keycloak users when SSO mappings are insufficient
- **Role Reset**: Overridden roles can be reset to allow Keycloak mappings to take precedence again

---

## 5. Key Features

### Monitoring & Observability
- Real-time instance pool status dashboard with role-based action visibility
- CPU and memory utilization tracking
- Peak instances calculation using hourly-bucketed algorithm (always >= current running)
- Node health status with heartbeat detection
- Node lifecycle logging (online/offline transitions)

### Configuration Management
- YAML-based pool configuration
- Remote configuration sync between nodes and backend
- Configuration versioning with hash-based change detection

### Scaling Operations
- Metric-based autoscaling (CPU/RAM thresholds)
- Scheduled scaling for predictable patterns
- Minimum and maximum instance limits
- Cooldown periods to prevent thrashing

### Security & Compliance
- Role-based access control (RBAC)
- API key authentication for nodes
- JWT-based user authentication
- Enterprise audit logging
- SSO integration via Keycloak

---

## 6. Deployment Options

### Development Environment
- Local Docker Compose setup
- SQLite or PostgreSQL database
- No authentication required

### Production Environment
- Containerized deployment (Docker)
- PostgreSQL with persistent storage
- Nginx reverse proxy with SSL termination
- Keycloak for enterprise SSO
- Multiple autoscaler nodes in different regions

---

## 7. Technology Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **React Query** - Server state management
- **React Router** - Navigation

### Backend
- **FastAPI** - API framework
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **python-jose** - JWT handling
- **passlib** - Password hashing

### Infrastructure
- **Docker** - Containerization
- **Nginx** - Reverse proxy
- **PostgreSQL** - Database
- **Keycloak** - Identity provider

---

## 8. Documentation Index

| Document | Description |
|----------|-------------|
| [System Architecture](./02-SYSTEM-ARCHITECTURE.md) | Detailed component architecture and interactions |
| [Database Schema](./03-DATABASE-SCHEMA.md) | Complete database structure and relationships |
| [Workflow Engine](./04-WORKFLOW-ENGINE.md) | Autoscaling logic and decision flow |
| [Integration Contract](./05-INTEGRATION-CONTRACT.md) | API specifications and contracts |
| [UI Wireframes](./06-UI-WIREFRAMES.md) | User interface design and layouts |
| [Workflow Diagrams](./07-WORKFLOW-DIAGRAMS.md) | Visual process flows |
