// ABOUTME: API integration functions for investment strategy management
// ABOUTME: Handles CRUD operations for strategies and recommendation fetching

import { InvestmentStrategy, StrategyDrivenRecommendationResponse } from '../types/strategy';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getStrategy(): Promise<InvestmentStrategy | null> {
  const response = await fetch(`${API_BASE}/api/strategy/`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error('Failed to fetch strategy');
  return response.json();
}

export async function createStrategy(
  data: Omit<InvestmentStrategy, 'id' | 'user_id' | 'created_at' | 'updated_at' | 'version'>
): Promise<InvestmentStrategy> {
  const response = await fetch(`${API_BASE}/api/strategy/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to create strategy');
  return response.json();
}

export async function updateStrategy(
  data: Partial<Omit<InvestmentStrategy, 'id' | 'user_id' | 'created_at' | 'updated_at' | 'version'>>
): Promise<InvestmentStrategy> {
  const response = await fetch(`${API_BASE}/api/strategy/`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to update strategy');
  return response.json();
}

export async function getRecommendations(
  forceRefresh: boolean = false
): Promise<StrategyDrivenRecommendationResponse> {
  const url = `${API_BASE}/api/strategy/recommendations?force_refresh=${forceRefresh}`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to fetch recommendations');
  return response.json();
}
