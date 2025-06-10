
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Copy, CheckCircle, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";

interface NodeRegistrationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onNodeRegistered: () => void;
}

export function NodeRegistrationDialog({ isOpen, onClose, onNodeRegistered }: NodeRegistrationDialogProps) {
  const { toast } = useToast();
  const [step, setStep] = useState<"form" | "success">("form");
  const [loading, setLoading] = useState(false);
  const [registrationData, setRegistrationData] = useState({
    name: "",
    region: "",
    ip_address: "",
    description: ""
  });
  const [registrationResult, setRegistrationResult] = useState<{
    node_id: number;
    api_key: string;
    name: string;
    region: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await apiClient.registerNode({
        name: registrationData.name,
        region: registrationData.region,
        ip_address: registrationData.ip_address || undefined,
        description: registrationData.description || undefined
      });

      if (response.error) {
        toast({
          title: "Registration Failed",
          description: response.error,
          variant: "destructive"
        });
        return;
      }

      setRegistrationResult(response.data!);
      setStep("success");
      onNodeRegistered();
    } catch (error) {
      toast({
        title: "Registration Failed",
        description: "An unexpected error occurred",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: `${label} copied to clipboard`,
    });
  };

  const handleClose = () => {
    setStep("form");
    setRegistrationData({ name: "", region: "", ip_address: "", description: "" });
    setRegistrationResult(null);
    onClose();
  };

  const generateConfigExample = () => {
    if (!registrationResult) return "";
    
    const backendUrl = window.location.origin.replace(':5173', ':8000').replace(':3000', ':8000');
    
    return `# Oracle Cloud Autoscaler Configuration
# Backend Integration
backend:
  url: "${backendUrl}"
  node_id: ${registrationResult.node_id}
  api_key: "${registrationResult.api_key}"

pools:
  - instance_pool_id: "ocid1.instancepool.oc1.${registrationResult.region}.example"
    compartment_id: "ocid1.compartment.oc1..example"
    region: "${registrationResult.region}"
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
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {step === "form" ? (
              <>Register New Autoscaling Node</>
            ) : (
              <>
                <CheckCircle className="w-5 h-5 text-dark-teal-500" />
                Node Registered Successfully!
              </>
            )}
          </DialogTitle>
          <DialogDescription>
            {step === "form" 
              ? "Enter the details for your new autoscaling node"
              : "Your node has been registered. Save these credentials securely."
            }
          </DialogDescription>
        </DialogHeader>

        {step === "form" && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Node Name *</Label>
                <Input
                  id="name"
                  value={registrationData.name}
                  onChange={(e) => setRegistrationData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Production Node 1"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="region">Oracle Cloud Region *</Label>
                <Input
                  id="region"
                  value={registrationData.region}
                  onChange={(e) => setRegistrationData(prev => ({ ...prev, region: e.target.value }))}
                  placeholder="e.g., us-ashburn-1"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="ip_address">IP Address (Optional)</Label>
              <Input
                id="ip_address"
                value={registrationData.ip_address}
                onChange={(e) => setRegistrationData(prev => ({ ...prev, ip_address: e.target.value }))}
                placeholder="e.g., 192.168.1.100"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Textarea
                id="description"
                value={registrationData.description}
                onChange={(e) => setRegistrationData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Brief description of this node's purpose"
                rows={3}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading} className="bg-dark-teal-600 hover:bg-dark-teal-700">
                {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Register Node
              </Button>
            </div>
          </form>
        )}

        {step === "success" && registrationResult && (
          <div className="space-y-4">
            <Card className="p-4 glass-card border-dark-teal-600/30">
              <h3 className="font-semibold mb-3 text-dark-teal-400">Node Credentials</h3>
              <div className="space-y-3">
                <div>
                  <Label className="text-sm text-muted-foreground">Node ID</Label>
                  <div className="flex items-center gap-2">
                    <Input value={registrationResult.node_id.toString()} readOnly className="font-mono" />
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => copyToClipboard(registrationResult.node_id.toString(), "Node ID")}
                    >
                      <Copy size={14} />
                    </Button>
                  </div>
                </div>
                <div>
                  <Label className="text-sm text-muted-foreground">API Key</Label>
                  <div className="flex items-center gap-2">
                    <Input value={registrationResult.api_key} readOnly className="font-mono text-xs" />
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => copyToClipboard(registrationResult.api_key, "API Key")}
                    >
                      <Copy size={14} />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>

            <Card className="p-4 glass-card">
              <h3 className="font-semibold mb-3">Configuration File</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Save this configuration as <code>config.yaml</code> in your autoscaling node directory:
              </p>
              <div className="bg-dark-bg/50 p-3 rounded text-xs font-mono whitespace-pre-wrap overflow-x-auto max-h-64">
                {generateConfigExample()}
              </div>
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={() => copyToClipboard(generateConfigExample(), "Configuration")}
              >
                <Copy size={14} className="mr-2" />
                Copy Configuration
              </Button>
            </Card>

            <div className="flex justify-end gap-2 pt-4">
              <Button onClick={handleClose} className="bg-dark-teal-600 hover:bg-dark-teal-700">
                Done
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
