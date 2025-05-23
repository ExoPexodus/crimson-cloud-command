
import { Server, Power, RefreshCw, Edit } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { StatusIndicator } from "@/components/dashboard/StatusIndicator";

interface InstancePoolCardProps {
  name: string;
  instances: number;
  maxInstances: number;
  status: "healthy" | "warning" | "error" | "inactive";
  region: string;
  cpuUsage: number;
  memoryUsage: number;
  onEdit?: () => void;
  onScaleUp?: () => void;
  onScaleDown?: () => void;
}

export function InstancePoolCard({
  name,
  instances,
  maxInstances,
  status,
  region,
  cpuUsage,
  memoryUsage,
  onEdit,
  onScaleUp,
  onScaleDown
}: InstancePoolCardProps) {
  return (
    <Card className="glass-card overflow-hidden hover:shadow-dark-teal-900/10 transition-all duration-300">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-2">
            <div className="rounded bg-dark-bg/80 p-1.5">
              <Server size={14} className="text-dark-teal-400" />
            </div>
            <CardTitle className="text-sm font-medium">{name}</CardTitle>
          </div>
          <StatusIndicator status={status} />
        </div>
        <div className="text-xs text-muted-foreground mt-1">
          {region} • {instances} active instances
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        <div className="space-y-3">
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>CPU</span>
              <span className="text-muted-foreground">{cpuUsage}%</span>
            </div>
            <Progress value={cpuUsage} className="h-1.5" indicatorClassName="bg-dark-teal-500" />
          </div>
          
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>Memory</span>
              <span className="text-muted-foreground">{memoryUsage}%</span>
            </div>
            <Progress value={memoryUsage} className="h-1.5" indicatorClassName="bg-dark-teal-400" />
          </div>
          
          <div className="space-y-1">
            <div className="flex justify-between text-xs">
              <span>Instances</span>
              <span className="text-muted-foreground">{instances}/{maxInstances}</span>
            </div>
            <Progress 
              value={(instances / maxInstances) * 100} 
              className="h-1.5" 
              indicatorClassName="bg-dark-teal-600"
            />
          </div>
        </div>
      </CardContent>
      <CardFooter className="pt-0 gap-2 flex justify-between border-t border-dark-bg-light/30 p-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-white hover:bg-dark-teal-800/20"
          onClick={onEdit}
        >
          <Edit size={14} />
        </Button>
        
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-white hover:bg-dark-teal-800/20"
            onClick={onScaleDown}
          >
            <RefreshCw size={14} />
          </Button>
          
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-white hover:bg-dark-teal-800/20"
            onClick={onScaleUp}
          >
            <Power size={14} />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
