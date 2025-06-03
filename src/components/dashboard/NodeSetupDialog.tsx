
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Copy, Download, ExternalLink, CheckCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface NodeSetupDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NodeSetupDialog({ isOpen, onClose }: NodeSetupDialogProps) {
  const { toast } = useToast();

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: `${label} copied to clipboard`,
    });
  };

  const centralAppUrl = window.location.origin;
  const backendUrl = centralAppUrl.replace(':5173', ':8000').replace(':3000', ':8000');
  
  const configExample = `# Oracle Cloud Autoscaler Configuration
# Backend Integration - connects to central management system
backend:
  url: "${backendUrl}"
  node_id: 1  # Will be assigned when you register the node
  api_key: ""  # Get this from your account settings

pools:
  - instance_pool_id: "ocid1.instancepool.oc1.ap-mumbai-1.example"
    compartment_id: "ocid1.compartment.oc1..example"
    region: "ap-mumbai-1"
    monitoring_method: "oci"
    
    # Scaling thresholds (percentage)
    cpu_threshold: 
      min: 10
      max: 75
    ram_threshold: 
      min: 20  
      max: 75
    
    # Scaling limits
    scaling_limits: 
      min: 2
      max: 10
    
    # Scheduled scaling (optional)
    schedules:
      - name: "business_hours"
        start_time: "09:00"
        end_time: "17:00"
        description: "Scale up during business hours"
    
    scheduler_max_instances: 8`;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-dark-teal-500" />
            Connect Your Autoscaling Node
          </DialogTitle>
          <DialogDescription>
            Follow these steps to connect your autoscaling node to this central application
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Step 1 */}
          <Card className="p-4 glass-card">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="bg-dark-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">1</span>
              Register Your Node
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              First, register your node with the central management system to get a node ID.
            </p>
            <div className="bg-dark-bg/50 p-3 rounded text-sm font-mono">
              POST {backendUrl}/nodes
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              You'll receive a node_id that you'll use in your configuration.
            </p>
          </Card>

          {/* Step 2 */}
          <Card className="p-4 glass-card">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="bg-dark-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">2</span>
              Configure Your Node
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Create a configuration file with your Oracle Cloud details and backend connection.
            </p>
            <div className="bg-dark-bg/50 p-3 rounded text-sm font-mono whitespace-pre-wrap overflow-x-auto">
              {configExample}
            </div>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => copyToClipboard(configExample, "Configuration")}
            >
              <Copy size={14} className="mr-2" />
              Copy Configuration
            </Button>
          </Card>

          {/* Step 3 */}
          <Card className="p-4 glass-card">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="bg-dark-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">3</span>
              Install Dependencies & Run
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Install Python dependencies and start the autoscaling node.
            </p>
            <div className="bg-dark-bg/50 p-3 rounded text-sm font-mono space-y-1">
              <div>cd autoscaler-node/auto_scaler_project</div>
              <div>pip install -r requirements.txt</div>
              <div>python src/main.py --config config.yaml</div>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => copyToClipboard("cd autoscaler-node/auto_scaler_project\npip install -r requirements.txt\npython src/main.py --config config.yaml", "Run commands")}
            >
              <Copy size={14} className="mr-2" />
              Copy Commands
            </Button>
          </Card>

          {/* Step 4 */}
          <Card className="p-4 glass-card">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="bg-dark-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">4</span>
              Verify Connection
            </h3>
            <p className="text-sm text-muted-foreground">
              Once your node is running, it will automatically send heartbeats to this central application every 30 seconds. 
              You should see your node appear as "Active" in the Nodes section within a few minutes.
            </p>
          </Card>

          {/* Integration Features */}
          <Card className="p-4 glass-card border-dark-teal-600/30">
            <h3 className="font-semibold mb-2 text-dark-teal-400">Integration Features</h3>
            <ul className="text-sm space-y-1 text-muted-foreground">
              <li>• Real-time pool metrics and analytics</li>
              <li>• Remote configuration management</li>
              <li>• Centralized monitoring and alerting</li>
              <li>• Historical scaling data and trends</li>
              <li>• Automatic node status tracking</li>
            </ul>
          </Card>
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
