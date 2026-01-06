
import { Server, RefreshCw, Settings, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StatusIndicator } from "@/components/dashboard/StatusIndicator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

interface InstancePoolCardProps {
  name: string;
  instances: number;
  maxInstances: number;
  minInstances?: number;
  status: "healthy" | "warning" | "error" | "inactive";
  region: string;
  cpuUsage: number;
  memoryUsage: number;
  nodeId?: number;
  onRefresh?: () => void;
  onConfigure?: () => void;
}

export function InstancePoolCard({
  name,
  instances,
  maxInstances,
  minInstances = 1,
  status,
  region,
  cpuUsage,
  memoryUsage,
  nodeId,
  onRefresh,
  onConfigure
}: InstancePoolCardProps) {
  const { user } = useAuth();
  const canManage = user?.role === 'ADMIN' || user?.role === 'DEVOPS';
  const getStatusBorderColor = () => {
    switch (status) {
      case "healthy":
        return "border-l-green-500";
      case "warning":
        return "border-l-yellow-500";
      case "error":
        return "border-l-destructive";
      case "inactive":
        return "border-l-muted-foreground";
      default:
        return "border-l-border";
    }
  };

  const getStatusTooltip = () => {
    switch (status) {
      case "healthy":
        return "Node is healthy and reporting normally";
      case "warning":
        return "Node heartbeat is delayed (5-10 min). Check connectivity.";
      case "error":
        return "Node is offline or unresponsive. Immediate attention required.";
      case "inactive":
        return "Node has not sent any heartbeats yet";
      default:
        return "";
    }
  };

  return (
    <TooltipProvider>
      <Card
        className={cn(
          "glass-card overflow-hidden hover:shadow-dark-blue-900/10 transition-all duration-300 border-l-4",
          getStatusBorderColor()
        )}
      >
        <CardHeader className="pb-2">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-2">
              <div className="rounded bg-dark-bg/80 p-1.5">
                <Server size={14} className="text-dark-blue-400" />
              </div>
              <CardTitle className="text-sm font-medium truncate max-w-[120px]" title={name}>
                {name}
              </CardTitle>
            </div>
            <Tooltip>
              <TooltipTrigger>
                <StatusIndicator status={status} />
              </TooltipTrigger>
              <TooltipContent side="left" className="max-w-[200px]">
                <p className="text-xs">{getStatusTooltip()}</p>
              </TooltipContent>
            </Tooltip>
          </div>
          <div className="text-xs text-muted-foreground mt-1">
            {region} • {instances}/{minInstances}-{maxInstances} instances
          </div>
        </CardHeader>
        <CardContent className="pb-3">
          <div className="space-y-3">
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span>CPU</span>
                <span
                  className={cn(
                    "font-medium",
                    cpuUsage > 80 ? "text-destructive" : cpuUsage > 60 ? "text-yellow-400" : "text-muted-foreground"
                  )}
                >
                  {cpuUsage}%
                </span>
              </div>
              <Progress
                value={cpuUsage}
                className="h-1.5"
                indicatorClassName={cn(
                  cpuUsage > 80 ? "bg-destructive" : cpuUsage > 60 ? "bg-yellow-500" : "bg-dark-blue-500"
                )}
              />
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span>Memory</span>
                <span
                  className={cn(
                    "font-medium",
                    memoryUsage > 80 ? "text-destructive" : memoryUsage > 60 ? "text-yellow-400" : "text-muted-foreground"
                  )}
                >
                  {memoryUsage}%
                </span>
              </div>
              <Progress
                value={memoryUsage}
                className="h-1.5"
                indicatorClassName={cn(
                  memoryUsage > 80 ? "bg-destructive" : memoryUsage > 60 ? "bg-yellow-500" : "bg-dark-blue-400"
                )}
              />
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span>Instances</span>
                <span className="text-muted-foreground">
                  {instances}/{maxInstances}
                </span>
              </div>
              <Progress
                value={maxInstances > 0 ? (instances / maxInstances) * 100 : 0}
                className="h-1.5"
                indicatorClassName="bg-dark-blue-600"
              />
            </div>
          </div>
        </CardContent>
        <CardFooter className="pt-0 gap-1 flex justify-center border-t border-dark-bg-light/30 p-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-muted-foreground hover:text-white hover:bg-dark-blue-800/20 text-xs"
            onClick={onRefresh}
          >
            <RefreshCw size={12} className="mr-1" />
            Refresh
          </Button>
          {canManage && onConfigure && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-muted-foreground hover:text-white hover:bg-dark-blue-800/20 text-xs"
              onClick={onConfigure}
            >
              <Settings size={12} className="mr-1" />
              Configure
            </Button>
          )}
          {canManage && nodeId && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-muted-foreground hover:text-white hover:bg-dark-blue-800/20 text-xs"
              asChild
            >
              <a href={`/nodes?id=${nodeId}`}>
                <ExternalLink size={12} className="mr-1" />
                View
              </a>
            </Button>
          )}
        </CardFooter>
      </Card>
    </TooltipProvider>
  );
}
