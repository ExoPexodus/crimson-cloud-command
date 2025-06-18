
import { MetricsChart } from "@/components/dashboard/MetricsChart";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

interface NodeAnalytics {
  avg_cpu_utilization: number;
  avg_memory_utilization: number;
  current_instances: number;
  active_instances: number;
  max_instances: number;
  oracle_pool_id: string;
}

export function MetricsChartsSection() {
  const [nodeActivityData, setNodeActivityData] = useState<Array<{ name: string; value: number }>>([]);
  const [instanceCountData, setInstanceCountData] = useState<Array<{ name: string; value: number }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetricsData = async () => {
      try {
        const nodesResponse = await apiClient.getNodes();
        if (nodesResponse.data) {
          // Get analytics for each node
          const analyticsPromises = nodesResponse.data.map(async (node: any) => {
            try {
              const response = await apiClient.getNodeAnalytics(node.id);
              return { nodeId: node.id, nodeName: node.name, analytics: response.data };
            } catch (error) {
              return { nodeId: node.id, nodeName: node.name, analytics: null };
            }
          });

          const results = await Promise.all(analyticsPromises);
          
          // Process node analytics data for charts
          const nodeChartData = results
            .filter(result => result.analytics)
            .map(result => ({
              name: result.nodeName,
              value: 1 // Each active node counts as 1
            }));

          const instanceChartData = results
            .filter(result => result.analytics)
            .map(result => ({
              name: result.nodeName,
              value: result.analytics.current_instances || 0
            }));

          setNodeActivityData(nodeChartData);
          setInstanceCountData(instanceChartData);
        }
      } catch (error) {
        console.error("Error fetching metrics data:", error);
        // Set empty arrays if no data
        setNodeActivityData([]);
        setInstanceCountData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchMetricsData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchMetricsData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="h-64 bg-dark-bg-light/20 rounded-lg animate-pulse"></div>
        <div className="h-64 bg-dark-bg-light/20 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <MetricsChart
        data={nodeActivityData}
        title="Active Nodes"
        color="#20B2AA"
      />
      <MetricsChart
        data={instanceCountData}
        title="Total Instances"
        color="#16A085"
      />
    </div>
  );
}
