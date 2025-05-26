
import { useState } from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { InstancePoolCard } from "@/components/dashboard/InstancePoolCard";
import { Plus, RefreshCw, Edit } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

// Extended mock data for all instance pools
const allInstancePools = [
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
  },
  {
    id: "pool-5",
    name: "Test Environment",
    instances: 2,
    maxInstances: 4,
    status: "healthy" as const,
    region: "US Central (Dallas)",
    cpuUsage: 35,
    memoryUsage: 42,
  },
  {
    id: "pool-6",
    name: "Analytics Pool",
    instances: 0,
    maxInstances: 6,
    status: "inactive" as const,
    region: "Europe (London)",
    cpuUsage: 0,
    memoryUsage: 0,
  }
];

const InstancePools = () => {
  const { toast } = useToast();
  const [refreshing, setRefreshing] = useState(false);
  
  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => {
      setRefreshing(false);
      toast({
        title: "Refreshed",
        description: "Instance pools data has been updated",
      });
    }, 1500);
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
                  <Button className="bg-dark-teal-600 hover:bg-dark-teal-700 text-white text-sm">
                    <Plus size={16} className="mr-2" />
                    Create New Pool
                  </Button>
                </div>
              </div>
              
              {/* Instance Pools Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {allInstancePools.map((pool) => (
                  <Card key={pool.id} className="glass-card overflow-hidden hover:shadow-dark-teal-900/10 transition-all duration-300">
                    <div className="p-4">
                      <InstancePoolCard
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
                      <div className="mt-3 pt-3 border-t border-dark-bg-light/30">
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-full border-dark-teal-600 text-dark-teal-400 hover:bg-dark-teal-800/20"
                          onClick={() => toast({ title: "Configure", description: `Opening configuration for ${pool.name}` })}
                        >
                          <Edit size={14} className="mr-2" />
                          Configure Pool
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default InstancePools;
