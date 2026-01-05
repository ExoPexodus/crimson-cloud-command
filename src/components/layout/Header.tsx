
import { Bell, User, LogOut, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/hooks/useAuth";
import { useNavigate } from "react-router-dom";

export function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
  };

  const handleSettings = () => {
    navigate('/settings');
  };

  return (
    <header className="border-b border-dark-bg-light/40 bg-dark-bg-lighter/80 backdrop-blur-md px-4 py-3 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-2">
        <SidebarTrigger className="border-0 bg-transparent hover:bg-dark-bg-light text-foreground" />
        <h1 className="font-semibold text-lg md:text-xl hidden md:block">Oracle Cloud Instance Manager</h1>
      </div>
      
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground hover:bg-dark-bg-light/50 relative">
          <Bell size={20} />
          <span className="absolute top-1 right-1.5 h-2 w-2 rounded-full bg-dark-blue-500 animate-pulse-blue" />
        </Button>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full bg-gradient-dark-blue hover:bg-gradient-dark-blue/80 transition-all duration-200">
              <User size={16} className="text-white" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 bg-dark-bg-lighter border-dark-bg-light">
            <DropdownMenuLabel className="text-foreground">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">{user?.full_name || 'User'}</p>
                <p className="text-xs text-muted-foreground">{user?.email}</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-dark-bg-light" />
            <DropdownMenuItem 
              onClick={handleSettings}
              className="text-foreground hover:bg-dark-bg-light cursor-pointer"
            >
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuItem 
              onClick={handleLogout}
              className="text-foreground hover:bg-dark-bg-light cursor-pointer"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
