// ABOUTME: Transaction list component with filtering, editing, and deletion
// ABOUTME: Displays manual and imported transactions with audit trail access

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { usePortfolioRefresh } from '../contexts/PortfolioRefreshContext';
import { TransactionForm } from './TransactionForm';
import type { Transaction } from './TransactionForm';
import './TransactionList.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface TransactionListItem extends Transaction {
  id: number;
  created_at: string;
  source: string;
  source_file?: string;
  deleted_at?: string;
  total_amount?: number;
}

interface AuditEntry {
  id: number;
  transaction_id: number;
  changed_at: string;
  changed_by: string;
  action: string;
  old_values?: any;
  new_values?: any;
  change_reason?: string;
}

export const TransactionList: React.FC = () => {
  const { triggerRefresh } = usePortfolioRefresh();
  const [transactions, setTransactions] = useState<TransactionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<Transaction | undefined>();
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [expandedAudit, setExpandedAudit] = useState<number | null>(null);
  const [auditHistory, setAuditHistory] = useState<Record<number, AuditEntry[]>>({});
  const [loadingAudit, setLoadingAudit] = useState<Record<number, boolean>>({});

  // Filters
  const [filters, setFilters] = useState({
    symbol: '',
    asset_type: '',
    transaction_type: '',
    source: '',
    include_deleted: false
  });

  useEffect(() => {
    fetchTransactions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  // Check for prefill data from rebalancing on mount
  useEffect(() => {
    const prefillData = sessionStorage.getItem('transaction_prefill')
    if (prefillData) {
      try {
        const data = JSON.parse(prefillData)
        setEditingTransaction(data as Transaction)
        setFormMode('create')
        setIsFormOpen(true)
        // Clear the prefill data after using it
        sessionStorage.removeItem('transaction_prefill')
      } catch (err) {
        console.error('Error parsing prefill data:', err)
      }
    }
  }, []);

  const fetchTransactions = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (filters.symbol) params.append('symbol', filters.symbol);
      if (filters.asset_type) params.append('asset_type', filters.asset_type);
      if (filters.transaction_type) params.append('transaction_type', filters.transaction_type);
      if (filters.source) params.append('source', filters.source);
      params.append('include_deleted', filters.include_deleted.toString());
      params.append('limit', '500');

      const response = await axios.get(`${API_URL}/api/transactions?${params.toString()}`);
      setTransactions(response.data);

      // Trigger portfolio refresh to update OpenPositionsCard and HoldingsTable
      console.log('[TransactionList] Transaction data updated, triggering portfolio refresh');
      triggerRefresh();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load transactions');
      console.error('Error loading transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClick = () => {
    setFormMode('create');
    setEditingTransaction(undefined);
    setIsFormOpen(true);
  };

  const handleEditClick = (transaction: TransactionListItem) => {
    setFormMode('edit');
    setEditingTransaction(transaction);
    setIsFormOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this transaction? You can restore it within 24 hours.')) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/api/transactions/${id}`);
      fetchTransactions();
    } catch (err: any) {
      alert(err.response?.data?.detail?.message || 'Failed to delete transaction');
    }
  };

  const handleRestore = async (id: number) => {
    try {
      await axios.post(`${API_URL}/api/transactions/${id}/restore`);
      fetchTransactions();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to restore transaction');
    }
  };

  const toggleAuditHistory = async (id: number) => {
    if (expandedAudit === id) {
      setExpandedAudit(null);
      return;
    }

    if (auditHistory[id]) {
      setExpandedAudit(id);
      return;
    }

    setLoadingAudit(prev => ({ ...prev, [id]: true }));

    try {
      const response = await axios.get(`${API_URL}/api/transactions/${id}/history`);
      setAuditHistory(prev => ({ ...prev, [id]: response.data }));
      setExpandedAudit(id);
    } catch (err) {
      console.error('Failed to load audit history:', err);
    } finally {
      setLoadingAudit(prev => ({ ...prev, [id]: false }));
    }
  };

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = type === 'checkbox' ? (e.target as HTMLInputElement).checked : undefined;

    setFilters(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const clearFilters = () => {
    setFilters({
      symbol: '',
      asset_type: '',
      transaction_type: '',
      source: '',
      include_deleted: false
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatNumber = (value: string | number) => {
    return parseFloat(value.toString()).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 8
    });
  };

  const getTransactionTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      BUY: 'badge-green',
      SELL: 'badge-red',
      DIVIDEND: 'badge-blue',
      STAKING: 'badge-purple',
      AIRDROP: 'badge-yellow',
      MINING: 'badge-orange',
      DEPOSIT: 'badge-blue',
      WITHDRAWAL: 'badge-red'
    };

    return <span className={`badge ${colors[type] || 'badge-gray'}`}>{type}</span>;
  };

  const getSourceBadge = (source: string) => {
    return source === 'MANUAL' ? (
      <span className="badge badge-manual">✏️ Manual</span>
    ) : (
      <span className="badge badge-csv">📄 CSV</span>
    );
  };

  if (loading && transactions.length === 0) {
    return <div className="transactions-loading">Loading transactions...</div>;
  }

  return (
    <div className="transactions-container">
      <div className="transactions-header">
        <div className="header-title">
          <h2>Transaction Management</h2>
          <span className="transaction-count">{transactions.length} transactions</span>
        </div>
        <button className="btn btn-primary" onClick={handleCreateClick}>
          ➕ Create Manual Transaction
        </button>
      </div>

      {/* Filters */}
      <div className="transactions-filters">
        <input
          type="text"
          name="symbol"
          placeholder="Filter by symbol..."
          value={filters.symbol}
          onChange={handleFilterChange}
          className="filter-input"
        />

        <select name="asset_type" value={filters.asset_type} onChange={handleFilterChange}>
          <option value="">All Asset Types</option>
          <option value="STOCK">Stocks</option>
          <option value="CRYPTO">Crypto</option>
          <option value="METAL">Metals</option>
        </select>

        <select name="transaction_type" value={filters.transaction_type} onChange={handleFilterChange}>
          <option value="">All Transaction Types</option>
          <option value="BUY">Buy</option>
          <option value="SELL">Sell</option>
          <option value="DIVIDEND">Dividend</option>
          <option value="STAKING">Staking</option>
          <option value="AIRDROP">Airdrop</option>
          <option value="MINING">Mining</option>
        </select>

        <select name="source" value={filters.source} onChange={handleFilterChange}>
          <option value="">All Sources</option>
          <option value="MANUAL">Manual</option>
          <option value="CSV">CSV Import</option>
        </select>

        <label className="filter-checkbox">
          <input
            type="checkbox"
            name="include_deleted"
            checked={filters.include_deleted}
            onChange={handleFilterChange}
          />
          Show Deleted
        </label>

        {(filters.symbol || filters.asset_type || filters.transaction_type || filters.source) && (
          <button className="btn-clear-filters" onClick={clearFilters}>
            Clear Filters
          </button>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Transaction Table */}
      <div className="transactions-table-container">
        <table className="transactions-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Symbol</th>
              <th>Type</th>
              <th>Quantity</th>
              <th>Price</th>
              <th>Fee</th>
              <th>Total</th>
              <th>Source</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 ? (
              <tr>
                <td colSpan={9} className="no-data">
                  No transactions found. Create your first manual transaction!
                </td>
              </tr>
            ) : (
              transactions.map(txn => (
                <React.Fragment key={txn.id}>
                  <tr className={txn.deleted_at ? 'deleted-row' : ''}>
                    <td>{formatDate(txn.transaction_date)}</td>
                    <td>
                      <strong>{txn.symbol}</strong>
                      <span className="asset-type">{txn.asset_type}</span>
                    </td>
                    <td>{getTransactionTypeBadge(txn.transaction_type)}</td>
                    <td className="number">{formatNumber(txn.quantity)}</td>
                    <td className="number">
                      {txn.price_per_unit ? `${txn.currency} ${formatNumber(txn.price_per_unit)}` : '-'}
                    </td>
                    <td className="number">{txn.fee ? formatNumber(txn.fee) : '-'}</td>
                    <td className="number">
                      {txn.total_amount ? `${txn.currency} ${formatNumber(txn.total_amount)}` : '-'}
                    </td>
                    <td>{getSourceBadge(txn.source)}</td>
                    <td className="actions">
                      {!txn.deleted_at ? (
                        <>
                          {txn.source === 'MANUAL' && (
                            <button
                              className="btn-icon btn-edit"
                              onClick={() => handleEditClick(txn)}
                              title="Edit"
                            >
                              ✏️
                            </button>
                          )}
                          <button
                            className="btn-icon btn-history"
                            onClick={() => toggleAuditHistory(txn.id)}
                            title="View History"
                          >
                            {expandedAudit === txn.id ? '📖' : '📜'}
                          </button>
                          <button
                            className="btn-icon btn-delete"
                            onClick={() => handleDelete(txn.id)}
                            title="Delete"
                          >
                            🗑️
                          </button>
                        </>
                      ) : (
                        <button
                          className="btn-icon btn-restore"
                          onClick={() => handleRestore(txn.id)}
                          title="Restore"
                        >
                          ↩️
                        </button>
                      )}
                    </td>
                  </tr>

                  {/* Audit History Row */}
                  {expandedAudit === txn.id && (
                    <tr className="audit-row">
                      <td colSpan={9}>
                        <div className="audit-history">
                          <h4>Transaction History</h4>
                          {loadingAudit[txn.id] ? (
                            <div className="audit-loading">Loading history...</div>
                          ) : auditHistory[txn.id]?.length > 0 ? (
                            <div className="audit-entries">
                              {auditHistory[txn.id].map(entry => (
                                <div key={entry.id} className="audit-entry">
                                  <div className="audit-header">
                                    <span className={`audit-action audit-${entry.action.toLowerCase()}`}>
                                      {entry.action}
                                    </span>
                                    <span className="audit-meta">
                                      {formatDate(entry.changed_at)} by {entry.changed_by}
                                    </span>
                                  </div>
                                  {entry.change_reason && (
                                    <div className="audit-reason">{entry.change_reason}</div>
                                  )}
                                  {entry.old_values && entry.new_values && (
                                    <div className="audit-changes">
                                      <details>
                                        <summary>View Changes</summary>
                                        <pre>{JSON.stringify({ old: entry.old_values, new: entry.new_values }, null, 2)}</pre>
                                      </details>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="no-audit">No history available</div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Transaction Form Modal */}
      <TransactionForm
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSuccess={fetchTransactions}
        transaction={editingTransaction}
        mode={formMode}
      />
    </div>
  );
};

export default TransactionList;
