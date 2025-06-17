
import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Settings, Save, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";

interface NodeConfigEditorProps {
  isOpen: boolean;
  onClose: () => void;
  nodeId: number | null;
  nodeName: string;
}

export function NodeConfigEditor({ isOpen, onClose, nodeId, nodeName }: NodeConfigEditorProps) {
  const { toast } = useToast();
  const [config, setConfig] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen && nodeId) {
      fetchConfig();
    }
  }, [isOpen, nodeId]);

  const fetchConfig = async () => {
    if (!nodeId) return;
    
    setLoading(true);
    try {
      const response = await apiClient.getNodeConfig(nodeId);
      if (response.data) {
        setConfig(JSON.stringify(response.data, null, 2));
      } else {
        setConfig("{}");
      }
    } catch (error) {
      console.error("Error fetching config:", error);
      toast({
        title: "Error",
        description: "Failed to fetch node configuration",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!nodeId) return;

    try {
      JSON.parse(config); // Validate JSON
    } catch (error) {
      toast({
        title: "Invalid JSON",
        description: "Please check your configuration syntax",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);
    try {
      const parsedConfig = JSON.parse(config);
      const response = await apiClient.updateNodeConfig(nodeId, parsedConfig);
      
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

  if (!nodeId) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-dark-teal-500" />
            Edit Configuration: {nodeName}
          </DialogTitle>
          <DialogDescription>
            Edit the configuration for this autoscaling node. Changes will be applied to the node automatically.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Configuration (JSON)</label>
            {loading ? (
              <div className="h-96 bg-dark-bg/50 rounded animate-pulse flex items-center justify-center">
                <p className="text-muted-foreground">Loading configuration...</p>
              </div>
            ) : (
              <Textarea
                value={config}
                onChange={(e) => setConfig(e.target.value)}
                className="h-96 font-mono text-sm"
                placeholder="Enter your configuration in JSON format..."
              />
            )}
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              <X size={14} className="mr-2" />
              Cancel
            </Button>
            <Button
              onClick={saveConfig}
              disabled={saving || loading}
              className="bg-dark-teal-600 hover:bg-dark-teal-700 text-white"
            >
              <Save size={14} className="mr-2" />
              {saving ? "Saving..." : "Save Configuration"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
