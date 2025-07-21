
import { useState, useEffect } from "react";
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
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Copy, Settings, Trash2, AlertTriangle, Edit, Save, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";

interface Node {
  id: number;
  name: string;
  region: string;
  status: "active" | "inactive" | "error";
  last_heartbeat?: string;
  created_at: string;
  api_key_hash?: string;
}

interface NodeConfigDialogProps {
  isOpen: boolean;
  onClose: () => void;
  node: Node | null;
  onNodeDeleted: () => void;
}

export function NodeConfigDialog({ isOpen, onClose, node, onNodeDeleted }: NodeConfigDialogProps) {
  const { toast } = useToast();
  const [deleting, setDeleting] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [currentConfig, setCurrentConfig] = useState("");
  const [editedConfig, setEditedConfig] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Fetch current configuration when dialog opens
  useEffect(() => {
    if (isOpen && node) {
      fetchCurrentConfig();
    }
  }, [isOpen, node]);

  const fetchCurrentConfig = async () => {
    if (!node) return;
    
    setLoading(true);
    try {
      const response = await apiClient.getNodeConfig(node.id);
      if (response.data) {
        setCurrentConfig(response.data.yaml_config);
        setEditedConfig(response.data.yaml_config);
      } else {
        // If no config exists, use template
        const template = generateConfigTemplate();
        setCurrentConfig(template);
        setEditedConfig(template);
      }
    } catch (error) {
      console.error('Failed to fetch config:', error);
      // Fallback to template
      const template = generateConfigTemplate();
      setCurrentConfig(template);
      setEditedConfig(template);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    if (!node) return;

    setSaving(true);
    try {
      const response = await apiClient.updateNodeConfig(node.id, editedConfig);
      if (response.error) {
        toast({
          title: "Save Failed",
          description: response.error,
          variant: "destructive"
        });
      } else {
        setCurrentConfig(editedConfig);
        setEditMode(false);
        toast({
          title: "Configuration Updated",
          description: "The node configuration has been saved successfully",
        });
      }
    } catch (error) {
      toast({
        title: "Save Failed",
        description: "An unexpected error occurred while saving",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const handleCancelEdit = () => {
    setEditedConfig(currentConfig);
    setEditMode(false);
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: `${label} copied to clipboard`,
    });
  };

  const handleDeleteNode = async () => {
    if (!node) return;

    setDeleting(true);
    try {
      const response = await apiClient.deleteNode(node.id);
      if (response.error) {
        toast({
          title: "Delete Failed",
          description: response.error,
          variant: "destructive"
        });
      } else {
        toast({
          title: "Node Deleted",
          description: "The node has been removed from the system",
        });
        onNodeDeleted();
        onClose();
      }
    } catch (error) {
      toast({
        title: "Delete Failed",
        description: "An unexpected error occurred",
        variant: "destructive"
      });
    } finally {
      setDeleting(false);
    }
  };

  const getBackendUrl = () => {
    return window.location.origin.replace(':5173', ':8000').replace(':3000', ':8000');
  };

  const generateConfigTemplate = () => {
    if (!node) return "";
    
    return `# Oracle Cloud Autoscaler Configuration
# Backend Integration
backend:
  url: "${getBackendUrl()}"
  node_id: ${node.id}
  api_key: "your-api-key-from-initial-registration"

pools:
  - instance_pool_id: "ocid1.instancepool.oc1.${node.region}.example"
    compartment_id: "ocid1.compartment.oc1..example"
    region: "${node.region}"
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

  if (!node) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-dark-blue-500" />
            Configure Node: {node.name}
          </DialogTitle>
          <DialogDescription>
            View node details, configuration, and manage this autoscaling node
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Node Information */}
          <Card className="p-4 glass-card border-dark-blue-600/30">
            <h3 className="font-semibold mb-3 text-dark-blue-400">Node Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <Label className="text-muted-foreground">Node Name</Label>
                <p className="font-medium">{node.name}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Region</Label>
                <p className="font-medium">{node.region}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Node ID</Label>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs">{node.id}</span>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => copyToClipboard(node.id.toString(), "Node ID")}
                  >
                    <Copy size={12} />
                  </Button>
                </div>
              </div>
              <div>
                <Label className="text-muted-foreground">Status</Label>
                <p className="font-medium capitalize">{node.status}</p>
              </div>
            </div>
          </Card>

          {/* Connection Details */}
          <Card className="p-4 glass-card">
            <h3 className="font-semibold mb-3">Connection Details</h3>
            <div className="space-y-3">
              <div>
                <Label className="text-sm text-muted-foreground">Backend URL</Label>
                <div className="flex items-center gap-2">
                  <Input value={getBackendUrl()} readOnly className="font-mono text-xs" />
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => copyToClipboard(getBackendUrl(), "Backend URL")}
                  >
                    <Copy size={14} />
                  </Button>
                </div>
              </div>
              
              <Card className="p-3 bg-yellow-500/10 border-yellow-600/30">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-medium text-yellow-600">API Key Access</p>
                    <p className="text-yellow-600/80">
                      The API key is only shown during initial registration for security reasons. 
                      If you need to regenerate it, you'll need to delete and recreate the node.
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          </Card>

          {/* Node Configuration */}
          <Card className="p-4 glass-card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">Node Configuration</h3>
              <div className="flex gap-2">
                {!editMode && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setEditMode(true)}
                    disabled={loading}
                  >
                    <Edit size={14} className="mr-2" />
                    Edit Config
                  </Button>
                )}
                {editMode && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCancelEdit}
                      disabled={saving}
                    >
                      <X size={14} className="mr-2" />
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSaveConfig}
                      disabled={saving}
                    >
                      <Save size={14} className="mr-2" />
                      {saving ? "Saving..." : "Save"}
                    </Button>
                  </>
                )}
              </div>
            </div>
            
            <p className="text-sm text-muted-foreground mb-3">
              {editMode 
                ? "Edit the YAML configuration for this autoscaling node:"
                : "Current YAML configuration for this autoscaling node:"
              }
            </p>

            {loading ? (
              <div className="bg-dark-bg/50 p-3 rounded min-h-[200px] flex items-center justify-center">
                <span className="text-muted-foreground">Loading configuration...</span>
              </div>
            ) : editMode ? (
              <Textarea
                value={editedConfig}
                onChange={(e) => setEditedConfig(e.target.value)}
                className="font-mono text-xs min-h-[300px] bg-dark-bg/50"
                placeholder="Enter YAML configuration..."
              />
            ) : (
              <div className="bg-dark-bg/50 p-3 rounded text-xs font-mono whitespace-pre-wrap overflow-x-auto max-h-64">
                {currentConfig || "No configuration available"}
              </div>
            )}

            {!editMode && (
              <div className="flex gap-2 mt-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(currentConfig, "Configuration")}
                  disabled={!currentConfig}
                >
                  <Copy size={14} className="mr-2" />
                  Copy Configuration
                </Button>
              </div>
            )}
          </Card>

          {/* Danger Zone */}
          <Card className="p-4 glass-card border-red-600/30 bg-red-500/5">
            <h3 className="font-semibold mb-3 text-red-400">Danger Zone</h3>
            <p className="text-sm text-muted-foreground mb-3">
              Delete this node from the central system. Note: If the node is still running and sending heartbeats, 
              it will automatically reappear in the system.
            </p>
            <Button
              variant="destructive"
              onClick={handleDeleteNode}
              disabled={deleting}
              className="bg-red-600 hover:bg-red-700"
            >
              <Trash2 size={14} className="mr-2" />
              {deleting ? "Deleting..." : "Delete Node"}
            </Button>
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
