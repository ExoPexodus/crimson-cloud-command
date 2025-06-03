const API_BASE_URL = "http://localhost:8000";

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

interface NodeApiKey {
  id: number;
  name: string;
  key: string;
  node_id: number;
  created_at: string;
  is_active: boolean;
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseURL}${endpoint}`;
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorText = await response.text();
        return { error: errorText || `HTTP ${response.status}` };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error('API request failed:', error);
      return { error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  // Auth methods
  async login(email: string, password: string): Promise<ApiResponse<{ access_token: string; token_type: string }>> {
    const formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);

    return this.request('/auth/login', {
      method: 'POST',
      headers: {},
      body: formData,
    });
  }

  async register(userData: { email: string; password: string; full_name: string }): Promise<ApiResponse<any>> {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  // System analytics
  async getSystemAnalytics(): Promise<ApiResponse<any>> {
    return this.request('/analytics/system');
  }

  // Pool analytics
  async getPoolAnalytics(nodeId?: number, hours: number = 24): Promise<ApiResponse<any[]>> {
    const params = new URLSearchParams();
    if (nodeId) params.append('node_id', nodeId.toString());
    params.append('hours', hours.toString());
    
    return this.request(`/analytics/pools?${params.toString()}`);
  }

  // Pool management
  async getPools(): Promise<ApiResponse<any[]>> {
    return this.request('/pools');
  }

  async createPool(poolData: any): Promise<ApiResponse<any>> {
    return this.request('/pools', {
      method: 'POST',
      body: JSON.stringify(poolData),
    });
  }

  async updatePool(poolId: number, poolData: any): Promise<ApiResponse<any>> {
    return this.request(`/pools/${poolId}`, {
      method: 'PUT',
      body: JSON.stringify(poolData),
    });
  }

  async deletePool(poolId: number): Promise<ApiResponse<void>> {
    return this.request(`/pools/${poolId}`, {
      method: 'DELETE',
    });
  }

  // Metrics
  async getMetrics(nodeId?: number): Promise<ApiResponse<any[]>> {
    const params = nodeId ? `?node_id=${nodeId}` : '';
    return this.request(`/metrics${params}`);
  }

  // Schedules
  async getSchedules(): Promise<ApiResponse<any[]>> {
    return this.request('/schedules');
  }

  async createSchedule(scheduleData: any): Promise<ApiResponse<any>> {
    return this.request('/schedules', {
      method: 'POST',
      body: JSON.stringify(scheduleData),
    });
  }

  async updateSchedule(scheduleId: number, scheduleData: any): Promise<ApiResponse<any>> {
    return this.request(`/schedules/${scheduleId}`, {
      method: 'PUT',
      body: JSON.stringify(scheduleData),
    });
  }

  async deleteSchedule(scheduleId: number): Promise<ApiResponse<void>> {
    return this.request(`/schedules/${scheduleId}`, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient();
