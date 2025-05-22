
import { Bell, Search, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SidebarTrigger } from "@/components/ui/sidebar";

export function Header() {
  return (
    <header className="border-b border-dark-bg-light bg-dark-bg-lighter px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <SidebarTrigger className="border-0 bg-transparent hover:bg-dark-bg-light text-foreground" />
        <h1 className="font-semibold text-lg md:text-xl hidden md:block">Oracle Cloud Instance Manager</h1>
      </div>
      
      <div className="flex-1 max-w-md mx-4 hidden md:block">
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search instances, containers..." 
            className="bg-dark-bg pl-8 border-dark-bg-light focus-visible:ring-dark-red-400"
          />
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground hover:bg-dark-bg-light relative">
          <Bell size={20} />
          <span className="absolute top-1 right-1.5 h-2 w-2 rounded-full bg-dark-red-500" />
        </Button>
        
        <div className="h-8 w-8 rounded-full bg-dark-red-900 border border-dark-red-700 flex items-center justify-center">
          <User size={16} />
        </div>
      </div>
    </header>
  );
}
