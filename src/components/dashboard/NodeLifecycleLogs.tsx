import { useState, useEffect, useRef, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { RefreshCw, History, ArrowUp, ArrowDown, Server, Download, FileJson, FileSpreadsheet, Radio } from "lucide-react";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface LifecycleLog {
  id: number;
  node_id: number;
  node_name: string | null;
  event_type: string;
  previous_status: string | null;
  new_status: string;
  reason: string | null;
  triggered_by: string | null;
  extra_data: string | null;
  timestamp: string;
}

interface NodeLifecycleLogsProps {
  nodeId?: number;
  nodes?: Array<{ id: number; name: string }>;
  pollingInterval?: number; // in milliseconds
  enableNotifications?: boolean;
}

export const NodeLifecycleLogs = ({ 
  nodeId, 
  nodes = [], 
  pollingInterval = 15000,
  enableNotifications = true 
}: NodeLifecycleLogsProps) => {
  const { toast } = useToast();
  const [logs, setLogs] = useState<LifecycleLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterNodeId, setFilterNodeId] = useState<string>(nodeId?.toString() || "all");
  const [filterEventType, setFilterEventType] = useState<string>("all");
  const [isPolling, setIsPolling] = useState(true);
  const lastLogIdRef = useRef<number | null>(null);
  const notifiedLogsRef = useRef<Set<number>>(new Set());

  const fetchLogs = useCallback(async (isInitial = false) => {
    try {
      if (!isInitial) setRefreshing(true);
      const params: { node_id?: number; event_type?: string; limit?: number } = { limit: 100 };
      
      if (filterNodeId !== "all") {
        params.node_id = parseInt(filterNodeId);
      }
      if (filterEventType !== "all") {
        params.event_type = filterEventType;
      }
      
      const response = await apiClient.getNodeLifecycleLogs(
        params.node_id,
        params.event_type,
        params.limit
      );
      
      if (response.data) {
        const newLogs = response.data;
        
        // Check for new offline events and show notifications
        if (enableNotifications && !isInitial && newLogs.length > 0) {
          const newOfflineEvents = newLogs.filter(log => 
            log.event_type === "WENT_OFFLINE" && 
            !notifiedLogsRef.current.has(log.id) &&
            (lastLogIdRef.current === null || log.id > lastLogIdRef.current)
          );
          
          newOfflineEvents.forEach(log => {
            notifiedLogsRef.current.add(log.id);
            toast({
              title: "⚠️ Node Went Offline",
              description: `${log.node_name || `Node #${log.node_id}`} went offline${log.reason ? `: ${log.reason}` : ''}`,
              variant: "destructive",
            });
          });

          // Also notify for nodes coming back online
          const newOnlineEvents = newLogs.filter(log => 
            log.event_type === "CAME_ONLINE" && 
            !notifiedLogsRef.current.has(log.id) &&
            (lastLogIdRef.current === null || log.id > lastLogIdRef.current)
          );
          
          newOnlineEvents.forEach(log => {
            notifiedLogsRef.current.add(log.id);
            toast({
              title: "✅ Node Back Online",
              description: `${log.node_name || `Node #${log.node_id}`} is back online`,
            });
          });
        }
        
        // Update last log ID for tracking new events
        if (newLogs.length > 0) {
          const maxId = Math.max(...newLogs.map(l => l.id));
          if (lastLogIdRef.current === null || maxId > lastLogIdRef.current) {
            lastLogIdRef.current = maxId;
          }
        }
        
        setLogs(newLogs);
      }
    } catch (error) {
      console.error("Error fetching lifecycle logs:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filterNodeId, filterEventType, enableNotifications, toast]);

  // Initial fetch
  useEffect(() => {
    fetchLogs(true);
  }, []);

  // Refetch when filters change
  useEffect(() => {
    if (!loading) {
      fetchLogs();
    }
  }, [filterNodeId, filterEventType]);

  // Polling for real-time updates
  useEffect(() => {
    if (!isPolling) return;
    
    const interval = setInterval(() => {
      fetchLogs();
    }, pollingInterval);
    
    return () => clearInterval(interval);
  }, [isPolling, pollingInterval, fetchLogs]);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp + 'Z');
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFullTimestamp = (timestamp: string) => {
    const date = new Date(timestamp + 'Z');
    return date.toISOString();
  };

  const getEventIcon = (eventType: string) => {
    if (eventType === "CAME_ONLINE") {
      return <ArrowUp size={14} className="text-green-500" />;
    }
    return <ArrowDown size={14} className="text-red-500" />;
  };

  const getEventBadge = (eventType: string) => {
    if (eventType === "CAME_ONLINE") {
      return (
        <Badge variant="outline" className="border-green-500/50 text-green-400 bg-green-500/10">
          Came Online
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="border-red-500/50 text-red-400 bg-red-500/10">
        Went Offline
      </Badge>
    );
  };

  const getTriggeredByBadge = (triggeredBy: string | null) => {
    if (!triggeredBy) return null;
    
    const colors: Record<string, string> = {
      heartbeat: "border-blue-500/50 text-blue-400 bg-blue-500/10",
      manual: "border-orange-500/50 text-orange-400 bg-orange-500/10",
      system: "border-purple-500/50 text-purple-400 bg-purple-500/10"
    };
    
    return (
      <Badge variant="outline" className={colors[triggeredBy] || "border-muted"}>
        {triggeredBy}
      </Badge>
    );
  };

  const exportAsJSON = () => {
    const data = logs.map(log => ({
      id: log.id,
      node_id: log.node_id,
      node_name: log.node_name,
      event_type: log.event_type,
      previous_status: log.previous_status,
      new_status: log.new_status,
      reason: log.reason,
      triggered_by: log.triggered_by,
      timestamp: formatFullTimestamp(log.timestamp)
    }));
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `node-lifecycle-logs-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast({
      title: "Export Complete",
      description: `Exported ${logs.length} logs as JSON`,
    });
  };

  const exportAsCSV = () => {
    const headers = ['ID', 'Node ID', 'Node Name', 'Event Type', 'Previous Status', 'New Status', 'Reason', 'Triggered By', 'Timestamp'];
    const rows = logs.map(log => [
      log.id,
      log.node_id,
      log.node_name || '',
      log.event_type,
      log.previous_status || '',
      log.new_status,
      log.reason || '',
      log.triggered_by || '',
      formatFullTimestamp(log.timestamp)
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `node-lifecycle-logs-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast({
      title: "Export Complete",
      description: `Exported ${logs.length} logs as CSV`,
    });
  };

  return (
    <Card className="glass-card">
      <div className="p-4 border-b border-dark-bg-light/30">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <div className="flex items-center gap-2">
            <History size={18} className="text-dark-blue-400" />
            <h3 className="font-semibold">Node Lifecycle Audit Log</h3>
            {isPolling && (
              <Badge variant="outline" className="border-green-500/50 text-green-400 bg-green-500/10 gap-1">
                <Radio size={10} className="animate-pulse" />
                Live
              </Badge>
            )}
          </div>
          
          <div className="flex items-center gap-2 flex-wrap">
            {/* Node Filter */}
            {!nodeId && nodes.length > 0 && (
              <Select value={filterNodeId} onValueChange={setFilterNodeId}>
                <SelectTrigger className="w-[160px] h-8 text-sm bg-dark-bg border-dark-bg-light">
                  <SelectValue placeholder="Filter by node" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Nodes</SelectItem>
                  {nodes.map((node) => (
                    <SelectItem key={node.id} value={node.id.toString()}>
                      {node.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            
            {/* Event Type Filter */}
            <Select value={filterEventType} onValueChange={setFilterEventType}>
              <SelectTrigger className="w-[140px] h-8 text-sm bg-dark-bg border-dark-bg-light">
                <SelectValue placeholder="Event type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Events</SelectItem>
                <SelectItem value="CAME_ONLINE">Came Online</SelectItem>
                <SelectItem value="WENT_OFFLINE">Went Offline</SelectItem>
              </SelectContent>
            </Select>
            
            {/* Export Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 border-dark-bg-light hover:bg-dark-bg-light"
                  disabled={logs.length === 0}
                >
                  <Download size={14} className="mr-1" />
                  Export
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={exportAsJSON}>
                  <FileJson size={14} className="mr-2" />
                  Export as JSON
                </DropdownMenuItem>
                <DropdownMenuItem onClick={exportAsCSV}>
                  <FileSpreadsheet size={14} className="mr-2" />
                  Export as CSV
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            
            {/* Live Toggle */}
            <Button
              variant={isPolling ? "default" : "outline"}
              size="sm"
              className={`h-8 ${isPolling ? 'bg-green-600 hover:bg-green-700' : 'border-dark-bg-light hover:bg-dark-bg-light'}`}
              onClick={() => setIsPolling(!isPolling)}
              title={isPolling ? "Disable live updates" : "Enable live updates"}
            >
              <Radio size={14} className={isPolling ? "animate-pulse" : ""} />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              className="h-8 border-dark-bg-light hover:bg-dark-bg-light"
              onClick={() => fetchLogs()}
              disabled={refreshing}
            >
              <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
            </Button>
          </div>
        </div>
      </div>
      
      <ScrollArea className="h-[400px]">
        {loading ? (
          <div className="p-4 space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-dark-bg-light/20 rounded animate-pulse" />
            ))}
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <History size={32} className="mb-3 opacity-50" />
            <p className="text-sm">No lifecycle events recorded yet</p>
            <p className="text-xs mt-1">Events will appear when nodes go online/offline</p>
          </div>
        ) : (
          <div className="divide-y divide-dark-bg-light/30">
            {logs.map((log) => (
              <div
                key={log.id}
                className="p-4 hover:bg-dark-bg-light/10 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-1 p-1.5 rounded-full bg-dark-bg-light/50">
                    {getEventIcon(log.event_type)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <div className="flex items-center gap-1.5">
                        <Server size={12} className="text-dark-blue-400" />
                        <span className="font-medium text-sm">
                          {log.node_name || `Node #${log.node_id}`}
                        </span>
                      </div>
                      {getEventBadge(log.event_type)}
                      {getTriggeredByBadge(log.triggered_by)}
                    </div>
                    
                    {log.reason && (
                      <p className="text-sm text-muted-foreground mb-1">
                        {log.reason}
                      </p>
                    )}
                    
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{formatTimestamp(log.timestamp)}</span>
                      {log.previous_status && (
                        <span className="flex items-center gap-1">
                          <span className="opacity-60">{log.previous_status}</span>
                          <span>→</span>
                          <span>{log.new_status}</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </Card>
  );
};

export default NodeLifecycleLogs;
