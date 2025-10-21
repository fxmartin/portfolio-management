// ABOUTME: React component for displaying database statistics dashboard
// ABOUTME: Shows transaction counts, breakdowns, and database health info

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './DatabaseStats.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface DatabaseStatsData {
  transactions: {
    total: number;
    byAssetType: Record<string, number>;
    byTransactionType: Record<string, number>;
    dateRange: {
      earliest?: string;
      latest?: string;
    };
  };
  symbols: {
    total: number;
    topSymbols: Array<{ symbol: string; count: number }>;
  };
  database: {
    tablesCount: Record<string, number>;
    totalRecords: number;
    isHealthy: boolean;
    lastImport?: string;
  };
}

interface DatabaseStatsProps {
  isOpen: boolean;
  onClose: () => void;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const DatabaseStats: React.FC<DatabaseStatsProps> = ({
  isOpen,
  onClose,
  autoRefresh = false,
  refreshInterval = 30000,
}) => {
  const [stats, setStats] = useState<DatabaseStatsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [isAutoRefreshing, setIsAutoRefreshing] = useState(autoRefresh);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API_URL}/api/database/stats/detailed`);
      setStats(response.data);
      setLastRefresh(new Date());
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch database statistics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchStats();
    }
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && isAutoRefreshing && refreshInterval > 0) {
      const interval = setInterval(fetchStats, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [isOpen, isAutoRefreshing, refreshInterval]);

  const formatNumber = (num: number): string => {
    return num.toLocaleString();
  };

  const formatDate = (dateStr: string | undefined): string => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getAssetTypeIcon = (type: string): string => {
    switch (type) {
      case 'METAL':
        return '🏆';
      case 'STOCK':
        return '📈';
      case 'CRYPTO':
        return '₿';
      default:
        return '📊';
    }
  };

  const getTransactionTypeIcon = (type: string): string => {
    switch (type) {
      case 'BUY':
        return '🛒';
      case 'SELL':
        return '💰';
      case 'DIVIDEND':
        return '💵';
      case 'STAKING':
        return '🔒';
      default:
        return '📋';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose} data-testid="modal-overlay">
      <div className="modal-content database-stats" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📊 Database Statistics</h2>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          {loading && !stats ? (
            <div className="loading">Loading statistics...</div>
          ) : error ? (
            <div className="error">{error}</div>
          ) : stats && stats.transactions && stats.symbols && stats.database ? (
            <div className="stats-container">
              {/* Overview Section */}
              <div className="stats-section">
                <h3>Overview</h3>
                <div className="stats-grid">
                  <div className="stat-card">
                    <div className="stat-label">Total Transactions</div>
                    <div className="stat-value">{formatNumber(stats.transactions.total)}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Unique Symbols</div>
                    <div className="stat-value">{formatNumber(stats.symbols.total)}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Total Records</div>
                    <div className="stat-value">{formatNumber(stats.database.totalRecords)}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Database Health</div>
                    <div className="stat-value">
                      {stats.database.isHealthy ? (
                        <span className="healthy">✅ Healthy</span>
                      ) : (
                        <span className="unhealthy">❌ Unhealthy</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Asset Type Breakdown */}
              <div className="stats-section">
                <h3>Transactions by Asset Type</h3>
                <div className="breakdown-list">
                  {Object.entries(stats.transactions.byAssetType).map(([type, count]) => (
                    <div key={type} className="breakdown-item">
                      <span className="breakdown-label">
                        {getAssetTypeIcon(type)} {type}
                      </span>
                      <span className="breakdown-value">{formatNumber(count)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Transaction Type Breakdown */}
              <div className="stats-section">
                <h3>Transactions by Type</h3>
                <div className="breakdown-list">
                  {Object.entries(stats.transactions.byTransactionType).map(([type, count]) => (
                    <div key={type} className="breakdown-item">
                      <span className="breakdown-label">
                        {getTransactionTypeIcon(type)} {type}
                      </span>
                      <span className="breakdown-value">{formatNumber(count)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Symbols */}
              <div className="stats-section">
                <h3>Top Symbols</h3>
                <div className="top-symbols">
                  {stats.symbols.topSymbols.map((item, index) => (
                    <div key={item.symbol} className="symbol-item">
                      <span className="symbol-rank">#{index + 1}</span>
                      <span className="symbol-name">{item.symbol}</span>
                      <span className="symbol-count">{formatNumber(item.count)} txns</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Date Range */}
              <div className="stats-section">
                <h3>Transaction Date Range</h3>
                <div className="date-range">
                  <div className="date-item">
                    <span className="date-label">Earliest:</span>
                    <span className="date-value">
                      {formatDate(stats.transactions.dateRange.earliest)}
                    </span>
                  </div>
                  <div className="date-item">
                    <span className="date-label">Latest:</span>
                    <span className="date-value">
                      {formatDate(stats.transactions.dateRange.latest)}
                    </span>
                  </div>
                  <div className="date-item">
                    <span className="date-label">Last Import:</span>
                    <span className="date-value">
                      {formatDate(stats.database.lastImport)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Table Counts */}
              <div className="stats-section">
                <h3>Database Tables</h3>
                <div className="table-counts">
                  {Object.entries(stats.database.tablesCount).map(([table, count]) => (
                    <div key={table} className="table-count-item">
                      <span className="table-name">{table}</span>
                      <span className="table-count">{formatNumber(count)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="loading">Waiting for data...</div>
          )}
        </div>

        <div className="modal-footer">
          <div className="footer-left">
            {lastRefresh && (
              <span className="last-refresh">
                Last updated: {lastRefresh.toLocaleTimeString()}
              </span>
            )}
          </div>
          <div className="footer-right">
            <label className="auto-refresh">
              <input
                type="checkbox"
                checked={isAutoRefreshing}
                onChange={(e) => setIsAutoRefreshing(e.target.checked)}
              />
              Auto-refresh (30s)
            </label>
            <button className="refresh-button" onClick={fetchStats} disabled={loading}>
              🔄 Refresh
            </button>
            <button className="close-modal-button" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DatabaseStats;