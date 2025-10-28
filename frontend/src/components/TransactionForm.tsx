// ABOUTME: Form component for creating and editing manual transactions
// ABOUTME: Supports all transaction types with validation and symbol autocomplete

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Modal } from './Modal';
import './TransactionForm.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Export Transaction interface for use in other components
export interface Transaction {
  id?: number;
  transaction_date: string;
  asset_type: 'STOCK' | 'CRYPTO' | 'METAL';
  transaction_type: 'BUY' | 'SELL' | 'STAKING' | 'AIRDROP' | 'MINING' | 'DEPOSIT' | 'WITHDRAWAL' | 'DIVIDEND';
  symbol: string;
  quantity: string | number;
  price_per_unit?: string | number;
  fee?: string | number;
  currency: string;
  notes?: string;
}

interface ValidationMessage {
  level: 'error' | 'warning' | 'info';
  message: string;
  field?: string;
  suggestion?: string;
}

interface TransactionFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  transaction?: Transaction;
  mode: 'create' | 'edit';
}

export const TransactionForm: React.FC<TransactionFormProps> = ({
  isOpen,
  onClose,
  onSuccess,
  transaction,
  mode
}) => {
  const [formData, setFormData] = useState<Transaction>({
    transaction_date: new Date().toISOString().slice(0, 16),
    asset_type: 'STOCK',
    transaction_type: 'BUY',
    symbol: '',
    quantity: '',
    price_per_unit: '',
    fee: 0,
    currency: 'EUR',
    notes: ''
  });

  const [errors, setErrors] = useState<ValidationMessage[]>([]);
  const [warnings, setWarnings] = useState<ValidationMessage[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [symbols, setSymbols] = useState<string[]>([]);
  const [showSymbolSuggestions, setShowSymbolSuggestions] = useState(false);

  // Load transaction data when editing
  useEffect(() => {
    if (mode === 'edit' && transaction) {
      setFormData({
        ...transaction,
        transaction_date: transaction.transaction_date.slice(0, 16),
        quantity: transaction.quantity.toString(),
        price_per_unit: transaction.price_per_unit?.toString() || '',
        fee: transaction.fee?.toString() || '0'
      });
    }
  }, [mode, transaction]);

  // Load existing symbols for autocomplete
  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/portfolio/positions`);
        const uniqueSymbols = [...new Set(response.data.map((p: any) => p.symbol))];
        setSymbols(uniqueSymbols);
      } catch (error) {
        console.error('Failed to load symbols:', error);
      }
    };
    fetchSymbols();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Clear field-specific errors
    setErrors(prev => prev.filter(err => err.field !== name));
  };

  const handleSymbolChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toUpperCase();
    setFormData(prev => ({ ...prev, symbol: value }));
    setShowSymbolSuggestions(value.length > 0);
    setErrors(prev => prev.filter(err => err.field !== 'symbol'));
  };

  const selectSymbol = (symbol: string) => {
    setFormData(prev => ({ ...prev, symbol }));
    setShowSymbolSuggestions(false);
  };

  const validateForm = async (): Promise<boolean> => {
    setErrors([]);
    setWarnings([]);

    try {
      const response = await axios.post(`${API_URL}/api/transactions/validate`, formData);

      const validationMessages = response.data.messages || [];
      const errorMessages = validationMessages.filter((m: ValidationMessage) => m.level === 'error');
      const warningMessages = validationMessages.filter((m: ValidationMessage) => m.level === 'warning');

      setErrors(errorMessages);
      setWarnings(warningMessages);

      return response.data.valid;
    } catch (error: any) {
      if (error.response?.data?.detail?.errors) {
        setErrors(error.response.data.detail.errors);
      } else {
        setErrors([{ level: 'error', message: 'Validation failed. Please check your inputs.' }]);
      }
      return false;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Validate first
      const isValid = await validateForm();
      if (!isValid) {
        setIsSubmitting(false);
        return;
      }

      // Submit transaction
      if (mode === 'create') {
        await axios.post(`${API_URL}/api/transactions`, formData);
      } else if (mode === 'edit' && transaction?.id) {
        await axios.put(`${API_URL}/api/transactions/${transaction.id}`, formData);
      }

      onSuccess();
      onClose();
      resetForm();
    } catch (error: any) {
      if (error.response?.data?.detail?.errors) {
        setErrors(error.response.data.detail.errors);
      } else if (error.response?.data?.detail?.message) {
        setErrors([{ level: 'error', message: error.response.data.detail.message }]);
      } else {
        setErrors([{ level: 'error', message: 'Failed to save transaction. Please try again.' }]);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      transaction_date: new Date().toISOString().slice(0, 16),
      asset_type: 'STOCK',
      transaction_type: 'BUY',
      symbol: '',
      quantity: '',
      price_per_unit: '',
      fee: 0,
      currency: 'EUR',
      notes: ''
    });
    setErrors([]);
    setWarnings([]);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const filteredSymbols = symbols.filter(s =>
    s.toUpperCase().includes(formData.symbol.toUpperCase())
  ).slice(0, 5);

  const requiresPrice = ['BUY', 'SELL'].includes(formData.transaction_type);

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={mode === 'create' ? 'Create Manual Transaction' : 'Edit Transaction'}
      className="transaction-form-modal"
    >
      <form onSubmit={handleSubmit} className="transaction-form">
        {/* Error Messages */}
        {errors.length > 0 && (
          <div className="form-messages error-messages">
            {errors.map((error, idx) => (
              <div key={idx} className="form-message error">
                <span className="message-icon">⚠️</span>
                <div>
                  <strong>{error.field ? `${error.field}: ` : ''}</strong>
                  {error.message}
                  {error.suggestion && (
                    <div className="message-suggestion">{error.suggestion}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Warning Messages */}
        {warnings.length > 0 && (
          <div className="form-messages warning-messages">
            {warnings.map((warning, idx) => (
              <div key={idx} className="form-message warning">
                <span className="message-icon">⚡</span>
                <div>
                  <strong>{warning.field ? `${warning.field}: ` : ''}</strong>
                  {warning.message}
                  {warning.suggestion && (
                    <div className="message-suggestion">{warning.suggestion}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Form Fields */}
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="asset_type">Asset Type *</label>
            <select
              id="asset_type"
              name="asset_type"
              value={formData.asset_type}
              onChange={handleChange}
              required
              disabled={mode === 'edit'}
            >
              <option value="STOCK">Stock 📈</option>
              <option value="CRYPTO">Crypto 💰</option>
              <option value="METAL">Metal 🥇</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="transaction_type">Transaction Type *</label>
            <select
              id="transaction_type"
              name="transaction_type"
              value={formData.transaction_type}
              onChange={handleChange}
              required
              disabled={mode === 'edit'}
            >
              <option value="BUY">Buy</option>
              <option value="SELL">Sell</option>
              <option value="DIVIDEND">Dividend</option>
              <option value="STAKING">Staking Reward</option>
              <option value="AIRDROP">Airdrop</option>
              <option value="MINING">Mining</option>
              <option value="DEPOSIT">Deposit</option>
              <option value="WITHDRAWAL">Withdrawal</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group symbol-group">
            <label htmlFor="symbol">Symbol *</label>
            <input
              type="text"
              id="symbol"
              name="symbol"
              value={formData.symbol}
              onChange={handleSymbolChange}
              onFocus={() => setShowSymbolSuggestions(formData.symbol.length > 0)}
              onBlur={() => setTimeout(() => setShowSymbolSuggestions(false), 200)}
              placeholder="e.g., AAPL, BTC, XAU"
              required
              disabled={mode === 'edit'}
              autoComplete="off"
            />
            {showSymbolSuggestions && filteredSymbols.length > 0 && (
              <div className="symbol-suggestions">
                {filteredSymbols.map(symbol => (
                  <div
                    key={symbol}
                    className="symbol-suggestion"
                    onClick={() => selectSymbol(symbol)}
                  >
                    {symbol}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="transaction_date">Date & Time *</label>
            <input
              type="datetime-local"
              id="transaction_date"
              name="transaction_date"
              value={formData.transaction_date}
              onChange={handleChange}
              max={new Date().toISOString().slice(0, 16)}
              required
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="quantity">Quantity *</label>
            <input
              type="number"
              id="quantity"
              name="quantity"
              value={formData.quantity}
              onChange={handleChange}
              step="any"
              min="0.00000001"
              placeholder="0.00"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="price_per_unit">
              Price per Unit {requiresPrice && '*'}
            </label>
            <input
              type="number"
              id="price_per_unit"
              name="price_per_unit"
              value={formData.price_per_unit}
              onChange={handleChange}
              step="any"
              min="0"
              placeholder="0.00"
              required={requiresPrice}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="fee">Fee</label>
            <input
              type="number"
              id="fee"
              name="fee"
              value={formData.fee}
              onChange={handleChange}
              step="any"
              min="0"
              placeholder="0.00"
            />
          </div>

          <div className="form-group">
            <label htmlFor="currency">Currency *</label>
            <select
              id="currency"
              name="currency"
              value={formData.currency}
              onChange={handleChange}
              required
            >
              <option value="EUR">EUR (€)</option>
              <option value="USD">USD ($)</option>
              <option value="GBP">GBP (£)</option>
              <option value="JPY">JPY (¥)</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows={3}
            maxLength={500}
            placeholder="Optional notes about this transaction..."
          />
          <div className="character-count">
            {formData.notes?.length || 0}/500 characters
          </div>
        </div>

        {/* Form Actions */}
        <div className="form-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <span className="spinner"></span>
                {mode === 'create' ? 'Creating...' : 'Saving...'}
              </>
            ) : (
              mode === 'create' ? 'Create Transaction' : 'Save Changes'
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
