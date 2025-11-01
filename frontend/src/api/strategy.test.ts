// ABOUTME: Tests for strategy API integration functions
// ABOUTME: Covers CRUD operations and error handling

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getStrategy, createStrategy, updateStrategy, getRecommendations } from './strategy';
import type { InvestmentStrategy } from '../types/strategy';

global.fetch = vi.fn();

const mockStrategy: InvestmentStrategy = {
  id: 1,
  user_id: 1,
  name: 'Growth Strategy',
  objective: 'GROWTH',
  time_horizon: 10,
  risk_tolerance: 'MODERATE',
  target_allocation: { stocks: 70, bonds: 20, crypto: 10 },
  rebalancing_threshold: 5.0,
  profit_taking_threshold: 20.0,
  loss_limit_threshold: -15.0,
  preferred_assets: ['AAPL', 'GOOGL'],
  excluded_assets: ['TSLA'],
  notes: 'Focus on tech growth',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  version: 1
};

describe('Strategy API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getStrategy', () => {
    it('should fetch existing strategy', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStrategy
      });

      const result = await getStrategy();

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/strategy/');
      expect(result).toEqual(mockStrategy);
    });

    it('should return null for 404', async () => {
      (fetch as any).mockResolvedValueOnce({
        status: 404,
        ok: false
      });

      const result = await getStrategy();

      expect(result).toBeNull();
    });

    it('should throw error for other failures', async () => {
      (fetch as any).mockResolvedValueOnce({
        status: 500,
        ok: false
      });

      await expect(getStrategy()).rejects.toThrow('Failed to fetch strategy');
    });
  });

  describe('createStrategy', () => {
    it('should create new strategy', async () => {
      const newStrategy = {
        name: 'Growth Strategy',
        objective: 'GROWTH' as const,
        time_horizon: 10,
        risk_tolerance: 'MODERATE' as const,
        target_allocation: { stocks: 70, bonds: 20, crypto: 10 },
        rebalancing_threshold: 5.0,
        profit_taking_threshold: 20.0,
        loss_limit_threshold: -15.0,
        preferred_assets: ['AAPL'],
        excluded_assets: [],
        notes: 'Test'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStrategy
      });

      const result = await createStrategy(newStrategy);

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/strategy/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newStrategy)
      });
      expect(result).toEqual(mockStrategy);
    });

    it('should throw error on failure', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: false
      });

      await expect(createStrategy({} as any)).rejects.toThrow('Failed to create strategy');
    });
  });

  describe('updateStrategy', () => {
    it('should update existing strategy', async () => {
      const updates = {
        name: 'Updated Strategy',
        profit_taking_threshold: 25.0
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockStrategy, ...updates })
      });

      const result = await updateStrategy(updates);

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/strategy/', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      expect(result.name).toBe('Updated Strategy');
    });

    it('should throw error on failure', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: false
      });

      await expect(updateStrategy({})).rejects.toThrow('Failed to update strategy');
    });
  });

  describe('getRecommendations', () => {
    const mockRecommendations = {
      alignment_score: 85,
      key_insights: ['Portfolio well-aligned'],
      profit_taking_opportunities: [],
      position_assessments: [],
      new_position_suggestions: [],
      action_plan: {
        immediate_actions: [],
        redeployment_options: [],
        gradual_adjustments: []
      },
      next_review_date: '2025-02-01'
    };

    it('should fetch recommendations without force refresh', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecommendations
      });

      const result = await getRecommendations();

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/strategy/recommendations?force_refresh=false');
      expect(result).toEqual(mockRecommendations);
    });

    it('should fetch recommendations with force refresh', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecommendations
      });

      const result = await getRecommendations(true);

      expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/strategy/recommendations?force_refresh=true');
      expect(result).toEqual(mockRecommendations);
    });

    it('should throw error on failure', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: false
      });

      await expect(getRecommendations()).rejects.toThrow('Failed to fetch recommendations');
    });
  });
});
