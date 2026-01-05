// API Configuration
// In production, use relative /api path (proxied by nginx)
// In development, use direct backend URL
const isDevelopment = import.meta.env.DEV;
const API_BASE_URL = isDevelopment 
  ? (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000')
  : '/api';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

interface SystemAnalytics {
  total_active_pools: number;
  total_current_instances: number;
  peak_instances_24h: number;
  max_active_pools_24h: number;
  avg_system_cpu: number;
  avg_system_memory: number;
  active_nodes: number;
  last_updated: string;
}

interface PoolAnalytics {
  id: number;
  pool_id: number;
  node_id: number;
  oracle_pool_id: string;
  timestamp: string;
  current_instances: number;
  active_instances: number;
  avg_cpu_utilization: number;
  avg_memory_utilization: number;
  max_cpu_utilization: number | null;
  max_memory_utilization: number | null;
  pool_status: string;
  is_active: boolean;
  scaling_event: string | null;
  scaling_reason: string | null;
  node_name: string | null;
}

interface NodeRegisterRequest {
  name: string;
  region: string;
  ip_address?: string;
  description?: string;
}

interface NodeRegisterResponse {
  node_id: number;
  api_key: string;
  name: string;
  region: string;
}

interface NodeAnalytics {
  avg_cpu_utilization: number;
  avg_memory_utilization: number;
  current_instances: number;
  max_instances: number;
}

interface NodeLifecycleLog {
  id: number;
  node_id: number;
  node_name: string | null;
  event_type: string;
  previous_status: string | null;
  new_status: string;
  reason: string | null;
  triggered_by: string | null;
  extra_data: string | null;
  timestamp: string;
}

interface AuditLog {
  id: number;
  user_id: number | null;
  user_email: string | null;
  user_role: string | null;
  action: string;
  category: string;
  resource_type: string | null;
  resource_id: string | null;
  resource_name: string | null;
  description: string | null;
  details: string | null;
  ip_address: string | null;
  user_agent: string | null;
  status: string;
  error_message: string | null;
  timestamp: string;
}

interface AuditLogSummary {
  period_hours: number;
  category_counts: Record<string, number>;
  status_counts: Record<string, number>;
  total_events: number;
  failure_count: number;
  recent_failures: Array<{
    id: number;
    action: string;
    user_email: string | null;
    error_message: string | null;
    timestamp: string | null;
  }>;
}

interface AuditLogFilters {
  category?: string;
  action?: string;
  user_id?: number;
  resource_type?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

interface PublicConfig {
  keycloak_enabled: boolean;
  keycloak_url: string;
  keycloak_realm: string;
  keycloak_client_id: string;
  api_base_url?: string;
}

class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('access_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    console.log(`🌐 API Request: ${options.method || 'GET'} ${url}`);
    console.log(`🔑 Token available: ${this.token ? 'YES' : 'NO'}`);
    if (this.token) {
      console.log(`🔑 Token (first 20 chars): ${this.token.substring(0, 20)}...`);
    }
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
        ...options.headers,
      },
      ...options,
    };
    
    if (this.token) {
      console.log(`📤 Authorization header set: Bearer ${this.token.substring(0, 20)}...`);
    }
    
    console.log(`📋 Request headers:`, config.headers);
    console.log(`📡 Making fetch request to: ${url}`);

    try {
      const response = await fetch(url, config);
      
      console.log(`📨 Response status: ${response.status} ${response.statusText}`);
      console.log(`📨 Response headers:`, Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ API Error ${response.status}:`, errorText);
        return { error: `HTTP ${response.status}: ${errorText}` };
      }

      const data = await response.json();
      console.log(`✅ API Success:`, data);
      return { data };
    } catch (error) {
      console.error('❌ API request failed:', error);
      return { error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  // Authentication
  async login(email: string, password: string): Promise<ApiResponse<{ access_token: string; token_type: string; user: any }>> {
    const formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);
    
    const result = await this.request<{ access_token: string; token_type: string; user: any }>('/auth/login', {
      method: 'POST',
      body: formData,
      headers: {}, // Remove Content-Type to let browser set it for FormData
    });
    
    if (result.data) {
      this.token = result.data.access_token;
      localStorage.setItem('access_token', this.token);
    }
    
    return result;
  }

  async loginWithKeycloak(code: string, redirectUri: string): Promise<ApiResponse<{ access_token: string; token_type: string; user: any }>> {
    const result = await this.request<{ access_token: string; token_type: string; user: any }>('/auth/keycloak/login', {
      method: 'POST',
      body: JSON.stringify({ code, redirect_uri: redirectUri }),
    });
    
    if (result.data) {
      this.token = result.data.access_token;
      localStorage.setItem('access_token', this.token);
    }
    
    return result;
  }

  async register(email: string, password: string, fullName: string): Promise<ApiResponse<any>> {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }

  async updateProfile(data: { full_name?: string; email?: string; current_password?: string; new_password?: string }): Promise<ApiResponse<any>> {
    return this.request('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  logout() {
    this.token = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_data');
  }

  // Admin endpoints
  async getAllUsers(): Promise<ApiResponse<any[]>> {
    return this.request('/admin/users');
  }

  async updateUserRole(userId: number, role: string): Promise<ApiResponse<any>> {
    return this.request(`/admin/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });
  }

  async getUserDetails(userId: number): Promise<ApiResponse<any>> {
    return this.request(`/admin/users/${userId}`);
  }

  // Nodes
  async getNodes(): Promise<ApiResponse<any[]>> {
    return this.request('/nodes');
  }

  async registerNode(node: NodeRegisterRequest): Promise<ApiResponse<NodeRegisterResponse>> {
    return this.request('/nodes/register', {
      method: 'POST',
      body: JSON.stringify(node),
    });
  }

  async createNode(node: any): Promise<ApiResponse<any>> {
    return this.request('/nodes', {
      method: 'POST',
      body: JSON.stringify(node),
    });
  }

  async updateNode(nodeId: number, node: any): Promise<ApiResponse<any>> {
    return this.request(`/nodes/${nodeId}`, {
      method: 'PUT',
      body: JSON.stringify(node),
    });
  }

  async deleteNode(nodeId: number): Promise<ApiResponse<void>> {
    return this.request(`/nodes/${nodeId}`, {
      method: 'DELETE',
    });
  }

  // Node Configuration
  async getNodeConfig(nodeId: number): Promise<ApiResponse<any>> {
    return this.request(`/nodes/${nodeId}/config`);
  }

  async updateNodeConfig(nodeId: number, yamlConfig: string): Promise<ApiResponse<any>> {
    return this.request(`/nodes/${nodeId}/config`, {
      method: 'PUT',
      body: JSON.stringify({ yaml_config: yamlConfig }),
    });
  }

  // Node Analytics
  async getNodeAnalytics(nodeId: number): Promise<ApiResponse<NodeAnalytics>> {
    return this.request(`/nodes/${nodeId}/analytics`);
  }

  // Node Lifecycle Logs
  async getNodeLifecycleLogs(
    nodeId?: number,
    eventType?: string,
    limit: number = 100
  ): Promise<ApiResponse<NodeLifecycleLog[]>> {
    const params = new URLSearchParams();
    if (nodeId) params.append('node_id', nodeId.toString());
    if (eventType) params.append('event_type', eventType);
    params.append('limit', limit.toString());
    
    return this.request(`/nodes/lifecycle-logs?${params.toString()}`);
  }

  // Metrics
  async getMetrics(nodeId?: number): Promise<ApiResponse<any[]>> {
    const endpoint = nodeId ? `/metrics?node_id=${nodeId}` : '/metrics';
    return this.request(endpoint);
  }

  async createMetric(metric: any): Promise<ApiResponse<any>> {
    return this.request('/metrics', {
      method: 'POST',
      body: JSON.stringify(metric),
    });
  }

  // Schedules
  async getSchedules(): Promise<ApiResponse<any[]>> {
    return this.request('/schedules');
  }

  async createSchedule(schedule: any): Promise<ApiResponse<any>> {
    return this.request('/schedules', {
      method: 'POST',
      body: JSON.stringify(schedule),
    });
  }

  async updateSchedule(scheduleId: number, schedule: any): Promise<ApiResponse<any>> {
    return this.request(`/schedules/${scheduleId}`, {
      method: 'PUT',
      body: JSON.stringify(schedule),
    });
  }

  async deleteSchedule(scheduleId: number): Promise<ApiResponse<void>> {
    return this.request(`/schedules/${scheduleId}`, {
      method: 'DELETE',
    });
  }

  // Analytics
  async getSystemAnalytics(): Promise<ApiResponse<SystemAnalytics>> {
    return this.request('/analytics/system');
  }

  async getPoolAnalytics(nodeId?: number, hours: number = 24): Promise<ApiResponse<PoolAnalytics[]>> {
    const params = new URLSearchParams();
    if (nodeId) params.append('node_id', nodeId.toString());
    params.append('hours', hours.toString());
    
    const endpoint = `/analytics/pools?${params.toString()}`;
    return this.request(endpoint);
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; message: string }>> {
    return this.request('/health');
  }

  // Public runtime config
  async getPublicConfig(): Promise<ApiResponse<PublicConfig>> {
    return this.request<PublicConfig>('/config');
  }

  // Audit Logs (Admin only)
  async getAuditLogs(filters: AuditLogFilters = {}): Promise<ApiResponse<AuditLog[]>> {
    const params = new URLSearchParams();
    if (filters.category) params.append('category', filters.category);
    if (filters.action) params.append('action', filters.action);
    if (filters.user_id) params.append('user_id', filters.user_id.toString());
    if (filters.resource_type) params.append('resource_type', filters.resource_type);
    if (filters.status) params.append('status', filters.status);
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    if (filters.search) params.append('search', filters.search);
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.offset) params.append('offset', filters.offset.toString());
    
    return this.request(`/admin/audit-logs?${params.toString()}`);
  }

  async getAuditLogSummary(hours: number = 24): Promise<ApiResponse<AuditLogSummary>> {
    return this.request(`/admin/audit-logs/summary?hours=${hours}`);
  }

  async getAuditLogCategories(): Promise<ApiResponse<{
    categories: Array<{ value: string; label: string }>;
    actions: Array<{ value: string; label: string; category: string }>;
    statuses: Array<{ value: string; label: string }>;
  }>> {
    return this.request('/admin/audit-logs/categories');
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
export default apiClient;

export type { AuditLog, AuditLogSummary, AuditLogFilters };
