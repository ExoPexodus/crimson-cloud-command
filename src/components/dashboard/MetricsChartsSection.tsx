import { MetricsChart } from "@/components/dashboard/MetricsChart";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { useSystemAnalytics } from "@/lib/hooks";
import { Card, CardContent, Skeleton } from "@mui/material";

interface PoolAnalytics {
  id: number;
  timestamp: string;
  current_instances: number;
  avg_cpu_utilization: number;
}

export const MetricsChartsSection = () => {
  const { data: analytics, isLoading, error } = useSystemAnalytics();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="space-y-2">
              <Skeleton className="h-4 w-[250px]" />
              <Skeleton className="h-4 w-[200px]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="space-y-2">
              <Skeleton className="h-4 w-[250px]" />
              <Skeleton className="h-4 w-[200px]" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">Unable to load metrics data</p>
        </CardContent>
      </Card>
    );
  }

  // Safely access data with proper type checking
  const systemData = analytics as any;
  const pools = systemData?.pools || [];
  const instances = systemData?.instances || [];

  // Calculate total metrics
  const totalCpuUtilization = pools.reduce((acc: number, pool: any) => acc + (pool?.avg_cpu_utilization || 0), 0) / Math.max(pools.length, 1);
  const totalMemoryUtilization = pools.reduce((acc: number, pool: any) => acc + (pool?.avg_memory_utilization || 0), 0) / Math.max(pools.length, 1);

  const [poolActivityData, setPoolActivityData] = useState<Array<{ name: string; value: number }>>([]);
  const [instanceCountData, setInstanceCountData] = useState<Array<{ name: string; value: number }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetricsData = async () => {
      try {
        const response = await apiClient.getPoolAnalytics(undefined, 24);
        if (response.data) {
          // Process pool analytics data for charts
          const groupedByHour = response.data.reduce((acc: Record<string, { pools: number; instances: number }>, item: PoolAnalytics) => {
            const hour = new Date(item.timestamp).getHours();
            const hourKey = `${hour.toString().padStart(2, '0')}:00`;
            
            if (!acc[hourKey]) {
              acc[hourKey] = { pools: 0, instances: 0 };
            }
            acc[hourKey].pools += 1;
            acc[hourKey].instances += item.current_instances;
            return acc;
          }, {});

          // Convert to chart data format
          const poolChartData = Object.entries(groupedByHour).map(([hour, data]) => ({
            name: hour,
            value: data.pools
          }));

          const instanceChartData = Object.entries(groupedByHour).map(([hour, data]) => ({
            name: hour,
            value: data.instances
          }));

          setPoolActivityData(poolChartData);
          setInstanceCountData(instanceChartData);
        }
      } catch (error) {
        console.error("Error fetching metrics data:", error);
        // Set empty arrays if no data
        setPoolActivityData([]);
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
  );
};
