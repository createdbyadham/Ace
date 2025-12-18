import { createRootRoute, Outlet } from '@tanstack/react-router';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/infrastructure/query/queryClient';
import { AuthProvider } from '@/context/AuthContext';
import { Toaster } from '@/components/ui/sonner';
import { ChatBot } from '@/components/chatbot';

export const Route = createRootRoute({
  component: RootComponent,
});

function RootComponent() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <div className="min-h-screen bg-background text-foreground">
          <Outlet />
          <Toaster position="top-right" />
          <ChatBot />
        </div>
      </AuthProvider>
    </QueryClientProvider>
  );
}

