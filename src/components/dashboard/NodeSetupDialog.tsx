
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Copy, Download, ExternalLink, CheckCircle, Plus } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { NodeRegistrationDialog } from "./NodeRegistrationDialog";

interface NodeSetupDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onNodeRegistered?: () => void;
}

export function NodeSetupDialog({ isOpen, onClose, onNodeRegistered }: NodeSetupDialogProps) {
  const { toast } = useToast();
  const [registrationDialogOpen, setRegistrationDialogOpen] = useState(false);

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
  node_id: 1  # Get this from node registration
  api_key: "your-api-key"  # Get this from node registration

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

  const handleNodeRegistered = () => {
    setRegistrationDialogOpen(false);
    if (onNodeRegistered) {
      onNodeRegistered();
    }
    toast({
      title: "Success!",
      description: "Node registered successfully. You can now configure it.",
    });
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-dark-teal-500" />
              Connect Your Autoscaling Node
            </DialogTitle>
            <DialogDescription>
              Choose how you want to set up your autoscaling node
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="register" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="register">Register New Node</TabsTrigger>
              <TabsTrigger value="manual">Manual Setup</TabsTrigger>
            </TabsList>

            <TabsContent value="register" className="space-y-4 mt-6">
              <Card className="p-6 glass-card border-dark-teal-600/30">
                <div className="text-center space-y-4">
                  <h3 className="text-xl font-semibold text-dark-teal-400">Quick Registration</h3>
                  <p className="text-muted-foreground">
                    Register your node with the central system to automatically generate credentials and configuration.
                  </p>
                  <Button 
                    onClick={() => setRegistrationDialogOpen(true)}
                    className="bg-dark-teal-600 hover:bg-dark-teal-700 text-white"
                    size="lg"
                  >
                    <Plus size={20} className="mr-2" />
                    Register New Node
                  </Button>
                </div>
              </Card>

              <Card className="p-4 glass-card">
                <h4 className="font-semibold mb-2">What happens when you register:</h4>
                <ul className="text-sm space-y-1 text-muted-foreground">
                  <li>• Automatic generation of secure API credentials</li>
                  <li>• Pre-configured YAML file with your node details</li>
                  <li>• Immediate connection to the central management system</li>
                  <li>• Real-time monitoring and configuration sync</li>
                </ul>
              </Card>
            </TabsContent>

            <TabsContent value="manual" className="space-y-6 mt-6">
              {/* Step 1 */}
              <Card className="p-4 glass-card">
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <span className="bg-dark-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">1</span>
                  Register Your Node Manually
                </h3>
                <p className="text-sm text-muted-foreground mb-3">
                  Make a POST request to register your node and get credentials.
                </p>
                <div className="bg-dark-bg/50 p-3 rounded text-sm font-mono">
                  POST {backendUrl}/nodes/register
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Send node details (name, region, etc.) to receive node_id and api_key.
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
                  Copy Configuration Template
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
                  <div>python src/main.py</div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => copyToClipboard("cd autoscaler-node/auto_scaler_project\npip install -r requirements.txt\npython src/main.py", "Run commands")}
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
                  Once your node is running, it will automatically send heartbeats to this central application every 60 seconds. 
                  You should see your node appear as "Active" in the Nodes section within a few minutes.
                </p>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Integration Features */}
          <Card className="p-4 glass-card border-dark-teal-600/30 mt-6">
            <h3 className="font-semibold mb-2 text-dark-teal-400">Integration Features</h3>
            <ul className="text-sm space-y-1 text-muted-foreground">
              <li>• Real-time pool metrics and analytics</li>
              <li>• Remote configuration management</li>
              <li>• Centralized monitoring and alerting</li>
              <li>• Historical scaling data and trends</li>
              <li>• Automatic node status tracking</li>
            </ul>
          </Card>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <NodeRegistrationDialog
        isOpen={registrationDialogOpen}
        onClose={() => setRegistrationDialogOpen(false)}
        onNodeRegistered={handleNodeRegistered}
      />
    </>
  );
}
