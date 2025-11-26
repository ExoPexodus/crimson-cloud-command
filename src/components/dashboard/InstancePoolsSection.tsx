
import { InstancePoolCard } from "@/components/dashboard/InstancePoolCard";
import { useToast } from "@/hooks/use-toast";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

interface Node {
  id: number;
  name: string;
  region: string;
  status: "ACTIVE" | "INACTIVE" | "ERROR" | "OFFLINE";
  last_heartbeat?: string;
}

interface NodeAnalytics {
  avg_cpu_utilization: number;
  avg_memory_utilization: number;
  current_instances: number;
  max_instances: number;
}

export function InstancePoolsSection() {
  const { toast } = useToast();
  const [nodes, setNodes] = useState<Node[]>([]);
  const [nodeAnalytics, setNodeAnalytics] = useState<Record<number, NodeAnalytics>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNodesData = async () => {
      try {
        // Fetch nodes
        const nodesResponse = await apiClient.getNodes();
        if (nodesResponse.data) {
          // Filter out offline nodes (backend already filters them, but adding defensive check)
          const activeNodes = nodesResponse.data.filter((node: Node) => 
            node.status !== 'OFFLINE' && (node.status === 'ACTIVE' || node.last_heartbeat)
          );
          setNodes(activeNodes);
          
          // Fetch analytics for each active node
          const analyticsPromises = activeNodes.map(async (node: Node) => {
            const analyticsResponse = await apiClient.getNodeAnalytics(node.id);
            return { nodeId: node.id, analytics: analyticsResponse.data };
          });
          
          const analyticsResults = await Promise.all(analyticsPromises);
          const analyticsMap: Record<number, NodeAnalytics> = {};
          
          analyticsResults.forEach(({ nodeId, analytics }) => {
            if (analytics) {
              analyticsMap[nodeId] = analytics;
            }
          });
          
          setNodeAnalytics(analyticsMap);
        }
      } catch (error) {
        console.error("Error fetching nodes data:", error);
        setNodes([]);
        setNodeAnalytics({});
      } finally {
        setLoading(false);
      }
    };

    fetchNodesData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchNodesData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefreshNode = async (nodeId: number) => {
    try {
      // Fetch updated analytics for the specific node
      const analyticsResponse = await apiClient.getNodeAnalytics(nodeId);
      if (analyticsResponse.data) {
        setNodeAnalytics(prev => ({
          ...prev,
          [nodeId]: analyticsResponse.data
        }));
        
        const node = nodes.find(n => n.id === nodeId);
        toast({
          title: "Refreshed",
          description: `Updated data for ${node?.name || 'node'}`,
        });
      }
    } catch (error) {
      toast({
        title: "Error", 
        description: "Failed to refresh node data",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div>
        <h2 className="text-lg font-medium mb-4">Active Autoscaling Nodes</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-48 bg-dark-bg-light/20 rounded-lg animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div>
        <h2 className="text-lg font-medium mb-4">Active Autoscaling Nodes</h2>
        <div className="text-center py-12 text-muted-foreground">
          <p>No active nodes found. Add some nodes to see their metrics.</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-medium mb-4">Active Autoscaling Nodes</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {nodes.slice(0, 8).map((node) => {
          const analytics = nodeAnalytics[node.id] || { 
            avg_cpu_utilization: 0, 
            avg_memory_utilization: 0, 
            current_instances: 0, 
            max_instances: 0 
          };
          
          const getNodeStatus = (): "healthy" | "warning" | "error" | "inactive" => {
            if (!node.last_heartbeat) return "inactive";
            
            const lastHeartbeat = new Date(node.last_heartbeat + 'Z'); // Ensure UTC
            const now = new Date();
            const timeDiff = now.getTime() - lastHeartbeat.getTime();
            const minutesDiff = timeDiff / (1000 * 60);
            
            if (minutesDiff > 10) return "error";
            if (minutesDiff > 5) return "warning";
            return "healthy";
          };
          
          return (
            <InstancePoolCard
              key={node.id}
              name={node.name}
              instances={analytics.current_instances}
              maxInstances={analytics.max_instances}
              status={getNodeStatus()}
              region={node.region}
              cpuUsage={Math.round(analytics.avg_cpu_utilization)}
              memoryUsage={Math.round(analytics.avg_memory_utilization)}
              onRefresh={() => handleRefreshNode(node.id)}
            />
          );
        })}
      </div>
    </div>
  );
}
