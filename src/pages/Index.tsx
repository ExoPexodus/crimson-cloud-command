
import { useState, useEffect } from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { InstancePoolCard } from "@/components/dashboard/InstancePoolCard";
import { MetricsChart } from "@/components/dashboard/MetricsChart";
import { Plus, RefreshCw, Server, Activity } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useIsMobile } from "@/hooks/use-mobile";
import { apiClient } from "@/lib/api";

// Mock data for recently active pools (will be replaced with real data later)
const recentInstancePools = [
  {
    id: "pool-1",
    name: "Production API Pool",
    instances: 4,
    maxInstances: 8,
    status: "healthy" as const,
    region: "US West (Phoenix)",
    cpuUsage: 62,
    memoryUsage: 48,
  },
  {
    id: "pool-2",
    name: "ML Training Workers",
    instances: 6,
    maxInstances: 10,
    status: "warning" as const,
    region: "US East (Ashburn)",
    cpuUsage: 78,
    memoryUsage: 65,
  },
  {
    id: "pool-3",
    name: "Database Cluster",
    instances: 3,
    maxInstances: 5,
    status: "healthy" as const,
    region: "Europe (Frankfurt)",
    cpuUsage: 45,
    memoryUsage: 72,
  },
  {
    id: "pool-4",
    name: "Dev Environment",
    instances: 1,
    maxInstances: 3,
    status: "inactive" as const,
    region: "Asia Pacific (Tokyo)",
    cpuUsage: 12,
    memoryUsage: 25,
  }
];

// Mock data for 24-hour metrics (will be enhanced with real data)
const poolActivityData = [
  { name: "00:00", value: 8 },
  { name: "04:00", value: 6 },
  { name: "08:00", value: 12 },
  { name: "12:00", value: 15 },
  { name: "16:00", value: 18 },
  { name: "20:00", value: 14 },
  { name: "24:00", value: 10 }
];

const instanceCountData = [
  { name: "00:00", value: 18 },
  { name: "04:00", value: 12 },
  { name: "08:00", value: 24 },
  { name: "12:00", value: 28 },
  { name: "16:00", value: 32 },
  { name: "20:00", value: 26 },
  { name: "24:00", value: 20 }
];

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

const Index = () => {
  const { toast } = useToast();
  const isMobile = useIsMobile();
  const [refreshing, setRefreshing] = useState(false);
  const [analytics, setAnalytics] = useState<SystemAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  
  const fetchAnalytics = async () => {
    try {
      const response = await apiClient.getSystemAnalytics();
      if (response.data) {
        setAnalytics(response.data);
      } else if (response.error) {
        console.error("Error fetching analytics:", response.error);
        toast({
          title: "Error",
          description: "Failed to fetch system analytics",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    // Set up polling to refresh analytics every 30 seconds
    const interval = setInterval(fetchAnalytics, 30000);
    return () => clearInterval(interval);
  }, []);
  
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAnalytics();
    setTimeout(() => {
      setRefreshing(false);
      toast({
        title: "Refreshed",
        description: "Data has been updated from Oracle Cloud API",
      });
    }, 1500);
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString();
  };
  
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <div className="flex-1 overflow-auto p-4 md:p-6 teal-scrollbar">
            <div className="max-w-7xl mx-auto">
              {/* Dashboard Header */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
                <div>
                  <h1 className="text-2xl font-bold mb-1">Instance Management</h1>
                  <p className="text-sm text-muted-foreground">
                    Monitor and manage your Oracle Cloud instances
                    {analytics && (
                      <span className="ml-2">
                        • Last updated: {formatTime(analytics.last_updated)}
                      </span>
                    )}
                  </p>
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
                  <Button className="bg-dark-teal-600 hover:bg-dark-teal-700 text-white text-sm">
                    <Plus size={16} className="mr-2" />
                    New Instance Pool
                  </Button>
                </div>
              </div>
              
              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                <Card className="glass-card border-dark-bg-light/50 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Active Pools (24h)</p>
                      <h3 className="text-2xl font-bold mt-1">
                        {loading ? "..." : analytics?.total_active_pools || 0}
                      </h3>
                    </div>
                    <div className="h-10 w-10 rounded-full bg-dark-teal-900/30 flex items-center justify-center">
                      <Server size={20} className="text-dark-teal-400" />
                    </div>
                  </div>
                  <div className="text-xs text-dark-teal-300 mt-2">
                    Max: {analytics?.max_active_pools_24h || 0} pools today
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
                    <div className="h-10 w-10 rounded-full bg-dark-teal-900/30 flex items-center justify-center">
                      <Activity size={20} className="text-dark-teal-400" />
                    </div>
                  </div>
                  <div className="text-xs text-dark-teal-300 mt-2">
                    Avg CPU: {analytics?.avg_system_cpu?.toFixed(1) || 0}%
                  </div>
                </Card>
                
                <Card className="glass-card border-dark-bg-light/50 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Current Total Instances</p>
                      <h3 className="text-2xl font-bold mt-1">
                        {loading ? "..." : analytics?.total_current_instances || 0}
                      </h3>
                    </div>
                    <div className="h-10 w-10 rounded-full bg-dark-teal-900/30 flex items-center justify-center">
                      <Server size={20} className="text-dark-teal-400" />
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground mt-2">
                    Active nodes: {analytics?.active_nodes || 0}
                  </div>
                </Card>
              </div>

              {/* 24-Hour Metrics Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <MetricsChart
                  data={poolActivityData}
                  title="Active Pools"
                  color="#20B2AA"
                />
                <MetricsChart
                  data={instanceCountData}
                  title="Total Instances"
                  color="#16A085"
                />
              </div>
              
              {/* Recently Active Instance Pools */}
              <div>
                <h2 className="text-lg font-medium mb-4">Recently Active Instance Pools</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {recentInstancePools.map((pool) => (
                    <InstancePoolCard
                      key={pool.id}
                      name={pool.name}
                      instances={pool.instances}
                      maxInstances={pool.maxInstances}
                      status={pool.status}
                      region={pool.region}
                      cpuUsage={pool.cpuUsage}
                      memoryUsage={pool.memoryUsage}
                      onScaleUp={() => toast({ title: "Scale Up", description: `Scaling up ${pool.name}` })}
                      onScaleDown={() => toast({ title: "Scale Down", description: `Scaling down ${pool.name}` })}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Index;
