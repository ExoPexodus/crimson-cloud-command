
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost' 
    ? `http://${window.location.hostname}:8000` 
    : 'http://localhost:8000');

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
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      console.log(`Making request to: ${url}`, config);
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`HTTP ${response.status} error:`, errorText);
        return { error: `HTTP ${response.status}: ${errorText}` };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error('Request failed:', error);
      return { error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  // Authentication
  async login(email: string, password: string): Promise<ApiResponse<{ access_token: string; token_type: string }>> {
    const formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);
    
    const result = await this.request<{ access_token: string; token_type: string }>('/auth/login', {
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

  async register(email: string, password: string, fullName: string): Promise<ApiResponse<any>> {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }

  logout() {
    this.token = null;
    localStorage.removeItem('access_token');
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

  // Pools
  async getPools(): Promise<ApiResponse<any[]>> {
    return this.request('/pools');
  }

  async createPool(pool: any): Promise<ApiResponse<any>> {
    return this.request('/pools', {
      method: 'POST',
      body: JSON.stringify(pool),
    });
  }

  async updatePool(poolId: number, pool: any): Promise<ApiResponse<any>> {
    return this.request(`/pools/${poolId}`, {
      method: 'PUT',
      body: JSON.stringify(pool),
    });
  }

  async deletePool(poolId: number): Promise<ApiResponse<void>> {
    return this.request(`/pools/${poolId}`, {
      method: 'DELETE',
    });
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
}

export const apiClient = new ApiClient(API_BASE_URL);
export default apiClient;
