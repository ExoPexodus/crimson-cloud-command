
import { Card } from "@/components/ui/card";
import { Server, Activity } from "lucide-react";

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

interface SystemMetricsCardsProps {
  analytics: SystemAnalytics | null;
  loading: boolean;
}

export function SystemMetricsCards({ analytics, loading }: SystemMetricsCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      <Card className="glass-card border-dark-bg-light/50 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Active Pools (24h)</p>
            <h3 className="text-2xl font-bold mt-1">
              {loading ? "..." : analytics?.total_active_pools || 0}
            </h3>
          </div>
          <div className="h-10 w-10 rounded-full bg-dark-blue-900/30 flex items-center justify-center">
            <Server size={20} className="text-dark-blue-400" />
          </div>
        </div>
        <div className="text-xs text-dark-blue-300 mt-2">
          Max today: {analytics?.max_active_pools_24h || 0} pools
        </div>
      </Card>
      
      <Card className="glass-card border-dark-bg-light/50 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Peak Instances (24h)</p>
            <h3 className="text-2xl font-bold mt-1">
              {loading ? "..." : analytics?.peak_instances_24h || 0}
            </h3>
          </div>
          <div className="h-10 w-10 rounded-full bg-dark-blue-900/30 flex items-center justify-center">
            <Activity size={20} className="text-dark-blue-400" />
          </div>
        </div>
        <div className="text-xs text-dark-blue-300 mt-2">
          Avg CPU: {analytics?.avg_system_cpu?.toFixed(1) || 0}%
        </div>
      </Card>
      
      <Card className="glass-card border-dark-bg-light/50 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Total Running Instances</p>
            <h3 className="text-2xl font-bold mt-1">
              {loading ? "..." : analytics?.total_current_instances || 0}
            </h3>
          </div>
          <div className="h-10 w-10 rounded-full bg-dark-blue-900/30 flex items-center justify-center">
            <Server size={20} className="text-dark-blue-400" />
          </div>
        </div>
        <div className="text-xs text-dark-blue-300 mt-2">
          Active nodes: {analytics?.active_nodes || 0}
        </div>
      </Card>
    </div>
  );
}
