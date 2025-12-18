import React from 'react';
import { Link } from '@tanstack/react-router';
import { LogOut, User, Settings, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import type { User as UserType } from '@/domain/auth/types';

interface NavbarProps {
  isAuthenticated?: boolean;
  user?: UserType | null;
  onLogout?: () => void;
  className?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ 
  isAuthenticated = false,
  user,
  onLogout,
  className = ''
}) => {
  const getInitials = (name: string) => {
    return name.charAt(0).toUpperCase();
  };

  return (
    <header className={`w-full py-4 px-8 flex justify-between items-center border-b border-border/10 z-10 transition-opacity duration-500 ${className}`}>
      <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
        <div className="h-8 w-8 rounded-lg bg-black outline outline-2 outline-white/10 flex items-center justify-center shadow-lg shadow-indigo-500/25">
          <span className="text-white font-bold text-lg">C</span>
        </div>
        <h1 className="text-xl font-semibold">Cardify</h1>
      </Link>
      <div className="absolute left-1/2 transform -translate-x-1/2">
        <nav className="hidden md:flex items-center gap-8">
          <Link to="/quiz" className="nav-link text-sm font-medium text-foreground/80 hover:text-foreground">Quiz</Link>
          <Link to="/flashcards" className="nav-link text-sm font-medium text-foreground/80 hover:text-foreground">Flash Cards</Link>
          <Link to="/files" className="nav-link text-sm font-medium text-foreground/80 hover:text-foreground">My Files</Link>
          <Link to="/summaries" className="nav-link text-sm font-medium text-foreground/80 hover:text-foreground">Summaries</Link>
        </nav>
      </div>
      <div className="flex items-center gap-4">
        {isAuthenticated ? (
          <>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-9 w-9 rounded-full">
                  <Avatar className="h-9 w-9">
                    <AvatarImage src={user?.avatar_url || ''} alt="User profile" />
                    <AvatarFallback className="bg-primary/10">
                      {user?.username ? getInitials(user.username) : user?.email ? getInitials(user.email) : '?'}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{user?.username || user?.email}</p>
                    <p className="text-xs leading-none text-muted-foreground">{user?.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuGroup>
                  <DropdownMenuItem asChild>
                    <Link to="/" className="flex items-center cursor-pointer w-full">
                      <User className="mr-2 h-4 w-4" />
                      <span>Profile</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/" className="flex items-center cursor-pointer w-full">
                      <Shield className="mr-2 h-4 w-4" />
                      <span>Security</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link to="/" className="flex items-center cursor-pointer w-full">
                      <Settings className="mr-2 h-4 w-4" />
                      <span>Settings</span>
                    </Link>
                  </DropdownMenuItem>
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  className="text-red-500 focus:text-red-500 cursor-pointer"
                  onClick={onLogout}
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </>
        ) : (
          <>
            <Link to="/login" className="text-sm font-medium text-foreground/80 hover:text-foreground">Log in</Link>
            <Link to="/register">
              <Button className="rounded-md bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500">
                Get started
              </Button>
            </Link>
          </>
        )}
      </div>
    </header>
  );
};

export default Navbar;
