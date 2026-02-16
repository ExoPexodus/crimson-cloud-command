import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, CheckCircle, XCircle } from "lucide-react";
import type { NodeHealthData } from "@/hooks/useNodeAnalytics";
import { cn } from "@/lib/utils";

interface NodeHealthTimelineProps {
    data: NodeHealthData | null;
    loading?: boolean;
}

export function NodeHealthTimeline({ data, loading }: NodeHealthTimelineProps) {
    // Calculate timeline segments
    const segments = useMemo(() => {
        if (!data?.periods || data.periods.length === 0) return [];

        const totalDuration = data.online_seconds + data.offline_seconds;
        if (totalDuration === 0) return [];

        return data.periods.map((period) => {
            const start = new Date(period.start).getTime();
            const end = new Date(period.end).getTime();
            const duration = (end - start) / 1000; // in seconds
            const widthPercent = (duration / totalDuration) * 100;

            return {
                ...period,
                widthPercent: Math.max(widthPercent, 0.5), // Minimum 0.5% for visibility
                duration,
            };
        });
    }, [data]);

    if (loading) {
        return (
            <Card className="glass-card">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Activity className="h-4 w-4 text-primary" />
                        Node Health Timeline
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="h-12 bg-muted/20 rounded animate-pulse" />
                </CardContent>
            </Card>
        );
    }

    if (!data) {
        return (
            <Card className="glass-card">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Activity className="h-4 w-4 text-primary" />
                        Node Health Timeline
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="text-muted-foreground text-sm text-center py-4">
                        No health data available
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="glass-card">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Activity className="h-4 w-4 text-primary" />
                        Node Health Timeline
                    </CardTitle>

                    {/* Uptime percentage badge */}
                    <div className={cn(
                        "flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium",
                        data.uptime_percent >= 99 ? "bg-green-500/20 text-green-400" :
                            data.uptime_percent >= 95 ? "bg-yellow-500/20 text-yellow-400" :
                                "bg-red-500/20 text-red-400"
                    )}>
                        {data.uptime_percent >= 99 ? (
                            <CheckCircle className="h-3 w-3" />
                        ) : (
                            <XCircle className="h-3 w-3" />
                        )}
                        {data.uptime_percent.toFixed(1)}% uptime
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {/* Status info */}
                <div className="flex items-center gap-4 mb-3 text-xs text-muted-foreground">
                    <span>Current: <span className={cn(
                        "font-medium",
                        data.current_status === "ACTIVE" ? "text-green-400" : "text-red-400"
                    )}>{data.current_status}</span></span>
                    {data.last_heartbeat && (
                        <span>Last heartbeat: {formatRelativeTime(data.last_heartbeat)}</span>
                    )}
                </div>

                {/* Timeline bar */}
                <div className="h-8 rounded-lg overflow-hidden flex bg-muted/20">
                    {segments.map((segment, index) => (
                        <div
                            key={index}
                            className={cn(
                                "h-full transition-all duration-300 relative group",
                                segment.status === "online" ? "bg-green-500" : "bg-red-500"
                            )}
                            style={{ width: `${segment.widthPercent}%` }}
                            title={`${segment.status}: ${formatDuration(segment.duration)}`}
                        >
                            {/* Tooltip on hover */}
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-popover text-popover-foreground text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                                {segment.status === "online" ? "Online" : "Offline"}: {formatDuration(segment.duration)}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Legend */}
                <div className="flex items-center gap-4 mt-3 text-xs">
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-green-500" />
                        <span className="text-muted-foreground">Online ({formatDuration(data.online_seconds)})</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded bg-red-500" />
                        <span className="text-muted-foreground">Offline ({formatDuration(data.offline_seconds)})</span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

function formatDuration(seconds: number): string {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.round(seconds / 3600)}h`;
    return `${Math.round(seconds / 86400)}d`;
}

function formatRelativeTime(timestamp: string): string {
    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.round(diffMs / 60000);

        if (diffMins < 1) return "just now";
        if (diffMins < 60) return `${diffMins}m ago`;
        const diffHours = Math.round(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        const diffDays = Math.round(diffHours / 24);
        return `${diffDays}d ago`;
    } catch {
        return timestamp;
    }
}
