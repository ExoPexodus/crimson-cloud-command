# Database Schema

## 1. Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATABASE SCHEMA OVERVIEW                              │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────┐
                    │    users    │
                    ├─────────────┤
                    │ id (PK)     │
                    │ email       │
                    │ full_name   │
                    │ role        │◄────────────┐
                    │ auth_provider│             │
                    │ keycloak_id │             │
                    └─────────────┘             │
                                                │
        ┌───────────────────────────────────────┼───────────────────┐
        │                                       │                   │
        ▼                                       │                   ▼
┌─────────────────┐                             │          ┌────────────────┐
│   audit_logs    │                             │          │ node_lifecycle │
├─────────────────┤                             │          │     _logs      │
│ id (PK)         │                             │          ├────────────────┤
│ user_id (FK)    │─────────────────────────────┘          │ id (PK)        │
│ user_email      │                                        │ node_id (FK)   │───┐
│ action          │                                        │ event_type     │   │
│ category        │                                        │ previous_status│   │
│ resource_type   │                                        │ new_status     │   │
│ description     │                                        │ reason         │   │
│ timestamp       │                                        │ timestamp      │   │
└─────────────────┘                                        └────────────────┘   │
                                                                                │
                            ┌─────────────────┐                                 │
                            │      nodes      │◄────────────────────────────────┘
                            ├─────────────────┤
                            │ id (PK)         │
           ┌───────────────►│ name            │◄──────────────────────┐
           │                │ region          │                       │
           │                │ ip_address      │                       │
           │                │ status          │                       │
           │                │ api_key_hash    │                       │
           │                │ last_heartbeat  │                       │
           │                └─────────────────┘                       │
           │                        │                                 │
           │           ┌────────────┼────────────┬──────────────┐     │
           │           │            │            │              │     │
           │           ▼            ▼            ▼              ▼     │
           │    ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┴───┐
           │    │   pools   │ │ schedules│ │ metrics  │ │ node_configurations│
           │    ├───────────┤ ├──────────┤ ├──────────┤ ├─────────────────┤
           │    │ id (PK)   │ │ id (PK)  │ │ id (PK)  │ │ id (PK)         │
           │    │ node_id   │ │ node_id  │ │ node_id  │ │ node_id (FK)    │
           │    │ oracle_id │ │ name     │ │ pool_id  │ │ yaml_config     │
           │    │ name      │ │ start    │ │ type     │ │ config_hash     │
           │    │ min/max   │ │ end      │ │ value    │ │ is_active       │
           │    │ status    │ │ target   │ │ timestamp│ └─────────────────┘
           │    └───────────┘ └──────────┘ └──────────┘
           │           │                        │
           │           │                        │
           │           ▼                        │
           │    ┌─────────────────┐             │
           │    │ pool_analytics  │             │
           │    ├─────────────────┤             │
           │    │ id (PK)         │             │
           │    │ pool_id (FK)    │─────────────┘
           │    │ node_id (FK)    │─────────────┘
           │    │ oracle_pool_id  │
           │    │ current/active  │
           │    │ avg_cpu/memory  │
           │    │ timestamp       │
           │    └─────────────────┘
           │
           │    ┌─────────────────┐
           │    │ node_heartbeats │
           │    ├─────────────────┤
           │    │ id (PK)         │
           └────│ node_id (FK)    │
                │ config_hash     │
                │ status          │
                │ metrics_data    │
                │ timestamp       │
                └─────────────────┘

                ┌─────────────────┐
                │system_analytics │
                ├─────────────────┤
                │ id (PK)         │
                │ timestamp       │
                │ total_pools     │
                │ total_instances │
                │ avg_cpu/memory  │
                │ active_nodes    │
                └─────────────────┘
