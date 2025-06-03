
import { Button } from "@/components/ui/button";
import { Plus, RefreshCw } from "lucide-react";

interface DashboardHeaderProps {
  lastUpdated?: string;
  refreshing: boolean;
  onRefresh: () => void;
  formatTime: (dateString: string) => string;
}

export function DashboardHeader({ 
  lastUpdated, 
  refreshing, 
  onRefresh, 
  formatTime 
}: DashboardHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
      <div>
        <h1 className="text-2xl font-bold mb-1">Instance Management</h1>
        <p className="text-sm text-muted-foreground">
          Monitor and manage your Oracle Cloud instances
          {lastUpdated && (
            <span className="ml-2">
              • Last updated: {formatTime(lastUpdated)}
            </span>
          )}
        </p>
      </div>
      <div className="flex gap-2 mt-3 sm:mt-0">
        <Button 
          variant="outline" 
          className="border-dark-bg-light hover:bg-dark-bg-light text-sm"
          onClick={onRefresh}
          disabled={refreshing}
        >
          <RefreshCw size={16} className={`mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
        <Button className="bg-dark-teal-600 hover:bg-dark-teal-700 text-white text-sm">
          <Plus size={16} className="mr-2" />
          New Instance Pool
        </Button>
      </div>
    </div>
  );
}
