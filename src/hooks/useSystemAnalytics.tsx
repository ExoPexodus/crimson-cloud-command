import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { formatLocalTime } from "@/lib/dateUtils";

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

export function useSystemAnalytics() {
  const { toast } = useToast();
  const [analytics, setAnalytics] = useState<SystemAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
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

  const formatTime = (dateString: string) => formatLocalTime(dateString);

  return {
    analytics,
    loading,
    refreshing,
    handleRefresh,
    formatTime,
  };
}
