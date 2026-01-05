import { Card } from "@/components/ui/card";
import { Server, Activity, AlertCircle } from "lucide-react";
import { parseUTCTimestamp } from "@/lib/dateUtils";

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
  // Check if data is stale (more than 10 minutes old)
  const isDataStale = () => {
    if (!analytics?.last_updated) return false;
    const lastUpdated = parseUTCTimestamp(analytics.last_updated);
    const now = new Date();
    const minutesDiff = (now.getTime() - lastUpdated.getTime()) / (1000 * 60);
    return minutesDiff > 10;
  };

  // Check if we have any meaningful data
  const hasNoData = analytics && 
    analytics.total_active_pools === 0 && 
    analytics.total_current_instances === 0 && 
    analytics.active_nodes === 0;

  const stale = isDataStale();

  const formatLastUpdated = () => {
    if (!analytics?.last_updated) return "";
    const lastUpdated = parseUTCTimestamp(analytics.last_updated);
    const now = new Date();
    const minutesDiff = Math.round((now.getTime() - lastUpdated.getTime()) / (1000 * 60));
    
    if (minutesDiff < 1) return "Just now";
    if (minutesDiff < 60) return `${minutesDiff}m ago`;
    const hoursDiff = Math.round(minutesDiff / 60);
    return `${hoursDiff}h ago`;
  };

  return (
    <div className="space-y-2">
      {(stale || hasNoData) && !loading && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/30 rounded-md px-3 py-2">
          <AlertCircle size={14} className="text-yellow-500" />
          {hasNoData ? (
            <span>No active nodes reporting. Data will appear when autoscaler nodes connect.</span>
          ) : (
            <span>Data may be stale. Last updated: {formatLastUpdated()}</span>
          )}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <Card className={`glass-card border-border/50 p-4 ${stale ? 'opacity-70' : ''}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Active Pools (24h)</p>
              <h3 className="text-2xl font-bold mt-1">
                {loading ? "..." : analytics?.total_active_pools || 0}
              </h3>
            </div>
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Server size={20} className="text-primary" />
            </div>
          </div>
          <div className="text-xs text-muted-foreground mt-2">
            Max today: {analytics?.max_active_pools_24h || 0} pools
          </div>
        </Card>
        
        <Card className={`glass-card border-border/50 p-4 ${stale ? 'opacity-70' : ''}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Peak Instances (24h)</p>
              <h3 className="text-2xl font-bold mt-1">
                {loading ? "..." : analytics?.peak_instances_24h || 0}
              </h3>
            </div>
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Activity size={20} className="text-primary" />
            </div>
          </div>
          <div className="text-xs text-muted-foreground mt-2">
            Avg CPU: {analytics?.avg_system_cpu?.toFixed(1) || 0}%
          </div>
        </Card>
        
        <Card className={`glass-card border-border/50 p-4 ${stale ? 'opacity-70' : ''}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Currently Running Instances</p>
              <h3 className="text-2xl font-bold mt-1">
                {loading ? "..." : analytics?.total_current_instances || 0}
              </h3>
            </div>
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Server size={20} className="text-primary" />
            </div>
          </div>
          <div className="text-xs text-muted-foreground mt-2">
            Active nodes: {analytics?.active_nodes || 0}
          </div>
        </Card>
      </div>
    </div>
  );
}
