import { useMemo } from "react";
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Cpu, HardDrive } from "lucide-react";
import type { NodeResourceData } from "@/hooks/useNodeAnalytics";

interface NodeResourceChartsProps {
    data: NodeResourceData[];
    loading?: boolean;
}

export function NodeResourceCharts({ data, loading }: NodeResourceChartsProps) {
    const chartData = useMemo(() => {
        return data.map((item) => ({
            ...item,
            time: formatTime(item.timestamp),
        }));
    }, [data]);

    if (loading) {
        return (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card className="glass-card h-[280px]">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <Cpu className="h-4 w-4 text-orange-400" />
                            CPU Utilization
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="h-[220px] flex items-center justify-center">
                        <div className="animate-pulse text-muted-foreground">Loading...</div>
                    </CardContent>
                </Card>
                <Card className="glass-card h-[280px]">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <HardDrive className="h-4 w-4 text-cyan-400" />
                            Memory Utilization
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="h-[220px] flex items-center justify-center">
                        <div className="animate-pulse text-muted-foreground">Loading...</div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (data.length === 0) {
        return (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <Card className="glass-card h-[280px]">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <Cpu className="h-4 w-4 text-orange-400" />
                            CPU Utilization
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="h-[220px] flex items-center justify-center">
                        <div className="text-muted-foreground text-sm">No data available</div>
                    </CardContent>
                </Card>
                <Card className="glass-card h-[280px]">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium flex items-center gap-2">
                            <HardDrive className="h-4 w-4 text-cyan-400" />
                            Memory Utilization
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="h-[220px] flex items-center justify-center">
                        <div className="text-muted-foreground text-sm">No data available</div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* CPU Chart */}
            <Card className="glass-card h-[280px]">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Cpu className="h-4 w-4 text-orange-400" />
                        CPU Utilization
                    </CardTitle>
                </CardHeader>
                <CardContent className="h-[220px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="cpuGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#F97316" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#F97316" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.3} />
                            <XAxis dataKey="time" stroke="#888" fontSize={11} tickLine={false} axisLine={false} />
                            <YAxis stroke="#888" fontSize={11} tickLine={false} axisLine={false} domain={[0, 100]} unit="%" />
                            <Tooltip
                                contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #333", borderRadius: "8px", fontSize: "12px" }}
                                formatter={(value: number) => [`${value.toFixed(1)}%`, "CPU"]}
                            />
                            <ReferenceLine y={80} stroke="#EF4444" strokeDasharray="3 3" opacity={0.5} />
                            <ReferenceLine y={60} stroke="#F59E0B" strokeDasharray="3 3" opacity={0.3} />
                            <Area
                                type="monotone"
                                dataKey="avg_cpu"
                                name="Avg CPU"
                                stroke="#F97316"
                                strokeWidth={2}
                                fill="url(#cpuGradient)"
                                dot={false}
                                activeDot={{ r: 4, fill: "#F97316" }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            {/* Memory Chart */}
            <Card className="glass-card h-[280px]">
                <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <HardDrive className="h-4 w-4 text-cyan-400" />
                        Memory Utilization
                    </CardTitle>
                </CardHeader>
                <CardContent className="h-[220px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="memoryGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#0EA5E9" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#0EA5E9" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.3} />
                            <XAxis dataKey="time" stroke="#888" fontSize={11} tickLine={false} axisLine={false} />
                            <YAxis stroke="#888" fontSize={11} tickLine={false} axisLine={false} domain={[0, 100]} unit="%" />
                            <Tooltip
                                contentStyle={{ backgroundColor: "#1a1a2e", border: "1px solid #333", borderRadius: "8px", fontSize: "12px" }}
                                formatter={(value: number) => [`${value.toFixed(1)}%`, "Memory"]}
                            />
                            <ReferenceLine y={80} stroke="#EF4444" strokeDasharray="3 3" opacity={0.5} />
                            <ReferenceLine y={60} stroke="#F59E0B" strokeDasharray="3 3" opacity={0.3} />
                            <Area
                                type="monotone"
                                dataKey="avg_memory"
                                name="Avg Memory"
                                stroke="#0EA5E9"
                                strokeWidth={2}
                                fill="url(#memoryGradient)"
                                dot={false}
                                activeDot={{ r: 4, fill: "#0EA5E9" }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>
        </div>
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
