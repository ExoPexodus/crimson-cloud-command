# Integration Contract / API Specifications

## 1. API Overview

| Base URL | Description |
|----------|-------------|
| `/api` | Production (proxied through Nginx) |
| `http://localhost:8000` | Development |

### Authentication

All authenticated endpoints require:
```
Authorization: Bearer <JWT_TOKEN>
```

Node endpoints require:
```
X-API-Key: <NODE_API_KEY>
```

---

## 2. Authentication Endpoints

### 2.1 Local Login

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

email=user@example.com&password=secret123
```

**Response: 200 OK**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "DEVOPS",
    "auth_provider": "local",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error: 401 Unauthorized**
```json
{
  "detail": "Incorrect email or password"
}
```

---

### 2.2 Keycloak Login

```http
POST /auth/keycloak/login
Content-Type: application/json

{
  "code": "authorization_code_from_keycloak",
  "redirect_uri": "http://localhost:3000/auth/callback"
}
```

**Response: 200 OK**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "email": "user@company.com",
    "full_name": "Jane Smith",
    "role": "ADMIN",
    "auth_provider": "keycloak",
    "keycloak_user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "is_active": true
  },
  "keycloak_data": {
    "user_info": {...},
    "groups": ["admins", "devops"]
  },
  "roles": ["admin", "devops-team"],
  "groups": ["/admins", "/devops"]
}
```

---

### 2.3 User Registration (Admin Only)

```http
POST /auth/register
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "email": "newuser@example.com",
  "password": "securePassword123",
  "full_name": "New User"
}
```

**Response: 200 OK**
```json
{
  "id": 3,
  "email": "newuser@example.com",
  "full_name": "New User",
  "role": "USER",
  "auth_provider": "local",
  "is_active": true,
  "created_at": "2024-01-15T14:00:00Z"
}
```

---

### 2.4 Update Profile

```http
PUT /auth/profile
Content-Type: application/json
Authorization: Bearer <token>

{
  "full_name": "John Updated",
  "email": "newemail@example.com",
  "current_password": "oldPassword123",
  "new_password": "newSecurePassword456"
}
```

**Response: 200 OK**
```json
{
  "id": 1,
  "email": "newemail@example.com",
  "full_name": "John Updated",
  "role": "DEVOPS"
}
```

---

## 3. Node Management Endpoints

### 3.1 Register Node

```http
POST /nodes/register
Content-Type: application/json

{
  "name": "autoscaler-us-east",
  "region": "us-ashburn-1",
  "ip_address": "10.0.1.100",
  "description": "US East autoscaling node"
}
```

**Response: 200 OK**
```json
{
  "node_id": 1,
  "api_key": "ask_abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
  "name": "autoscaler-us-east",
  "region": "us-ashburn-1"
}
```

---

### 3.2 List Nodes

```http
GET /nodes
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "name": "autoscaler-us-east",
    "region": "us-ashburn-1",
    "ip_address": "10.0.1.100",
    "description": "US East autoscaling node",
    "status": "ACTIVE",
    "has_api_key": true,
    "last_heartbeat": "2024-01-15T14:30:00Z",
    "created_at": "2024-01-10T09:00:00Z",
    "pools": [
      {
        "id": 1,
        "oracle_pool_id": "ocid1.instancepool.oc1...",
        "name": "web-servers",
        "status": "healthy",
        "current_instances": 3
      }
    ]
  }
]
```

---

### 3.3 Get Node Details

```http
GET /nodes/{node_id}
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "id": 1,
  "name": "autoscaler-us-east",
  "region": "us-ashburn-1",
  "ip_address": "10.0.1.100",
  "description": "US East autoscaling node",
  "status": "ACTIVE",
  "has_api_key": true,
  "last_heartbeat": "2024-01-15T14:30:00Z",
  "created_at": "2024-01-10T09:00:00Z"
}
```

---

### 3.4 Update Node

```http
PUT /nodes/{node_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "autoscaler-us-east-updated",
  "description": "Updated description"
}
```

---

### 3.5 Delete Node

```http
DELETE /nodes/{node_id}
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "message": "Node deleted successfully"
}
```

---

### 3.6 Get Node Configuration

