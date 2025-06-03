
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Copy, Download, ExternalLink, CheckCircle, Key } from "lucide-react";
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
  api_key: "your-generated-api-key-here"  # Generate this from the Nodes page

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
              1. Go to the Nodes page in this application<br/>
              2. Click "Add Node" to register a new node<br/>
              3. Fill in your node details (name, region, IP address, etc.)
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              You'll receive a node_id that you'll use in your configuration.
            </p>
          </Card>

          {/* Step 2 */}
          <Card className="p-4 glass-card border-amber-500/30">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="bg-dark-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">2</span>
              <Key className="w-4 h-4 text-amber-500" />
              Generate API Key
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Generate a secure API key for your node to authenticate with the backend.
            </p>
            <div className="bg-dark-bg/50 p-3 rounded text-sm font-mono space-y-1">
              <div>1. Go to the Nodes page and find your registered node</div>
              <div>2. Click "Manage API Keys" for your node</div>
              <div>3. Create a new API key with a descriptive name</div>
              <div>4. Copy the generated key (it won't be shown again!)</div>
            </div>
            <div className="mt-3 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md">
              <p className="text-sm text-amber-800 dark:text-amber-200">
                <strong>Important:</strong> Store the API key securely. It will only be displayed once when created.
              </p>
            </div>
          </Card>

          {/* Step 3 */}
          <Card className="p-4 glass-card">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="bg-dark-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">3</span>
              Configure Your Node
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Create a configuration file with your Oracle Cloud details, node ID, and API key.
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

          {/* Step 4 */}
          <Card className="p-4 glass-card">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="bg-dark-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">4</span>
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

          {/* Step 5 */}
          <Card className="p-4 glass-card">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="bg-dark-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">5</span>
              Verify Connection
            </h3>
            <p className="text-sm text-muted-foreground">
              Once your node is running with the correct API key, it will automatically send heartbeats to this central application every 30 seconds. 
              You should see your node appear as "Active" in the Nodes section within a few minutes.
            </p>
          </Card>

          {/* Authentication Info */}
          <Card className="p-4 glass-card border-blue-600/30">
            <h3 className="font-semibold mb-2 text-blue-400 flex items-center gap-2">
              <Key className="w-4 h-4" />
              Authentication Details
            </h3>
            <ul className="text-sm space-y-1 text-muted-foreground">
              <li>• Node authentication uses API keys sent via X-API-Key header</li>
              <li>• Each node can have multiple API keys for different purposes</li>
              <li>• API keys can be deactivated without affecting other keys</li>
              <li>• Heartbeat and configuration endpoints require valid API keys</li>
            </ul>
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
