
import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Settings, Save, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";

interface Node {
  id: number;
  name: string;
  region: string;
  status: "active" | "inactive" | "error";
  last_heartbeat?: string;
  created_at: string;
}

interface NodeConfigEditorProps {
  isOpen: boolean;
  onClose: () => void;
  node: Node | null;
}

export function NodeConfigEditor({ isOpen, onClose, node }: NodeConfigEditorProps) {
  const { toast } = useToast();
  const [config, setConfig] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen && node) {
      loadNodeConfig();
    }
  }, [isOpen, node]);

  const loadNodeConfig = async () => {
    if (!node) return;

    setLoading(true);
    try {
      const response = await apiClient.getNodeConfig(node.id);
      if (response.error) {
        toast({
          title: "Load Failed",
          description: response.error,
          variant: "destructive"
        });
        setConfig("{}");
      } else {
        setConfig(response.data?.yaml_config || "{}");
      }
    } catch (error) {
      toast({
        title: "Load Failed",
        description: "Failed to load node configuration",
        variant: "destructive"
      });
      setConfig("{}");
    } finally {
      setLoading(false);
    }
  };

  const saveNodeConfig = async () => {
    if (!node) return;

    // Validate JSON
    try {
      JSON.parse(config);
    } catch (error) {
      toast({
        title: "Invalid JSON",
        description: "Please check your JSON syntax",
        variant: "destructive"
      });
      return;
    }

    setSaving(true);
    try {
      const response = await apiClient.updateNodeConfig(node.id, config);
      if (response.error) {
        toast({
          title: "Save Failed",
          description: response.error,
          variant: "destructive"
        });
      } else {
        toast({
          title: "Configuration Saved",
          description: "The node configuration has been updated successfully",
        });
        onClose();
      }
    } catch (error) {
      toast({
        title: "Save Failed",
        description: "An unexpected error occurred",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  if (!node) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-dark-teal-500" />
            Configure Node: {node.name}
          </DialogTitle>
          <DialogDescription>
            Edit the JSON configuration for this autoscaling node
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Node Information */}
          <Card className="p-4 glass-card border-dark-teal-600/30">
            <h3 className="font-semibold mb-3 text-dark-teal-400">Node Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Node Name:</span>
                <p className="font-medium">{node.name}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Region:</span>
                <p className="font-medium">{node.region}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Node ID:</span>
                <p className="font-mono text-xs">{node.id}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Status:</span>
                <p className="font-medium capitalize">{node.status}</p>
              </div>
            </div>
          </Card>

          {/* Configuration Editor */}
          <Card className="p-4 glass-card">
            <h3 className="font-semibold mb-3">Node Configuration (JSON)</h3>
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="w-6 h-6 animate-spin" />
                <span className="ml-2">Loading configuration...</span>
              </div>
            ) : (
              <div className="space-y-3">
                <textarea
                  value={config}
                  onChange={(e) => setConfig(e.target.value)}
                  className="w-full h-96 p-3 bg-dark-bg/50 border border-dark-bg-light/30 rounded text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-dark-teal-500"
                  placeholder="Enter JSON configuration..."
                />
                <p className="text-xs text-muted-foreground">
                  Edit the configuration in JSON format. Changes will be applied to the autoscaling node.
                </p>
              </div>
            )}
          </Card>
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={saveNodeConfig}
            disabled={saving || loading}
            className="bg-dark-teal-600 hover:bg-dark-teal-700"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Configuration
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
