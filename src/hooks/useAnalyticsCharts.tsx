import { useState, useEffect, useCallback } from "react";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";

interface InstanceTrendData {
    timestamp: string;
    total_instances: number;
    active_pools: number;
    avg_cpu: number;
    avg_memory: number;
}

interface ScalingPatternData {
    by_hour: Array<{
        timestamp: string;
        scale_up: number;
        scale_down: number;
        failed: number;
    }>;
    totals: {
        scale_up: number;
        scale_down: number;
        failed: number;
        other: number;
    };
    period_hours: number;
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

export function useAnalyticsCharts(initialTimeRange: TimeRange = "24h") {
    const { toast } = useToast();
    const [timeRange, setTimeRange] = useState<TimeRange>(initialTimeRange);
    const [instanceTrends, setInstanceTrends] = useState<InstanceTrendData[]>([]);
    const [scalingPatterns, setScalingPatterns] = useState<ScalingPatternData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            const hours = timeRangeToHours[timeRange];
            const interval = timeRangeToInterval[timeRange];

            // Fetch both datasets in parallel
            const [trendsResponse, patternsResponse] = await Promise.all([
                apiClient.getInstanceTrends(hours, interval),
                apiClient.getScalingPatterns(hours),
            ]);

            if (trendsResponse.data) {
                setInstanceTrends(trendsResponse.data);
            } else if (trendsResponse.error) {
                console.error("Error fetching instance trends:", trendsResponse.error);
            }

            if (patternsResponse.data) {
                setScalingPatterns(patternsResponse.data);
            } else if (patternsResponse.error) {
                console.error("Error fetching scaling patterns:", patternsResponse.error);
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Unknown error";
            setError(errorMessage);
            console.error("Error fetching analytics charts:", err);
            toast({
                title: "Error",
                description: "Failed to fetch analytics data",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    }, [timeRange, toast]);

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
        instanceTrends,
        scalingPatterns,
        loading,
        error,
        refresh: fetchData,
    };
}

export type { TimeRange, InstanceTrendData, ScalingPatternData };
