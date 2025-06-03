
import { InstancePoolCard } from "@/components/dashboard/InstancePoolCard";
import { useToast } from "@/hooks/use-toast";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

interface Pool {
  id: number;
  name: string;
  oracle_pool_id: string;
  current_instances: number;
  max_instances: number;
  status: "healthy" | "warning" | "error" | "inactive";
  node: {
    region: string;
  };
}

interface PoolAnalytics {
  pool_id: number;
  avg_cpu_utilization: number;
  avg_memory_utilization: number;
  timestamp: string;
}

export function InstancePoolsSection() {
  const { toast } = useToast();
  const [pools, setPools] = useState<Pool[]>([]);
  const [poolMetrics, setPoolMetrics] = useState<Record<number, { cpu: number; memory: number }>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPoolsData = async () => {
      try {
        // Fetch pools
        const poolsResponse = await apiClient.getPools();
        if (poolsResponse.data) {
          setPools(poolsResponse.data);
          
          // Fetch recent analytics for each pool
          const analyticsResponse = await apiClient.getPoolAnalytics(undefined, 1);
          if (analyticsResponse.data) {
            const metrics: Record<number, { cpu: number; memory: number }> = {};
            analyticsResponse.data.forEach((analytics: PoolAnalytics) => {
              metrics[analytics.pool_id] = {
                cpu: analytics.avg_cpu_utilization,
                memory: analytics.avg_memory_utilization
              };
            });
            setPoolMetrics(metrics);
          }
        }
      } catch (error) {
        console.error("Error fetching pools data:", error);
        setPools([]);
        setPoolMetrics({});
      } finally {
        setLoading(false);
      }
    };

    fetchPoolsData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchPoolsData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleScaleAction = async (poolId: number, action: 'up' | 'down', poolName: string) => {
    try {
      // This would typically call an API to scale the pool
      // For now, just show a toast
      toast({
        title: `Scale ${action === 'up' ? 'Up' : 'Down'}`,
        description: `Scaling ${action} ${poolName}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to scale ${poolName}`,
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div>
        <h2 className="text-lg font-medium mb-4">Recently Active Instance Pools</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-48 bg-dark-bg-light/20 rounded-lg animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (pools.length === 0) {
    return (
      <div>
        <h2 className="text-lg font-medium mb-4">Recently Active Instance Pools</h2>
        <div className="text-center py-12 text-muted-foreground">
          <p>No instance pools found. Add some nodes to see pool data.</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-medium mb-4">Recently Active Instance Pools</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {pools.slice(0, 8).map((pool) => {
          const metrics = poolMetrics[pool.id] || { cpu: 0, memory: 0 };
          return (
            <InstancePoolCard
              key={pool.id}
              name={pool.name}
              instances={pool.current_instances}
              maxInstances={pool.max_instances}
              status={pool.status}
              region={pool.node?.region || "Unknown"}
              cpuUsage={Math.round(metrics.cpu)}
              memoryUsage={Math.round(metrics.memory)}
              onScaleUp={() => handleScaleAction(pool.id, 'up', pool.name)}
              onScaleDown={() => handleScaleAction(pool.id, 'down', pool.name)}
            />
          );
        })}
      </div>
    </div>
  );
}
