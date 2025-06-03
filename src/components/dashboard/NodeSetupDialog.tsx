
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
  const configExample = `# Autoscaling Node Configuration
central_app:
  url: "${centralAppUrl}"
  api_key: "your-api-key-here"

node:
  name: "Production Node"
  region: "us-west-2"
  
oracle_cloud:
  config_file: "~/.oci/config"
  profile: "DEFAULT"

instance_pools:
  - name: "Web Servers"
    oracle_pool_id: "ocid1.instancepool.oc1..."
    min_instances: 2
    max_instances: 10
    target_cpu: 70
    target_memory: 80`;

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
              Download the Autoscaling Node
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Clone or download the autoscaling node from the project repository.
            </p>
            <div className="bg-dark-bg/50 p-3 rounded text-sm font-mono">
              git clone https://github.com/your-repo/autoscaling-node.git
            </div>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => copyToClipboard("git clone https://github.com/your-repo/autoscaling-node.git", "Git command")}
            >
              <Copy size={14} className="mr-2" />
              Copy Command
            </Button>
          </Card>

          {/* Step 2 */}
          <Card className="p-4 glass-card">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <span className="bg-dark-teal-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">2</span>
              Configure Your Node
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Create a configuration file with your Oracle Cloud details and central app connection.
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
              Set Up Oracle Cloud Credentials
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Ensure your Oracle Cloud Infrastructure (OCI) credentials are properly configured.
            </p>
            <ul className="text-sm space-y-1 text-muted-foreground">
              <li>• Install the OCI CLI and configure it with your credentials</li>
              <li>• Create an OCI config file at ~/.oci/config</li>
              <li>• Ensure your user has permissions to manage instance pools</li>
            </ul>
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
              <div>cd autoscaling-node</div>
              <div>pip install -r requirements.txt</div>
              <div>python src/main.py --config config.yaml</div>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => copyToClipboard("cd autoscaling-node\npip install -r requirements.txt\npython src/main.py --config config.yaml", "Run commands")}
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
              Once your node is running, it will automatically register with this central application. 
              You should see your instance pools appear on this dashboard within a few minutes.
            </p>
          </Card>

          {/* Additional Resources */}
          <Card className="p-4 glass-card border-dark-teal-600/30">
            <h3 className="font-semibold mb-2 text-dark-teal-400">Additional Resources</h3>
            <div className="space-y-2">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start"
                onClick={() => window.open('/docs/setup-guide', '_blank')}
              >
                <ExternalLink size={14} className="mr-2" />
                Detailed Setup Guide
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start"
                onClick={() => window.open('/docs/troubleshooting', '_blank')}
              >
                <ExternalLink size={14} className="mr-2" />
                Troubleshooting Guide
              </Button>
            </div>
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
