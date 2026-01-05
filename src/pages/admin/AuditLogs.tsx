import { useState, useEffect, useMemo } from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { 
  RefreshCw, 
  Search, 
  Download, 
  Filter, 
  X,
  Shield,
  User,
  Server,
  Settings,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  FileText,
  CalendarIcon
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import type { AuditLog, AuditLogSummary, AuditLogFilters } from "@/lib/api";
import { format, subDays, startOfDay, endOfDay } from "date-fns";
import { cn } from "@/lib/utils";

type DateRange = {
  from: Date | undefined;
  to: Date | undefined;
};

const AuditLogsPage = () => {
  const { toast } = useToast();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [summary, setSummary] = useState<AuditLogSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Filter state
  const [filters, setFilters] = useState<AuditLogFilters>({
    limit: 100,
    offset: 0
  });
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState<DateRange>({ from: undefined, to: undefined });
  const [categories, setCategories] = useState<Array<{ value: string; label: string }>>([]);
  const [actions, setActions] = useState<Array<{ value: string; label: string; category: string }>>([]);

  useEffect(() => {
    fetchCategories();
    fetchLogs();
    fetchSummary();
  }, []);

  useEffect(() => {
    const debounce = setTimeout(() => {
      if (searchQuery !== filters.search) {
        setFilters(prev => ({ ...prev, search: searchQuery || undefined, offset: 0 }));
      }
    }, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery]);

  useEffect(() => {
    fetchLogs();
  }, [filters]);

  const fetchCategories = async () => {
    const response = await apiClient.getAuditLogCategories();
    if (response.data) {
      setCategories(response.data.categories);
      setActions(response.data.actions);
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await apiClient.getAuditLogs(filters);
      if (response.data) {
        setLogs(response.data);
      }
    } catch (error) {
      console.error("Error fetching audit logs:", error);
      toast({
        title: "Error",
        description: "Failed to fetch audit logs",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchSummary = async () => {
    const response = await apiClient.getAuditLogSummary(24);
    if (response.data) {
      setSummary(response.data);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchLogs();
    fetchSummary();
  };

  const clearFilters = () => {
    setFilters({ limit: 100, offset: 0 });
    setSearchQuery("");
    setDateRange({ from: undefined, to: undefined });
  };

  const applyDateRange = (range: DateRange) => {
    setDateRange(range);
    setFilters(prev => ({
      ...prev,
      start_date: range.from ? startOfDay(range.from).toISOString() : undefined,
      end_date: range.to ? endOfDay(range.to).toISOString() : undefined,
      offset: 0
    }));
  };

  const setQuickDateRange = (days: number) => {
    const to = new Date();
    const from = subDays(to, days);
    applyDateRange({ from, to });
  };

  const formatDateRange = () => {
    if (!dateRange.from) return "Select dates";
    if (!dateRange.to) return format(dateRange.from, "MMM dd, yyyy");
    return `${format(dateRange.from, "MMM dd")} - ${format(dateRange.to, "MMM dd, yyyy")}`;
  };

  const exportLogs = () => {
    const csvContent = [
      ["Timestamp", "User", "Action", "Category", "Resource", "Status", "Description"].join(","),
      ...logs.map(log => [
        log.timestamp,
        log.user_email || "System",
        log.action,
        log.category,
        log.resource_name || log.resource_type || "-",
        log.status,
        `"${(log.description || "").replace(/"/g, '""')}"`
      ].join(","))
    ].join("\n");
    
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-logs-${format(new Date(), "yyyy-MM-dd-HHmmss")}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast({
      title: "Export Complete",
      description: `Exported ${logs.length} audit log entries`
    });
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "AUTH": return <Shield size={14} className="text-blue-400" />;
      case "USER": return <User size={14} className="text-purple-400" />;
      case "NODE": return <Server size={14} className="text-green-400" />;
      case "CONFIG": return <Settings size={14} className="text-orange-400" />;
      case "SYSTEM": return <Activity size={14} className="text-cyan-400" />;
      case "ADMIN": return <Shield size={14} className="text-red-400" />;
      default: return <FileText size={14} className="text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: string) => {
    if (status === "SUCCESS") {
      return (
        <Badge variant="outline" className="gap-1 bg-green-500/10 text-green-400 border-green-500/30">
          <CheckCircle size={12} />
          Success
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="gap-1 bg-red-500/10 text-red-400 border-red-500/30">
        <XCircle size={12} />
        Failure
      </Badge>
    );
  };

  const getCategoryBadge = (category: string) => {
    const colors: Record<string, string> = {
      AUTH: "bg-blue-500/10 text-blue-400 border-blue-500/30",
      USER: "bg-purple-500/10 text-purple-400 border-purple-500/30",
      NODE: "bg-green-500/10 text-green-400 border-green-500/30",
      CONFIG: "bg-orange-500/10 text-orange-400 border-orange-500/30",
      SYSTEM: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
      ADMIN: "bg-red-500/10 text-red-400 border-red-500/30",
      POOL: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30"
    };
    
    return (
      <Badge variant="outline" className={`gap-1 ${colors[category] || "bg-muted"}`}>
        {getCategoryIcon(category)}
        {category}
      </Badge>
    );
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return format(new Date(timestamp), "MMM dd, HH:mm:ss");
    } catch {
      return timestamp;
    }
  };

  const formatFullTimestamp = (timestamp: string) => {
    try {
      return format(new Date(timestamp), "PPpp");
    } catch {
      return timestamp;
    }
  };

  const hasActiveFilters = filters.category || filters.action || filters.status || filters.search || dateRange.from;

  // Filter actions based on selected category
  const filteredActions = useMemo(() => {
    if (!filters.category) return actions;
    return actions.filter(a => a.category === filters.category);
  }, [actions, filters.category]);

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <div className="flex-1 overflow-auto p-4 md:p-6 teal-scrollbar">
            <div className="max-w-7xl mx-auto space-y-6">
              {/* Page Header */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                  <h1 className="text-2xl font-bold mb-1">Audit Logs</h1>
                  <p className="text-sm text-muted-foreground">
                    Enterprise-level audit trail for all system activities
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={exportLogs}
                    disabled={logs.length === 0}
                  >
                    <Download size={16} className="mr-2" />
                    Export CSV
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleRefresh}
                    disabled={refreshing}
                  >
                    <RefreshCw size={16} className={`mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                    Refresh
                  </Button>
                </div>
              </div>

              {/* Summary Cards */}
              {summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card className="glass-card">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
                        <Activity size={14} />
                        Total Events (24h)
                      </div>
                      <div className="text-2xl font-bold">{summary.total_events}</div>
                    </CardContent>
                  </Card>
                  <Card className="glass-card">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
                        <CheckCircle size={14} className="text-green-400" />
                        Successful
                      </div>
                      <div className="text-2xl font-bold text-green-400">
                        {summary.status_counts.SUCCESS || 0}
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="glass-card">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
                        <AlertTriangle size={14} className="text-red-400" />
                        Failed
                      </div>
                      <div className="text-2xl font-bold text-red-400">
                        {summary.failure_count}
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="glass-card">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
                        <Shield size={14} className="text-blue-400" />
                        Auth Events
                      </div>
                      <div className="text-2xl font-bold text-blue-400">
                        {summary.category_counts.AUTH || 0}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Filters */}
              <Card className="glass-card">
                <CardContent className="p-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2">
                      <Filter size={16} className="text-muted-foreground" />
                      <span className="text-sm font-medium">Filters:</span>
                    </div>
                    
                    <div className="flex-1 min-w-[200px] max-w-sm">
                      <div className="relative">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                        <Input
                          placeholder="Search logs..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="pl-9 h-9"
                        />
                      </div>
                    </div>

                    <Select 
                      value={filters.category || "all"} 
                      onValueChange={(value) => setFilters(prev => ({ 
                        ...prev, 
                        category: value === "all" ? undefined : value,
                        action: undefined,
                        offset: 0 
                      }))}
                    >
                      <SelectTrigger className="w-[140px] h-9">
                        <SelectValue placeholder="Category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Categories</SelectItem>
                        {categories.map(cat => (
                          <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <Select 
                      value={filters.action || "all"} 
                      onValueChange={(value) => setFilters(prev => ({ 
                        ...prev, 
                        action: value === "all" ? undefined : value,
                        offset: 0 
                      }))}
                    >
                      <SelectTrigger className="w-[160px] h-9">
                        <SelectValue placeholder="Action" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Actions</SelectItem>
                        {filteredActions.map(act => (
                          <SelectItem key={act.value} value={act.value}>{act.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    <Select 
                      value={filters.status || "all"} 
                      onValueChange={(value) => setFilters(prev => ({ 
                        ...prev, 
                        status: value === "all" ? undefined : value,
                        offset: 0 
                      }))}
                    >
                      <SelectTrigger className="w-[120px] h-9">
                        <SelectValue placeholder="Status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="SUCCESS">Success</SelectItem>
                        <SelectItem value="FAILURE">Failure</SelectItem>
                      </SelectContent>
                    </Select>

                    {/* Date Range Picker */}
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className={cn(
                            "h-9 justify-start text-left font-normal min-w-[180px]",
                            !dateRange.from && "text-muted-foreground"
                          )}
                        >
                          <CalendarIcon size={14} className="mr-2" />
                          {formatDateRange()}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <div className="p-3 border-b border-border">
                          <div className="flex gap-2 flex-wrap">
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="h-7 text-xs"
                              onClick={() => setQuickDateRange(1)}
                            >
                              Today
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="h-7 text-xs"
                              onClick={() => setQuickDateRange(7)}
                            >
                              Last 7 days
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="h-7 text-xs"
                              onClick={() => setQuickDateRange(30)}
                            >
                              Last 30 days
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="h-7 text-xs"
                              onClick={() => setQuickDateRange(90)}
                            >
                              Last 90 days
                            </Button>
                          </div>
                        </div>
                        <Calendar
                          mode="range"
                          selected={dateRange}
                          onSelect={(range) => {
                            if (range) {
                              applyDateRange({ from: range.from, to: range.to });
                            }
                          }}
                          numberOfMonths={2}
                          disabled={(date) => date > new Date()}
                          className={cn("p-3 pointer-events-auto")}
                        />
                        {dateRange.from && (
                          <div className="p-3 border-t border-border flex justify-end">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => applyDateRange({ from: undefined, to: undefined })}
                            >
                              Clear dates
                            </Button>
                          </div>
                        )}
                      </PopoverContent>
                    </Popover>

                    {hasActiveFilters && (
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={clearFilters}
                        className="h-9"
                      >
                        <X size={14} className="mr-1" />
                        Clear
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Logs Table */}
              <Card className="glass-card">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Activity Log</CardTitle>
                    <span className="text-sm text-muted-foreground">
                      Showing {logs.length} entries
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[600px]">
                    {loading ? (
                      <div className="p-8 text-center text-muted-foreground">
                        Loading audit logs...
                      </div>
                    ) : logs.length === 0 ? (
                      <div className="p-8 text-center text-muted-foreground">
                        <FileText size={48} className="mx-auto mb-4 opacity-50" />
                        <p>No audit logs found</p>
                        {hasActiveFilters && (
                          <Button 
                            variant="link" 
                            onClick={clearFilters}
                            className="mt-2"
                          >
                            Clear filters
                          </Button>
                        )}
                      </div>
                    ) : (
                      <div className="divide-y divide-border">
                        {logs.map((log) => (
                          <div 
                            key={log.id} 
                            className="p-4 hover:bg-muted/30 transition-colors"
                          >
                            <div className="flex items-start gap-4">
                              {/* Timestamp */}
                              <div className="flex-shrink-0 w-24 text-xs text-muted-foreground">
                                <div className="flex items-center gap-1">
                                  <Clock size={12} />
                                  {formatTimestamp(log.timestamp)}
                                </div>
                              </div>

                              {/* Main Content */}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 flex-wrap mb-1">
                                  {getCategoryBadge(log.category)}
                                  <Badge variant="secondary" className="font-mono text-xs">
                                    {log.action}
                                  </Badge>
                                  {getStatusBadge(log.status)}
                                </div>
                                
                                <p className="text-sm mb-1">
                                  {log.description || `${log.action} performed`}
                                </p>
                                
                                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                  <span className="flex items-center gap-1">
                                    <User size={12} />
                                    {log.user_email || "System"}
                                  </span>
                                  {log.resource_name && (
                                    <span>
                                      Resource: <span className="text-foreground">{log.resource_name}</span>
                                    </span>
                                  )}
                                  {log.ip_address && (
                                    <span>IP: {log.ip_address}</span>
                                  )}
                                </div>
                                
                                {log.error_message && (
                                  <div className="mt-2 p-2 bg-red-500/10 rounded text-xs text-red-400 border border-red-500/20">
                                    {log.error_message}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default AuditLogsPage;
