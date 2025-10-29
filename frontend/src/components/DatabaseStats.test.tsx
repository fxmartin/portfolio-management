// ABOUTME: Unit tests for the DatabaseStats component
// ABOUTME: Tests display, formatting, auto-refresh, and error handling

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import DatabaseStats from './DatabaseStats';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Mock axios
vi.mock('axios');
const mockedAxios = axios as vi.Mocked<typeof axios>;

describe('DatabaseStats', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should not render when isOpen is false', () => {
    render(<DatabaseStats isOpen={false} onClose={mockOnClose} />);
    expect(screen.queryByText('Database Statistics')).not.toBeInTheDocument();
  });

  it('should render modal when isOpen is true', () => {
    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);
    expect(screen.getByText('📊 Database Statistics')).toBeInTheDocument();
  });

  it('should fetch stats when modal opens', async () => {
    const mockStats = {
      transactions: {
        total: 100,
        byAssetType: { STOCK: 50, CRYPTO: 30, METAL: 20 },
        byTransactionType: { BUY: 60, SELL: 40 },
        dateRange: {
          earliest: '2023-01-01T00:00:00',
          latest: '2023-12-31T23:59:59',
        },
      },
      symbols: {
        total: 15,
        topSymbols: [
          { symbol: 'AAPL', count: 20 },
          { symbol: 'BTC', count: 15 },
        ],
      },
      database: {
        tablesCount: {
          transactions: 100,
          positions: 15,
          price_history: 500,
          portfolio_snapshots: 30,
        },
        totalRecords: 645,
        isHealthy: true,
        lastImport: '2023-12-31T12:00:00',
      },
    };

    mockedAxios.get.mockResolvedValueOnce({ data: mockStats });

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/database/stats/detailed')
      );
    });

    await waitFor(() => {
      // Check that the data was rendered (using getAllByText for duplicated values)
      expect(screen.getAllByText('100').length).toBeGreaterThan(0);
      expect(screen.getAllByText('15').length).toBeGreaterThan(0);
      expect(screen.getByText('645')).toBeInTheDocument();
    });
  });

  it('should display error message when fetch fails', async () => {
    mockedAxios.get.mockRejectedValueOnce({
      response: { data: { detail: 'Database connection failed' } },
    });

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('Database connection failed')).toBeInTheDocument();
    });
  });

  it('should format numbers with thousand separators', async () => {
    const mockStats = {
      transactions: {
        total: 10000,
        byAssetType: {},
        byTransactionType: {},
        dateRange: {},
      },
      symbols: { total: 0, topSymbols: [] },
      database: {
        tablesCount: {},
        totalRecords: 50000,
        isHealthy: true,
      },
    };

    mockedAxios.get.mockResolvedValueOnce({ data: mockStats });

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('10,000')).toBeInTheDocument();
      expect(screen.getByText('50,000')).toBeInTheDocument();
    });
  });

  it('should display healthy status correctly', async () => {
    const mockStats = {
      transactions: { total: 0, byAssetType: {}, byTransactionType: {}, dateRange: {} },
      symbols: { total: 0, topSymbols: [] },
      database: {
        tablesCount: {},
        totalRecords: 0,
        isHealthy: true,
      },
    };

    mockedAxios.get.mockResolvedValueOnce({ data: mockStats });

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('✅ Healthy')).toBeInTheDocument();
    });
  });

  it('should display unhealthy status correctly', async () => {
    const mockStats = {
      transactions: { total: 0, byAssetType: {}, byTransactionType: {}, dateRange: {} },
      symbols: { total: 0, topSymbols: [] },
      database: {
        tablesCount: {},
        totalRecords: 0,
        isHealthy: false,
      },
    };

    mockedAxios.get.mockResolvedValueOnce({ data: mockStats });

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('❌ Unhealthy')).toBeInTheDocument();
    });
  });

  it('should call onClose when close button is clicked', () => {
    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    const closeButton = screen.getByRole('button', { name: '×' });
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should call onClose when overlay is clicked', () => {
    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    const overlay = screen.getByTestId('modal-overlay');
    fireEvent.click(overlay);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it('should not call onClose when modal content is clicked', () => {
    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    const modalContent = screen.getByText('📊 Database Statistics');
    fireEvent.click(modalContent);

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('should refresh data when refresh button is clicked', async () => {
    const mockStats = {
      transactions: { total: 100, byAssetType: {}, byTransactionType: {}, dateRange: {} },
      symbols: { total: 0, topSymbols: [] },
      database: { tablesCount: {}, totalRecords: 100, isHealthy: true },
    };

    mockedAxios.get.mockResolvedValue({ data: mockStats });

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getAllByText('100').length).toBeGreaterThan(0);
    });

    // Clear previous calls
    mockedAxios.get.mockClear();

    // Click refresh button
    const refreshButton = screen.getByText('🔄 Refresh');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/database/stats/detailed')
      );
    });
  });

  it('should toggle auto-refresh checkbox', async () => {
    const mockStats = {
      transactions: { total: 0, byAssetType: {}, byTransactionType: {}, dateRange: {} },
      symbols: { total: 0, topSymbols: [] },
      database: { tablesCount: {}, totalRecords: 0, isHealthy: true },
    };

    mockedAxios.get.mockResolvedValue({ data: mockStats });

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} autoRefresh={false} />);

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalled();
    });

    // Check initial state
    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();

    // Toggle checkbox
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();

    // Toggle back
    fireEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });

  it('should display asset type breakdown with icons', async () => {
    const mockStats = {
      transactions: {
        total: 0,
        byAssetType: {
          METAL: 10,
          STOCK: 20,
          CRYPTO: 30,
        },
        byTransactionType: {},
        dateRange: {},
      },
      symbols: { total: 0, topSymbols: [] },
      database: { tablesCount: {}, totalRecords: 0, isHealthy: true },
    };

    mockedAxios.get.mockResolvedValueOnce({ data: mockStats });

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('🏆 METAL')).toBeInTheDocument();
      expect(screen.getByText('📈 STOCK')).toBeInTheDocument();
      expect(screen.getByText('₿ CRYPTO')).toBeInTheDocument();
    });
  });

  it('should display top symbols correctly', async () => {
    const mockStats = {
      transactions: { total: 0, byAssetType: {}, byTransactionType: {}, dateRange: {} },
      symbols: {
        total: 5,
        topSymbols: [
          { symbol: 'AAPL', count: 50 },
          { symbol: 'BTC', count: 30 },
          { symbol: 'XAU', count: 20 },
        ],
      },
      database: { tablesCount: {}, totalRecords: 0, isHealthy: true },
    };

    mockedAxios.get.mockResolvedValueOnce({ data: mockStats });

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText('#1')).toBeInTheDocument();
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('50 txns')).toBeInTheDocument();

      expect(screen.getByText('#2')).toBeInTheDocument();
      expect(screen.getByText('BTC')).toBeInTheDocument();
      expect(screen.getByText('30 txns')).toBeInTheDocument();

      expect(screen.getByText('#3')).toBeInTheDocument();
      expect(screen.getByText('XAU')).toBeInTheDocument();
      expect(screen.getByText('20 txns')).toBeInTheDocument();
    });
  });

  it('should format dates correctly', async () => {
    const mockStats = {
      transactions: {
        total: 0,
        byAssetType: {},
        byTransactionType: {},
        dateRange: {
          earliest: '2023-01-15T10:30:00',
          latest: '2023-12-31T23:59:59',
        },
      },
      symbols: { total: 0, topSymbols: [] },
      database: {
        tablesCount: {},
        totalRecords: 0,
        isHealthy: true,
        lastImport: '2023-12-31T15:30:45',
      },
    };

    mockedAxios.get.mockResolvedValueOnce({ data: mockStats });

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    await waitFor(() => {
      // Check that dates are formatted
      const dateElements = screen.getAllByText(/2023/);
      expect(dateElements.length).toBeGreaterThan(0);
    });
  });

  it('should display last refresh timestamp', async () => {
    const mockStats = {
      transactions: { total: 0, byAssetType: {}, byTransactionType: {}, dateRange: {} },
      symbols: { total: 0, topSymbols: [] },
      database: { tablesCount: {}, totalRecords: 0, isHealthy: true },
    };

    mockedAxios.get.mockResolvedValueOnce({ data: mockStats });

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });
  });

  it('should disable refresh button while loading', async () => {
    // Create a promise that we can control
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockedAxios.get.mockReturnValue(promise);

    render(<DatabaseStats isOpen={true} onClose={mockOnClose} />);

    // Button should be loading
    await waitFor(() => {
      const refreshButton = screen.getByText('🔄 Refresh');
      expect(refreshButton).toBeDisabled();
    });

    // Resolve the promise
    resolvePromise!({ data: {
      transactions: { total: 0, byAssetType: {}, byTransactionType: {}, dateRange: {} },
      symbols: { total: 0, topSymbols: [] },
      database: { tablesCount: {}, totalRecords: 0, isHealthy: true },
    }});

    // Button should be enabled again
    await waitFor(() => {
      const refreshButton = screen.getByText('🔄 Refresh');
      expect(refreshButton).not.toBeDisabled();
    });
  });
});