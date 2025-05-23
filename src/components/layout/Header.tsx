
import { Bell, Search, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SidebarTrigger } from "@/components/ui/sidebar";

export function Header() {
  return (
    <header className="border-b border-dark-bg-light/40 bg-dark-bg-lighter/80 backdrop-blur-md px-4 py-3 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-2">
        <SidebarTrigger className="border-0 bg-transparent hover:bg-dark-bg-light text-foreground" />
        <h1 className="font-semibold text-lg md:text-xl hidden md:block">Oracle Cloud Instance Manager</h1>
      </div>
      
      <div className="flex-1 max-w-md mx-4 hidden md:block">
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search instances, containers..." 
            className="bg-dark-bg/60 pl-8 border-dark-bg-light/40 focus-visible:ring-dark-teal-500 hover:border-dark-teal-800/50"
          />
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground hover:bg-dark-bg-light/50 relative">
          <Bell size={20} />
          <span className="absolute top-1 right-1.5 h-2 w-2 rounded-full bg-dark-teal-500 animate-pulse-teal" />
        </Button>
        
        <div className="h-8 w-8 rounded-full bg-gradient-dark-teal flex items-center justify-center shadow-md">
          <User size={16} className="text-white" />
        </div>
      </div>
    </header>
  );
}
