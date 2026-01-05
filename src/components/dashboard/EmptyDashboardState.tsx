import { Server, ArrowRight, CheckCircle2, Settings, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface EmptyDashboardStateProps {
  onRegisterNode: () => void;
}

export function EmptyDashboardState({ onRegisterNode }: EmptyDashboardStateProps) {
  const steps = [
    {
      icon: Server,
      title: "Register a Node",
      description: "Connect your first autoscaler node to start monitoring",
      isActive: true,
    },
    {
      icon: Settings,
      title: "Configure Autoscaling",
      description: "Set up scaling rules, thresholds, and schedules",
      isActive: false,
    },
    {
      icon: Activity,
      title: "Monitor & Optimize",
      description: "Track metrics and fine-tune your configuration",
      isActive: false,
    },
  ];

  return (
    <Card className="glass-card border-dashed">
      <CardContent className="py-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
            <Server className="h-8 w-8 text-primary" />
          </div>
          <h2 className="text-xl font-semibold mb-2">Welcome to Autoscaler</h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Get started by connecting your first autoscaler node. Once connected, you'll see real-time metrics and scaling activity here.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto mb-8">
          {steps.map((step, index) => (
            <div
              key={step.title}
              className={`relative flex flex-col items-center p-4 rounded-lg border ${
                step.isActive
                  ? "border-primary bg-primary/5"
                  : "border-border bg-muted/5 opacity-60"
              }`}
            >
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute -right-2 top-1/2 transform -translate-y-1/2 z-10">
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
              )}
              <div
                className={`flex items-center justify-center w-10 h-10 rounded-full mb-3 ${
                  step.isActive ? "bg-primary/20" : "bg-muted/20"
                }`}
              >
                {step.isActive ? (
                  <step.icon className="h-5 w-5 text-primary" />
                ) : (
                  <step.icon className="h-5 w-5 text-muted-foreground" />
                )}
              </div>
              <h3 className={`text-sm font-medium mb-1 ${step.isActive ? "" : "text-muted-foreground"}`}>
                {step.title}
              </h3>
              <p className="text-xs text-muted-foreground text-center">{step.description}</p>
            </div>
          ))}
        </div>

        <div className="flex justify-center gap-4">
          <Button onClick={onRegisterNode} className="gap-2">
            <Server className="h-4 w-4" />
            Register Your First Node
          </Button>
        </div>

        <div className="mt-8 pt-6 border-t border-border/50">
          <div className="flex items-start gap-3 max-w-lg mx-auto text-sm text-muted-foreground">
            <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-foreground">Quick Setup</p>
              <p>
                Node registration takes less than 2 minutes. You'll receive an API key to configure your autoscaler instance.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
