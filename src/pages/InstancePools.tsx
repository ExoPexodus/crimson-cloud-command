
import { useState, useEffect } from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { InstancePoolCard } from "@/components/dashboard/InstancePoolCard";
import { Plus, RefreshCw, Edit } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
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

const InstancePools = () => {
  const { toast } = useToast();
  const [pools, setPools] = useState<Pool[]>([]);
  const [poolMetrics, setPoolMetrics] = useState<Record<number, { cpu: number; memory: number }>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchPoolsData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchPoolsData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchPoolsData = async () => {
    try {
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
      setRefreshing(false);
    }
  };
  
  const handleRefresh = () => {
    setRefreshing(true);
    fetchPoolsData();
  };

  const handleCreatePool = () => {
    toast({
      title: "Pool Creation",
      description: "Pool creation coming soon! Pools are automatically detected from connected autoscaling nodes.",
    });
  };

  const handleScaleAction = async (poolId: number, action: 'up' | 'down', poolName: string) => {
    try {
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
  
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <div className="flex-1 overflow-auto p-4 md:p-6 teal-scrollbar">
            <div className="max-w-7xl mx-auto">
              {/* Page Header */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
                <div>
                  <h1 className="text-2xl font-bold mb-1">Instance Pools</h1>
                  <p className="text-sm text-muted-foreground">Manage and configure your Oracle Cloud instance pools</p>
                </div>
                <div className="flex gap-2 mt-3 sm:mt-0">
                  <Button 
                    variant="outline" 
                    className="border-dark-bg-light hover:bg-dark-bg-light text-sm"
                    onClick={handleRefresh}
                    disabled={refreshing}
                  >
                    <RefreshCw size={16} className={`mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                    {refreshing ? 'Refreshing...' : 'Refresh'}
                  </Button>
                  <Button 
                    className="bg-dark-teal-600 hover:bg-dark-teal-700 text-white text-sm"
                    onClick={handleCreatePool}
                  >
                    <Plus size={16} className="mr-2" />
                    Create New Pool
                  </Button>
                </div>
              </div>
              
              {/* Loading State */}
              {loading && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[1, 2, 3, 4, 5, 6].map((i) => (
                    <div key={i} className="h-64 bg-dark-bg-light/20 rounded-lg animate-pulse"></div>
                  ))}
                </div>
              )}

              {/* Empty State */}
              {!loading && pools.length === 0 && (
                <div className="text-center py-12">
                  <h3 className="text-lg font-medium mb-2">No Instance Pools Found</h3>
                  <p className="text-muted-foreground mb-4">
                    Start your autoscaling nodes to see pool data here automatically.
                  </p>
                  <div className="bg-dark-bg-light/30 rounded-lg p-4 max-w-md mx-auto">
                    <p className="text-sm text-muted-foreground">
                      Pools are automatically detected when autoscaling nodes connect to the backend.
                    </p>
                  </div>
                </div>
              )}
              
              {/* Instance Pools Grid */}
              {!loading && pools.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {pools.map((pool) => {
                    const metrics = poolMetrics[pool.id] || { cpu: 0, memory: 0 };
                    return (
                      <Card key={pool.id} className="glass-card overflow-hidden hover:shadow-dark-teal-900/10 transition-all duration-300">
                        <div className="p-4">
                          <InstancePoolCard
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
                          <div className="mt-3 pt-3 border-t border-dark-bg-light/30">
                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full border-dark-teal-600 text-dark-teal-400 hover:bg-dark-teal-800/20"
                              onClick={() => toast({ title: "Configuration", description: "Pool configuration coming soon!" })}
                            >
                              <Edit size={14} className="mr-2" />
                              Configure Pool
                            </Button>
                          </div>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default InstancePools;
