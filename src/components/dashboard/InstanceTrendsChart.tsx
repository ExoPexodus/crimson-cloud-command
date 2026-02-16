import { useMemo } from "react";
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp } from "lucide-react";
import type { InstanceTrendData } from "@/hooks/useAnalyticsCharts";

interface InstanceTrendsChartProps {
    data: InstanceTrendData[];
    loading?: boolean;
}

export function InstanceTrendsChart({ data, loading }: InstanceTrendsChartProps) {
    // Format data for the chart
    const chartData = useMemo(() => {
        return data.map((item) => ({
            ...item,
            // Format timestamp to readable time
            time: formatTime(item.timestamp),
            instances: item.total_instances,
        }));
    }, [data]);

    if (loading) {
        return (
            <Card className="glass-card h-[300px]">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-primary" />
                        Instance Count Trends
                    </CardTitle>
                </CardHeader>
                <CardContent className="h-[240px] flex items-center justify-center">
                    <div className="animate-pulse text-muted-foreground">Loading chart data...</div>
                </CardContent>
            </Card>
        );
    }

    if (data.length === 0) {
        return (
            <Card className="glass-card h-[300px]">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-primary" />
                        Instance Count Trends
                    </CardTitle>
                </CardHeader>
                <CardContent className="h-[240px] flex items-center justify-center">
                    <div className="text-muted-foreground text-sm">No data available for this time range</div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="glass-card h-[300px]">
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-primary" />
                    Instance Count Trends
                </CardTitle>
            </CardHeader>
            <CardContent className="h-[240px]">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                        data={chartData}
                        margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                        <defs>
                            <linearGradient id="instanceGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#14B8A6" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#14B8A6" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.3} />
                        <XAxis
                            dataKey="time"
                            stroke="#888"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            stroke="#888"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                            allowDecimals={false}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: "#1a1a2e",
                                border: "1px solid #333",
                                borderRadius: "8px",
                                fontSize: "12px",
                            }}
                            labelStyle={{ color: "#fff" }}
                            formatter={(value: number) => [value, "Instances"]}
                        />
                        <Legend
                            wrapperStyle={{ fontSize: "11px" }}
                            iconType="circle"
                        />
                        <Area
                            type="monotone"
                            dataKey="instances"
                            name="Running Instances"
                            stroke="#14B8A6"
                            strokeWidth={2}
                            fill="url(#instanceGradient)"
                            dot={false}
                            activeDot={{ r: 4, fill: "#14B8A6" }}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}

function formatTime(timestamp: string): string {
    try {
        const date = new Date(timestamp);
        const hours = date.getHours().toString().padStart(2, "0");
        const minutes = date.getMinutes().toString().padStart(2, "0");
        return `${hours}:${minutes}`;
    } catch {
        return timestamp;
    }
}
