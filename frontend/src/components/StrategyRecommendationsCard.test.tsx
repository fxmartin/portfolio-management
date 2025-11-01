// ABOUTME: Tests for StrategyRecommendationsCard component
// ABOUTME: Covers rendering, user interactions, localStorage, and export functionality

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import StrategyRecommendationsCard from './StrategyRecommendationsCard';
import type { StrategyDrivenRecommendationResponse } from '../types/strategy';


const mockRecommendations: StrategyDrivenRecommendationResponse = {
  alignment_score: 85,
  key_insights: [
    'Portfolio is well-diversified across asset classes',
    'Tech sector exposure is within target range',
    'Consider profit-taking on high performers'
  ],
  profit_taking_opportunities: [
    {
      symbol: 'AAPL',
      current_pnl_pct: 35.5,
      threshold: 20.0,
      recommendation: 'TAKE_PROFIT',
      transaction_details: {
        transaction_type: 'SELL',
        symbol: 'AAPL',
        quantity: 50,
        price: 180.50,
        total: 9025.00,
        notes: 'Profit-taking: 35.5% gain exceeds 20.0% threshold'
      },
      rationale: 'Strong performance exceeds profit-taking threshold'
    }
  ],
  position_assessments: [
    {
      symbol: 'GOOGL',
      action: 'HOLD',
      fits_strategy: true,
      rationale: 'Aligns with growth objective, within allocation targets'
    },
    {
      symbol: 'TSLA',
      action: 'CLOSE',
      fits_strategy: false,
      rationale: 'Listed in excluded assets'
    }
  ],
  new_position_suggestions: [
    {
      category: 'Tech Growth',
      symbols: ['MSFT', 'NVDA'],
      rationale: 'Complement existing tech holdings'
    }
  ],
  action_plan: {
    immediate_actions: ['Take profit on AAPL (50 shares)'],
    redeployment_options: ['Reinvest AAPL proceeds into MSFT or NVDA'],
    gradual_adjustments: ['Monitor GOOGL for rebalancing needs']
  },
  next_review_date: '2025-02-01'
};

