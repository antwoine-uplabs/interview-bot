import { describe, it, expect, vi, beforeEach } from 'vitest';
import { healthCheck } from './api';

// Mock localStorage
beforeEach(() => {
  global.localStorage = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    length: 0,
    key: vi.fn(),
  };
});

describe('API Service', () => {
  describe('healthCheck', () => {
    it('should return health status from API', async () => {
      const result = await healthCheck();
      
      expect(result).toHaveProperty('status');
      expect(result).toHaveProperty('dependencies');
      expect(result.status).toBe('ok');
      expect(result.dependencies).toHaveProperty('supabase', 'connected');
    });
  });
});