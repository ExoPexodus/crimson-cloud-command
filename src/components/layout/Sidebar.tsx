
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
} from "@/components/ui/sidebar";
import { Home, Settings, Users, Activity, LogOut } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";

const allNavItems = [
  {
    title: "Dashboard",
    url: "/",
    icon: Home,
    requiredRole: null, // accessible to all authenticated users
  },
  {
    title: "Nodes",
    url: "/nodes",
    icon: Activity,
    requiredRole: 'DEVOPS' as const,
  },
];

const allManagementItems = [
  {
    title: "Settings",
    icon: Settings,
    url: "/settings",
    requiredRole: null, // accessible to all authenticated users
  },
  {
    title: "Users",
    icon: Users,
    url: "/admin/users",
    requiredRole: 'ADMIN' as const,
  },
];

export function AppSidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, hasRole } = useAuth();

  // Filter navigation items based on user permissions
  const navItems = allNavItems.filter(item => 
    !item.requiredRole || hasRole(item.requiredRole)
  );

  // Filter management items based on user permissions
  const managementItems = allManagementItems.filter(item => 
    !item.requiredRole || hasRole(item.requiredRole)
  );

  const handleLogout = () => {
    logout();
  };

  return (
    <Sidebar>
      <SidebarHeader className="border-b border-dark-bg-light/40 p-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-gradient-dark-blue flex items-center justify-center shadow-md">
            <Activity size={16} className="text-white" />
          </div>
          <span className="font-semibold text-lg">OCI Manager</span>
        </div>
      </SidebarHeader>
      
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton 
                    asChild
                    isActive={location.pathname === item.url}
                    className="data-[active=true]:bg-dark-blue-800/30 data-[active=true]:text-dark-blue-300 hover:bg-dark-bg-light/50"
                  >
                    <a href="#" onClick={(e) => { e.preventDefault(); navigate(item.url); }}>
                      <item.icon />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {managementItems.length > 0 && (
          <SidebarGroup>
            <SidebarGroupLabel>Management</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {managementItems.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton 
                      asChild
                      isActive={location.pathname === item.url}
                      className="data-[active=true]:bg-dark-blue-800/30 data-[active=true]:text-dark-blue-300 hover:bg-dark-bg-light/50"
                    >
                      <a href="#" onClick={(e) => { e.preventDefault(); navigate(item.url); }}>
                        <item.icon />
                        <span>{item.title}</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter className="border-t border-dark-bg-light/40 p-2">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={handleLogout} className="hover:bg-dark-bg-light/50 text-muted-foreground hover:text-foreground">
              <LogOut />
              <span>Logout</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
