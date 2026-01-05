import { MetricsChart } from "@/components/dashboard/MetricsChart";
import { DateRangeSelector } from "@/components/dashboard/DateRangeSelector";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { parseUTCTimestamp } from "@/lib/dateUtils";

interface PoolAnalytics {
  id: number;
  node_id: number;
  pool_id?: number;
  timestamp: string;
  current_instances: number;
  avg_cpu_utilization: number;
}

export function MetricsChartsSection() {
  const [poolActivityData, setPoolActivityData] = useState<Array<{ name: string; value: number }>>([]);
  const [instanceCountData, setInstanceCountData] = useState<Array<{ name: string; value: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState({ from: new Date(Date.now() - 24 * 60 * 60 * 1000), to: new Date(), type: "24h" });

  const getDateRangeLabel = () => {
    switch (dateRange.type) {
      case "24h":
        return "Last 24 hours";
      case "7d":
        return "Last 7 days";
      case "30d":
        return "Last 30 days";
      case "custom":
        return `${dateRange.from.toLocaleDateString()} - ${dateRange.to.toLocaleDateString()}`;
      default:
        return "Last 24 hours";
    }
  };

  const fetchMetricsData = async () => {
    try {
      setLoading(true);
      
      // Calculate hours from date range to pass to API
      const hours = Math.ceil((dateRange.to.getTime() - dateRange.from.getTime()) / (1000 * 60 * 60));
      
      // Get pool analytics data with calculated hours
      const poolResponse = await apiClient.getPoolAnalytics(undefined, hours);
      
      if (poolResponse.data) {
        // Filter data by date range
        const filteredData = poolResponse.data.filter((item: PoolAnalytics) => {
          const itemDate = parseUTCTimestamp(item.timestamp);
          return itemDate >= dateRange.from && itemDate <= dateRange.to;
        });

        const hoursDiff = Math.ceil((dateRange.to.getTime() - dateRange.from.getTime()) / (1000 * 60 * 60));

        // Group data by appropriate time intervals based on range
        // Parse as UTC and display in local timezone
        const getTimeKey = (timestamp: string) => {
          const date = parseUTCTimestamp(timestamp);
          if (hoursDiff <= 24) {
            // Hourly for 24h or less - show in local time
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

        // FIX: Track unique pool_ids instead of node_ids for "Active Pools" chart
        const groupedData = filteredData.reduce((acc: Record<string, { activePools: Set<number>; totalInstances: number }>, item: PoolAnalytics) => {
          const timeKey = getTimeKey(item.timestamp);
          
          if (!acc[timeKey]) {
            acc[timeKey] = { activePools: new Set(), totalInstances: 0 };
          }
          
          // Use pool_id if available, otherwise fall back to node_id for backwards compatibility
          const poolIdentifier = item.pool_id || item.node_id;
          acc[timeKey].activePools.add(poolIdentifier);
          acc[timeKey].totalInstances += item.current_instances || 0;
          
          return acc;
        }, {});

        // Convert to chart data format
        const poolChartData = Object.entries(groupedData)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([time, data]) => ({
            name: time,
            value: data.activePools.size // Now correctly counts pools, not nodes
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
        <div className="h-64 bg-muted/20 rounded-lg animate-pulse"></div>
        <div className="h-64 bg-muted/20 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  const dateRangeLabel = getDateRangeLabel();
  const hasPoolData = poolActivityData.length > 0;
  const hasInstanceData = instanceCountData.length > 0;

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
        {hasPoolData ? (
          <MetricsChart
            data={poolActivityData}
            title="Active Pools"
            color="#20B2AA"
            dateRangeLabel={dateRangeLabel}
          />
        ) : (
          <div className="p-4 rounded-lg glass-card h-full flex flex-col items-center justify-center min-h-[200px]">
            <p className="text-muted-foreground text-sm text-center">
              No pool activity data available for this time period.
            </p>
            <p className="text-muted-foreground/60 text-xs mt-2 text-center">
              Pool data will appear when autoscaler nodes report metrics.
            </p>
          </div>
        )}
        {hasInstanceData ? (
          <MetricsChart
            data={instanceCountData}
            title="Total Instances" 
            color="#16A085"
            dateRangeLabel={dateRangeLabel}
          />
        ) : (
          <div className="p-4 rounded-lg glass-card h-full flex flex-col items-center justify-center min-h-[200px]">
            <p className="text-muted-foreground text-sm text-center">
              No instance data available for this time period.
            </p>
            <p className="text-muted-foreground/60 text-xs mt-2 text-center">
              Instance counts will appear when autoscaler nodes report metrics.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
