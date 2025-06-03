
import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Copy, Plus, Trash2, Key, Eye, EyeOff } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";

interface NodeApiKey {
  id: number;
  name: string;
  key: string;
  node_id: number;
  created_at: string;
  is_active: boolean;
}

interface NodeApiKeysDialogProps {
  isOpen: boolean;
  onClose: () => void;
  nodeId: number;
  nodeName: string;
}

export function NodeApiKeysDialog({ isOpen, onClose, nodeId, nodeName }: NodeApiKeysDialogProps) {
  const { toast } = useToast();
  const [apiKeys, setApiKeys] = useState<NodeApiKey[]>([]);
  const [loading, setLoading] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [creatingKey, setCreatingKey] = useState(false);
  const [visibleKeys, setVisibleKeys] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (isOpen) {
      fetchApiKeys();
    }
  }, [isOpen, nodeId]);

  const fetchApiKeys = async () => {
    setLoading(true);
    try {
      const response = await apiClient.getNodeApiKeys(nodeId);
      if (response.data) {
        setApiKeys(response.data);
      }
    } catch (error) {
      console.error("Error fetching API keys:", error);
    } finally {
      setLoading(false);
    }
  };

  const createApiKey = async () => {
    if (!newKeyName.trim()) {
      toast({
        title: "Error",
        description: "Please provide a name for the API key",
        variant: "destructive",
      });
      return;
    }

    setCreatingKey(true);
    try {
      const response = await apiClient.createNodeApiKey(nodeId, newKeyName);
      if (response.data) {
        toast({
          title: "API Key Created",
          description: "New API key has been generated successfully",
        });
        setNewKeyName("");
        fetchApiKeys();
      } else if (response.error) {
        toast({
          title: "Error",
          description: response.error,
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create API key",
        variant: "destructive",
      });
    } finally {
      setCreatingKey(false);
    }
  };

  const deactivateApiKey = async (keyId: number) => {
    try {
      const response = await apiClient.deactivateApiKey(keyId);
      if (response.error) {
        toast({
          title: "Error",
          description: response.error,
          variant: "destructive",
        });
      } else {
        toast({
          title: "API Key Deactivated",
          description: "The API key has been deactivated",
        });
        fetchApiKeys();
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to deactivate API key",
        variant: "destructive",
      });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: "API key copied to clipboard",
    });
  };

  const toggleKeyVisibility = (keyId: number) => {
    setVisibleKeys(prev => {
      const newSet = new Set(prev);
      if (newSet.has(keyId)) {
        newSet.delete(keyId);
      } else {
        newSet.add(keyId);
      }
      return newSet;
    });
  };

  const maskKey = (key: string) => {
    return key.substring(0, 8) + "..." + key.substring(key.length - 8);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Key className="w-5 h-5 text-dark-teal-500" />
            API Keys for {nodeName}
          </DialogTitle>
          <DialogDescription>
            Manage API keys for this node. Each key can be used to authenticate the node with the backend.
          </DialogDescription>
        </DialogHeader>

        {/* Create New API Key */}
        <Card className="p-4 glass-card border-dark-teal-600/30">
          <h3 className="font-semibold mb-3 text-dark-teal-400">Create New API Key</h3>
          <div className="flex gap-2">
            <Input
              placeholder="Enter key name (e.g., Production Key)"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && createApiKey()}
            />
            <Button 
              onClick={createApiKey} 
              disabled={creatingKey || !newKeyName.trim()}
              className="bg-dark-teal-600 hover:bg-dark-teal-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              {creatingKey ? "Creating..." : "Create"}
            </Button>
          </div>
        </Card>

        {/* API Keys List */}
        <div className="space-y-3">
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading API keys...</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No API keys found. Create your first API key above.
            </div>
          ) : (
            apiKeys.map((apiKey) => (
              <Card key={apiKey.id} className="p-4 glass-card">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium">{apiKey.name}</h4>
                      <span className={`px-2 py-1 rounded text-xs ${
                        apiKey.is_active 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                      }`}>
                        {apiKey.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <code className="text-sm bg-muted px-2 py-1 rounded font-mono">
                        {visibleKeys.has(apiKey.id) ? apiKey.key : maskKey(apiKey.key)}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleKeyVisibility(apiKey.id)}
                        className="h-6 w-6 p-0"
                      >
                        {visibleKeys.has(apiKey.id) ? (
                          <EyeOff className="w-3 h-3" />
                        ) : (
                          <Eye className="w-3 h-3" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(apiKey.key)}
                        className="h-6 w-6 p-0"
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Created: {new Date(apiKey.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  
                  {apiKey.is_active && (
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Deactivate API Key</AlertDialogTitle>
                          <AlertDialogDescription>
                            This will deactivate the API key "{apiKey.name}". The node will no longer be able to authenticate using this key. This action cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction 
                            onClick={() => deactivateApiKey(apiKey.id)}
                            className="bg-red-600 hover:bg-red-700"
                          >
                            Deactivate
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  )}
                </div>
              </Card>
            ))
          )}
        </div>

        <div className="flex justify-end pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
