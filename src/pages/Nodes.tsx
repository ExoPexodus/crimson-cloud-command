
import { useState, useEffect } from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Plus, RefreshCw, Settings, Activity, Server, Cpu, HardDrive } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { NodeSetupDialog } from "@/components/dashboard/NodeSetupDialog";
import { NodeConfigDialog } from "@/components/dashboard/NodeConfigDialog";
import { StatusIndicator } from "@/components/dashboard/StatusIndicator";

interface Node {
  id: number;
  name: string;
  region: string;
  status: "active" | "inactive" | "error";
  last_heartbeat?: string;
  created_at: string;
  api_key_hash?: string;
}

interface NodeAnalytics {
  avg_cpu_utilization: number;
  avg_memory_utilization: number;
  current_instances: number;
  max_instances: number;
}

const Nodes = () => {
  const { toast } = useToast();
  const [nodes, setNodes] = useState<Node[]>([]);
  const [nodeAnalytics, setNodeAnalytics] = useState<Record<number, NodeAnalytics>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [setupDialogOpen, setSetupDialogOpen] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  useEffect(() => {
    fetchNodes();
    
    // Refresh every 30 seconds to check node status
    const interval = setInterval(fetchNodes, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchNodes = async () => {
    try {
      console.log("Fetching nodes...");
      const response = await apiClient.getNodes();
      if (response.data) {
        console.log("Nodes fetched:", response.data);
        setNodes(response.data);
        
        // Fetch analytics for each node
        const analyticsPromises = response.data.map(async (node: Node) => {
          try {
            console.log(`Fetching analytics for node ${node.id}...`);
            const analyticsResponse = await apiClient.getNodeAnalytics(node.id);
            console.log(`Analytics for node ${node.id}:`, analyticsResponse);
            return { nodeId: node.id, analytics: analyticsResponse.data };
          } catch (error) {
            console.error(`Error fetching analytics for node ${node.id}:`, error);
            return { nodeId: node.id, analytics: null };
          }
        });
        
        const analyticsResults = await Promise.all(analyticsPromises);
        const analyticsMap: Record<number, NodeAnalytics> = {};
        
        analyticsResults.forEach(({ nodeId, analytics }) => {
          if (analytics) {
            analyticsMap[nodeId] = analytics;
          }
        });
        
        console.log("Analytics map:", analyticsMap);
        setNodeAnalytics(analyticsMap);
      }
    } catch (error) {
      console.error("Error fetching nodes:", error);
      setNodes([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };
  
  const handleRefresh = () => {
    setRefreshing(true);
    fetchNodes();
  };

  const handleCreateNode = () => {
    setSetupDialogOpen(true);
  };

  const handleConfigureNode = (node: Node) => {
    setSelectedNode(node);
    setConfigDialogOpen(true);
  };

  const handleNodeDeleted = () => {
    fetchNodes(); // Refresh the list
  };

  const getNodeStatus = (node: Node): "healthy" | "warning" | "error" | "inactive" => {
    console.log(`Calculating status for node ${node.id}:`, {
      last_heartbeat: node.last_heartbeat,
      status: node.status
    });
    
    if (!node.last_heartbeat) {
      console.log(`Node ${node.id} has no heartbeat, marking as inactive`);
      return "inactive";
    }
    
    const lastHeartbeat = new Date(node.last_heartbeat + 'Z'); // Ensure it's treated as UTC
    const now = new Date();
    const timeDiff = now.getTime() - lastHeartbeat.getTime();
    const minutesDiff = timeDiff / (1000 * 60);
    
    console.log(`Node ${node.id} last heartbeat was ${minutesDiff} minutes ago`);
    
    if (minutesDiff > 10) return "error";
    if (minutesDiff > 5) return "warning";
    return "healthy";
  };

  const formatLastSeen = (lastHeartbeat?: string) => {
    if (!lastHeartbeat) return "Never";
    
    // Parse the UTC timestamp from the backend and convert to local time
    const lastSeen = new Date(lastHeartbeat + 'Z'); // Ensure it's treated as UTC
    const now = new Date();
    const timeDiff = now.getTime() - lastSeen.getTime();
    const minutesDiff = Math.floor(timeDiff / (1000 * 60));
    
    if (minutesDiff < 1) return "Just now";
    if (minutesDiff < 60) return `${minutesDiff}m ago`;
    
    const hoursDiff = Math.floor(minutesDiff / 60);
    if (hoursDiff < 24) return `${hoursDiff}h ago`;
    
    const daysDiff = Math.floor(hoursDiff / 24);
    return `${daysDiff}d ago`;
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
                  <h1 className="text-2xl font-bold mb-1">Autoscaling Nodes</h1>
                  <p className="text-sm text-muted-foreground">Manage your connected autoscaling nodes</p>
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
                    onClick={handleCreateNode}
                  >
                    <Plus size={16} className="mr-2" />
                    Add New Node
                  </Button>
                </div>
              </div>
              
              {/* Loading State */}
              {loading && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-64 bg-dark-bg-light/20 rounded-lg animate-pulse"></div>
                  ))}
                </div>
              )}

              {/* Empty State */}
              {!loading && nodes.length === 0 && (
                <div className="text-center py-12">
                  <Activity className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No Nodes Connected</h3>
                  <p className="text-muted-foreground mb-4">
                    Connect your first autoscaling node to start managing your Oracle Cloud instances.
                  </p>
                  <Button 
                    className="bg-dark-teal-600 hover:bg-dark-teal-700 text-white"
                    onClick={handleCreateNode}
                  >
                    <Plus size={16} className="mr-2" />
                    Setup Your First Node
                  </Button>
                </div>
              )}
              
              {/* Nodes Grid */}
              {!loading && nodes.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {nodes.map((node) => {
                    const status = getNodeStatus(node);
                    const analytics = nodeAnalytics[node.id];
                    
                    console.log(`Rendering node ${node.id}:`, { status, analytics });
                    
                    return (
                      <Card key={node.id} className="glass-card overflow-hidden hover:shadow-dark-teal-900/10 transition-all duration-300">
                        <div className="p-4">
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <h3 className="font-semibold text-lg">{node.name}</h3>
                              <p className="text-sm text-muted-foreground">{node.region}</p>
                            </div>
                            <StatusIndicator status={status} showLabel={false} />
                          </div>
                          
                          {/* Instance Pool Metrics */}
                          <div className="space-y-3 mb-4">
                            <div className="flex items-center gap-2 text-sm font-medium">
                              <Server size={16} className="text-dark-teal-400" />
                              <span>Instance Pool Metrics</span>
                            </div>
                            
                            {analytics ? (
                              <div className="space-y-2">
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-1">
                                      <Cpu size={12} className="text-dark-teal-400" />
                                      <span>CPU Usage</span>
                                    </div>
                                    <span className="text-muted-foreground">{Math.round(analytics.avg_cpu_utilization)}%</span>
                                  </div>
                                  <Progress 
                                    value={analytics.avg_cpu_utilization} 
                                    className="h-1.5" 
                                    indicatorClassName="bg-dark-teal-500" 
                                  />
                                </div>
                                
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-1">
                                      <HardDrive size={12} className="text-dark-teal-400" />
                                      <span>Memory Usage</span>
                                    </div>
                                    <span className="text-muted-foreground">{Math.round(analytics.avg_memory_utilization)}%</span>
                                  </div>
                                  <Progress 
                                    value={analytics.avg_memory_utilization} 
                                    className="h-1.5" 
                                    indicatorClassName="bg-dark-teal-400" 
                                  />
                                </div>
                                
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-1">
                                      <Server size={12} className="text-dark-teal-400" />
                                      <span>Instances</span>
                                    </div>
                                    <span className="text-muted-foreground">{analytics.current_instances}/{analytics.max_instances}</span>
                                  </div>
                                  <Progress 
                                    value={analytics.max_instances > 0 ? (analytics.current_instances / analytics.max_instances) * 100 : 0} 
                                    className="h-1.5" 
                                    indicatorClassName="bg-dark-teal-600" 
                                  />
                                </div>
                              </div>
                            ) : (
                              <div className="space-y-2">
                                <div className="text-xs text-muted-foreground text-center py-2">
                                  No metrics available yet
                                </div>
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-1">
                                      <Cpu size={12} className="text-muted-foreground" />
                                      <span>CPU Usage</span>
                                    </div>
                                    <span className="text-muted-foreground">--</span>
                                  </div>
                                  <Progress value={0} className="h-1.5" indicatorClassName="bg-gray-400" />
                                </div>
                                
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-1">
                                      <HardDrive size={12} className="text-muted-foreground" />
                                      <span>Memory Usage</span>
                                    </div>
                                    <span className="text-muted-foreground">--</span>
                                  </div>
                                  <Progress value={0} className="h-1.5" indicatorClassName="bg-gray-400" />
                                </div>
                                
                                <div className="space-y-1">
                                  <div className="flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-1">
                                      <Server size={12} className="text-muted-foreground" />
                                      <span>Instances</span>
                                    </div>
                                    <span className="text-muted-foreground">--/--</span>
                                  </div>
                                  <Progress value={0} className="h-1.5" indicatorClassName="bg-gray-400" />
                                </div>
                              </div>
                            )}
                          </div>
                          
                          <div className="space-y-2 text-sm border-t border-dark-bg-light/30 pt-3">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Status:</span>
                              <StatusIndicator status={status} />
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Last seen:</span>
                              <span>{formatLastSeen(node.last_heartbeat)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Node ID:</span>
                              <span className="font-mono text-xs">{node.id}</span>
                            </div>
                          </div>
                          
                          <div className="mt-4 pt-3 border-t border-dark-bg-light/30">
                            <Button
                              variant="outline"
                              size="sm"
                              className="w-full border-dark-teal-600 text-dark-teal-400 hover:bg-dark-teal-800/20"
                              onClick={() => handleConfigureNode(node)}
                            >
                              <Settings size={14} className="mr-2" />
                              Configure Node
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

      {/* Dialogs */}
      <NodeSetupDialog
        isOpen={setupDialogOpen}
        onClose={() => setSetupDialogOpen(false)}
        onNodeRegistered={fetchNodes}
      />

      <NodeConfigDialog
        isOpen={configDialogOpen}
        onClose={() => setConfigDialogOpen(false)}
        node={selectedNode}
        onNodeDeleted={handleNodeDeleted}
      />
    </SidebarProvider>
  );
};

export default Nodes;
