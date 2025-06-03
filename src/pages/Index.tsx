
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { useIsMobile } from "@/hooks/use-mobile";
import { useSystemAnalytics } from "@/hooks/useSystemAnalytics";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { SystemMetricsCards } from "@/components/dashboard/SystemMetricsCards";
import { MetricsChartsSection } from "@/components/dashboard/MetricsChartsSection";
import { InstancePoolsSection } from "@/components/dashboard/InstancePoolsSection";

const Index = () => {
  const isMobile = useIsMobile();
  const { analytics, loading, refreshing, handleRefresh, formatTime } = useSystemAnalytics();
  
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
              
              <SystemMetricsCards analytics={analytics} loading={loading} />
              
              <MetricsChartsSection />
              
              <InstancePoolsSection />
            </div>
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Index;
