
import { MetricsChart } from "@/components/dashboard/MetricsChart";
import { DateRangeSelector } from "@/components/dashboard/DateRangeSelector";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

interface PoolAnalytics {
  id: number;
  node_id: number;
  timestamp: string;
  current_instances: number;
  avg_cpu_utilization: number;
}

export function MetricsChartsSection() {
  const [poolActivityData, setPoolActivityData] = useState<Array<{ name: string; value: number }>>([]);
  const [instanceCountData, setInstanceCountData] = useState<Array<{ name: string; value: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({ from: new Date(Date.now() - 24 * 60 * 60 * 1000), to: new Date(), type: "24h" });

  const fetchMetricsData = async () => {
    try {
      setLoading(true);
      
      // Get both nodes and pool analytics data
      const [nodesResponse, poolResponse] = await Promise.all([
        apiClient.getNodes(),
        apiClient.getPoolAnalytics()
      ]);
      
      if (nodesResponse.data && poolResponse.data) {
        // Filter data by date range
        const filteredData = poolResponse.data.filter((item: PoolAnalytics) => {
          const itemDate = new Date(item.timestamp);
          return itemDate >= dateRange.from && itemDate <= dateRange.to;
        });

        const hoursDiff = Math.ceil((dateRange.to.getTime() - dateRange.from.getTime()) / (1000 * 60 * 60));

        // Group data by appropriate time intervals based on range
        const getTimeKey = (timestamp: string) => {
          const date = new Date(timestamp);
          if (hoursDiff <= 24) {
            // Hourly for 24h or less
            return `${date.getHours().toString().padStart(2, '0')}:00`;
          } else if (hoursDiff <= 168) {
            // Daily for up to 7 days
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          } else {
            // Weekly for longer periods
            const weekStart = new Date(date);
            weekStart.setDate(date.getDate() - date.getDay());
            return weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          }
        };

        const groupedData = filteredData.reduce((acc: Record<string, { activeNodes: Set<number>; totalInstances: number }>, item: PoolAnalytics) => {
          const timeKey = getTimeKey(item.timestamp);
          
          if (!acc[timeKey]) {
            acc[timeKey] = { activeNodes: new Set(), totalInstances: 0 };
          }
          
          // Find the node that corresponds to this pool analytics entry
          const node = nodesResponse.data.find(n => n.id === item.node_id);
          if (node) {
            acc[timeKey].activeNodes.add(node.id);
            acc[timeKey].totalInstances += item.current_instances || 0;
          }
          
          return acc;
        }, {});

        // Convert to chart data format
        const poolChartData = Object.entries(groupedData)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([time, data]) => ({
            name: time,
            value: data.activeNodes.size // Active pools = active nodes
          }));

        const instanceChartData = Object.entries(groupedData)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([time, data]) => ({
            name: time,
            value: data.totalInstances
          }));

        setPoolActivityData(poolChartData);
        setInstanceCountData(instanceChartData);
      }
    } catch (error) {
      console.error("Error fetching metrics data:", error);
      setPoolActivityData([]);
      setInstanceCountData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetricsData();
    
    // Only auto-refresh for 24h view
    if (dateRange.type === "24h") {
      const interval = setInterval(fetchMetricsData, 30000);
      return () => clearInterval(interval);
    }
  }, [dateRange]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="h-64 bg-dark-bg-light/20 rounded-lg animate-pulse"></div>
        <div className="h-64 bg-dark-bg-light/20 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-medium">Analytics</h2>
        <DateRangeSelector 
          onRangeChange={setDateRange}
          defaultRange="24h"
        />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
    </div>
  );
}