```http
GET /nodes/{node_id}/config
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "id": 1,
  "node_id": 1,
  "yaml_config": "pools:\n  - instance_pool_id: \"ocid1...\"\n    ...",
  "config_hash": "a1b2c3d4e5f6...",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

### 3.7 Update Node Configuration

```http
PUT /nodes/{node_id}/config
Content-Type: application/json
Authorization: Bearer <token>

{
  "yaml_config": "pools:\n  - instance_pool_id: \"ocid1.instancepool.oc1...\"\n    name: \"web-servers\"\n    region: \"us-ashburn-1\"\n    monitoring_method: \"oci\"\n    cpu_threshold: 80\n    ram_threshold: 80\n    scaling_limits:\n      min: 2\n      max: 10\n"
}
```

**Response: 200 OK**
```json
{
  "id": 2,
  "node_id": 1,
  "yaml_config": "...",
  "config_hash": "f6e5d4c3b2a1...",
  "is_active": true,
  "created_at": "2024-01-15T14:45:00Z"
}
```

---

### 3.8 Get Node Analytics

```http
GET /nodes/{node_id}/analytics
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "avg_cpu_utilization": 45.5,
  "avg_memory_utilization": 62.3,
  "current_instances": 5,
  "max_instances": 10
}
```

---

### 3.9 Get Node Lifecycle Logs

```http
GET /nodes/lifecycle-logs?node_id=1&event_type=WENT_OFFLINE&limit=50
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "node_id": 1,
    "node_name": "autoscaler-us-east",
    "event_type": "WENT_OFFLINE",
    "previous_status": "ACTIVE",
    "new_status": "OFFLINE",
    "reason": "Heartbeat timeout after 5 minutes",
    "triggered_by": "heartbeat",
    "extra_data": null,
    "timestamp": "2024-01-15T14:35:00Z"
  }
]
```

---

## 4. Heartbeat Endpoint (Node Authentication)

### 4.1 Send Heartbeat

```http
POST /heartbeat
Content-Type: application/json
X-API-Key: <node_api_key>

{
  "node_id": 1,
  "status": "active",
  "config_hash": "a1b2c3d4e5f6...",
  "pool_analytics": [
    {
      "oracle_pool_id": "ocid1.instancepool.oc1...",
      "current_instances": 3,
      "active_instances": 3,
      "avg_cpu_utilization": 45.5,
      "avg_memory_utilization": 62.3,
      "max_cpu_utilization": 78.2,
      "max_memory_utilization": 71.4,
      "pool_status": "healthy",
      "is_active": true,
      "scaling_event": null,
      "scaling_reason": null
    }
  ]
}
```

**Response: 200 OK**
```json
{
  "status": "ok",
  "config_update_needed": false,
  "timestamp": "2024-01-15T14:30:00Z"
}
```

**Response: 200 OK (Config Update Needed)**
```json
{
  "status": "ok",
  "config_update_needed": true,
  "timestamp": "2024-01-15T14:30:00Z"
}
```

---

## 5. Analytics Endpoints

### 5.1 Get System Analytics

```http
GET /analytics/system
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
{
  "total_active_pools": 5,
  "total_current_instances": 23,
  "peak_instances_24h": 35,
  "max_active_pools_24h": 6,
  "avg_system_cpu": 52.4,
  "avg_system_memory": 68.7,
  "active_nodes": 3,
  "last_updated": "2024-01-15T14:30:00Z"
}
```

---

### 5.2 Get Pool Analytics

```http
GET /analytics/pools?node_id=1&hours=24
Authorization: Bearer <token>
```

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "pool_id": 1,
    "node_id": 1,
    "oracle_pool_id": "ocid1.instancepool.oc1...",
    "timestamp": "2024-01-15T14:00:00Z",
    "current_instances": 3,
    "active_instances": 3,
    "avg_cpu_utilization": 45.5,
    "avg_memory_utilization": 62.3,
    "max_cpu_utilization": 78.2,
    "max_memory_utilization": 71.4,
    "pool_status": "healthy",
    "is_active": true,
    "scaling_event": "SCALE_UP",
    "scaling_reason": "CPU threshold exceeded"
  }
]
```

---

## 6. Admin Endpoints

### 6.1 List All Users

