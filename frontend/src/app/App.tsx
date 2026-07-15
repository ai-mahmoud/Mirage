import { RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/auth-context";
import { CurrentSessionProvider } from "@/contexts/session-context";
import { router } from "@/router/router";

const queryClient = new QueryClient();

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <CurrentSessionProvider>
          <RouterProvider router={router} />
        </CurrentSessionProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
