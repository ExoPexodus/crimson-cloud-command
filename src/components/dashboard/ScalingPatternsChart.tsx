import { useMemo } from "react";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";
import type { ScalingPatternData } from "@/hooks/useAnalyticsCharts";

interface ScalingPatternsChartProps {
    data: ScalingPatternData | null;
    loading?: boolean;
}

export function ScalingPatternsChart({ data, loading }: ScalingPatternsChartProps) {
    // Format data for the chart
    const chartData = useMemo(() => {
        if (!data?.by_hour) return [];
        return data.by_hour.map((item) => ({
            ...item,
            time: formatTime(item.timestamp),
        }));
    }, [data]);

    const totals = data?.totals || { scale_up: 0, scale_down: 0, failed: 0 };

    if (loading) {
        return (
            <Card className="glass-card h-[300px]">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Activity className="h-4 w-4 text-primary" />
                        Scaling Events Distribution
                    </CardTitle>
                </CardHeader>
                <CardContent className="h-[240px] flex items-center justify-center">
                    <div className="animate-pulse text-muted-foreground">Loading chart data...</div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="glass-card h-[300px]">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Activity className="h-4 w-4 text-primary" />
                        Scaling Events Distribution
                    </CardTitle>
                    {/* Summary badges */}
                    <div className="flex items-center gap-3 text-xs">
                        <div className="flex items-center gap-1">
                            <TrendingUp className="h-3 w-3 text-green-400" />
                            <span className="text-green-400 font-medium">{totals.scale_up}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <TrendingDown className="h-3 w-3 text-blue-400" />
                            <span className="text-blue-400 font-medium">{totals.scale_down}</span>
                        </div>
                        {totals.failed > 0 && (
                            <div className="flex items-center gap-1">
                                <AlertTriangle className="h-3 w-3 text-red-400" />
                                <span className="text-red-400 font-medium">{totals.failed}</span>
                            </div>
                        )}
                    </div>
                </div>
            </CardHeader>
            <CardContent className="h-[240px]">
                {chartData.length === 0 ? (
                    <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                        No scaling events in this time range
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                            data={chartData}
                            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                        >
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
                            />
                            <Legend
                                wrapperStyle={{ fontSize: "11px" }}
                                iconType="circle"
                            />
                            <Bar
                                dataKey="scale_up"
                                name="Scale Up"
                                fill="#22C55E"
                                radius={[2, 2, 0, 0]}
                                maxBarSize={20}
                            />
                            <Bar
                                dataKey="scale_down"
                                name="Scale Down"
                                fill="#3B82F6"
                                radius={[2, 2, 0, 0]}
                                maxBarSize={20}
                            />
                            <Bar
                                dataKey="failed"
                                name="Failed"
                                fill="#EF4444"
                                radius={[2, 2, 0, 0]}
                                maxBarSize={20}
                            />
                        </BarChart>
                    </ResponsiveContainer>
                )}
            </CardContent>
        </Card>
    );
}

function formatTime(timestamp: string): string {
    try {
        const date = new Date(timestamp);
        const hours = date.getHours().toString().padStart(2, "0");
        return `${hours}:00`;
    } catch {
        return timestamp;
    }
}
