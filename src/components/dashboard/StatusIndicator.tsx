
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

type StatusType = "healthy" | "warning" | "error" | "inactive";

interface StatusIndicatorProps {
  status: StatusType;
  label?: string;
  showLabel?: boolean;
  className?: string;
}

export function StatusIndicator({ 
  status, 
  label, 
  showLabel = true, 
  className 
}: StatusIndicatorProps) {
  const statusConfig = {
    healthy: {
      color: "bg-green-500",
      pulseColor: "bg-green-500/50",
      label: label || "Healthy",
    },
    warning: {
      color: "bg-yellow-500",
      pulseColor: "bg-yellow-500/50",
      label: label || "Warning",
    },
    error: {
      color: "bg-dark-red-500",
      pulseColor: "bg-dark-red-500/50",
      label: label || "Error",
    },
    inactive: {
      color: "bg-gray-400",
      pulseColor: "bg-gray-400/50",
      label: label || "Inactive",
    },
  };

  const config = statusConfig[status];

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn("flex items-center gap-2", className)}>
            <div className="relative flex items-center">
              <div className={`h-2.5 w-2.5 rounded-full ${config.color}`} />
              <div className={`absolute h-2.5 w-2.5 rounded-full ${config.pulseColor} animate-pulse-red`} />
            </div>
            {showLabel && <span className="text-xs text-muted-foreground">{config.label}</span>}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>Status: {config.label}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
