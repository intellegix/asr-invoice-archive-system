import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 30 * 60 * 1000, // 30 minutes
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Cache invalidation helpers
export const invalidateQueries = {
  documents: () => queryClient.invalidateQueries({ queryKey: ['documents'] }),
  metrics: () => queryClient.invalidateQueries({ queryKey: ['metrics'] }),
  vendors: () => queryClient.invalidateQueries({ queryKey: ['vendors'] }),
  projects: () => queryClient.invalidateQueries({ queryKey: ['projects'] }),
};