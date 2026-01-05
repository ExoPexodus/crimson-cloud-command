import { AlertTriangle, WifiOff, Clock, AlertCircle, X, ChevronDown, ChevronUp } from "lucide-react";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Alert {
  id: string;
  type: "offline" | "warning" | "config_drift" | "scaling_failure";
  severity: "error" | "warning" | "info";
  title: string;
  message: string;
  nodeId?: number;
  nodeName?: string;
  timestamp: string;
}

interface NodeLifecycleLog {
  id: number;
  node_id: number;
  node_name: string | null;
  event_type: string;
  previous_status: string | null;
  new_status: string;
  reason: string | null;
  timestamp: string;
}

interface Node {
  id: number;
  name: string;
  status: string;
  last_heartbeat?: string;
}

export function AlertsStrip() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchAlerts = async () => {
      const newAlerts: Alert[] = [];

      try {
        // Fetch recent lifecycle logs for offline events
        const lifecycleResponse = await apiClient.getNodeLifecycleLogs(undefined, undefined, 50);
        if (lifecycleResponse.data) {
          const recentOffline = lifecycleResponse.data
            .filter((log: NodeLifecycleLog) => log.event_type === "WENT_OFFLINE")
            .slice(0, 5);

          recentOffline.forEach((log: NodeLifecycleLog) => {
            const alertId = `offline-${log.node_id}-${log.id}`;
            if (!dismissedAlerts.has(alertId)) {
              newAlerts.push({
                id: alertId,
                type: "offline",
                severity: "error",
                title: "Node Offline",
                message: `${log.node_name || `Node ${log.node_id}`} went offline`,
                nodeId: log.node_id,
                nodeName: log.node_name || undefined,
                timestamp: log.timestamp,
              });
            }
          });
        }

        // Fetch nodes with stale heartbeats (warning state)
        const nodesResponse = await apiClient.getNodes();
        if (nodesResponse.data) {
          nodesResponse.data.forEach((node: Node) => {
            if (node.last_heartbeat && node.status !== "OFFLINE") {
              const lastHeartbeat = new Date(node.last_heartbeat + "Z");
              const now = new Date();
              const minutesDiff = (now.getTime() - lastHeartbeat.getTime()) / (1000 * 60);

              if (minutesDiff > 5 && minutesDiff <= 10) {
                const alertId = `warning-${node.id}`;
                if (!dismissedAlerts.has(alertId)) {
                  newAlerts.push({
                    id: alertId,
                    type: "warning",
                    severity: "warning",
                    title: "Stale Heartbeat",
                    message: `${node.name} hasn't reported in ${Math.round(minutesDiff)} minutes`,
                    nodeId: node.id,
                    nodeName: node.name,
                    timestamp: node.last_heartbeat,
                  });
                }
              }
            }
          });
        }

        // Fetch pool analytics for scaling failures
        const poolResponse = await apiClient.getPoolAnalytics(undefined, 6);
        if (poolResponse.data) {
          const failedScaling = poolResponse.data
            .filter((p) => p.scaling_event?.includes("FAILED"))
            .slice(0, 3);

          failedScaling.forEach((pool) => {
            const alertId = `scaling-${pool.id}`;
            if (!dismissedAlerts.has(alertId)) {
              newAlerts.push({
                id: alertId,
                type: "scaling_failure",
                severity: "error",
                title: "Scaling Failed",
                message: pool.scaling_reason || "Scaling operation failed",
                nodeId: pool.node_id,
                timestamp: pool.timestamp,
              });
            }
          });
        }
      } catch (error) {
        console.error("Error fetching alerts:", error);
      }

      setAlerts(newAlerts);
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [dismissedAlerts]);

  const dismissAlert = (alertId: string) => {
    setDismissedAlerts((prev) => new Set([...prev, alertId]));
  };

  const getAlertIcon = (type: Alert["type"]) => {
    switch (type) {
      case "offline":
        return <WifiOff className="h-4 w-4" />;
      case "warning":
        return <Clock className="h-4 w-4" />;
      case "config_drift":
        return <AlertCircle className="h-4 w-4" />;
      case "scaling_failure":
        return <AlertTriangle className="h-4 w-4" />;
    }
  };

  const getSeverityStyles = (severity: Alert["severity"]) => {
    switch (severity) {
      case "error":
        return "bg-destructive/10 border-destructive/30 text-destructive";
      case "warning":
        return "bg-yellow-500/10 border-yellow-500/30 text-yellow-400";
      case "info":
        return "bg-primary/10 border-primary/30 text-primary";
    }
  };

  if (alerts.length === 0) {
    return null;
  }

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-yellow-400" />
          <span className="text-sm font-medium">Active Alerts</span>
          <span className="bg-destructive/20 text-destructive text-xs px-2 py-0.5 rounded-full font-medium">
            {alerts.length}
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="h-6 px-2 text-muted-foreground hover:text-foreground"
        >
          {isCollapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
        </Button>
      </div>

      {!isCollapsed && (
        <div className="space-y-2">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={cn(
                "flex items-center justify-between p-3 rounded-lg border",
                getSeverityStyles(alert.severity)
              )}
            >
              <div className="flex items-center gap-3">
                {getAlertIcon(alert.type)}
                <div>
                  <div className="text-sm font-medium">{alert.title}</div>
                  <div className="text-xs opacity-80">{alert.message}</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs opacity-60">
                  {new Date(alert.timestamp + "Z").toLocaleTimeString()}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => dismissAlert(alert.id)}
                  className="h-6 w-6 p-0 opacity-60 hover:opacity-100"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
