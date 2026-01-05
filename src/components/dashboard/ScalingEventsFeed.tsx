import { TrendingUp, TrendingDown, Activity, Clock } from "lucide-react";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

interface ScalingEvent {
  id: number;
  poolId: number;
  nodeId: number;
  oraclePoolId: string;
  nodeName: string | null;
  eventType: "SCALE_UP" | "SCALE_DOWN" | "MANUAL_SCALE" | "FAILED";
  reason: string | null;
  currentInstances: number;
  timestamp: string;
}

interface PoolAnalytics {
  id: number;
  pool_id: number;
  node_id: number;
  oracle_pool_id: string;
  timestamp: string;
  current_instances: number;
  scaling_event: string | null;
  scaling_reason: string | null;
  node_name: string | null;
}

export function ScalingEventsFeed() {
  const [events, setEvents] = useState<ScalingEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchScalingEvents = async () => {
      try {
        const response = await apiClient.getPoolAnalytics(undefined, 24);
        if (response.data) {
          const scalingEvents = response.data
            .filter((p: PoolAnalytics) => p.scaling_event)
            .map((p: PoolAnalytics) => ({
              id: p.id,
              poolId: p.pool_id,
              nodeId: p.node_id,
              oraclePoolId: p.oracle_pool_id,
              nodeName: p.node_name,
              eventType: parseEventType(p.scaling_event),
              reason: p.scaling_reason,
              currentInstances: p.current_instances,
              timestamp: p.timestamp,
            }))
            .slice(0, 10);

          setEvents(scalingEvents);
        }
      } catch (error) {
        console.error("Error fetching scaling events:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchScalingEvents();
    const interval = setInterval(fetchScalingEvents, 60000);
    return () => clearInterval(interval);
  }, []);

  const parseEventType = (event: string | null): ScalingEvent["eventType"] => {
    if (!event) return "MANUAL_SCALE";
    const upper = event.toUpperCase();
    if (upper.includes("UP") || upper.includes("INCREASE")) return "SCALE_UP";
    if (upper.includes("DOWN") || upper.includes("DECREASE")) return "SCALE_DOWN";
    if (upper.includes("FAIL")) return "FAILED";
    return "MANUAL_SCALE";
  };

  const getEventIcon = (type: ScalingEvent["eventType"]) => {
    switch (type) {
      case "SCALE_UP":
        return <TrendingUp className="h-4 w-4 text-green-400" />;
      case "SCALE_DOWN":
        return <TrendingDown className="h-4 w-4 text-blue-400" />;
      case "FAILED":
        return <Activity className="h-4 w-4 text-destructive" />;
      default:
        return <Activity className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getEventLabel = (type: ScalingEvent["eventType"]) => {
    switch (type) {
      case "SCALE_UP":
        return "Scaled Up";
      case "SCALE_DOWN":
        return "Scaled Down";
      case "FAILED":
        return "Failed";
      default:
        return "Manual Scale";
    }
  };

  const getEventStyles = (type: ScalingEvent["eventType"]) => {
    switch (type) {
      case "SCALE_UP":
        return "border-l-green-500";
      case "SCALE_DOWN":
        return "border-l-blue-500";
      case "FAILED":
        return "border-l-destructive";
      default:
        return "border-l-muted-foreground";
    }
  };

  if (loading) {
    return (
      <Card className="glass-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Recent Scaling Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-muted/20 rounded animate-pulse" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (events.length === 0) {
    return (
      <Card className="glass-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Recent Scaling Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-muted-foreground text-sm">
            <Activity className="h-8 w-8 mx-auto mb-2 opacity-40" />
            <p>No scaling events in the last 24 hours</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Recent Scaling Events
          <span className="ml-auto text-xs text-muted-foreground font-normal">Last 24h</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2 teal-scrollbar">
          {events.map((event) => (
            <div
              key={event.id}
              className={cn(
                "flex items-start gap-3 p-3 rounded-lg bg-muted/10 border-l-2",
                getEventStyles(event.eventType)
              )}
            >
              <div className="mt-0.5">{getEventIcon(event.eventType)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium truncate">
                    {event.nodeName || `Pool ${event.oraclePoolId.slice(-8)}`}
                  </span>
                  <span className="text-xs px-1.5 py-0.5 rounded bg-muted/30">
                    {getEventLabel(event.eventType)}
                  </span>
                </div>
                {event.reason && (
                  <p className="text-xs text-muted-foreground mt-0.5 truncate">
                    {event.reason}
                  </p>
                )}
                <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {formatDistanceToNow(new Date(event.timestamp + "Z"), { addSuffix: true })}
                  <span className="opacity-60">• {event.currentInstances} instances</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
