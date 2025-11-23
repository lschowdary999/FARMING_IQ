import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useNavigate } from "react-router-dom";
import { 
  Tractor, 
  User, 
  Settings, 
  LogOut, 
  Bell,
  Menu
} from "lucide-react";

interface DashboardHeaderProps {
  onToggleSidebar: () => void;
  sidebarCollapsed: boolean;
}

import { useAuth } from "@/context/AuthContext";

const DashboardHeader = ({ onToggleSidebar, sidebarCollapsed }: DashboardHeaderProps) => {
  const [notifications] = useState(3);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  // Get today's date
  const today = new Date();
  const formattedDate = today.toLocaleDateString('en-US', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });

  return (
    <header className="bg-card border-b border-border px-4 py-3 h-16 flex items-center justify-between sticky top-0 z-40">
      {/* Left section */}
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleSidebar}
          className="lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </Button>
        
        {/* Logo and brand */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Tractor className="h-8 w-8 text-primary" />
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold text-foreground">FarmIQ</h1>
              <p className="text-xs text-muted-foreground">Smart Farming Dashboard</p>
            </div>
          </div>
        </div>
      </div>

      {/* Center section - Date */}
      <div className="hidden md:flex items-center">
        <div className="text-center">
          <p className="text-sm font-medium text-foreground">Today</p>
          <p className="text-xs text-muted-foreground">{formattedDate}</p>
        </div>
      </div>

      {/* Right section */}
      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <Button variant="ghost" size="sm" className="relative">
          <Bell className="h-5 w-5" />
          {notifications > 0 && (
            <span className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-destructive text-destructive-foreground text-xs flex items-center justify-center">
              {notifications}
            </span>
          )}
        </Button>

        {/* Profile dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center space-x-2 hover:bg-accent">
              <Avatar className="h-8 w-8">
                <AvatarImage src="/farmer-avatar.jpg" alt="Farmer" />
                <AvatarFallback className="bg-primary text-primary-foreground">
                  <User className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="hidden sm:block text-left">
                <p className="text-sm font-medium">{user?.username || "Guest"}</p>
                <p className="text-xs text-muted-foreground">Farmer</p>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56 bg-card" align="end">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate("/profile") }>
              <User className="mr-2 h-4 w-4" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate("/settings") }>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout}>
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

export default DashboardHeader;