describe('StrategyRecommendationsCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn(() => Promise.resolve())
      }
    });
  });

  afterEach(() => {
    cleanup();
  });

  const renderComponent = (props = {}) => {
    const defaultProps = {
      recommendations: mockRecommendations,
      loading: false,
      error: null,
      onRefresh: vi.fn(),
      onNavigateToTransactions: vi.fn()
    };

    return render(
      <StrategyRecommendationsCard {...defaultProps} {...props} />
    );
  };

  it('should render alignment score', () => {
    renderComponent();
    expect(screen.getByText(/portfolio alignment score/i)).toBeInTheDocument();
    // AlignmentScoreGauge component should be present (score is rendered in SVG)
    const card = document.querySelector('.alignment-section');
    expect(card).toBeInTheDocument();
  });

  it('should render key insights', () => {
    renderComponent();
    expect(screen.getByText(/portfolio is well-diversified/i)).toBeInTheDocument();
    expect(screen.getByText(/tech sector exposure/i)).toBeInTheDocument();
    expect(screen.getByText(/consider profit-taking/i)).toBeInTheDocument();
  });

  it('should render profit-taking opportunities table', () => {
    renderComponent();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('35.5%')).toBeInTheDocument();
    expect(screen.getByText('20.0%')).toBeInTheDocument();
    expect(screen.getByText('TAKE_PROFIT')).toBeInTheDocument();
    expect(screen.getByText(/50 × \$180.50/)).toBeInTheDocument();
    expect(screen.getByText('$9,025.00')).toBeInTheDocument();
  });

  it('should copy transaction data to clipboard', async () => {
    renderComponent();
    const copyButton = screen.getByRole('button', { name: /copy/i });

    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        expect.stringContaining('"transaction_type": "SELL"')
      );
    });
  });

  it('should navigate to transaction form with prefill data', () => {
    const onNavigateToTransactions = vi.fn();
    renderComponent({ onNavigateToTransactions });

    // Find the create button by title attribute
    const createButtons = document.querySelectorAll('button[title="Create transaction"]');
    expect(createButtons.length).toBeGreaterThan(0);

    fireEvent.click(createButtons[0]);

    // Should store data in localStorage
    const stored = localStorage.getItem('transaction_prefill_data');
    expect(stored).toBeTruthy();
    const parsed = JSON.parse(stored!);
    expect(parsed).toEqual(mockRecommendations.profit_taking_opportunities[0].transaction_details);

    // Should call navigation callback
    expect(onNavigateToTransactions).toHaveBeenCalled();
  });

  it('should toggle planned status in localStorage', () => {
    renderComponent();
    const plannedButtons = document.querySelectorAll('button[title*="planned"]');
    expect(plannedButtons.length).toBeGreaterThan(0);

    // Mark as planned
    fireEvent.click(plannedButtons[0]);

    const saved = localStorage.getItem('planned_strategy_transactions');
    expect(saved).toBeTruthy();
    const parsed = JSON.parse(saved!);
    expect(parsed).toContain('AAPL-SELL-50');

    // Unmark
    fireEvent.click(plannedButtons[0]);

    const savedAfter = localStorage.getItem('planned_strategy_transactions');
    const parsedAfter = JSON.parse(savedAfter!);
    expect(parsedAfter).not.toContain('AAPL-SELL-50');
  });

  it('should show checkmark when transaction is planned', () => {
    localStorage.setItem('planned_strategy_transactions', JSON.stringify(['AAPL-SELL-50']));

    renderComponent();

    const plannedButtons = document.querySelectorAll('button[title*="planned"]');
    expect(plannedButtons.length).toBeGreaterThan(0);
    expect(plannedButtons[0]).toHaveClass('planned');
  });

  it('should render position assessments with color-coded actions', () => {
    renderComponent();

    expect(screen.getByText('GOOGL')).toBeInTheDocument();
    expect(screen.getByText('HOLD')).toBeInTheDocument();
    expect(screen.getByText(/aligns with growth objective/i)).toBeInTheDocument();

    expect(screen.getByText('TSLA')).toBeInTheDocument();
    expect(screen.getByText('CLOSE')).toBeInTheDocument();
    expect(screen.getByText(/listed in excluded assets/i)).toBeInTheDocument();
  });

  it('should render new position suggestions', () => {
    renderComponent();

    expect(screen.getByText('Tech Growth')).toBeInTheDocument();
    expect(screen.getByText(/MSFT, NVDA/)).toBeInTheDocument();
    expect(screen.getByText(/complement existing tech holdings/i)).toBeInTheDocument();
  });

  it('should render action plan accordion', () => {
    renderComponent();

    // Check for action plan section
    expect(screen.getByText(/action plan/i)).toBeInTheDocument();

    // Immediate actions section should be visible (default expanded)
    expect(screen.getByText(/immediate actions/i)).toBeInTheDocument();
    expect(screen.getByText(/take profit on aapl/i)).toBeInTheDocument();
  });

  it('should export all actions to CSV', () => {
    const createElementSpy = vi.spyOn(document, 'createElement');
    const clickSpy = vi.fn();
    const appendChildSpy = vi.spyOn(document.body, 'appendChild');
    const removeChildSpy = vi.spyOn(document.body, 'removeChild');

    createElementSpy.mockReturnValue({
      click: clickSpy,
      setAttribute: vi.fn(),
      style: {},
      href: '',
      download: ''
    } as any);

    renderComponent();

    const exportButton = screen.getByText(/export all actions/i);
    fireEvent.click(exportButton);

    expect(createElementSpy).toHaveBeenCalledWith('a');
    expect(clickSpy).toHaveBeenCalled();
  });

  it('should render next review date', () => {
    renderComponent();
    expect(screen.getByText(/next review: february 1, 2025/i)).toBeInTheDocument();
  });

  it('should render loading state', () => {
    renderComponent({ loading: true, recommendations: null });
    expect(screen.getByText(/loading recommendations/i)).toBeInTheDocument();
  });

  it('should render error state', () => {
    renderComponent({ error: 'Failed to load', recommendations: null });
    expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
  });

  it('should call onRefresh when refresh button clicked', () => {
    const onRefresh = vi.fn();
    renderComponent({ onRefresh });

    const refreshButton = screen.getByText(/refresh/i);
    fireEvent.click(refreshButton);

    expect(onRefresh).toHaveBeenCalled();
  });

  it('should render empty state when no recommendations', () => {
    renderComponent({ recommendations: null });
    expect(screen.getByText(/no recommendations available/i)).toBeInTheDocument();
  });
});