```http
GET /admin/users
Authorization: Bearer <admin_token>
```

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "email": "admin@example.com",
    "full_name": "Admin User",
    "role": "ADMIN",
    "auth_provider": "local",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "email": "devops@example.com",
    "full_name": "DevOps User",
    "role": "DEVOPS",
    "auth_provider": "keycloak",
    "is_active": true,
    "created_at": "2024-01-05T10:00:00Z"
  }
]
```

---

### 6.2 Update User Role

```http
PUT /admin/users/{user_id}/role
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "role": "DEVOPS"
}
```

**Response: 200 OK**
```json
{
  "id": 2,
  "email": "user@example.com",
  "full_name": "User Name",
  "role": "DEVOPS"
}
```

---

### 6.3 Get Audit Logs

```http
GET /admin/audit-logs?category=AUTH&status=SUCCESS&limit=100&offset=0
Authorization: Bearer <admin_token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| category | string | AUTH, NODE, POOL, USER, CONFIG, SYSTEM |
| action | string | Specific action filter |
| user_id | integer | Filter by user |
| resource_type | string | Filter by resource type |
| status | string | SUCCESS or FAILURE |
| start_date | string | ISO date (YYYY-MM-DD) |
| end_date | string | ISO date (YYYY-MM-DD) |
| search | string | Search in descriptions |
| limit | integer | Max results (default: 100) |
| offset | integer | Pagination offset |

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "user_email": "admin@example.com",
    "user_role": "ADMIN",
    "action": "LOGIN_SUCCESS",
    "category": "AUTH",
    "resource_type": null,
    "resource_id": null,
    "resource_name": null,
    "description": "User admin@example.com logged in successfully",
    "details": "{\"method\": \"local\"}",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "status": "SUCCESS",
    "error_message": null,
    "timestamp": "2024-01-15T10:30:00Z"
  }
]
```

---

### 6.4 Get Audit Log Summary

```http
GET /admin/audit-logs/summary?hours=24
Authorization: Bearer <admin_token>
```

**Response: 200 OK**
```json
{
  "period_hours": 24,
  "total_events": 156,
  "failure_count": 3,
  "category_counts": {
    "AUTH": 45,
    "NODE": 67,
    "POOL": 34,
    "USER": 5,
    "CONFIG": 3,
    "SYSTEM": 2
  },
  "status_counts": {
    "SUCCESS": 153,
    "FAILURE": 3
  },
  "recent_failures": [
    {
      "id": 150,
      "action": "LOGIN_FAILURE",
      "user_email": "unknown@example.com",
      "error_message": "Invalid credentials",
      "timestamp": "2024-01-15T14:20:00Z"
    }
  ]
}
```

---

### 6.5 Get Audit Categories

```http
GET /admin/audit-logs/categories
Authorization: Bearer <admin_token>
```

**Response: 200 OK**
```json
{
  "categories": [
    { "value": "AUTH", "label": "Authentication" },
    { "value": "NODE", "label": "Node Management" },
    { "value": "POOL", "label": "Pool Operations" },
    { "value": "USER", "label": "User Management" },
    { "value": "CONFIG", "label": "Configuration" },
    { "value": "SYSTEM", "label": "System Events" }
  ],
  "actions": [
    { "value": "LOGIN_SUCCESS", "label": "Login Success", "category": "AUTH" },
    { "value": "LOGIN_FAILURE", "label": "Login Failure", "category": "AUTH" },
    { "value": "NODE_CREATED", "label": "Node Created", "category": "NODE" },
    { "value": "NODE_DELETED", "label": "Node Deleted", "category": "NODE" }
  ],
  "statuses": [
    { "value": "SUCCESS", "label": "Success" },
    { "value": "FAILURE", "label": "Failure" }
  ]
}
```

---

## 7. Health Check

```http
GET /health
```

**Response: 200 OK**
```json
{
  "status": "healthy",
  "message": "Oracle Cloud Autoscaling Management API is running"
}
```

---

## 8. Public Configuration

```http
GET /config
```

**Response: 200 OK**
```json
{
  "keycloak_enabled": true,
  "keycloak_url": "https://keycloak.example.com",
  "keycloak_realm": "autoscaler",
  "keycloak_client_id": "autoscaler-ui",
  "api_base_url": "https://api.example.com"
}
```

---

## 9. Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |

---

## 10. Rate Limiting

| Endpoint Type | Limit |
|---------------|-------|
| Authentication | 10 requests/minute |
| Heartbeat | 2 requests/minute per node |
| API (authenticated) | 100 requests/minute |
| API (admin) | 200 requests/minute |
