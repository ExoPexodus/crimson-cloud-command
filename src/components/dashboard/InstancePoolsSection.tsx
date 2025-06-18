
import { useToast } from "@/hooks/use-toast";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

interface Node {
  id: number;
  name: string;
  region: string;
  status: "active" | "inactive" | "error";
  last_heartbeat?: string;
  created_at: string;
}

interface NodeAnalytics {
  avg_cpu_utilization: number;
  avg_memory_utilization: number;
  current_instances: number;
  active_instances: number;
  max_instances: number;
  oracle_pool_id: string;
}

export function InstancePoolsSection() {
  const { toast } = useToast();
  const [nodes, setNodes] = useState<Node[]>([]);
  const [nodeMetrics, setNodeMetrics] = useState<Record<number, NodeAnalytics>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNodesData = async () => {
      try {
        // Fetch nodes
        const nodesResponse = await apiClient.getNodes();
        if (nodesResponse.data) {
          setNodes(nodesResponse.data);
          
          // Fetch analytics for each node
          const analyticsPromises = nodesResponse.data.map(async (node: Node) => {
            try {
              const response = await apiClient.getNodeAnalytics(node.id);
              return { nodeId: node.id, analytics: response.data };
            } catch (error) {
              return { nodeId: node.id, analytics: null };
            }
          });

          const results = await Promise.all(analyticsPromises);
          const metrics: Record<number, NodeAnalytics> = {};
          
          results.forEach(({ nodeId, analytics }) => {
            if (analytics) {
              metrics[nodeId] = analytics;
            }
          });
          setNodeMetrics(metrics);
        }
      } catch (error) {
        console.error("Error fetching nodes data:", error);
        setNodes([]);
        setNodeMetrics({});
      } finally {
        setLoading(false);
      }
    };

    fetchNodesData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchNodesData, 30000);
    return () => clearInterval(interval);
  }, []);

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
          <p>No active nodes found. Add some nodes to see their status.</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-medium mb-4">Active Autoscaling Nodes Overview</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {nodes.slice(0, 8).map((node) => {
          const metrics = nodeMetrics[node.id];
          const status = node.last_heartbeat ? "healthy" : "inactive";
          
          return (
            <div
              key={node.id}
              className="glass-card p-4 rounded-lg border border-dark-bg-light/30"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-medium text-sm">{node.name}</h3>
                  <p className="text-xs text-muted-foreground">{node.region}</p>
                </div>
                <div className={`w-2 h-2 rounded-full ${
                  status === "healthy" ? "bg-green-500" : "bg-red-500"
                }`} />
              </div>
              
              {metrics && (
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">CPU:</span>
                    <span>{Math.round(metrics.avg_cpu_utilization)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Memory:</span>
                    <span>{Math.round(metrics.avg_memory_utilization)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Instances:</span>
                    <span>{metrics.current_instances}/{metrics.max_instances}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
