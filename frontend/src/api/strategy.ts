// ABOUTME: API integration functions for investment strategy management
// ABOUTME: Handles CRUD operations for strategies and recommendation fetching

import type { InvestmentStrategy, StrategyDrivenRecommendationResponse } from '../types/strategy';

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
  if (!response.ok) {
    // Try to parse validation error details
    try {
      const errorData = await response.json();
      if (errorData.detail && Array.isArray(errorData.detail)) {
        const messages = errorData.detail.map((err: any) => err.msg).join(', ');
        throw new Error(messages);
      }
    } catch (parseError) {
      // If can't parse, use generic message
    }
    throw new Error('Failed to create strategy');
  }
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
  if (!response.ok) {
    // Try to parse validation error details
    try {
      const errorData = await response.json();
      if (errorData.detail && Array.isArray(errorData.detail)) {
        const messages = errorData.detail.map((err: any) => err.msg).join(', ');
        throw new Error(messages);
      }
    } catch (parseError) {
      // If can't parse, use generic message
    }
    throw new Error('Failed to update strategy');
  }
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

export async function getRecommendationsStreaming(
  onProgress?: (chunk: string) => void
): Promise<StrategyDrivenRecommendationResponse> {
  const url = `${API_BASE}/api/strategy/recommendations/stream`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Failed to fetch recommendations');
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('Response body is not readable');
  }

  const decoder = new TextDecoder();
  let accumulated = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      accumulated += chunk;

      // Call progress callback if provided
      if (onProgress) {
        onProgress(chunk);
      }
    }

    // Strip markdown code block markers if present
    let jsonText = accumulated.trim();
    if (jsonText.startsWith('```json')) {
      jsonText = jsonText.replace(/^```json\s*/, '').replace(/```\s*$/, '');
    } else if (jsonText.startsWith('```')) {
      jsonText = jsonText.replace(/^```\s*/, '').replace(/```\s*$/, '');
    }

    // Parse the accumulated JSON
    return JSON.parse(jsonText);
  } catch (error) {
    throw new Error(`Failed to parse streaming response: ${error}`);
  }
}
