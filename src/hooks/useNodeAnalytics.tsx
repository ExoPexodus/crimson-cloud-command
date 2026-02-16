import { useState, useEffect, useCallback } from "react";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";

interface NodeHealthData {
    node_id: number;
    node_name: string;
    current_status: string;
    uptime_percent: number;
    online_seconds: number;
    offline_seconds: number;
    periods: Array<{
        status: string;
        start: string;
        end: string;
    }>;
    last_heartbeat: string | null;
    period_hours: number;
}

interface NodeResourceData {
    timestamp: string;
    avg_cpu: number;
    avg_memory: number;
    max_cpu: number;
    max_memory: number;
    total_instances: number;
}

type TimeRange = "1h" | "6h" | "24h" | "7d" | "30d";

const timeRangeToHours: Record<TimeRange, number> = {
    "1h": 1,
    "6h": 6,
    "24h": 24,
    "7d": 168,
    "30d": 720,
};

const timeRangeToInterval: Record<TimeRange, string> = {
    "1h": "minute",
    "6h": "hour",
    "24h": "hour",
    "7d": "hour",
    "30d": "day",
};

export function useNodeAnalytics(nodeId: number, initialTimeRange: TimeRange = "24h") {
    const { toast } = useToast();
    const [timeRange, setTimeRange] = useState<TimeRange>(initialTimeRange);
    const [healthData, setHealthData] = useState<NodeHealthData | null>(null);
    const [resourceData, setResourceData] = useState<NodeResourceData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        if (!nodeId) return;

        try {
            setLoading(true);
            setError(null);

            const hours = timeRangeToHours[timeRange];
            const interval = timeRangeToInterval[timeRange];

            // Fetch both datasets in parallel
            const [healthResponse, resourceResponse] = await Promise.all([
                apiClient.getNodeHealth(nodeId, hours),
                apiClient.getNodeResources(nodeId, hours, interval),
            ]);

            if (healthResponse.data) {
                setHealthData(healthResponse.data);
            } else if (healthResponse.error) {
                console.error("Error fetching node health:", healthResponse.error);
            }

            if (resourceResponse.data) {
                setResourceData(resourceResponse.data);
            } else if (resourceResponse.error) {
                console.error("Error fetching node resources:", resourceResponse.error);
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Unknown error";
            setError(errorMessage);
            console.error("Error fetching node analytics:", err);
            toast({
                title: "Error",
                description: "Failed to fetch node analytics",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    }, [nodeId, timeRange, toast]);

    useEffect(() => {
        fetchData();
        // Auto-refresh every 60 seconds
        const interval = setInterval(fetchData, 60000);
        return () => clearInterval(interval);
    }, [fetchData]);

    const handleTimeRangeChange = (newRange: TimeRange) => {
        setTimeRange(newRange);
    };

    return {
        timeRange,
        setTimeRange: handleTimeRangeChange,
        healthData,
        resourceData,
        loading,
        error,
        refresh: fetchData,
    };
}

export type { TimeRange, NodeHealthData, NodeResourceData };
