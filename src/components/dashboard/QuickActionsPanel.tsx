import { Pause, Play, RefreshCw, Server, Settings } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface QuickActionsPanelProps {
  onRegisterNode: () => void;
  autoscalingPaused?: boolean;
}

export function QuickActionsPanel({ onRegisterNode, autoscalingPaused = false }: QuickActionsPanelProps) {
  const { toast } = useToast();
  const [isPaused, setIsPaused] = useState(autoscalingPaused);
  const [isSyncing, setIsSyncing] = useState(false);

  const handleToggleAutoscaling = () => {
    setIsPaused(!isPaused);
    toast({
      title: isPaused ? "Autoscaling Resumed" : "Autoscaling Paused",
      description: isPaused
        ? "All autoscaling operations are now active"
        : "All autoscaling operations have been paused",
    });
  };

  const handleSyncConfigs = async () => {
    setIsSyncing(true);
    // Simulate config sync
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsSyncing(false);
    toast({
      title: "Configurations Synced",
      description: "All node configurations have been synchronized",
    });
  };

  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <Settings className="h-4 w-4" />
          Quick Actions
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {/* Toggle Autoscaling */}
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-start gap-2 h-10"
              size="sm"
            >
              {isPaused ? (
                <>
                  <Play className="h-4 w-4 text-green-400" />
                  <span>Resume Autoscaling</span>
                </>
              ) : (
                <>
                  <Pause className="h-4 w-4 text-yellow-400" />
                  <span>Pause Autoscaling</span>
                </>
              )}
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>
                {isPaused ? "Resume Autoscaling?" : "Pause Autoscaling?"}
              </AlertDialogTitle>
              <AlertDialogDescription>
                {isPaused
                  ? "This will resume all autoscaling operations across all nodes. Instances will scale based on configured rules."
                  : "This will pause all autoscaling operations across all nodes. Instances will remain at their current count until resumed."}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleToggleAutoscaling}>
                {isPaused ? "Resume" : "Pause"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Sync Configs */}
        <Button
          variant="outline"
          className="w-full justify-start gap-2 h-10"
          size="sm"
          onClick={handleSyncConfigs}
          disabled={isSyncing}
        >
          <RefreshCw className={`h-4 w-4 ${isSyncing ? "animate-spin" : ""}`} />
          <span>{isSyncing ? "Syncing..." : "Force Sync Configs"}</span>
        </Button>

        {/* Register Node */}
        <Button
          variant="outline"
          className="w-full justify-start gap-2 h-10"
          size="sm"
          onClick={onRegisterNode}
        >
          <Server className="h-4 w-4 text-primary" />
          <span>Register New Node</span>
        </Button>

        {/* Status Indicator */}
        <div className="pt-3 mt-3 border-t border-border/50">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Autoscaling Status</span>
            <div className="flex items-center gap-1.5">
              <div
                className={`w-2 h-2 rounded-full ${
                  isPaused ? "bg-yellow-400" : "bg-green-400"
                } animate-pulse`}
              />
              <span className={isPaused ? "text-yellow-400" : "text-green-400"}>
                {isPaused ? "Paused" : "Active"}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
