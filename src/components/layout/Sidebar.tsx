
import React, { useState } from "react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { 
  Home, 
  Server, 
  Settings, 
  LogOut
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";

export function AppSidebar() {
  const [open, setOpen] = useState(true);
  const { logout } = useAuth();
  const { toast } = useToast();
  
  const navigationItems = [
    { title: "Dashboard", icon: Home, url: "/" },
    { title: "Instance Pools", icon: Server, url: "/instance-pools" },
    { title: "Settings", icon: Settings, url: "/settings" },
  ];

  const handleLogout = () => {
    logout();
    toast({
      title: "Logged out",
      description: "You have been successfully logged out",
    });
  };

  return (
    <Sidebar className="border-r border-dark-bg-light/40 bg-sidebar/80 backdrop-blur-sm">
      <SidebarHeader className="py-4">
        <div className={cn("flex items-center gap-2 px-4", !open && "justify-center")}>
          <div className="h-8 w-8 rounded-md bg-gradient-dark-teal flex items-center justify-center shadow-lg">
            <Server size={20} className="text-white" />
          </div>
          {open && (
            <span className="font-bold text-lg text-white">
              OracleOps<span className="text-dark-teal-400">.</span>
            </span>
          )}
        </div>
      </SidebarHeader>
      
      <SidebarContent className="teal-scrollbar">
        <SidebarGroup>
          <SidebarGroupLabel className="text-muted-foreground text-xs uppercase tracking-wider">
            {open ? "Management" : ""}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild className="hover:bg-dark-teal-800/20 data-[active]:bg-dark-teal-900/30 transition-all">
                    <a href={item.url} className={cn(
                      "flex items-center gap-3 rounded-md",
                      location.pathname === item.url && "bg-dark-teal-900/30"
                    )}>
                      <item.icon size={20} className={cn(
                        "text-muted-foreground", 
                        location.pathname === item.url && "text-dark-teal-400"
                      )} />
                      {open && <span>{item.title}</span>}
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      
      <SidebarFooter className="border-t border-dark-bg-light/40">
        <SidebarMenu className="p-2">
          <SidebarMenuItem>
            <SidebarMenuButton 
              asChild 
              className="hover:bg-dark-teal-800/20 transition-all cursor-pointer"
              onClick={handleLogout}
            >
              <div className="flex items-center gap-3 rounded-md">
                <LogOut size={20} className="text-muted-foreground" />
                {open && <span>Log Out</span>}
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
