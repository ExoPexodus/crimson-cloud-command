import { Card } from "@/components/ui/card";
import { Server, Activity, AlertCircle, Cpu, HardDrive, TrendingUp } from "lucide-react";
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

  const kpis = [
    {
      label: "Active Nodes",
      value: analytics?.active_nodes || 0,
      icon: Server,
      color: "text-green-400",
      bgColor: "bg-green-500/10",
    },
    {
      label: "Active Pools",
      value: analytics?.total_active_pools || 0,
      icon: Activity,
      color: "text-primary",
      bgColor: "bg-primary/10",
    },
    {
      label: "Running Instances",
      value: analytics?.total_current_instances || 0,
      icon: Server,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
    },
    {
      label: "Peak (24h)",
      value: analytics?.peak_instances_24h || 0,
      icon: TrendingUp,
      color: "text-purple-400",
      bgColor: "bg-purple-500/10",
    },
    {
      label: "Avg CPU",
      value: `${analytics?.avg_system_cpu?.toFixed(1) || 0}%`,
      icon: Cpu,
      color: "text-orange-400",
      bgColor: "bg-orange-500/10",
    },
    {
      label: "Avg Memory",
      value: `${analytics?.avg_system_memory?.toFixed(1) || 0}%`,
      icon: HardDrive,
      color: "text-cyan-400",
      bgColor: "bg-cyan-500/10",
    },
  ];

  return (
    <div className="space-y-4 mb-6">
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
      
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {kpis.map((kpi) => (
          <Card
            key={kpi.label}
            className={`glass-card border-border/50 p-3 ${stale ? "opacity-70" : ""}`}
          >
            <div className="flex items-center gap-2">
              <div className={`h-8 w-8 rounded-lg ${kpi.bgColor} flex items-center justify-center`}>
                <kpi.icon size={16} className={kpi.color} />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground truncate">{kpi.label}</p>
                <p className="text-lg font-bold leading-tight">
                  {loading ? "..." : kpi.value}
                </p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