```

---

## 2. Table Definitions

### 2.1 Users Table

Stores user accounts for authentication and authorization.

```sql
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),           -- NULL for Keycloak users
    full_name       VARCHAR(255) NOT NULL,
    role            user_role DEFAULT 'USER',
    auth_provider   auth_provider DEFAULT 'local',
    keycloak_user_id VARCHAR(255) UNIQUE,
    role_override   BOOLEAN DEFAULT FALSE,  -- When TRUE, ignores Keycloak role mapping
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Enums
CREATE TYPE user_role AS ENUM ('USER', 'DEVOPS', 'ADMIN');
CREATE TYPE auth_provider AS ENUM ('local', 'keycloak');
```

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `email` | VARCHAR(255) | Unique user email |
| `hashed_password` | VARCHAR(255) | bcrypt hashed password (NULL for SSO users) |
| `full_name` | VARCHAR(255) | Display name |
| `role` | ENUM | USER, DEVOPS, or ADMIN |
| `auth_provider` | ENUM | local or keycloak |
| `keycloak_user_id` | VARCHAR(255) | Keycloak subject ID |
| `role_override` | BOOLEAN | When TRUE, admin-assigned role persists instead of Keycloak mapping |
| `is_active` | BOOLEAN | Account active status |
| `created_at` | TIMESTAMP | Account creation time |

---

### 2.2 Nodes Table

Stores autoscaler node registrations.

```sql
CREATE TABLE nodes (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    region          VARCHAR(100) NOT NULL,
    ip_address      VARCHAR(45),
    description     TEXT,
    status          node_status DEFAULT 'INACTIVE',
    api_key_hash    VARCHAR(64) UNIQUE,     -- SHA-256 hash of API key
    last_heartbeat  TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TYPE node_status AS ENUM ('ACTIVE', 'INACTIVE', 'ERROR', 'OFFLINE');
```

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `name` | VARCHAR(255) | Node display name |
| `region` | VARCHAR(100) | OCI region identifier |
| `ip_address` | VARCHAR(45) | Node IP address |
| `description` | TEXT | Optional description |
| `status` | ENUM | ACTIVE, INACTIVE, ERROR, OFFLINE |
| `api_key_hash` | VARCHAR(64) | Hashed API key for authentication |
| `last_heartbeat` | TIMESTAMP | Last successful heartbeat |
| `created_at` | TIMESTAMP | Node registration time |

---

### 2.3 Pools Table

Stores instance pool configurations managed by nodes.

```sql
CREATE TABLE pools (
    id               SERIAL PRIMARY KEY,
    node_id          INTEGER REFERENCES nodes(id) NOT NULL,
    oracle_pool_id   VARCHAR(255) UNIQUE NOT NULL,
    name             VARCHAR(255) NOT NULL,
    region           VARCHAR(100) NOT NULL,
    min_instances    INTEGER DEFAULT 1,
    max_instances    INTEGER DEFAULT 10,
    current_instances INTEGER DEFAULT 1,
    status           pool_status DEFAULT 'healthy',
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE TYPE pool_status AS ENUM ('healthy', 'warning', 'error');
```

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `node_id` | INTEGER | Foreign key to nodes |
| `oracle_pool_id` | VARCHAR(255) | OCI instance pool OCID |
| `name` | VARCHAR(255) | Pool display name |
| `region` | VARCHAR(100) | OCI region |
| `min_instances` | INTEGER | Minimum scaling limit |
| `max_instances` | INTEGER | Maximum scaling limit |
| `current_instances` | INTEGER | Current instance count |
| `status` | ENUM | healthy, warning, error |
| `created_at` | TIMESTAMP | Pool creation time |

---

### 2.4 Metrics Table

Stores time-series metrics data for nodes and pools.

```sql
CREATE TABLE metrics (
    id          SERIAL PRIMARY KEY,
    node_id     INTEGER REFERENCES nodes(id) NOT NULL,
    pool_id     INTEGER REFERENCES pools(id),
    metric_type VARCHAR(100) NOT NULL,
    value       FLOAT NOT NULL,
    unit        VARCHAR(50) NOT NULL,
    timestamp   TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_metrics_node_timestamp ON metrics(node_id, timestamp);
CREATE INDEX idx_metrics_pool_timestamp ON metrics(pool_id, timestamp);
```

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `node_id` | INTEGER | Foreign key to nodes |
| `pool_id` | INTEGER | Foreign key to pools (optional) |
| `metric_type` | VARCHAR(100) | cpu, memory, instances, etc. |
| `value` | FLOAT | Metric value |
| `unit` | VARCHAR(50) | percent, count, bytes, etc. |
| `timestamp` | TIMESTAMP | Metric collection time |

---

### 2.5 Schedules Table

Stores scheduled scaling configurations.

```sql
CREATE TABLE schedules (
    id               SERIAL PRIMARY KEY,
    node_id          INTEGER REFERENCES nodes(id) NOT NULL,
    name             VARCHAR(255) NOT NULL,
    start_time       VARCHAR(5) NOT NULL,    -- HH:MM format
    end_time         VARCHAR(5) NOT NULL,    -- HH:MM format
    target_instances INTEGER NOT NULL,
    is_active        BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMP DEFAULT NOW()
);
```

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `node_id` | INTEGER | Foreign key to nodes |
| `name` | VARCHAR(255) | Schedule name |
| `start_time` | VARCHAR(5) | Start time (HH:MM) |
| `end_time` | VARCHAR(5) | End time (HH:MM) |
| `target_instances` | INTEGER | Target instance count during schedule |
| `is_active` | BOOLEAN | Schedule enabled status |
| `created_at` | TIMESTAMP | Schedule creation time |

---

### 2.6 Audit Logs Table

Stores comprehensive audit trail of all actions.

```sql
CREATE TABLE audit_logs (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_email      VARCHAR(255),
    user_role       VARCHAR(50),
    action          VARCHAR(100) NOT NULL,
    category        VARCHAR(50) NOT NULL,
    resource_type   VARCHAR(100),
    resource_id     VARCHAR(255),
    resource_name   VARCHAR(255),
    description     TEXT,
    details         TEXT,                    -- JSON data
    ip_address      VARCHAR(45),
    user_agent      TEXT,
    status          VARCHAR(20) DEFAULT 'SUCCESS',
    error_message   TEXT,
    timestamp       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_category ON audit_logs(category);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
```

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `user_id` | INTEGER | Acting user (nullable) |
| `user_email` | VARCHAR(255) | User email at time of action |
| `user_role` | VARCHAR(50) | User role at time of action |
| `action` | VARCHAR(100) | Action identifier (e.g., NODE_CREATED) |
| `category` | VARCHAR(50) | AUTH, NODE, POOL, USER, CONFIG, SYSTEM |
| `resource_type` | VARCHAR(100) | Type of affected resource |
| `resource_id` | VARCHAR(255) | ID of affected resource |
| `resource_name` | VARCHAR(255) | Name of affected resource |
| `description` | TEXT | Human-readable description |
| `details` | TEXT | JSON with additional data |
| `ip_address` | VARCHAR(45) | Client IP address |
| `user_agent` | TEXT | Client user agent |
| `status` | VARCHAR(20) | SUCCESS or FAILURE |
| `error_message` | TEXT | Error details if failed |
| `timestamp` | TIMESTAMP | Action timestamp |

---

### 2.7 Node Configuration Table

Stores YAML configurations for nodes.

```sql
CREATE TABLE node_configurations (
    id          SERIAL PRIMARY KEY,
    node_id     INTEGER REFERENCES nodes(id) NOT NULL,
    yaml_config TEXT NOT NULL,
    config_hash VARCHAR(64) NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);
```

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `node_id` | INTEGER | Foreign key to nodes |
| `yaml_config` | TEXT | Full YAML configuration |
| `config_hash` | VARCHAR(64) | SHA-256 hash for change detection |
| `is_active` | BOOLEAN | Current active configuration |
| `created_at` | TIMESTAMP | Configuration version timestamp |

---

### 2.8 Node Heartbeat Table

Stores heartbeat history from nodes.

```sql
CREATE TABLE node_heartbeats (
    id           SERIAL PRIMARY KEY,
    node_id      INTEGER REFERENCES nodes(id) NOT NULL,
    config_hash  VARCHAR(64),
    status       VARCHAR(50) NOT NULL,
    error_message TEXT,
    metrics_data TEXT,                       -- JSON data
    timestamp    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_heartbeat_node_time ON node_heartbeats(node_id, timestamp);
```

---

### 2.9 Node Lifecycle Logs Table

Tracks node status transitions.

```sql
CREATE TABLE node_lifecycle_logs (
    id              SERIAL PRIMARY KEY,
    node_id         INTEGER REFERENCES nodes(id) NOT NULL,
    event_type      VARCHAR(50) NOT NULL,    -- WENT_OFFLINE, CAME_ONLINE
    previous_status VARCHAR(50),
    new_status      VARCHAR(50) NOT NULL,
    reason          TEXT,
    triggered_by    VARCHAR(100),            -- heartbeat, manual, system
    extra_data      TEXT,                    -- JSON metadata
    timestamp       TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lifecycle_node ON node_lifecycle_logs(node_id);
CREATE INDEX idx_lifecycle_time ON node_lifecycle_logs(timestamp);
```

---

### 2.10 Pool Analytics Table

Stores detailed pool performance data.

```sql
CREATE TABLE pool_analytics (
    id                     SERIAL PRIMARY KEY,
    pool_id                INTEGER REFERENCES pools(id) NOT NULL,
    node_id                INTEGER REFERENCES nodes(id) NOT NULL,
    oracle_pool_id         VARCHAR(255) NOT NULL,
    timestamp              TIMESTAMP DEFAULT NOW(),
    current_instances      INTEGER NOT NULL,
    active_instances       INTEGER NOT NULL,
    avg_cpu_utilization    FLOAT NOT NULL,
    avg_memory_utilization FLOAT NOT NULL,
    max_cpu_utilization    FLOAT,
    max_memory_utilization FLOAT,
    pool_status            VARCHAR(50) DEFAULT 'healthy',
    is_active              BOOLEAN DEFAULT TRUE,
    scaling_event          VARCHAR(100),
    scaling_reason         TEXT
);

CREATE INDEX idx_pool_analytics_time ON pool_analytics(timestamp);
CREATE INDEX idx_pool_analytics_pool ON pool_analytics(pool_id);
```

---

### 2.11 System Analytics Table

Stores aggregated system-wide metrics.

```sql
CREATE TABLE system_analytics (
    id                    SERIAL PRIMARY KEY,
    timestamp             TIMESTAMP DEFAULT NOW(),
    total_active_pools    INTEGER DEFAULT 0,
    total_current_instances INTEGER DEFAULT 0,
    total_active_instances INTEGER DEFAULT 0,
    avg_system_cpu        FLOAT DEFAULT 0.0,
    avg_system_memory     FLOAT DEFAULT 0.0,
    max_system_cpu        FLOAT DEFAULT 0.0,
    max_system_memory     FLOAT DEFAULT 0.0,
    peak_instances_24h    INTEGER DEFAULT 0,
    max_active_pools_24h  INTEGER DEFAULT 0,
    active_nodes          INTEGER DEFAULT 0
);
```

---

## 3. Relationships Summary

| Parent Table | Child Table | Relationship | On Delete |
|--------------|-------------|--------------|-----------|
| users | audit_logs | One-to-Many | SET NULL |
| nodes | pools | One-to-Many | CASCADE |
| nodes | metrics | One-to-Many | CASCADE |
| nodes | schedules | One-to-Many | CASCADE |
| nodes | node_configurations | One-to-Many | CASCADE |
| nodes | node_heartbeats | One-to-Many | CASCADE |
| nodes | node_lifecycle_logs | One-to-Many | CASCADE |
| nodes | pool_analytics | One-to-Many | CASCADE |
| pools | metrics | One-to-Many | CASCADE |
| pools | pool_analytics | One-to-Many | CASCADE |
