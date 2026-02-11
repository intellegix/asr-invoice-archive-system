import { queryClient, invalidateQueries } from '../queryClient';

describe('queryClient', () => {
  describe('default query options', () => {
    const defaultOptions = queryClient.getDefaultOptions();

    it('staleTime is 5 minutes', () => {
      expect(defaultOptions.queries?.staleTime).toBe(5 * 60 * 1000);
    });

    it('gcTime is 30 minutes', () => {
      expect(defaultOptions.queries?.gcTime).toBe(30 * 60 * 1000);
    });

    it('refetchOnWindowFocus is false', () => {
      expect(defaultOptions.queries?.refetchOnWindowFocus).toBe(false);
    });

    it('retry returns false for 4xx errors', () => {
      const retryFn = defaultOptions.queries?.retry as (
        failureCount: number,
        error: any,
      ) => boolean;

      expect(retryFn(0, { response: { status: 400 } })).toBe(false);
      expect(retryFn(0, { response: { status: 404 } })).toBe(false);
      expect(retryFn(0, { response: { status: 422 } })).toBe(false);
      expect(retryFn(0, { response: { status: 499 } })).toBe(false);
    });

    it('retry allows retries for 5xx errors', () => {
      const retryFn = defaultOptions.queries?.retry as (
        failureCount: number,
        error: any,
      ) => boolean;

      expect(retryFn(0, { response: { status: 500 } })).toBe(true);
      expect(retryFn(1, { response: { status: 502 } })).toBe(true);
      expect(retryFn(2, { response: { status: 503 } })).toBe(true);
    });

    it('retry stops after 3 failures', () => {
      const retryFn = defaultOptions.queries?.retry as (
        failureCount: number,
        error: any,
      ) => boolean;

      // failureCount is 0-indexed: 0, 1, 2 are allowed (< 3), 3 is not
      expect(retryFn(3, { response: { status: 500 } })).toBe(false);
      expect(retryFn(4, { response: { status: 500 } })).toBe(false);
    });
  });

  describe('invalidateQueries helpers', () => {
    it('has invalidation helpers for documents, metrics, vendors, and projects', () => {
      expect(invalidateQueries).toHaveProperty('documents');
      expect(invalidateQueries).toHaveProperty('metrics');
      expect(invalidateQueries).toHaveProperty('vendors');
      expect(invalidateQueries).toHaveProperty('projects');

      expect(typeof invalidateQueries.documents).toBe('function');
      expect(typeof invalidateQueries.metrics).toBe('function');
      expect(typeof invalidateQueries.vendors).toBe('function');
      expect(typeof invalidateQueries.projects).toBe('function');
    });
  });
});
