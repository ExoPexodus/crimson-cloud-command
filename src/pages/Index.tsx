
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { useSystemAnalytics } from "@/hooks/useSystemAnalytics";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { SystemMetricsCards } from "@/components/dashboard/SystemMetricsCards";
import { InstancePoolsSection } from "@/components/dashboard/InstancePoolsSection";
import { AlertsStrip } from "@/components/dashboard/AlertsStrip";
import { ScalingEventsFeed } from "@/components/dashboard/ScalingEventsFeed";
import { QuickActionsPanel } from "@/components/dashboard/QuickActionsPanel";
import { EmptyDashboardState } from "@/components/dashboard/EmptyDashboardState";
import { NodeSetupDialog } from "@/components/dashboard/NodeSetupDialog";
import { useState } from "react";

const Index = () => {
  const { analytics, loading, refreshing, handleRefresh, formatTime } = useSystemAnalytics();
  const [isNodeSetupOpen, setIsNodeSetupOpen] = useState(false);

  const hasNodes = analytics?.active_nodes && analytics.active_nodes > 0;

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <div className="flex-1 overflow-auto p-4 md:p-6 teal-scrollbar">
            <div className="max-w-7xl mx-auto">
              <DashboardHeader
                lastUpdated={analytics?.last_updated}
                refreshing={refreshing}
                onRefresh={handleRefresh}
                formatTime={formatTime}
              />

              {/* Alerts Strip - Always visible when there are alerts */}
              <AlertsStrip />

              {/* KPI Cards Strip */}
              <SystemMetricsCards analytics={analytics} loading={loading} />

              {/* Show empty state OR main content */}
              {!loading && !hasNodes ? (
                <EmptyDashboardState onRegisterNode={() => setIsNodeSetupOpen(true)} />
              ) : (
                <>
                  {/* Main Content Grid: Scaling Events + Quick Actions */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
                    <div className="lg:col-span-2">
                      <ScalingEventsFeed />
                    </div>
                    <div className="lg:col-span-1">
                      <QuickActionsPanel onRegisterNode={() => setIsNodeSetupOpen(true)} />
                    </div>
                  </div>

                  {/* Instance Pools Grid */}
                  <InstancePoolsSection />
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Node Setup Dialog */}
      <NodeSetupDialog 
        isOpen={isNodeSetupOpen} 
        onClose={() => setIsNodeSetupOpen(false)} 
      />
    </SidebarProvider>
  );
};

export default Index;
