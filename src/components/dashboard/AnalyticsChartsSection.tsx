import { useAnalyticsCharts, TimeRange } from "@/hooks/useAnalyticsCharts";
import { InstanceTrendsChart } from "./InstanceTrendsChart";
import { ScalingPatternsChart } from "./ScalingPatternsChart";
import { Button } from "@/components/ui/button";
import { RefreshCw, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";

const timeRangeOptions: { value: TimeRange; label: string }[] = [
    { value: "1h", label: "1H" },
    { value: "6h", label: "6H" },
    { value: "24h", label: "24H" },
    { value: "7d", label: "7D" },
    { value: "30d", label: "30D" },
];

export function AnalyticsChartsSection() {
    const {
        timeRange,
        setTimeRange,
        instanceTrends,
        scalingPatterns,
        loading,
        refresh,
    } = useAnalyticsCharts("24h");

    return (
        <div className="mb-6">
            {/* Section Header with Time Range Selector */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-primary" />
                    <h2 className="text-sm font-semibold text-foreground">Analytics</h2>
                </div>

                <div className="flex items-center gap-2">
                    {/* Time Range Buttons */}
                    <div className="flex items-center bg-muted/30 rounded-lg p-0.5">
                        {timeRangeOptions.map((option) => (
                            <Button
                                key={option.value}
                                variant="ghost"
                                size="sm"
                                className={cn(
                                    "h-7 px-3 text-xs font-medium transition-all",
                                    timeRange === option.value
                                        ? "bg-primary text-primary-foreground hover:bg-primary/90"
                                        : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                                )}
                                onClick={() => setTimeRange(option.value)}
                            >
                                {option.label}
                            </Button>
                        ))}
                    </div>

                    {/* Refresh Button */}
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 w-7 p-0"
                        onClick={refresh}
                        disabled={loading}
                    >
                        <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                    </Button>
                </div>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <InstanceTrendsChart data={instanceTrends} loading={loading} />
                <ScalingPatternsChart data={scalingPatterns} loading={loading} />
            </div>
        </div>
    );
}
