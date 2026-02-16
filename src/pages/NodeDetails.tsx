import { useParams, useNavigate } from "react-router-dom";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useNodeAnalytics, TimeRange } from "@/hooks/useNodeAnalytics";
import { NodeHealthTimeline } from "@/components/dashboard/NodeHealthTimeline";
import { NodeResourceCharts } from "@/components/dashboard/NodeResourceCharts";
import { NodeLifecycleLogs } from "@/components/dashboard/NodeLifecycleLogs";
import { ArrowLeft, Server, RefreshCw, MapPin, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";

const timeRangeOptions: { value: TimeRange; label: string }[] = [
    { value: "1h", label: "1H" },
    { value: "6h", label: "6H" },
    { value: "24h", label: "24H" },
    { value: "7d", label: "7D" },
    { value: "30d", label: "30D" },
];

interface NodeInfo {
    id: number;
    name: string;
    region: string;
    status: string;
    last_heartbeat: string | null;
}

const NodeDetails = () => {
    const { nodeId } = useParams<{ nodeId: string }>();
    const navigate = useNavigate();
    const numericNodeId = nodeId ? parseInt(nodeId, 10) : 0;

    const [nodeInfo, setNodeInfo] = useState<NodeInfo | null>(null);
    const [nodeLoading, setNodeLoading] = useState(true);

    const {
        timeRange,
        setTimeRange,
        healthData,
        resourceData,
        loading,
        refresh,
    } = useNodeAnalytics(numericNodeId, "24h");

    // Fetch basic node info
    useEffect(() => {
        const fetchNodeInfo = async () => {
            if (!numericNodeId) return;
            try {
                const response = await apiClient.getNodes();
                if (response.data) {
                    const node = response.data.find((n: any) => n.id === numericNodeId);
                    if (node) {
                        setNodeInfo({
                            id: node.id,
                            name: node.name,
                            region: node.region,
                            status: node.status,
                            last_heartbeat: node.last_heartbeat,
                        });
                    }
                }
            } catch (error) {
                console.error("Error fetching node info:", error);
            } finally {
                setNodeLoading(false);
            }
        };
        fetchNodeInfo();
    }, [numericNodeId]);

    if (!nodeId || isNaN(numericNodeId)) {
        return (
            <SidebarProvider>
                <div className="min-h-screen flex w-full">
                    <AppSidebar />
                    <div className="flex-1 flex flex-col overflow-hidden">
                        <Header />
                        <div className="flex-1 flex items-center justify-center">
                            <div className="text-muted-foreground">Invalid node ID</div>
                        </div>
                    </div>
                </div>
            </SidebarProvider>
        );
    }

    return (
        <SidebarProvider>
            <div className="min-h-screen flex w-full">
                <AppSidebar />
                <div className="flex-1 flex flex-col overflow-hidden">
                    <Header />
                    <div className="flex-1 overflow-auto p-4 md:p-6 teal-scrollbar">
                        <div className="max-w-7xl mx-auto">
                            {/* Header with back button */}
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-4">
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => navigate(-1)}
                                        className="gap-2"
                                    >
                                        <ArrowLeft className="h-4 w-4" />
                                        Back
                                    </Button>

                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                                            <Server className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <h1 className="text-xl font-semibold">
                                                {nodeLoading ? "Loading..." : nodeInfo?.name || `Node ${nodeId}`}
                                            </h1>
                                            {nodeInfo && (
                                                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                                    <span className="flex items-center gap-1">
                                                        <MapPin className="h-3 w-3" />
                                                        {nodeInfo.region}
                                                    </span>
                                                    <span className={cn(
                                                        "px-1.5 py-0.5 rounded text-xs font-medium",
                                                        nodeInfo.status === "ACTIVE" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                                                    )}>
                                                        {nodeInfo.status}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Time range and refresh controls */}
                                <div className="flex items-center gap-2">
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

                            {/* Node Health Timeline */}
                            <div className="mb-6">
                                <NodeHealthTimeline data={healthData} loading={loading} />
                            </div>

                            {/* Resource Charts */}
                            <div className="mb-6">
                                <NodeResourceCharts data={resourceData} loading={loading} />
                            </div>

                            {/* Node Lifecycle Logs */}
                            <div className="mb-6">
                                <NodeLifecycleLogs nodeId={numericNodeId} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </SidebarProvider>
    );
};

export default NodeDetails;
