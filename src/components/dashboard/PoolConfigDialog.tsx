
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";

interface PoolConfigDialogProps {
  isOpen: boolean;
  onClose: () => void;
  poolName: string;
  poolId: string;
}

const defaultYamlConfig = `pools:
  - instance_pool_id: "ocid1.instancepool.oc1.ap-mumbai-1......."
    compartment_id: "ocid1.compartment.oc1......."
    region: "india-west"
    monitoring_method: "oci"
    prometheus_url: "http://localhost:9090"
    cpu_threshold: {min: 30, max: 75}
    ram_threshold: {min: 20, max: 75}
    scaling_limits: {min: 1, max: 10}
    scheduler_max_instances: 3
    schedules:
      - start_time: "05:30"
        end_time: "05:50"
      - start_time: "6:00"
        end_time: "7:00"
      - start_time: "7:40"
        end_time: "8:00"`;

export function PoolConfigDialog({ isOpen, onClose, poolName, poolId }: PoolConfigDialogProps) {
  const [yamlConfig, setYamlConfig] = useState(defaultYamlConfig);
  const { toast } = useToast();

  const handleSave = () => {
    try {
      // Here you would validate the YAML and send it to your backend
      console.log("Saving YAML config for pool:", poolId, yamlConfig);
      
      toast({
        title: "Configuration Saved",
        description: `YAML configuration for ${poolName} has been updated successfully.`,
      });
      
      onClose();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save configuration. Please check your YAML syntax.",
        variant: "destructive",
      });
    }
  };

  const handleReset = () => {
    setYamlConfig(defaultYamlConfig);
    toast({
      title: "Configuration Reset",
      description: "YAML configuration has been reset to default values.",
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">
            Configure Pool: {poolName}
          </DialogTitle>
          <DialogDescription>
            Edit the YAML configuration for this instance pool. Make sure to follow the correct YAML syntax.
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex-1 min-h-0 mt-4">
          <Textarea
            value={yamlConfig}
            onChange={(e) => setYamlConfig(e.target.value)}
            className="h-full min-h-[400px] font-mono text-sm bg-dark-bg border-dark-bg-light resize-none"
            placeholder="Enter your YAML configuration here..."
          />
        </div>
        
        <DialogFooter className="gap-2 mt-4">
          <Button
            variant="outline"
            onClick={handleReset}
            className="border-dark-bg-light hover:bg-dark-bg-light"
          >
            Reset to Default
          </Button>
          <Button
            variant="outline"
            onClick={onClose}
            className="border-dark-bg-light hover:bg-dark-bg-light"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            className="bg-dark-teal-600 hover:bg-dark-teal-700 text-white"
          >
            Save Configuration
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
