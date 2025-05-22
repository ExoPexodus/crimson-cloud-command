
import { useState } from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { InstancePoolCard } from "@/components/dashboard/InstancePoolCard";
import { MetricsChart } from "@/components/dashboard/MetricsChart";
import { AutoscaleConfig } from "@/components/dashboard/AutoscaleConfig";
import { Plus, RefreshCw, Server } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useIsMobile } from "@/hooks/use-mobile";

// Mock data
const generateMockData = (count: number, min: number, max: number) => {
  return Array.from({ length: count }).map((_, i) => ({
    name: `${i}h`,
    value: Math.floor(Math.random() * (max - min) + min)
  }));
};

const cpuData = generateMockData(24, 10, 90);
const memoryData = generateMockData(24, 20, 80);
const instanceData = generateMockData(24, 2, 8);

const instancePools = [
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

const Index = () => {
  const { toast } = useToast();
  const isMobile = useIsMobile();
  const [refreshing, setRefreshing] = useState(false);
  
  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => {
      setRefreshing(false);
      toast({
        title: "Refreshed",
        description: "Data has been updated from Oracle Cloud API",
      });
    }, 1500);
  };
  
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <div className="flex-1 overflow-auto p-4 md:p-6 red-scrollbar">
            <div className="max-w-7xl mx-auto">
              {/* Dashboard Header */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
                <div>
                  <h1 className="text-2xl font-bold mb-1">Instance Management</h1>
                  <p className="text-sm text-muted-foreground">Monitor and manage your Oracle Cloud instances</p>
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
                  <Button className="bg-dark-red-600 hover:bg-dark-red-700 text-white text-sm">
                    <Plus size={16} className="mr-2" />
                    New Instance Pool
                  </Button>
                </div>
              </div>
              
              {/* Instance Pool Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <Card className="glass-card border-dark-bg-light/50 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Total Instances</p>
                      <h3 className="text-2xl font-bold mt-1">14</h3>
                    </div>
                    <div className="h-10 w-10 rounded-full bg-dark-red-900/30 flex items-center justify-center">
                      <Server size={20} className="text-dark-red-400" />
                    </div>
                  </div>
                  <div className="text-xs text-dark-red-300 mt-2">+2 from last week</div>
                </Card>
                
                <Card className="glass-card border-dark-bg-light/50 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Active Pools</p>
                      <h3 className="text-2xl font-bold mt-1">4</h3>
                    </div>
                    <div className="h-10 w-10 rounded-full bg-dark-red-900/30 flex items-center justify-center">
                      <Server size={20} className="text-dark-red-400" />
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground mt-2">No change</div>
                </Card>
                
                <Card className="glass-card border-dark-bg-light/50 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Avg CPU Load</p>
                      <h3 className="text-2xl font-bold mt-1">56%</h3>
                    </div>
                    <div className="h-10 w-10 rounded-full bg-dark-red-900/30 flex items-center justify-center">
                      <Server size={20} className="text-dark-red-400" />
                    </div>
                  </div>
                  <div className="text-xs text-dark-red-300 mt-2">+12% from yesterday</div>
                </Card>
                
                <Card className="glass-card border-dark-bg-light/50 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Containers</p>
                      <h3 className="text-2xl font-bold mt-1">32</h3>
                    </div>
                    <div className="h-10 w-10 rounded-full bg-dark-red-900/30 flex items-center justify-center">
                      <Server size={20} className="text-dark-red-400" />
                    </div>
                  </div>
                  <div className="text-xs text-dark-red-300 mt-2">+5 from last week</div>
                </Card>
              </div>
              
              {/* Main dashboard content */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left column - Instance pools */}
                <div className="lg:col-span-2 space-y-6">
                  <h2 className="text-lg font-medium mb-4">Instance Pools</h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {instancePools.map((pool) => (
                      <InstancePoolCard
                        key={pool.id}
                        name={pool.name}
                        instances={pool.instances}
                        maxInstances={pool.maxInstances}
                        status={pool.status}
                        region={pool.region}
                        cpuUsage={pool.cpuUsage}
                        memoryUsage={pool.memoryUsage}
                        onEdit={() => toast({ title: "Edit", description: `Editing ${pool.name}` })}
                        onScaleUp={() => toast({ title: "Scale Up", description: `Scaling up ${pool.name}` })}
                        onScaleDown={() => toast({ title: "Scale Down", description: `Scaling down ${pool.name}` })}
                      />
                    ))}
                  </div>
                  
                  {/* Charts section */}
                  <h2 className="text-lg font-medium mb-4 mt-8">Resource Metrics</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <MetricsChart 
                      data={cpuData} 
                      title="CPU Usage" 
                      valueSuffix="%" 
                      color="#FF3333" 
                    />
                    <MetricsChart 
                      data={memoryData} 
                      title="Memory Usage" 
                      valueSuffix="%" 
                      color="#FF9933" 
                    />
                    <MetricsChart 
                      data={instanceData} 
                      title="Active Instances" 
                      color="#3366FF" 
                    />
                  </div>
                </div>
                
                {/* Right column - Configuration */}
                <div>
                  <h2 className="text-lg font-medium mb-4">Configuration</h2>
                  <AutoscaleConfig 
                    instancePoolId="pool-1" 
                    onSave={(values) => console.log("Saved config:", values)} 
                  />
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
