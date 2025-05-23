
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Activity, RefreshCw, Save } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface AutoscaleConfigProps {
  instancePoolId: string;
  defaultValues?: AutoscaleValues;
  onSave?: (values: AutoscaleValues) => void;
}

interface AutoscaleValues {
  enabled: boolean;
  minInstances: number;
  maxInstances: number;
  cpuThreshold: number;
  cooldownPeriod: number;
  scaleUpBy: number;
}

export function AutoscaleConfig({ 
  instancePoolId,
  defaultValues = {
    enabled: true,
    minInstances: 2,
    maxInstances: 10,
    cpuThreshold: 75,
    cooldownPeriod: 300,
    scaleUpBy: 2
  },
  onSave
}: AutoscaleConfigProps) {
  const [values, setValues] = useState<AutoscaleValues>(defaultValues);
  const { toast } = useToast();
  
  const handleSave = () => {
    if (onSave) {
      onSave(values);
    }
    
    toast({
      title: "Configuration saved",
      description: `Autoscaling settings updated for pool ${instancePoolId}`,
    });
  };
  
  return (
    <Card className="glass-card shadow-lg">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-medium">Autoscaling Configuration</CardTitle>
            <CardDescription>Configure autoscaling rules for instance pool</CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Label htmlFor="autoscale-toggle" className="text-sm">Enabled</Label>
            <Switch 
              id="autoscale-toggle" 
              checked={values.enabled}
              onCheckedChange={(checked) => setValues({...values, enabled: checked})}
              className="data-[state=checked]:bg-dark-teal-500"
            />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="rules">
          <TabsList className="bg-dark-bg mb-4">
            <TabsTrigger value="rules" className="data-[state=active]:bg-dark-teal-800/30 data-[state=active]:text-dark-teal-50">
              <RefreshCw size={16} className="mr-2" />
              Scaling Rules
            </TabsTrigger>
            <TabsTrigger value="monitoring" className="data-[state=active]:bg-dark-teal-800/30 data-[state=active]:text-dark-teal-50">
              <Activity size={16} className="mr-2" />
              Monitoring
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="rules" className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="min-instances">Minimum Instances</Label>
                <Input
                  id="min-instances"
                  type="number"
                  value={values.minInstances}
                  onChange={(e) => setValues({...values, minInstances: parseInt(e.target.value)})}
                  className="bg-dark-bg/60 border-dark-bg-light/40 focus-visible:ring-dark-teal-500"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max-instances">Maximum Instances</Label>
                <Input
                  id="max-instances"
                  type="number"
                  value={values.maxInstances}
                  onChange={(e) => setValues({...values, maxInstances: parseInt(e.target.value)})}
                  className="bg-dark-bg/60 border-dark-bg-light/40 focus-visible:ring-dark-teal-500"
                />
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>CPU Threshold (%)</Label>
                  <span className="text-sm text-muted-foreground">{values.cpuThreshold}%</span>
                </div>
                <Slider
                  value={[values.cpuThreshold]}
                  min={0}
                  max={100}
                  step={5}
                  onValueChange={(value) => setValues({...values, cpuThreshold: value[0]})}
                  className="[&>span]:bg-dark-teal-500"
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Cooldown Period (seconds)</Label>
                  <span className="text-sm text-muted-foreground">{values.cooldownPeriod}s</span>
                </div>
                <Slider
                  value={[values.cooldownPeriod]}
                  min={60}
                  max={900}
                  step={30}
                  onValueChange={(value) => setValues({...values, cooldownPeriod: value[0]})}
                  className="[&>span]:bg-dark-teal-500"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="scale-up-by">Scale up by (instances)</Label>
                <Input
                  id="scale-up-by"
                  type="number"
                  value={values.scaleUpBy}
                  onChange={(e) => setValues({...values, scaleUpBy: parseInt(e.target.value)})}
                  className="bg-dark-bg/60 border-dark-bg-light/40 focus-visible:ring-dark-teal-500"
                />
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="monitoring">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label className="text-sm text-muted-foreground">Monitoring settings</Label>
                <p className="text-xs text-muted-foreground">
                  Configure metrics monitoring and alerting policies for this instance pool.
                  Additional settings will be available after connecting to Oracle Cloud API.
                </p>
              </div>
              
              <div className="rounded-md border border-dark-bg-light/30 bg-dark-bg/60 p-4 text-center">
                <p className="text-sm">Connect to Oracle Cloud API to configure advanced monitoring</p>
                <Button variant="outline" className="mt-2 text-xs border-dark-teal-700/50 hover:bg-dark-teal-800/20">
                  Connect API
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
      <CardFooter className="border-t border-dark-bg-light/30 pt-4">
        <Button 
          onClick={handleSave} 
          className="bg-dark-teal-600 hover:bg-dark-teal-700 text-white ml-auto"
        >
          <Save size={16} className="mr-2" />
          Save Configuration
        </Button>
      </CardFooter>
    </Card>
  );
}
